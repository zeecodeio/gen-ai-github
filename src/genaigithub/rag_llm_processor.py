from abc import ABC, abstractmethod
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS, Chroma, PGVector
from langchain_community.chat_models import ChatOpenAI
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.documents import Document
from typing import List, Dict, Any
from pymongo import MongoClient
import logging
from genaigithub.config.languages import LANGUAGE_MAPPING
from uuid import uuid4
from langchain_text_splitters import (
    Language,
    RecursiveCharacterTextSplitter,
)
from langchain.chains import (
    create_history_aware_retriever,
    create_retrieval_chain,
)

from langchain.chains.combine_documents import create_stuff_documents_chain

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class VectorStoreInterface(ABC):
    @abstractmethod
    def create_vector_store_from_documents(self, texts, embeddings):
        pass

    @abstractmethod
    def create_vector_store_from_texts(self, texts, embeddings):
        pass

    @abstractmethod
    def as_retriever(self):
        pass


class FAISSVectorStore(VectorStoreInterface):
    def create_vector_store_from_documents(self, texts, embeddings):
        return FAISS.from_documents(texts, embeddings)

    def create_vector_store_from_texts(self, texts, embeddings):
        return FAISS.from_texts(texts, embeddings)

    def as_retriever(self):
        return self.vector_store.as_retriever()


class ChromaVectorStore(VectorStoreInterface):
    def create_vector_store_from_documents(self, texts, embeddings):
        return Chroma.from_documents(texts, embeddings)

    def create_vector_store_from_texts(self, texts, embeddings):
        return Chroma.from_texts(texts, embeddings)

    def as_retriever(self):
        return self.vector_store.as_retriever()


class PGVectorStore(VectorStoreInterface):
    def __init__(self, connection_string):
        self.connection_string = connection_string
        self.vector_store = None

    def create_vector_store_from_documents(self, documents, embeddings):
        self.vector_store = PGVector.from_documents(
            documents, embeddings, connection_string=self.connection_string, collection_name="pr_changes"
        )
        return self.vector_store

    def create_vector_store_from_texts(self, pr_chuncks, embeddings):
        self.vector_store = PGVector.from_texts(
            pr_chuncks, embeddings, connection_string=self.connection_string, collection_name="pr_changes"
        )
        return self.vector_store

    def as_retriever(self):
        return self.vector_store.as_retriever()
    
    def cleanup(self):
        """Clean up the PostgreSQL vector store instance"""
        if self.vector_store:
            # Delete all entries in the collection
            self.vector_store.delete_collection()
            # Reset the instance
            self.vector_store = None


class MongoDBVectorStore(VectorStoreInterface):
    def __init__(self, connection_string):
        self.mongodb_database = "genaigithub"
        self.mongodb_collection = "pr_changes"
        self.atlas_vector_search_index_name = "pr-index-changes"
        self.connection_string = connection_string
        self.client = MongoClient(connection_string)
        self.collection = self.client[self.mongodb_database][self.mongodb_collection]

    def create_vector_store_from_documents(self, documents, embeddings):
        vector_store = MongoDBAtlasVectorSearch(
            collection=self.collection,
            embedding=embeddings,
            index_name=self.atlas_vector_search_index_name,
            relevance_score_fn="cosine",
        )
        uuids = [str(uuid4()) for _ in range(len(documents))]
        vector_store.add_documents(documents=documents, ids=uuids)
        return vector_store

    def create_vector_store_from_texts(self, texts, embeddings):
        return None

    def as_retriever(self):
        return self.vector_store.as_retriever()


class RAGLLMProcessor:
    def __init__(
        self,
        openai_api_key: str,
        vector_store: VectorStoreInterface,
        memory_key: str = "chat_history",
        model_name: str = "gpt-3.5-turbo",
    ):
        self.openai_api_key = openai_api_key
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        self.llm = ChatOpenAI(temperature=0, model_name=model_name, openai_api_key=openai_api_key)
        self.memory = ConversationBufferMemory(memory_key=memory_key, return_messages=True)
        self.vector_store = vector_store
        self.chat_history = []

    def create_vector_store_from_documents(self, documents: List[object]):
        logger.info("Creating vector store from documents")
        texts = [chunk["text"] for chunk in documents]
        metadatas = [chunk["metadata"] for chunk in documents]
        documents = self.text_splitter.create_documents(texts=texts, metadatas=metadatas)
        return self.vector_store.create_vector_store_from_documents(documents, embeddings=self.embeddings)

    def reset_memory(self):
        logger.info("Clearing memory for new session or PR")
        self.memory.clear()
        if self.vector_store:
            self.vector_store.cleanup()

    def get_chat_history(self):
        """Returns current chat history."""
        return self.memory.chat_memory.messages

    def reset_chat_history(self):
        self.chat_history = []

    def rebuild_chat_history(self, history):
        for message in history:
            self.chat_history.append(HumanMessage(content=message["question"]))
            self.chat_history.append(AIMessage(content=message["response"]))

    def create_qa_chain(self, retriever) -> ConversationalRetrievalChain:
        logger.info("Creating question-answering chain using the given vector store")
        system_prompt = """
        You are a tech leader, software architect, and PR reviewer assistant for question-answering tasks.
        Objective:
            - Automate the review process for pull requests.
            - Provide detailed and actionable feedback on code changes.
            - Identify potential bugs, security vulnerabilities, and coding standard violations.
            - Suggest improvements and best practices.
        Answer questions based strictly on the following context and provide clear, actionable responses.
                ---
                Context: {context}
                """
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", "{input}"),
            ]
        )
        combine_docs_chain = create_stuff_documents_chain(self.llm, self.prompt)

        contextualize_system_prompt = """
            Given a chat history and the latest user question, which might reference context in the chat history,
            reformulate the question into a standalone form that captures all relevant details, allowing it to be
            understood independently of prior conversation.
        """

        self.contextualize_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", contextualize_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )

        history_aware_retriever = create_history_aware_retriever(self.llm, retriever, self.contextualize_prompt)
        qa_chain = create_retrieval_chain(history_aware_retriever, combine_docs_chain)

        return qa_chain

    def process_files_data(self, files_data):
        chunks_with_metadata = []
        logger.info(f"Processing {len(files_data)} files")

        for file in files_data:
            # Split patch content using language-specific separators
            file_name = file["filename"]
            print(str(file))
            logger.info(f"Processing file: {file_name}")
            extension = file_name.split(".")[-1]
            language = LANGUAGE_MAPPING.get(extension, "python")
            patch_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                separators=RecursiveCharacterTextSplitter.get_separators_for_language(language),
            )
            patch_content = file.get("patch", "")
            patch_chunks = patch_splitter.split_text(patch_content)
            
            content = file.get("content", "")
            content_chunks = patch_splitter.split_text(content)

            # Convert other file attributes to a string and split (if needed)
            other_content = f"""
                File Name: {file.get('filename', '')}
                File Status: {file.get('status', '')}
                File Changes: {file.get('changes', '')}
                File Additions: {file.get('additions', '')}
                File Deletions: {file.get('deletions', '')}
            """
            other_chunks = self.text_splitter.split_text(other_content)

            # Combine patch and other content chunks
            for chunk in patch_chunks + other_chunks + content_chunks:
                chunks_with_metadata.append(
                    {
                        "text": chunk,
                        "metadata": {
                            "repo_name": file.get("repo_name", ""),
                            "pr_number": file.get("pr_number", ""),
                            "filename": file.get("filename", ""),
                            "status": file.get("status", ""),
                            "changes": file.get("changes", ""),
                            "additions": file.get("additions", ""),
                            "deletions": file.get("deletions", ""),
                        },
                    }
                )

        return chunks_with_metadata

    def process_commits_data(self, commits_data):
        chunks_with_metadata = []
        logger.info(f"Processing {len(commits_data)} commits")
        for commit in commits_data:
            content = f"""
                Commit ID: {commit.get('commit_id', '')}
                Commit Message: {commit.get('commit_message', '')}
                Commit Author: {commit.get('commit_author', '')}
                Commit Author Email: {commit.get('commit_author_email', '')}
                Commit Date: {commit.get('commit_date', '')}
            """

            chunks = self.text_splitter.split_text(content)

            for chunk in chunks:
                chunks_with_metadata.append(
                    {
                        "text": chunk,
                        "metadata": {
                            "repo_name": commit["repo_name"],
                            "pr_number": commit["pr_number"],
                            "commit_id": commit["commit_id"],
                            "commit_message": commit["commit_message"],
                            "commit_author": commit["commit_author"],
                            "commit_author_email": commit["commit_author_email"],
                            "commit_date": commit["commit_date"],
                        },
                    }
                )

        return chunks_with_metadata

    def process_pr_data(self, pr_data):
        chunks_with_metadata = []
        logger.info(f"Processing {len(pr_data)} PRs")
        for data in pr_data:
            content = f"""
                Repo Name: {data.get('repo_name', '')}
                PR Number: {data.get('pr_number', '')}
                Description: {data.get('description', '')}
                Changed Files: {data.get('changed_files', '')}
                Comments: {data.get('comments', '')}
            """
            chunks = self.text_splitter.split_text(content)

            for chunk in chunks:
                chunks_with_metadata.append(
                    {
                        "text": chunk,
                        "metadata": {
                            "repo_name": data["repo_name"],
                            "pr_number": data["pr_number"],
                            "description": data["description"],
                            "changed_files": data["changed_files"],
                            "comments": data["changed_files"],
                        },
                    }
                )

        return chunks_with_metadata

    def process_pr_files(self, pr_files: List[Dict[str, Any]]) -> List[str]:
        logger.info("Processing PR files and returning list of formatted strings")
        documents = []
        for file in pr_files:
            filename = file["filename"]
            content = file.get("content", "")
            patch = file.get("patch", "")
            document = f"Filename: {filename}\n\nContent:\n{content}\n\nPatch:\n{patch}"
            documents.append(document)
        return documents

    def log_prompt(self, prompt_content):
        logger.info("Logging each message in the constructed prompt")
        logger.info("Prompt used for qa_chain:")
        for message in prompt_content:
            logger.info(f"{message.type.capitalize()} message: {message.content}")

    def generate_response(self, qa_chain: ConversationalRetrievalChain, query: str, context) -> str:
        logger.info("Generating response using QA chain")
        prompt_content = self.contextualize_prompt.format_messages(chat_history=context, input=query)
        self.log_prompt(prompt_content)
        response = qa_chain.invoke({"input": query, "chat_history": context})["answer"]
        self.memory.save_context({"input": query}, {"output": response})
        return response

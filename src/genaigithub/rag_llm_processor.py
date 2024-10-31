from abc import ABC, abstractmethod
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS, Chroma, PGVector
from langchain_community.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage
from typing import List, Dict, Any
from langchain_text_splitters import (
    Language,
    RecursiveCharacterTextSplitter,
)
from langchain.chains import (
    create_history_aware_retriever,
    create_retrieval_chain,
)

from langchain.chains.combine_documents import create_stuff_documents_chain

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

    def create_vector_store_from_documents(self, documents, embeddings):
        return PGVector.from_documents(
            documents,
            embeddings,
            connection_string=self.connection_string,
            collection_name="pr_changes"
        )
        
        
    def create_vector_store_from_texts(self, pr_chuncks, embeddings):
        return PGVector.from_texts(
            pr_chuncks,
            embeddings,
            connection_string=self.connection_string,
            collection_name="pr_changes"
        )

    def as_retriever(self):
        return self.vector_store.as_retriever()

class RAGLLMProcessor:
    def __init__(self, openai_api_key: str, vector_store: VectorStoreInterface, memory_key: str = "chat_history", model_name: str = "gpt-3.5-turbo"):
        self.openai_api_key = openai_api_key
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        self.llm = ChatOpenAI(temperature=0, model_name=model_name, openai_api_key=openai_api_key)
        self.memory = ConversationBufferMemory(memory_key=memory_key, return_messages=True)
        self.vector_store = vector_store
        self.chat_history = []

    def create_vector_store_from_documents(self, documents: List[str]):
        """Create a vector store from the given documents."""
        texts = [chunk["text"] for chunk in documents]
        metadatas = [chunk["metadata"] for chunk in documents]
        documents = self.text_splitter.create_documents(texts=texts, metadatas=metadatas)
        return self.vector_store.create_vector_store_from_documents(documents, embeddings=self.embeddings)
    
    def reset_chat_history(self):
        self.chat_history = []
        
    def rebuild_chat_history(self, history):
        for message in history:
            self.chat_history.append(HumanMessage(content=message["question"]))
            self.chat_history.append(AIMessage(content=message["response"]))
    
    def create_qa_chain(self, retriever) -> ConversationalRetrievalChain:
        """Create a question-answering chain using the given vector store."""
        system_prompt = (
            "You are a tech leader, software architect and pr reviewer assistant for question-answering tasks."
            "Objective: - Automate the review process for pull requests. - Provide detailed and actionable feedback on code changes. - Identify potential bugs, security vulnerabilities, and coding standard violations. - Suggest improvements and best practices."
            "\n\n"
            "{context}"
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", "{input}"),
            ]
        )
        combine_docs_chain = create_stuff_documents_chain(self.llm, prompt)
        
        
        contextualize_system_prompt = (
            "Given a chat history and the latest user question "
            "which might reference context in the chat history, "
            "formulate a standalone question which can be understood "
            "without the chat history. Do NOT answer the question, "
            "just reformulate it if needed and otherwise return it as is."
        )
        
        contextualize_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", contextualize_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        
        history_aware_retriever = create_history_aware_retriever(
            self.llm, retriever, contextualize_prompt
        )
        
        qa_chain = create_retrieval_chain(history_aware_retriever, combine_docs_chain)
        
        return qa_chain
        
    def process_pr_data(self, pr_data):
        chunks_with_metadata = []
        for data in pr_data:
            content = f"{str(data)}"
            
            chunks = self.text_splitter.split_text(content)
            
            for chunk in chunks:
                if data['type'] == 'pr':
                    chunks_with_metadata.append({
                        "text": chunk,
                        "metadata": {
                            "repo_name": data["repo_name"],
                            "pr_number": data["pr_number"],
                            "description": data["description"],
                            "changed_files": data["changed_files"],
                            "comments": data["changed_files"]
                        }
                    })
                
                if data['type'] == 'commit':
                    chunks_with_metadata.append({
                        "text": chunk,
                        "metadata": {
                            "repo_name": data["repo_name"],
                            "pr_number": data["pr_number"],
                            "commit_id": data["commit_id"],
                            "commit_message": data["commit_message"],
                            "commit_author": data["commit_author"],
                            "commit_author_email": data["commit_author_email"],
                            "commit_date": data["commit_date"]
                        }
                    })
                    
                if data['type'] == 'file':
                    chunks_with_metadata.append({
                        "text": chunk,
                        "metadata": {
                            "repo_name": data["repo_name"],
                            "pr_number": data["pr_number"],
                            "filename": data["filename"],
                            "patch": data["patch"],
                            "status": data["status"],
                            "changes": data["changes"],
                            "additions": data["additions"],
                            "deletions": data["deletions"]
                        }
                    })
        
        return chunks_with_metadata

    def process_pr_files(self, pr_files: List[Dict[str, Any]]) -> List[str]:
        """Process PR files and return a list of formatted strings."""
        documents = []
        for file in pr_files:
            filename = file["filename"]
            content = file.get("content", "")
            patch = file.get("patch", "")
            document = f"Filename: {filename}\n\nContent:\n{content}\n\nPatch:\n{patch}"
            documents.append(document)
        return documents

    def generate_response(self, qa_chain: ConversationalRetrievalChain, query: str) -> str:
        """Generate a response using the QA chain."""
        response = qa_chain.invoke({"input": query, "chat_history": self.chat_history})['answer']
        self.chat_history.extend(
            [
                HumanMessage(content=query),
                AIMessage(content=response),
            ]
        )
        return response
        


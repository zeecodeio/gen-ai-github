from abc import ABC, abstractmethod
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS, Chroma, PGVector
from langchain_community.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from typing import List, Dict, Any

class VectorStoreInterface(ABC):
    @abstractmethod
    def create_vector_store(self, texts, embeddings):
        pass

    @abstractmethod
    def as_retriever(self):
        pass

class FAISSVectorStore(VectorStoreInterface):
    def create_vector_store(self, texts, embeddings):
        return FAISS.from_documents(texts, embeddings)

    def as_retriever(self):
        return self.vector_store.as_retriever()

class ChromaVectorStore(VectorStoreInterface):
    def create_vector_store(self, texts, embeddings):
        return Chroma.from_documents(texts, embeddings)

    def as_retriever(self):
        return self.vector_store.as_retriever()

class PGVectorStore(VectorStoreInterface):
    def __init__(self, connection_string):
        self.connection_string = connection_string

    def create_vector_store(self, texts, embeddings):
        return PGVector.from_documents(
            texts,
            embeddings,
            connection_string=self.connection_string,
            collection_name="pr_changes"
        )

    def as_retriever(self):
        return self.vector_store.as_retriever()

class RAGLLMProcessor:
    def __init__(self, openai_api_key: str, vector_store: VectorStoreInterface, model_name: str = "gpt-3.5-turbo"):
        self.openai_api_key = openai_api_key
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        self.llm = ChatOpenAI(temperature=0, model_name=model_name, openai_api_key=openai_api_key)
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        self.vector_store = vector_store

    def create_vector_store(self, documents: List[str]):
        """Create a vector store from the given documents."""
        texts = self.text_splitter.create_documents(documents)
        return self.vector_store.create_vector_store(texts, self.embeddings)

    def create_qa_chain(self, vector_store) -> ConversationalRetrievalChain:
        """Create a question-answering chain using the given vector store."""
        return ConversationalRetrievalChain.from_llm(
            self.llm,
            retriever=vector_store.as_retriever(),
            memory=self.memory
        )

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
        return qa_chain({"question": query})["answer"]

# Example usage
if __name__ == "__main__":
    import os
    from env_config import github_token, openai_api_key, repo_name, pr_number, postgres_db, postgres_user, postgres_password

    # Use PGVector for testing
    pg_connection_string = f"postgresql+psycopg://{postgres_user}:{postgres_password}@localhost:6024/{postgres_db}"
    vector_store = PGVectorStore(pg_connection_string)

    # Create the processor with PGVector
    processor = RAGLLMProcessor(openai_api_key, vector_store, model_name="gpt-4")

    # Example PR files (you would get these from the GitHub API)
    pr_files = [
        {"filename": "example.py", "content": "def hello():\n    print('Hello, World!')", "patch": "@@ -0,0 +1,2 @@\n+def hello():\n+    print('Hello, World!')"},
        # Add more files as needed
    ]

    documents = processor.process_pr_files(pr_files)
    vector_store = processor.create_vector_store(documents)
    qa_chain = processor.create_qa_chain(vector_store)

    query = "What changes were made in the PR?"
    response = processor.generate_response(qa_chain, query)
    print(f"Query: {query}")
    print(f"Response: {response}")

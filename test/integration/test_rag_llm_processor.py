import os
import pytest
from dotenv import load_dotenv
from genaigithub.rag_llm_processor import RAGLLMProcessor
from genaigithub.env_config import openai_api_key, github_token, repo_owner, repo_name

# Load environment variables from .env file
load_dotenv()

@pytest.fixture
def rag_llm_processor():
    # Initialize the RAGLLMProcessor with necessary parameters
    # You may need to adjust these based on your actual implementation
    return RAGLLMProcessor(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        github_token=os.getenv("GITHUB_TOKEN"),
        repo_owner=os.getenv("REPO_OWNER"),
        repo_name=os.getenv("REPO_NAME")
    )

def test_rag_llm_processor_initialization(rag_llm_processor):
    assert isinstance(rag_llm_processor, RAGLLMProcessor)

@pytest.mark.integration
def test_process_query(rag_llm_processor):
    query = "What are the main features of this project?"
    result = rag_llm_processor.process_query(query)
    
    assert isinstance(result, str)
    assert len(result) > 0

@pytest.mark.integration
def test_retrieve_relevant_documents(rag_llm_processor):
    query = "How to use the main function?"
    documents = rag_llm_processor.retrieve_relevant_documents(query)
    
    assert isinstance(documents, list)
    assert len(documents) > 0

@pytest.mark.integration
def test_generate_response(rag_llm_processor):
    query = "Explain the purpose of the RAGLLMProcessor class"
    relevant_docs = rag_llm_processor.retrieve_relevant_documents(query)
    response = rag_llm_processor.generate_response(query, relevant_docs)
    
    assert isinstance(response, str)
    assert len(response) > 0


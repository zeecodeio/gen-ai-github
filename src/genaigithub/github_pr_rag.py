from github import Github

from genaigithub.config.env_config import github_token, openai_api_key, repo_name, pr_number, postgres_db, postgres_user, postgres_password, postgres_host, postgres_port

import os
import logging
from langchain_community.chat_models import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import PGVector
from langchain_openai import OpenAIEmbeddings
from langchain.chains import create_retrieval_chain
import base64
from langchain.chains.combine_documents import create_stuff_documents_chain



# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Initialize GitHub client
g = Github(github_token)

if not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = openai_api_key
    
def get_pr_data(repo_name, pr_number):
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)
    
    commits = pr.get_commits()
    
    # Collect PR description, changed files, and comments
    description = pr.body
    changed_files = [file.filename for file in pr.get_files()]
    comments = [comment.body for comment in pr.get_comments()]
    messages = ""
    patches = ""
    for commit in commits:
        messages += commit.commit.message
        for file in commit.files:
            if file.patch:
                patches += file.patch
    
    return description, changed_files, comments, patches, messages

def add_comment(pr, comment):
    return pr.create_comment(comment)
    
def get_repo_content(repo_name):
    repo = g.get_repo(repo_name)
    contents = repo.get_contents("")
 
    repo_contents = []
    while contents:
        file_content = contents.pop(0)
        if file_content.type == "dir":
            contents.extend(repo.get_contents(file_content.path))
        else:
            encoded_content = file_content.content
            decoded_content = base64.b64decode(encoded_content)
            repo_contents.append(f"{file_content.path} -> {decoded_content}")
            
    return repo_contents

def process_pr_data(pr_data, contents):
    description, changed_files, comments, messages, patches = pr_data
    
    # Combine all text data
    all_text = f"PR Description: {description}\n\n"
    all_text += f"Changed Files: {', '.join(changed_files)}\n\n"
    all_text += f"Comments: {' '.join(comments)}"
    all_text += f"Messages: {' '.join(messages)}"
    all_text += f"Patches: {' '.join(patches)}"
    all_text += f"Contents: {' '.join(contents)}"
    
    # Split text into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=200)
    splits = text_splitter.split_text(all_text)
    
    return splits

def create_vectorstore(pr_chunks):
    connection_string = f"postgresql+psycopg://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"
    logger.info(f"Connecting to PostgreSQL at {postgres_host}:{postgres_port} with database {postgres_db}")
    vectorstore = PGVector.from_texts(
        texts=pr_chunks,
        embedding=OpenAIEmbeddings(),
        connection_string=connection_string,
        collection_name="pr_reviews"
    )
    return vectorstore

def setup_rag(vectorstore):
    retriever = vectorstore.as_retriever()
    llm = ChatOpenAI(temperature=0, api_key=openai_api_key)
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
    combine_docs_chain = create_stuff_documents_chain(llm, prompt)
    qa_chain = create_retrieval_chain(retriever, combine_docs_chain)
    
    return qa_chain

def review_pr(qa_chain):
    questions = [
        "What are the main changes in this PR?",
        "Are there any potential security issues?",
        "Does the code follow best practices according to name conventions and known code styles for the language?",
        "Are there sufficient tests for the changes?",
        "What suggestions can you make to improve the code?"
    ]
    
    review = []
    for question in questions:
        answer = qa_chain.invoke({"input": question})
        review.append(answer)
    
    return review


def main():  
    pr_data = get_pr_data(repo_name, pr_number)
    # Process the PR data
    contents = get_repo_content(repo_name)
    pr_chunks = process_pr_data(pr_data, contents)
    
    # Create vectorstore
    vectorstore = create_vectorstore(pr_chunks)

    # Set up RAG
    qa_chain = setup_rag(vectorstore)
    # Generate PR review
    pr_review = review_pr(qa_chain)
    print(pr_review)

if __name__ == "__main__":
    main()

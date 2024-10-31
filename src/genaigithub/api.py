from flask import Flask, request, jsonify
import logging
from genaigithub.config.env_config import (
    github_token,
    openai_api_key,
    default_repo_name,
    postgres_db,
    postgres_user,
    postgres_password,
    postgres_host,
    postgres_port,
)
from genaigithub.github_pr_interaction import GitHubRAGPRInteraction
from genaigithub.rag_llm_processor import RAGLLMProcessor, PGVectorStore
from genaigithub.config.database import init_db
from langchain_core.messages import AIMessage, HumanMessage
from datetime import datetime, timedelta
from flask_cors import CORS
from flask_cors import cross_origin

from github import Github

app = Flask(__name__)
CORS(
    app,
    supports_credentials=True,  # Add This
    origins=[
        "http://localhost:4200"
    ],  # You'll need this, you cannot use * (wildcard domain) when using supports_credentials=True
)

init_db()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Use PGVector for the vector store
pg_connection_string = (
    f"postgresql+psycopg://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"
)
logger.info(f"Connecting to PostgreSQL at {postgres_host}:{postgres_port} with database {postgres_db}")
pg_vector_store = PGVectorStore(pg_connection_string)

# Constants for pagination limits
MAX_REPOS_PER_PAGE = 5
MAX_PRS_PER_PAGE = 5


@app.before_request
def before_request():
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }
    if request.method.lower() == "options":
        return jsonify(headers), 200


@app.route("/hello", methods=["GET"])
def hello():
    return jsonify({"response": "hello"})


@app.route("/repositories", methods=["GET"])
@cross_origin()
def get_all_repositories():
    github = Github(github_token)
    page = request.args.get("page", 0, type=int)
    organization = request.args.get("organization", "spring-projects")
    logger.info(f"Searching for issues in organization {organization}")
    # repos = github.get_organization(organization).get_repos()

    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    logger.info(f"Searching for issues created after {seven_days_ago}")
    issues = github.search_issues(
        f"type:pr review:none is:open created:>{seven_days_ago} is:unmerged org:{organization}"
    )
    logger.info(f"Found {issues.totalCount} issues")

    page = issues.get_page(page)

    total_count = issues.totalCount
    repos_data = []

    logger.info(f"Found {len(page)} issues")

    count = 0

    for issue in page:
        repo = issue.repository
        logger.info(f"Found repo {repo.full_name}")
        logger.info(f"Found issue {issue.title}")
        repo_name = repo.full_name
        if repo:
            repo_data = {
                "name": repo.name,
                "owner": repo.owner.login,
                "full_name": repo.full_name,
                "description": repo.description,
                "url": repo.html_url,
                "language": repo.language,
                "created_at": repo.created_at,
                "updated_at": repo.updated_at,
                "total_count": total_count,
            }
            if repo_name not in [r["full_name"] for r in repos_data]:
                repos_data.append(repo_data)
                count += 1
                if count >= MAX_REPOS_PER_PAGE:
                    break
            continue
        else:
            logger.error(f"No repo found for issue {issue.title}")

    return jsonify({"repositories": repos_data, "total_count": total_count})


@app.route("/pulls", methods=["GET"])
@cross_origin()
def get_all_open_pull_requests():
    github = Github(github_token)

    repo_name = request.args.get("repo_name")
    page = request.args.get("page", 0, type=int)

    if not repo_name:
        return jsonify({"error": "Repo name is required"}), 400

    repo = github.get_repo(repo_name)

    pulls = repo.get_pulls(state="open")

    page = pulls.get_page(page)
    total_count = pulls.totalCount

    prs_data = []
    count = 0
    for pr in page:
        pr_data = {
            "number": pr.number,
            "title": pr.title,
            "body": pr.body,
            "state": pr.state,
            "created_at": pr.created_at,
            "updated_at": pr.updated_at,
            "user": pr.user.login,
            "html_url": pr.html_url,
        }
        count += 1
        if count >= MAX_PRS_PER_PAGE:
            break
        prs_data.append(pr_data)

    return jsonify({"pull_requests": prs_data, "total_count": total_count})


@app.route("/process_pr", methods=["POST"])
@cross_origin()
def process_pr():
    data = request.json
    pr_number = int(data.get("pr_number"))
    repo_name = data.get("repo_name", default_repo_name)
    history = data.get("history", [])
    question = data.get("question", "What changes were made in the PR?")

    if not pr_number:
        return jsonify({"error": "PR number is required"}), 400

    if not repo_name:
        return jsonify({"error": "Repo name is required"}), 400

    repo_name_for_memory = default_repo_name.replace("/", "_")
    repo_name_for_query = repo_name.split("/")[1]

    logger.info(f"Processing PR {pr_number} for repo {repo_name} - question: {question}")

    github_pr_interaction = GitHubRAGPRInteraction(github_token, repo_name, pr_number)
    pr_data = github_pr_interaction.get_pr_data()

    processor = RAGLLMProcessor(
        openai_api_key,
        pg_vector_store,
        memory_key=f"chat_history_{repo_name_for_memory}_{pr_number}",
        model_name="gpt-4",
    )
    chunks_with_metadata = processor.process_pr_data(pr_data)
    vector_store = processor.create_vector_store_from_documents(chunks_with_metadata)

    retriever = vector_store.as_retriever()
    retriever.search_kwargs = {"filter": {"repo_name": repo_name_for_query, "pr_number": pr_number}}

    qa_chain = processor.create_qa_chain(retriever)
    if len(history) == 0:
        processor.reset_chat_history()

    response = processor.generate_response(qa_chain, question)

    if len(processor.chat_history) > 1:
        for message in processor.chat_history:
            if isinstance(message, HumanMessage):
                logger.info(f"Human message: {message.content}")
                history.append({"question": message.content})
            elif isinstance(message, AIMessage):
                logger.info(f"AI message: {message.content}")
                if history and "question" in history[-1]:
                    history[-1]["response"] = message.content
            else:
                logger.info(f"Unknown message type: {message}")

    return jsonify(
        {"question": question, "response": response, "history": history, "repo_name": repo_name, "pr_number": pr_number}
    )


# def run_server():
#     app.run(host='0.0.0.0', port=5005)

# if __name__ == "__main__":
#     app.run(debug=True)

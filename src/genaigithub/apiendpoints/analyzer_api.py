import logging

from flask_cors import cross_origin
from flask import request, jsonify, Blueprint
from urllib.parse import quote_plus

from genaigithub.github_pr_interaction import GitHubRAGPRInteraction
from genaigithub.rag_llm_processor import RAGLLMProcessor, PGVectorStore, MongoDBVectorStore
from genaigithub.config.database import init_db

from genaigithub.config.env_config import github_token, openai_api_key, default_repo_name
from genaigithub.config.env_config import mongodb_host, mongodb_username, mongodb_password
from genaigithub.config.env_config import pg_password, pg_host, pg_port, pg_database, pg_user, pg_ssl_root_cert
from genaigithub.data_processing.preprocessor import CodeReviewPreprocessor

from genaigithub.mongodb_manager import MongoDBManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

escaped_password = quote_plus(pg_password)
pg_connection_string = (
    f"postgresql+psycopg://{pg_user}:{escaped_password}@{pg_host}:{pg_port}/{pg_database}"
    f"?sslmode=verify-full"
    f"&sslrootcert={quote_plus(pg_ssl_root_cert)}"  # Escape path characters
)

mongodb_connection_string = f"mongodb+srv://{mongodb_username}:{mongodb_password}@{mongodb_host}/?retryWrites=true&w=majority&appName=zeecode-genai-github"

logger.info(pg_connection_string)
logger.info(mongodb_connection_string)
logger.info(f"Connecting to MongoDB at {mongodb_host}")
logger.info(f"Connecting to PostgreSQL at {pg_host}:{pg_port} with database {pg_database}")

pg_vector_store = PGVectorStore(pg_connection_string)
mongodb_vector_store = MongoDBVectorStore(mongodb_connection_string)
mongodb_manager = MongoDBManager(mongodb_connection_string)
preprocessor = CodeReviewPreprocessor()

processor_mapping = {}

def get_processor(repo_name_for_memory, pr_number, openai_api_key, vector_store):
    processor_key = f"{repo_name_for_memory}_{pr_number}"
    if processor_key not in processor_mapping:
        processor_mapping[processor_key] = RAGLLMProcessor(
            openai_api_key=openai_api_key,
            vector_store=vector_store,
            memory_key=f"chat_history_{repo_name_for_memory}_{pr_number}",
            model_name="gpt-4",
        )
    return processor_mapping[processor_key]

analyzer_api = Blueprint('analyzer_api', __name__)

@analyzer_api.route("/process_pr", methods=["POST"])
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

    repo_name_for_memory = repo_name.replace("/", "_")
    repo_name_for_query = repo_name.split("/")[1]

    logger.info(f"Processing PR {pr_number} for repo {repo_name} - question: {question}")

    try:
        # Fetch and process new data if needed
        logger.info("Fetching fresh PR data from GitHub")
        github_pr_interaction = GitHubRAGPRInteraction(github_token, repo_name, pr_number)
        pr_data, commits_data, files_data = github_pr_interaction.get_pr_data()

        # Process and cache the chunks
        chunks_with_metadata = preprocessor.process_all_data(
            pr_data=pr_data,
            commits_data=commits_data,
            files_data=files_data
        )
        
        # Set up RAG with processed chunks
        processor = get_processor(repo_name_for_memory, pr_number, openai_api_key, pg_vector_store)
        vector_store = processor.create_vector_store_from_documents(chunks_with_metadata)
        retriever = vector_store.as_retriever()
        retriever.search_kwargs = {"filter": {"repo_name": repo_name_for_query, "pr_number": pr_number}}

        # Generate response
        qa_chain = processor.create_qa_chain(retriever)
        if len(history) == 0:
            processor.reset_memory()

        context = processor.get_chat_history()
        response = processor.generate_response(qa_chain, question, context=context)
        history_messages = processor.get_chat_history()

        # Format response
        history = [
            {"question": msg.content, "response": next_msg.content}
            for msg, next_msg in zip(history_messages[::2], history_messages[1::2])
        ]
        history = history[::-1]

        return jsonify({
            "question": question, 
            "response": response, 
            "history": history, 
            "repo_name": repo_name, 
            "pr_number": pr_number
        })

    except Exception as e:
        logger.error(f"Error processing PR: {str(e)}")
        return jsonify({"error": str(e)}), 500
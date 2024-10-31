from dotenv import load_dotenv
import os

# Load the .env file
load_dotenv()

github_token = os.getenv("GITHUB_TOKEN")
openai_api_key = os.getenv("OPENAI_API_KEY")
default_repo_name = os.getenv("REPO_NAME")
pr_number = int(os.getenv("PR_NUMBER", 0))
postgres_db = os.getenv("POSTGRES_DB", "vectorstore")
postgres_user = os.getenv("POSTGRES_USER", "user")
postgres_password = os.getenv("POSTGRES_PASSWORD", "password")
postgres_host = os.getenv("POSTGRES_HOST", "localhost")
postgres_port = os.getenv("POSTGRES_PORT", 6024)

mongodb_host = os.getenv("MONGODB_HOST", "localhost")
mongodb_port = os.getenv("MONGODB_PORT", "27017")
mongodb_database = os.getenv("MONGODB_DATABASE", "genaigithub")
mongodb_username = os.getenv("MONGODB_USERNAME", "root")
mongodb_password = os.getenv("MONGODB_PASSWORD", "rootpassword")

from dotenv import load_dotenv
import os

# Load the .env file
load_dotenv()

github_token = os.getenv('GITHUB_TOKEN')
openai_api_key = os.getenv('OPENAI_API_KEY')
default_repo_name = os.getenv('REPO_NAME')
pr_number = int(os.getenv('PR_NUMBER', 0))
postgres_db = os.getenv('POSTGRES_DB')
postgres_user = os.getenv('POSTGRES_USER')
postgres_password = os.getenv('POSTGRES_PASSWORD')

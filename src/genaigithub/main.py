from github import Github

from genaigithub.entities.repository import Repository
from genaigithub.entities.pull_request import PullRequest, PRStatus
from genaigithub.entities.pr_file import PrFile, FileStatus
from genaigithub.entities.ai_suggestion import AiSuggestion

from genaigithub.config.database import init_db

from genaigithub.config.env_config import github_token, openai_api_key
from genaigithub.config.env_config import postgres_db, postgres_user, postgres_password, postgres_host, postgres_port
from genaigithub.config.env_config import default_repo_name, pr_number
from genaigithub.github_pr_interaction import GitHubRAGPRInteraction
from genaigithub.rag_llm_processor import RAGLLMProcessor, PGVectorStore

# init_db()

github = Github(github_token)
repos = github.get_user().get_repos()

for issue in github.search_issues('type:pr review:none created:>2024-10-20 is:open is:unmerged org:spring-projects'):
    print(issue)
    
organization = "spring-projects"
repos = github.get_organization(organization).get_repos()
for repo in repos:
    pulls = repo.get_pulls()
    print(pulls.totalCount)
    print(repo.full_name)

total_count = repos.totalCount

for repo in repos:
    repo_data = {
        "name": repo.name,
        "owner": repo.owner.login,
        "full_name": repo.full_name,
        "description": repo.description,
        "url": repo.html_url,
        "language": repo.language,
        "created_at": repo.created_at,
        "updated_at": repo.updated_at,
        "total_count": total_count
    }
    # Get all open pull requests for this repo
    pulls = repo.get_pulls(state='open')
    for pr in pulls:
        pr_data = {
            "number": pr.number,
            "title": pr.title,
            "body": pr.body,
            "state": pr.state,
            "created_at": pr.created_at,
            "updated_at": pr.updated_at,
            "user": pr.user.login,
            "html_url": pr.html_url
        }
        print(f"Pull Request #{pr.number}:")
        print(pr_data)
    print(repo_data)


# pg_connection_string = f"postgresql+psycopg://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"
# vector_store = PGVectorStore(pg_connection_string)

# repo_name_for_memory = default_repo_name.replace("/", "_")

# # Create the processor with PGVector
# processor = RAGLLMProcessor(openai_api_key, vector_store, memory_key=f"chat_history_{repo_name_for_memory}_{pr_number}", model_name="gpt-4")

# # Use the provided repo_name or fall back to the one from .env
# repo_name = default_repo_name
# github_pr_interaction = GitHubRAGPRInteraction(github_token, repo_name, pr_number)
# pr_data = github_pr_interaction.get_pr_data()

# chunks_with_metadata = processor.process_pr_data(pr_data)

# repo_name_for_query = repo_name.split('/')[1]
# vector_store = processor.create_vector_store_from_documents(chunks_with_metadata)

# retriever = vector_store.as_retriever()
# retriever.search_kwargs = {
#     "filter": {"repo_name": repo_name_for_query, "pr_number": pr_number}
# }

# qa_chain = processor.create_qa_chain(retriever)
# processor.reset_chat_history()

# questions = [
#         "What are the main changes in this PR?",
#         "Are there any potential security issues?",
#         "Does the code follow best practices according to name conventions and known code styles for the language?",
#         "Are there sufficient tests for the changes?",
#         "What suggestions can you make to improve the code?"
#     ]
    
# review = []
# history = []
# for question in questions:
#     answer = processor.generate_response(qa_chain, question)
#     print(f"Query: {question}")
#     print("\n")
#     print(f"Response: {answer}")
#     print("\n")
#     review.append({question: question, answer: answer})



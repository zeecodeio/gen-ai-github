import click
from genaigithub.config.env_config import github_token, openai_api_key, default_repo_name, postgres_db, postgres_user, postgres_password, postgres_host, postgres_port
from genaigithub.github_pr_interaction import GitHubRAGPRInteraction
from genaigithub.rag_llm_processor import RAGLLMProcessor, PGVectorStore

@click.command()
@click.option('--pr-number', required=True, type=int, help='The PR number to process')
@click.option('--query', default="What changes were made in the PR?", help='The query to ask about the PR')
@click.option('--repo-name', help='The GitHub repository name (owner/repo)')
def process_pr(pr_number, query, repo_name):
    """Process a GitHub PR and answer questions about it."""
    # Use PGVector for the vector store
    pg_connection_string = f"postgresql+psycopg://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"
    vector_store = PGVectorStore(pg_connection_string)

    # Create the processor with PGVector
    processor = RAGLLMProcessor(openai_api_key, vector_store, model_name="gpt-4")

    # Use the provided repo_name or fall back to the one from .env
    repo_name = repo_name or default_repo_name
    github_pr_interaction = GitHubRAGPRInteraction(github_token, repo_name, pr_number)
    all_text = github_pr_interaction.process_pr_data()

    vector_store = processor.create_vector_store_from_string(all_text)
    qa_chain = processor.create_qa_chain(vector_store)

    response = processor.generate_response(qa_chain, query)

    click.echo(f"Query: {query}")
    click.echo(f"Response: {response}")


def main():  
    process_pr()

if __name__ == "__main__":
    main()
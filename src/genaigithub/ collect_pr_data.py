from genaigithub.services.mongodb_service import MongoDBService
from genaigithub.data_collection.github_data_collector import GitHubDataCollector
from genaigithub.config.env_config import (
    github_token,
    mongodb_connection_string
)

def collect_pr_data(repo_name: str, pr_number: int):
    # Initialize services
    mongodb_service = MongoDBService(mongodb_connection_string)
    collector = GitHubDataCollector(github_token, mongodb_service)

    try:
        # Collect and save PR data
        repository, pull_request = collector.collect_and_save_pr_data(repo_name, pr_number)

        # Get PR files
        pr_files = mongodb_service.get_pr_files(pull_request)

        # Example: Save an AI suggestion for each file
        for pr_file in pr_files:
            collector.save_ai_suggestion(
                pull_request=pull_request,
                pr_file=pr_file,
                suggestion="Consider adding more documentation to this file.",
                line_number=1,
                original_code=pr_file.patch,
                suggested_code=pr_file.patch + "\n# Added documentation",
                reasoning="Documentation helps maintain code quality",
                metadata={
                    "confidence": 0.85,
                    "category": "documentation"
                }
            )

    finally:
        mongodb_service.close()

if __name__ == "__main__":
    collect_pr_data("owner/repo", 123)
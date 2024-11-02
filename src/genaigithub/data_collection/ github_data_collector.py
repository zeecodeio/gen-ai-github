from typing import Dict, Any, Tuple
from github import Github
import logging
from datetime import datetime

from genaigithub.services.mongodb_service import MongoDBService
from genaigithub.entities.repository import Repository
from genaigithub.entities.pull_request import PullRequest
from genaigithub.entities.pr_file import PrFile

logger = logging.getLogger(__name__)

class GitHubDataCollector:
    def __init__(self, github_token: str, mongodb_service: MongoDBService):
        self.github = Github(github_token)
        self.mongodb_service = mongodb_service

    def collect_and_save_pr_data(self, repo_name: str, pr_number: int) -> Tuple[Repository, PullRequest]:
        """Collect and save all PR-related data"""
        try:
            # Get repository data
            github_repo = self.github.get_repo(repo_name)
            repo_data = {
                'name': github_repo.name,
                'owner': github_repo.owner.login,
                'description': github_repo.description,
                'is_active': not github_repo.archived
            }
            repository = self.mongodb_service.save_repository(repo_data)

            # Get PR data
            github_pr = github_repo.get_pull(pr_number)
            pr_data = {
                'pr_number': pr_number,
                'title': github_pr.title,
                'description': github_pr.body,
                'author': github_pr.user.login,
                'status': github_pr.state,
                'base_branch': github_pr.base.ref,
                'head_branch': github_pr.head.ref,
                'created_at': github_pr.created_at,
                'updated_at': github_pr.updated_at,
                'closed_at': github_pr.closed_at
            }
            pull_request = self.mongodb_service.save_pull_request(pr_data, repository)

            # Get and save file data
            for file in github_pr.get_files():
                file_data = {
                    'filename': file.filename,
                    'status': file.status,
                    'additions': file.additions,
                    'deletions': file.deletions,
                    'changes': file.changes,
                    'patch': file.patch
                }
                self.mongodb_service.save_pr_file(file_data, pull_request)

            return repository, pull_request

        except Exception as e:
            logger.error(f"Error collecting PR data: {str(e)}")
            raise

    def save_ai_suggestion(self, 
                         pull_request: PullRequest, 
                         pr_file: PrFile, 
                         suggestion: str,
                         line_number: int = None,
                         original_code: str = None,
                         suggested_code: str = None,
                         reasoning: str = None,
                         metadata: Dict[str, Any] = None):
        """Save an AI suggestion for a specific file in a PR"""
        try:
            suggestion_data = {
                'suggestion': suggestion,
                'line_number': line_number,
                'original_code': original_code,
                'suggested_code': suggested_code,
                'reasoning': reasoning,
                'metadata': metadata or {},
                'status': 'PENDING'
            }
            
            return self.mongodb_service.save_ai_suggestion(
                suggestion_data,
                pull_request,
                pr_file
            )
        except Exception as e:
            logger.error(f"Error saving AI suggestion: {str(e)}")
            raise
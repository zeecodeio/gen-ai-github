from typing import Dict, List, Any, Optional
from datetime import datetime
from mongoengine import connect, disconnect
import logging

from genaigithub.entities.repository import Repository
from genaigithub.entities.pull_request import PullRequest, PRStatus
from genaigithub.entities.pr_file import PrFile, FileStatus
from genaigithub.entities.ai_suggestion import AiSuggestion, SuggestionStatus

logger = logging.getLogger(__name__)

class MongoDBService:
    def __init__(self, connection_string: str):
        """Initialize MongoDB connection"""
        self.connection_string = connection_string
        self._connect()

    def _connect(self):
        """Establish connection to MongoDB"""
        try:
            connect(host=self.connection_string)
            logger.info("Successfully connected to MongoDB")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise

    def close(self):
        """Close MongoDB connection"""
        disconnect()
        logger.info("MongoDB connection closed")

    def save_repository(self, repo_data: Dict[str, Any]) -> Repository:
        """Save or update repository information"""
        try:
            repo = Repository.objects(
                name=repo_data['name'],
                owner=repo_data['owner']
            ).first()

            if not repo:
                repo = Repository(
                    name=repo_data['name'],
                    owner=repo_data['owner'],
                    description=repo_data.get('description', ''),
                    is_active=repo_data.get('is_active', True)
                )
            else:
                repo.description = repo_data.get('description', repo.description)
                repo.is_active = repo_data.get('is_active', repo.is_active)

            repo.save()
            logger.info(f"Saved repository: {repo.owner}/{repo.name}")
            return repo
        except Exception as e:
            logger.error(f"Error saving repository: {str(e)}")
            raise

    def save_pull_request(self, pr_data: Dict[str, Any], repository: Repository) -> PullRequest:
        """Save or update pull request information"""
        try:
            pr = PullRequest.objects(
                repository=repository,
                pr_number=pr_data['pr_number']
            ).first()

            if not pr:
                pr = PullRequest(
                    repository=repository,
                    pr_number=pr_data['pr_number'],
                    title=pr_data['title'],
                    description=pr_data.get('description', ''),
                    author=pr_data['author'],
                    status=PRStatus[pr_data['status'].upper()],
                    base_branch=pr_data.get('base_branch'),
                    head_branch=pr_data.get('head_branch'),
                    created_at=pr_data.get('created_at', datetime.now()),
                    updated_at=pr_data.get('updated_at'),
                    closed_at=pr_data.get('closed_at')
                )
            else:
                pr.title = pr_data['title']
                pr.description = pr_data.get('description', pr.description)
                pr.status = PRStatus[pr_data['status'].upper()]
                pr.updated_at = pr_data.get('updated_at', datetime.now())
                pr.closed_at = pr_data.get('closed_at', pr.closed_at)

            pr.save()
            logger.info(f"Saved PR #{pr.pr_number} for repository: {repository.owner}/{repository.name}")
            return pr
        except Exception as e:
            logger.error(f"Error saving pull request: {str(e)}")
            raise

    def save_pr_file(self, file_data: Dict[str, Any], pull_request: PullRequest) -> PrFile:
        """Save or update PR file information"""
        try:
            pr_file = PrFile.objects(
                pull_request=pull_request,
                filename=file_data['filename']
            ).first()

            if not pr_file:
                pr_file = PrFile(
                    pull_request=pull_request,
                    filename=file_data['filename'],
                    status=FileStatus[file_data['status'].upper()],
                    additions=file_data.get('additions', 0),
                    deletions=file_data.get('deletions', 0),
                    changes=file_data.get('changes', 0),
                    patch=file_data.get('patch', '')
                )
            else:
                pr_file.status = FileStatus[file_data['status'].upper()]
                pr_file.additions = file_data.get('additions', pr_file.additions)
                pr_file.deletions = file_data.get('deletions', pr_file.deletions)
                pr_file.changes = file_data.get('changes', pr_file.changes)
                pr_file.patch = file_data.get('patch', pr_file.patch)

            pr_file.save()
            logger.info(f"Saved file {pr_file.filename} for PR #{pull_request.pr_number}")
            return pr_file
        except Exception as e:
            logger.error(f"Error saving PR file: {str(e)}")
            raise

    def save_ai_suggestion(self, suggestion_data: Dict[str, Any], pull_request: PullRequest, pr_file: PrFile) -> AiSuggestion:
        """Save or update AI suggestion"""
        try:
            suggestion = AiSuggestion(
                pull_request=pull_request,
                pr_file=pr_file,
                suggestion=suggestion_data['suggestion'],
                line_number=suggestion_data.get('line_number'),
                original_code=suggestion_data.get('original_code'),
                suggested_code=suggestion_data.get('suggested_code'),
                status=SuggestionStatus[suggestion_data.get('status', 'PENDING').upper()],
                reasoning=suggestion_data.get('reasoning', ''),
                metadata=suggestion_data.get('metadata', {})
            )

            suggestion.save()
            logger.info(f"Saved AI suggestion for file {pr_file.filename} in PR #{pull_request.pr_number}")
            return suggestion
        except Exception as e:
            logger.error(f"Error saving AI suggestion: {str(e)}")
            raise

    def get_repository(self, owner: str, name: str) -> Optional[Repository]:
        """Retrieve repository by owner and name"""
        return Repository.objects(owner=owner, name=name).first()

    def get_pull_request(self, repository: Repository, pr_number: int) -> Optional[PullRequest]:
        """Retrieve pull request by repository and PR number"""
        return PullRequest.objects(repository=repository, pr_number=pr_number).first()

    def get_pr_files(self, pull_request: PullRequest) -> List[PrFile]:
        """Retrieve all files for a specific pull request"""
        return PrFile.objects(pull_request=pull_request)

    def get_ai_suggestions(self, pull_request: PullRequest, pr_file: Optional[PrFile] = None) -> List[AiSuggestion]:
        """Retrieve AI suggestions for a pull request, optionally filtered by file"""
        query = {'pull_request': pull_request}
        if pr_file:
            query['pr_file'] = pr_file
        return AiSuggestion.objects(**query)
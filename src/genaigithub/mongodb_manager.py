from typing import Dict, Any, Tuple, Optional, List
from datetime import datetime
from mongoengine import connect, disconnect

from genaigithub.entities.repository import Repository
from genaigithub.entities.pull_request import PullRequest, PRStatus
from genaigithub.entities.pr_file import PrFile, FileStatus
from genaigithub.entities.code_review import CodeReview, CodeChange, Review
from genaigithub.entities.ai_suggestion import AiSuggestion

class MongoDBManager:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        connect(host=connection_string)

    def save_pr_review_data(self, repo_name: str, pr_data: Dict, commits_data: list, files_data: list) -> Tuple[Repository, PullRequest, list[PrFile]]:
        # Save Repository
        repo = self._get_or_create_repository(repo_name)
        
        # Save Pull Request
        pull_request = self._get_or_create_pull_request(repo, pr_data)
        
        # Save PR Files
        pr_files = []
        for file_data in files_data:
            pr_file = self._get_or_create_pr_file(pull_request, file_data)
            pr_files.append(pr_file)
            
        # Save Code Review
        code_review = self._create_code_review(pull_request, files_data)
        
        return repo, pull_request, pr_files

    def _get_or_create_repository(self, repo_name: str) -> Repository:
        owner, name = repo_name.split('/')
        repo = Repository.objects(owner=owner, name=name).first()
        if not repo:
            repo = Repository(
                owner=owner,
                name=name,
                is_active=True
            ).save()
        return repo

    def _get_or_create_pull_request(self, repo: Repository, pr_data: Dict) -> PullRequest:
        pr = PullRequest.objects(repository=repo, pr_number=pr_data['pr_number']).first()
        if not pr:
            pr = PullRequest(
                repository=repo,
                pr_number=pr_data['pr_number'],
                title=pr_data.get('title', ''),
                description=pr_data.get('description', ''),
                author=pr_data.get('commit_author', ''),
                status=PRStatus.OPEN,
                created_at=datetime.now()
            ).save()
        return pr

    def _get_or_create_pr_file(self, pull_request: PullRequest, file_data: Dict) -> PrFile:
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
            ).save()
        return pr_file

    def _create_code_review(self, pull_request: PullRequest, files_data: list) -> CodeReview:
        code_changes = []
        for file_data in files_data:
            code_change = CodeChange(
                filename=file_data['filename'],
                language=file_data.get('language', 'unknown'),
                patch=file_data.get('patch', ''),
                additions=file_data.get('additions', 0),
                deletions=file_data.get('deletions', 0)
            )
            code_changes.append(code_change)

        code_review = CodeReview(
            pr_number=pull_request.pr_number,
            repository=f"{pull_request.repository.owner}/{pull_request.repository.name}",
            created_at=datetime.now(),
            changes=code_changes
        ).save()
        
        return code_review
    
    def get_code_review(self, repo_name: str, pr_number: int) -> Optional[CodeReview]:
        """Get existing code review with all related data"""
        return CodeReview.objects(
            repository=repo_name,
            pr_number=pr_number
        ).first()

    def cache_processed_chunks(self, repo_name: str, pr_number: int, 
                             chunks_with_metadata: List[Dict]) -> None:
        """Cache processed chunks in MongoDB"""
        code_review = self.get_code_review(repo_name, pr_number)
        if code_review:
            code_review.processed_chunks = chunks_with_metadata
            code_review.last_processed = datetime.now()
            code_review.save()

    def save_ai_suggestion(self, pull_request: PullRequest, pr_file: PrFile, 
                         suggestion: str, metadata: Dict[str, Any]) -> AiSuggestion:
        ai_suggestion = AiSuggestion(
            pull_request=pull_request,
            pr_file=pr_file,
            suggestion=suggestion,
            metadata=metadata
        ).save()
        return ai_suggestion
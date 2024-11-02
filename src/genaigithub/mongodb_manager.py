from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
from mongoengine import connect, disconnect
import logging

from genaigithub.entities.repository import Repository
from genaigithub.entities.pull_request import PullRequest, PRStatus
from genaigithub.entities.pr_file import PrFile, FileStatus
from genaigithub.entities.code_review import CodeReview, CodeChange, Review
from genaigithub.entities.ai_suggestion import AiSuggestion, SuggestionStatus

logger = logging.getLogger(__name__)

class MongoDBManager:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        connect(host=connection_string)
        
    def save_ai_suggestion(self, 
                         pull_request: PullRequest, 
                         pr_file: Optional[PrFile], 
                         suggestion: str,
                         metadata: Dict[str, Any]) -> AiSuggestion:
        """
        Save an AI suggestion for a pull request
        
        Args:
            pull_request: The PullRequest object
            pr_file: Optional PrFile object (can be None for general PR suggestions)
            suggestion: The suggestion text
            metadata: Additional metadata about the suggestion
        """
        try:
            ai_suggestion = AiSuggestion(
                pull_request=pull_request,
                pr_file=pr_file,
                suggestion=suggestion,
                status=SuggestionStatus.PENDING,
                created_at=datetime.now(),
                metadata=metadata
            )
            
            # Add file-specific metadata if pr_file is provided
            if pr_file:
                ai_suggestion.metadata.update({
                    'filename': pr_file.filename,
                    'file_status': pr_file.status,
                    'file_changes': {
                        'additions': pr_file.additions,
                        'deletions': pr_file.deletions,
                        'total_changes': pr_file.changes
                    }
                })

            ai_suggestion.save()
            logger.info(f"Saved AI suggestion for PR #{pull_request.pr_number}")
            return ai_suggestion

        except Exception as e:
            logger.error(f"Error saving AI suggestion: {str(e)}")
            raise

    def get_ai_suggestions(self, 
                         pull_request: PullRequest, 
                         pr_file: Optional[PrFile] = None,
                         status: Optional[SuggestionStatus] = None) -> List[AiSuggestion]:
        """
        Get AI suggestions for a pull request
        
        Args:
            pull_request: The PullRequest object
            pr_file: Optional PrFile to filter suggestions for a specific file
            status: Optional status to filter suggestions
        """
        query = {'pull_request': pull_request}
        
        if pr_file:
            query['pr_file'] = pr_file
        
        if status:
            query['status'] = status
            
        return AiSuggestion.objects(**query).order_by('-created_at')

    def save_pr_review_data(self, repo_name: str, pr_data: Dict, commits_data: list, files_data: list) -> Tuple[Repository, PullRequest, list[PrFile]]:
        """Save all PR-related data and return the created objects"""
        try:
            # 1. Save Repository
            owner, name = repo_name.split('/')
            repo = self._get_or_create_repository(owner, name)

            # 2. Save Pull Request
            pull_request = self._get_or_create_pull_request(repo, pr_data)

            # 3. Save PR Files
            pr_files = []
            for file_data in files_data:
                pr_file = self._get_or_create_pr_file(pull_request, file_data)
                pr_files.append(pr_file)

            # 4. Save Code Review
            code_review = self._create_or_update_code_review(
                pull_request=pull_request,
                pr_files=pr_files,
                files_data=files_data
            )

            return repo, pull_request, pr_files

        except Exception as e:
            logger.error(f"Error saving PR review data: {str(e)}")
            raise

    def _get_or_create_repository(self, owner: str, name: str) -> Repository:
        """Get or create a repository record"""
        repo = Repository.objects(owner=owner, name=name).first()
        if not repo:
            repo = Repository(
                owner=owner,
                name=name,
                is_active=True
            ).save()
        return repo

    def _get_or_create_pull_request(self, repo: Repository, pr_data: Dict) -> PullRequest:
        """Get or create a pull request record"""
        pr = PullRequest.objects(
            repository=repo,
            pr_number=pr_data['pr_number']
        ).first()

        if not pr:
            pr = PullRequest(
                repository=repo,
                pr_number=pr_data['pr_number'],
                title=pr_data.get('title', ''),
                description=pr_data.get('description', ''),
                author=pr_data.get('commit_author', ''),
                status=PRStatus.OPEN,  # You might want to get this from pr_data
                base_branch=pr_data.get('base_branch', ''),
                head_branch=pr_data.get('head_branch', ''),
                created_at=datetime.now()
            ).save()
        return pr

    def _get_or_create_pr_file(self, pull_request: PullRequest, file_data: Dict) -> PrFile:
        """Get or create a PR file record"""
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

    def _create_or_update_code_review(self, pull_request: PullRequest, pr_files: List[PrFile], files_data: List[Dict]) -> CodeReview:
        """Create or update a code review record"""
        try:
            # Try to find existing code review
            code_review = CodeReview.objects(
                repository=f"{pull_request.repository.owner}/{pull_request.repository.name}",
                pr_number=pull_request.pr_number
            ).first()

            # Create new code review if it doesn't exist
            if not code_review:
                code_review = CodeReview(
                    repository=f"{pull_request.repository.owner}/{pull_request.repository.name}",
                    pr_number=pull_request.pr_number,
                    pull_request=pull_request,  # Set the required reference
                    pr_files=pr_files,
                    created_at=datetime.now()
                )
            else:
                # Update existing code review
                code_review.pull_request = pull_request
                code_review.pr_files = pr_files

            # Update code changes
            code_changes = []
            for file_data in files_data:
                code_change = CodeChange(
                    filename=file_data['filename'],
                    language=file_data.get('language', self._detect_language(file_data['filename'])),
                    patch=file_data.get('patch', ''),
                    additions=file_data.get('additions', 0),
                    deletions=file_data.get('deletions', 0)
                )
                code_changes.append(code_change)

            code_review.changes = code_changes
            code_review.save()

            return code_review

        except Exception as e:
            logger.error(f"Error creating/updating code review: {str(e)}")
            raise

    def _detect_language(self, filename: str) -> str:
        """Detect programming language from filename"""
        extension = filename.split('.')[-1] if '.' in filename else ''
        return {
            'cpp': 'cpp',
            'go': 'go', 
            'java': 'java',
            'kt': 'kotlin',
            'js': 'js',
            'ts': 'ts',
            'php': 'php',
            'proto': 'proto',
            'py': 'python',
            'rst': 'rst',
            'rb': 'ruby',
            'rs': 'rust',
            'scala': 'scala',
            'swift': 'swift',
            'md': 'markdown',
            'tex': 'latex',
            'html': 'html',
            'sol': 'sol',
            'cs': 'csharp',
            'cbl': 'cobol',
            'c': 'c',
            'lua': 'lua',
            'pl': 'perl',
            'hs': 'haskell',
            'ex': 'elixir',
            'ps1': 'powershell'
        }.get(extension.lower(), 'unknown')

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
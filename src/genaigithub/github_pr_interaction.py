from github import Github
from github.PullRequest import PullRequest
from github.Repository import Repository
from typing import List, Dict, Any

class GitHubRAGPRInteraction:
    def __init__(self, token: str, repo_owner: str, repo_name: str, pr_number: int):
        self.github = Github(token)
        self.repo: Repository = self.github.get_repo(f"{repo_owner}/{repo_name}")
        self.pr: PullRequest = self.repo.get_pull(pr_number)

    def list_pr_comments(self) -> List[Dict[str, Any]]:
        """List all comments on a specific PR."""
        return [comment.raw_data for comment in self.pr.get_issue_comments()]

    def add_pr_comment(self, comment_body: str) -> Dict[str, Any]:
        """Add a new comment to a specific PR."""
        comment = self.pr.create_comment(comment_body)
        return comment
    
    def get_pr_data(self) -> Dict[str, Any]:
        commits = self.pr.get_commits()
        
        # Collect PR description, changed files, and comments
        description = self.pr.body
        changed_files = [file.filename for file in self.pr.get_files()]
        comments = [comment.body for comment in self.pr.get_comments()]
        messages = ""
        patches = ""
        for commit in commits:
            messages += commit.commit.message
            for file in commit.files:
                if file.patch:
                    patches += file.patch
        
        return {
            "description": description,
            "changed_files": changed_files,
            "comments": comments,
            "patches": patches,
            "messages": messages
        }

    def get_pr_details(self) -> Dict[str, Any]:
        """Get details of a specific PR."""
        return self.pr.raw_data

    def get_pr_files(self) -> List[Dict[str, Any]]:
        """Get the list of files changed in a PR."""
        return [file.raw_data for file in self.pr.get_files()]

    def get_file_content(self, file_path: str, ref: str) -> str:
        """Get the content of a file from the repository."""
        content = self.repo.get_contents(file_path, ref=ref)
        return content.decoded_content.decode('utf-8')

    def get_pr_diff(self) -> str:
        """Get the diff of a PR."""
        return self.pr.diff()

from github import Github
from github.PullRequest import PullRequest
from github.Repository import Repository
import base64
from typing import List, Dict, Any

class GitHubRAGPRInteraction:
    def __init__(self, token: str, repo_name: str, pr_number: int):
        self.github = Github(token)
        self.repo: Repository = self.github.get_repo(repo_name)
        self.pr: PullRequest = self.repo.get_pull(pr_number)

    def list_pr_comments(self) -> List[Dict[str, Any]]:
        """List all comments on a specific PR."""
        return [comment.raw_data for comment in self.pr.get_issue_comments()]

    def add_pr_comment(self, comment_body: str) -> Dict[str, Any]:
        """Add a new comment to a specific PR."""
        comment = self.pr.create_comment(comment_body)
        return comment
    
    def get_pr_data(self):
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
        
        return description, changed_files, comments, patches, messages
    
    def get_repo_content(self):
        contents = self.repo.get_contents("")
    
        repo_contents = []
        while contents:
            file_content = contents.pop(0)
            if file_content.type == "dir":
                contents.extend(self.repo.get_contents(file_content.path))
            else:
                encoded_content = file_content.content
                decoded_content = base64.b64decode(encoded_content)
                repo_contents.append(f"{file_content.path} -> {decoded_content}")
                
        return repo_contents
    
    
    def process_pr_data(self):
        description, changed_files, comments, messages, patches = self.get_pr_data()
        contents = self.get_repo_content()
        
        # Combine all text data
        all_text = f"PR Description: {description}\n\n"
        all_text += f"Changed Files: {', '.join(changed_files)}\n\n"
        all_text += f"Comments: {' '.join(comments)}"
        all_text += f"Messages: {' '.join(messages)}"
        all_text += f"Patches: {' '.join(patches)}"
        all_text += f"Contents: {' '.join(contents)}"
        
        return all_text

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

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
        pr_data = []
        pr_info = {}

        pr_info["repo_name"] = self.repo.name
        pr_info["pr_number"] = self.pr.number
        pr_info["description"] = self.pr.body
        pr_info["changed_files"] = [file.filename for file in self.pr.get_files()]
        pr_info["comments"] = [comment.body for comment in self.pr.get_comments()]
        pr_info["type"] = "pr"

        pr_data.append(pr_info)

        for commit in commits:
            commit_data = {}

            commit_data["repo_name"] = self.repo.name
            commit_data["pr_number"] = self.pr.number
            commit_data["commit_id"] = commit.sha
            commit_data["commit_message"] = commit.commit.message
            commit_data["commit_author"] = commit.commit.author.name
            commit_data["commit_author_email"] = commit.commit.author.email
            commit_data["commit_date"] = commit.commit.last_modified

            commit_data["type"] = "commit"

            pr_data.append(commit_data)

            for file in commit.files:
                file_data = {}

                if file.patch:

                    file_data["repo_name"] = self.repo.name
                    file_data["pr_number"] = self.pr.number
                    file_data["filename"] = file.filename
                    file_data["patch"] = file.patch
                    file_data["status"] = file.status
                    file_data["changes"] = file.changes
                    file_data["additions"] = file.additions
                    file_data["deletions"] = file.deletions

                    file_data["type"] = "file"
                    pr_data.append(file_data)

        return pr_data

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

    def get_pr_details(self) -> Dict[str, Any]:
        """Get details of a specific PR."""
        return self.pr.raw_data

    def get_pr_files(self) -> List[Dict[str, Any]]:
        """Get the list of files changed in a PR."""
        return [file.raw_data for file in self.pr.get_files()]

    def get_file_content(self, file_path: str, ref: str) -> str:
        """Get the content of a file from the repository."""
        content = self.repo.get_contents(file_path, ref=ref)
        return content.decoded_content.decode("utf-8")

    def get_pr_diff(self) -> str:
        """Get the diff of a PR."""
        return self.pr.diff()

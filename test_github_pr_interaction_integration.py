import os
import pytest
from dotenv import load_dotenv
from src.genaigithub.github_pr_interaction import GitHubRAGPRInteraction

# Load environment variables from .env file
load_dotenv()

@pytest.fixture
def github_pr_interaction():
    github_token = os.getenv("GITHUB_TOKEN")
    repo_owner = os.getenv("REPO_OWNER")
    repo_name = os.getenv("REPO_NAME")
    pr_number = os.getenv("PR_NUMBER")
    
    if not all([github_token, repo_owner, repo_name, pr_number]):
        pytest.skip("Missing required environment variables in .env file")
    
    return GitHubRAGPRInteraction(
        token=github_token,
        repo_owner=repo_owner,
        repo_name=repo_name,
        pr_number=int(pr_number)
    )

def test_github_pr_interaction_initialization(github_pr_interaction):
    assert isinstance(github_pr_interaction, GitHubRAGPRInteraction)

def test_list_pr_comments(github_pr_interaction):
    comments = github_pr_interaction.list_pr_comments()
    assert isinstance(comments, list)
    # Add more specific assertions based on expected comment structure

def test_add_pr_comment(github_pr_interaction):
    comment_body = "Test comment from pytest"
    response = github_pr_interaction.add_pr_comment(comment_body)
    assert isinstance(response, dict)
    # Add more specific assertions based on expected response structure

def test_get_pr_data(github_pr_interaction):
    pr_data = github_pr_interaction.get_pr_data()
    assert isinstance(pr_data, dict)
    assert "description" in pr_data
    assert "changed_files" in pr_data
    assert "comments" in pr_data
    assert "patches" in pr_data
    assert "messages" in pr_data

def test_get_pr_details(github_pr_interaction):
    details = github_pr_interaction.get_pr_details()
    assert isinstance(details, dict)
    # Add more specific assertions based on expected PR details structure

def test_get_pr_files(github_pr_interaction):
    files = github_pr_interaction.get_pr_files()
    assert isinstance(files, list)
    # Add more specific assertions based on expected file structure

def test_get_file_content(github_pr_interaction):
    # You'll need to provide a valid file path and ref for this test
    file_path = "README.md"  # Replace with a valid file path
    ref = "main"  # Replace with a valid branch or commit SHA
    content = github_pr_interaction.get_file_content(file_path, ref)
    assert isinstance(content, str)
    assert len(content) > 0

def test_get_pr_diff(github_pr_interaction):
    diff = github_pr_interaction.get_pr_diff()
    assert isinstance(diff, str)
    assert len(diff) > 0

# Add more test functions for any additional methods in GitHubRAGPRInteraction


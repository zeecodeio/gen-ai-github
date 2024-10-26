import pytest
from unittest.mock import Mock, patch
from genaigithub.github_pr_rag import get_pr_data

@pytest.fixture
def mock_github():
    with patch('genaigithub.github_pr_rag.Github') as mock_github:
        yield mock_github

@pytest.fixture
def mock_repo(mock_github):
    mock_repo = Mock()
    mock_github.return_value.get_repo.return_value = mock_repo
    return mock_repo

@pytest.fixture
def mock_pr(mock_repo):
    mock_pr = Mock()
    mock_repo.get_pull.return_value = mock_pr
    return mock_pr

def test_get_pr_data(mock_pr):
    # Arrange
    mock_pr.body = "Test PR description"
    mock_file = Mock()
    mock_file.filename = "test_file.py"
    mock_pr.get_files.return_value = [mock_file]
    mock_comment = Mock()
    mock_comment.body = "Test comment"
    mock_pr.get_comments.return_value = [mock_comment]

    # Act
    description, changed_files, comments = get_pr_data("owner/repo", 123)

    # Assert
    assert description == "Test PR description"
    assert changed_files == ["test_file.py"]
    assert comments == ["Test comment"]

def test_get_pr_data_empty(mock_pr):
    # Arrange
    mock_pr.body = ""
    mock_pr.get_files.return_value = []
    mock_pr.get_comments.return_value = []

    # Act
    description, changed_files, comments = get_pr_data("owner/repo", 123)

    # Assert
    assert description == ""
    assert changed_files == []
    assert comments == []

@pytest.mark.parametrize("repo_name,pr_number", [
    ("owner/repo", 123),
    ("another/repo", 456),
])
def test_get_pr_data_calls(mock_github, mock_repo, mock_pr, repo_name, pr_number):
    # Act
    get_pr_data(repo_name, pr_number)

    # Assert
    mock_github.return_value.get_repo.assert_called_once_with(repo_name)
    mock_repo.get_pull.assert_called_once_with(pr_number)
    mock_pr.get_files.assert_called_once()
    mock_pr.get_comments.assert_called_once()

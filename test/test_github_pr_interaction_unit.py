import pytest
from unittest.mock import Mock
from genaigithub.github_pr_interaction import GitHubRAGPRInteraction


@pytest.fixture
def mock_github(mocker):
    """Fixture to mock the Github class and its get_repo method."""
    mock_github_class = mocker.patch("genaigithub.github_pr_interaction.Github", autospec=True)
    mock_github_instance = mock_github_class.return_value

    # Mock the get_repo method to return a mock repository
    mock_repo = Mock()
    mock_github_instance.get_repo.return_value = mock_repo
    
    mock_pr = Mock()
    mock_repo.get_pull.return_value = mock_pr

    return mock_github_instance, mock_repo, mock_pr

@pytest.fixture
def interaction(mock_github):
    """Fixture to provide a GitHubRAGPRInteraction instance."""
    mock_github_instance, mock_repo, mock_pr = mock_github
    return GitHubRAGPRInteraction("fake_token", "owner", "repo", 123)

def test_create_pr_comment(interaction, mock_github):
    # Arrange: Mock the pull request and the comment method
    mock_github_instance, mock_repo, mock_pr = mock_github

    # Arrange: Mock the pull request and the comment method
    mock_pr_comment = Mock()
    mock_pr_comment.body = "Test comment"
    mock_pr.create_comment.return_value = mock_pr_comment
    
    # Act: Call the method to create a comment
    result_comment = interaction.add_pr_comment("Test comment")

    # Assert: Verify interactions
    mock_repo.get_pull.assert_called_once_with(123)
    mock_pr.create_comment.assert_called_once_with("Test comment")
    print(result_comment)
    assert result_comment.body == "Test comment"
    
    
def test_list_pr_comments(interaction, mock_github):
    # Arrange: Mock the pull request and the comment method
    mock_github_instance, mock_repo, mock_pr = mock_github

    # Arrange: Mock the pull request and the comment method
    mock_pr_comment = Mock()
    mock_pr_comment.body = "Test comment"
    mock_pr.create_comment.return_value = mock_pr_comment
    
    # Act: Call the method to create a comment
    result_comment = interaction.add_pr_comment("Test comment")

    # Assert: Verify interactions
    mock_repo.get_pull.assert_called_once_with(123)
    mock_pr.create_comment.assert_called_once_with("Test comment")
    print(result_comment)
    assert result_comment.body == "Test comment"
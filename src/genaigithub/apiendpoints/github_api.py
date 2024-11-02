import logging

from github import Github
from flask import request, jsonify, Blueprint
from flask_cors import cross_origin
from datetime import datetime, timedelta

from genaigithub.config.env_config import github_token

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

MAX_REPOS_PER_PAGE = 5
MAX_PRS_PER_PAGE = 5

github_api = Blueprint('github_api', __name__)

@github_api.route("/pull_requests", methods=["GET"])
@cross_origin()
def get_all_open_pull_requests():
    github = Github(github_token)

    repo_name = request.args.get("repo_name")
    page = request.args.get("page", 0, type=int)

    if not repo_name:
        return jsonify({"error": "Repo name is required"}), 400

    repo = github.get_repo(repo_name)
    pulls = repo.get_pulls(state="open")
    page = pulls.get_page(page)
    total_count = pulls.totalCount

    prs_data = []
    count = 0
    for pr in page:
        pr_data = {
            "number": pr.number,
            "title": pr.title,
            "body": pr.body,
            "state": pr.state,
            "created_at": pr.created_at,
            "updated_at": pr.updated_at,
            "user": pr.user.login,
            "html_url": pr.html_url,
        }
        count += 1
        if count >= MAX_PRS_PER_PAGE:
            break
        prs_data.append(pr_data)

    return jsonify({"pull_requests": prs_data, "total_count": total_count})

@github_api.route("/repositories", methods=["GET"])
@cross_origin()
def get_all_repositories():
    github = Github(github_token)
    page = request.args.get("page", 0, type=int)
    organization = request.args.get("organization", "spring-projects")
    logger.info(f"Searching for issues in organization {organization}")
    # repos = github.get_organization(organization).get_repos()

    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    logger.info(f"Searching for issues created after {seven_days_ago}")
    issues = github.search_issues(
        f"type:pr review:none is:open created:>{seven_days_ago} is:unmerged org:{organization}"
    )
    logger.info(f"Found {issues.totalCount} issues")

    page = issues.get_page(page)

    total_count = issues.totalCount
    repos_data = []

    logger.info(f"Found {len(page)} issues")

    count = 0

    for issue in page:
        repo = issue.repository
        logger.info(f"Found repo {repo.full_name}")
        logger.info(f"Found issue {issue.title}")
        repo_name = repo.full_name
        if repo:
            repo_data = {
                "name": repo.name,
                "owner": repo.owner.login,
                "full_name": repo.full_name,
                "description": repo.description,
                "url": repo.html_url,
                "language": repo.language,
                "created_at": repo.created_at,
                "updated_at": repo.updated_at,
                "total_count": total_count,
            }
            if repo_name not in [r["full_name"] for r in repos_data]:
                repos_data.append(repo_data)
                count += 1
                if count >= MAX_REPOS_PER_PAGE:
                    break
            continue
        else:
            logger.error(f"No repo found for issue {issue.title}")

    return jsonify({"repositories": repos_data, "total_count": total_count})

from github import Github

from env_config import github_token, repo_name, pr_number


g = Github(github_token)
print(g)
repo = g.get_repo(repo_name)
pr = repo.get_pull(pr_number)

prs = repo.get_pulls()

print(prs)

print(pr.body)
print(repo)
print(pr)

pr.create_comment("hey there")
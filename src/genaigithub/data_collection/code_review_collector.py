# src/genaigithub/data_collection/code_review_collector.py
from typing import List, Dict, Any
from github import Github
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class CodeReviewCollector:
    def __init__(self, github_token: str):
        self.github = Github(github_token)
        
    def collect_historical_reviews(self, organization: str, days_back: int = 30) -> List[Dict[str, Any]]:
        """Collect historical code reviews from an organization."""
        collected_data = []
        cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        
        try:
            # Search for merged PRs with reviews
            query = f"org:{organization} is:pr is:merged updated:>{cutoff_date}"
            prs = self.github.search_issues(query)
            
            for pr in prs:
                repo = pr.repository
                pr_data = {
                    'pr_number': pr.number,
                    'title': pr.title,
                    'body': pr.body,
                    'created_at': pr.created_at,
                    'merged_at': pr.closed_at,
                    'repository': repo.full_name,
                    'reviews': [],
                    'changes': [],
                }
                
                # Get full PR object
                full_pr = repo.get_pull(pr.number)
                
                # Collect reviews
                for review in full_pr.get_reviews():
                    pr_data['reviews'].append({
                        'reviewer': review.user.login,
                        'state': review.state,
                        'body': review.body,
                        'submitted_at': review.submitted_at
                    })
                
                # Collect file changes
                for file in full_pr.get_files():
                    pr_data['changes'].append({
                        'filename': file.filename,
                        'status': file.status,
                        'additions': file.additions,
                        'deletions': file.deletions,
                        'patch': file.patch
                    })
                
                collected_data.append(pr_data)
                
            return collected_data
            
        except Exception as e:
            logger.error(f"Error collecting review data: {str(e)}")
            raise
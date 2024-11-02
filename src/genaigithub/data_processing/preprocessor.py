# src/genaigithub/data_processing/preprocessor.py
from typing import List, Dict, Any
import re
import logging
from langchain.text_splitter import RecursiveCharacterTextSplitter
from genaigithub.config.languages import LANGUAGE_MAPPING

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class CodeReviewPreprocessor:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        
    def get_cached_chunks(self, code_review) -> List[Dict]:
        """Convert cached CodeReview document to chunks with metadata"""
        chunks_with_metadata = []
        
        # Process basic PR info
        pr_chunk = {
            "text": f"""
                Repository: {code_review.repository}
                PR Number: {code_review.pr_number}
                Created At: {code_review.created_at}
            """,
            "metadata": {
                "repo_name": code_review.repository,
                "pr_number": code_review.pr_number,
                "type": "pr_info"
            }
        }
        chunks_with_metadata.append(pr_chunk)
        
        # Process code changes
        for change in code_review.changes:
            if change.patch:
                chunks = self.text_splitter.split_text(change.patch)
                for chunk in chunks:
                    chunks_with_metadata.append({
                        "text": chunk,
                        "metadata": {
                            "repo_name": code_review.repository,
                            "pr_number": code_review.pr_number,
                            "filename": change.filename,
                            "language": change.language,
                            "type": "code_change"
                        }
                    })
        
        # Process reviews if any
        for review in code_review.reviews:
            if review.comment:
                chunks = self.text_splitter.split_text(review.comment)
                for chunk in chunks:
                    chunks_with_metadata.append({
                        "text": chunk,
                        "metadata": {
                            "repo_name": code_review.repository,
                            "pr_number": code_review.pr_number,
                            "reviewer": review.reviewer,
                            "type": "review_comment"
                        }
                    })
        
        return chunks_with_metadata
 
    def process_all_data(self, pr_data: List[Dict], commits_data: List[Dict], 
                        files_data: List[Dict]) -> List[Dict]:
        """Process all PR data and return chunks with metadata"""
        chunks_with_metadata = []
        
        # Process PR data
        for data in pr_data:
            chunks = self._process_pr_chunk(data)
            chunks_with_metadata.extend(chunks)
            
        # Process commits
        for commit in commits_data:
            chunks = self._process_commit_chunk(commit)
            chunks_with_metadata.extend(chunks)
            
        # Process files
        for file in files_data:
            chunks = self._process_file_chunk(file)
            chunks_with_metadata.extend(chunks)
            
        return chunks_with_metadata
    
    def clean_code_snippet(self, code: str) -> str:
        """Clean code snippets by removing unnecessary whitespace and comments."""
        # Remove empty lines
        code = re.sub(r'\n\s*\n', '\n', code)
        # Remove trailing whitespace
        code = re.sub(r'\s+$', '', code, flags=re.MULTILINE)
        return code
    
    def process_review_data(self, review_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single review entry."""
        processed_data = {
            'metadata': {
                'pr_number': review_data['pr_number'],
                'repository': review_data['repository'],
                'created_at': review_data['created_at']
            },
            'changes': [],
            'reviews': []
        }
        
        # Process code changes
        for change in review_data['changes']:
            if change['patch']:
                extension = change['filename'].split('.')[-1]
                language = LANGUAGE_MAPPING.get(extension, 'python')
                
                processed_change = {
                    'filename': change['filename'],
                    'language': language,
                    'clean_patch': self.clean_code_snippet(change['patch']),
                    'stats': {
                        'additions': change['additions'],
                        'deletions': change['deletions']
                    }
                }
                processed_data['changes'].append(processed_change)
        
        # Process reviews
        for review in review_data['reviews']:
            if review['body']:
                processed_review = {
                    'reviewer': review['reviewer'],
                    'clean_comment': self.clean_code_snippet(review['body']),
                    'state': review['state']
                }
                processed_data['reviews'].append(processed_review)
        
        return processed_data

    def _process_pr_chunk(self, data: Dict) -> List[Dict]:
        content = f"""
            Repo Name: {data.get('repo_name', '')}
            PR Number: {data.get('pr_number', '')}
            Description: {data.get('description', '')}
            Changed Files: {', '.join(data.get('changed_files', []))}
            Comments: {' | '.join(data.get('comments', []))}
        """
        chunks = self.text_splitter.split_text(content)
        return [{
            "text": chunk,
            "metadata": {
                "repo_name": data["repo_name"],
                "pr_number": data["pr_number"],
                "type": "pr_info"
            }
        } for chunk in chunks]

    def _process_commit_chunk(self, commit: Dict) -> List[Dict]:
        """Process a single commit and return chunks with metadata"""
        # Format commit information into readable text
        content = f"""
            Commit ID: {commit.get('commit_id', '')}
            Author: {commit.get('commit_author', '')} <{commit.get('commit_author_email', '')}>
            Date: {commit.get('commit_date', '')}
            
            Commit Message:
            {commit.get('commit_message', '')}
        """
        
        chunks = self.text_splitter.split_text(content)
    
        return [{
            "text": chunk,
            "metadata": {
                "repo_name": commit.get("repo_name"),
                "pr_number": commit.get("pr_number"),
                "commit_id": commit.get("commit_id"),
                "commit_author": commit.get("commit_author"),
                "type": "commit"
            }
        } for chunk in chunks]

    def _process_file_chunk(self, file: Dict) -> List[Dict]:
        """Process a single file and return chunks with metadata"""
        chunks_with_metadata = []
        
        # Get file extension and determine language
        filename = file.get('filename', '')
        logger.info(f"filename {filename}")
        extension = filename.split(".")[-1]
        logger.info(f"extension {extension}")
        language = LANGUAGE_MAPPING.get(extension, 'unknown')
        logger.info(f"language {language}")
        
        if language == 'unknown':
            logger.warning(f"Unknown language for file {filename}")
            code_splitter = self.text_splitter
        else:
            # Create language-specific text splitter for code
            code_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                separators=RecursiveCharacterTextSplitter.get_separators_for_language(language)
            )
        
        # Process file metadata
        file_info = f"""
            File: {filename}
            Status: {file.get('status', '')}
            Changes: {file.get('changes', 0)} lines 
            (+{file.get('additions', 0)}, -{file.get('deletions', 0)})
        """
        
        # Add file info chunks
        info_chunks = self.text_splitter.split_text(file_info)
        chunks_with_metadata.extend([{
            "text": chunk,
            "metadata": {
                "repo_name": file.get("repo_name"),
                "pr_number": file.get("pr_number"),
                "filename": filename,
                "language": language,
                "type": "file_info"
            }
        } for chunk in info_chunks])
        
        # Process patch if available
        if file.get('patch'):
            patch_chunks = code_splitter.split_text(file['patch'])
            chunks_with_metadata.extend([{
                "text": chunk,
                "metadata": {
                    "repo_name": file.get("repo_name"),
                    "pr_number": file.get("pr_number"),
                    "filename": filename,
                    "language": language,
                    "type": "patch"
                }
            } for chunk in patch_chunks])
        
        # Process full file content if available
        if file.get('content'):
            try:
                content_chunks = code_splitter.split_text(file['content'])
                chunks_with_metadata.extend([{
                    "text": chunk,
                    "metadata": {
                        "repo_name": file.get("repo_name"),
                        "pr_number": file.get("pr_number"),
                        "filename": filename,
                        "language": language,
                        "type": "content"
                    }
                } for chunk in content_chunks])
            except Exception as e:
                logger.warning(f"Error processing file content for {filename}: {str(e)}")
        
        return chunks_with_metadata
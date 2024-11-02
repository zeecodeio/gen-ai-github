# src/genaigithub/data_collection/collect_and_process.py
from genaigithub.data_collection.code_review_collector import CodeReviewCollector
from genaigithub.data_processing.preprocessor import CodeReviewPreprocessor
from genaigithub.config.env_config import github_token

def collect_and_process_reviews():
    # Initialize collectors and processors
    collector = CodeReviewCollector(github_token)
    preprocessor = CodeReviewPreprocessor()
    
    # Collect raw data
    raw_data = collector.collect_historical_reviews("spring-projects", days_back=30)
    
    # Process each review
    processed_data = []
    for review_data in raw_data:
        processed_review = preprocessor.process_review_data(review_data)
        processed_data.append(processed_review)
    
    return processed_data
from genaigithub.github_pr_rag import *


def test_pr_review():
    pr_data = get_pr_data(repo_name, pr_number)
    # Process the PR data
    contents = get_repo_content(repo_name)
    pr_chunks = process_pr_data(pr_data, contents)
    
    # Create vectorstore
    vectorstore = create_vectorstore(pr_chunks)

    # Set up RAG
    qa_chain = setup_rag(vectorstore)
    # Generate PR review
    pr_review = review_pr(qa_chain)
    print(pr_review)
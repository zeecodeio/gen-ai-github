from flask import Flask, request, jsonify
from genaigithub.env_config import github_token, openai_api_key, default_repo_name, postgres_db, postgres_user, postgres_password
from genaigithub.github_pr_interaction import GitHubRAGPRInteraction
from genaigithub.rag_llm_processor import RAGLLMProcessor, PGVectorStore
from genaigithub.github_pr_interaction import GitHubRAGPRInteraction

app = Flask(__name__)

# Use PGVector for the vector store
pg_connection_string = f"postgresql+psycopg://{postgres_user}:{postgres_password}@localhost:6024/{postgres_db}"
vector_store = PGVectorStore(pg_connection_string)

# Create the processor with PGVector
processor = RAGLLMProcessor(openai_api_key, vector_store, model_name="gpt-4")

@app.route('/process_pr', methods=['POST'])
def process_pr():
    data = request.json
    pr_number = data.get('pr_number')
    repo_name = data.get('repo_name', default_repo_name)
    query = data.get('query', "What changes were made in the PR?")

    if not pr_number:
        return jsonify({"error": "PR number is required"}), 400
    
    if not repo_name:
        return jsonify({"error": "Repo name is required"}), 400

    github_pr_interaction = GitHubRAGPRInteraction(github_token, repo_name, pr_number)
    all_text = github_pr_interaction.process_pr_data()

    vector_store = processor.create_vector_store_from_string(all_text)
    qa_chain = processor.create_qa_chain(vector_store)

    response = processor.generate_response(qa_chain, query)

    return jsonify({
        "query": query,
        "response": response
    })

def run_server():
    app.run(host='0.0.0.0', port=5000)

if __name__ == "__main__":
    app.run(debug=True)

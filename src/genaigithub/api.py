import logging

from flask_cors import CORS
from flask import Flask, request, jsonify

from genaigithub.apiendpoints.github_api import github_api
from genaigithub.apiendpoints.analyzer_api import analyzer_api

app = Flask(__name__)

CORS(app, supports_credentials=True, origins=["http://localhost:4200"])  # Add This

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@app.before_request
def before_request():
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }
    if request.method.lower() == "options":
        return jsonify(headers), 200


@app.route("/hello", methods=["GET"])
def hello():
    return jsonify({"response": "hello"})


app.register_blueprint(github_api, url_prefix='/github')
app.register_blueprint(analyzer_api, url_prefix='/analyzer')


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
# gen-ai-github

## Getting Started

```
cp requirements-refs/$whatever requirements.txt
asdf local python 3.12.6
python -m venv venv
source venv/bin/activate
pip install -r requirements

pip install -e .
# and/or
pyproject-build .
pip install dist/gen_ai_github-0.0.1-py3-none-any.whl
```

## For Console Scripts 



```
[options.entry_points]
console_scripts =
    pr-reviewer-cli = genaigithub.cli:main
gui_scripts =
    pr-reviewer-api = genaigithub.api:run_server
```


## RAG

````python
# Initialize GitHub client
# Example usage
# Process the PR data
# Create vectorstore
# Set up RAG
# Generate PR review
```
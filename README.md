# gen-ai-github

## Getting Started

```
cp requirements-refs/$whatever requirements.txt
asdf local python 3.12.6
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Install from Source

```bash
pip install -e .
# and/or
pyproject-build .
pip install dist/gen_ai_github-0.0.1-py3-none-any.whl

```

## Entry Points

- API Server
- CLI

```
[options.entry_points]
console_scripts =
    pr-reviewer-cli = genaigithub.cli:main
gui_scripts =
    pr-reviewer-api = genaigithub.api:run_server
```

## Update .env file with the information used in the docker-compose-dev.yml file

## Running Locally

```bash
docker compose -f docker-compose-dev.yml up
pip install -e .
gunicorn --timeout 200 -w 4 'genaigithub.api:app'
```

## Running Locally with Docker

```bash
docker compose -f docker-compose.yml up
```





# gen-ai-github

## Getting Started

```
cp requirements-refs/$whatever requirements.txt
asdf local python 3.11.7
python --python $(which python)
pipenv shell
pipenv install
tox
pyproject-build .
```

## For Console Scripts 

- [setuptools entry-point](https://setuptools.pypa.io/en/latest/userguide/entry_point.html#)

```
[options.entry_points]
console_scripts =****
    hello-world = timmins:hello_world
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
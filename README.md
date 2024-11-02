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

supported languages
```python
{
    'cpp': 'cpp',
    'go': 'go', 
    'java': 'java',
    'kt': 'kotlin',
    'js': 'js',
    'ts': 'ts',
    'php': 'php',
    'proto': 'proto',
    'py': 'python',
    'rst': 'rst',
    'rb': 'ruby',
    'rs': 'rust',
    'scala': 'scala',
    'swift': 'swift',
    'md': 'markdown',
    'tex': 'latex',
    'html': 'html',
    'sol': 'sol',
    'cs': 'csharp',
    'cbl': 'cobol',
    'c': 'c',
    'lua': 'lua',
    'pl': 'perl',
    'hs': 'haskell',
    'ex': 'elixir',
    'ps1': 'powershell'
}
```

```
[options.entry_points]
console_scripts =
    pr-reviewer-cli = genaigithub.cli:main
gui_scripts =
    pr-reviewer-api = genaigithub.api:run_server
```


## RAG

```python

 response = processor.generate_response(qa_chain, question)
    history_messages = processor.get_chat_history()

    history = [{"question": msg.content, "response": next_msg.content}
           for msg, next_msg in zip(history_messages[::2], history_messages[1::2])]

    history = history[::-1]

    return jsonify({
        "question": question,
        "response": response,
        "history": history,
        "repo_name": repo_name,
        "pr_number": pr_number
    })

def generate_response(self, qa_chain: ConversationalRetrievalChain, query: str, context) -> str:
        """Generate a response using the QA chain."""
        prompt_content = self.contextualize_prompt.format_messages(chat_history=context, input=query)
        # Log the prompt
        logger.info("Prompt used for qa_chain:")
        for message in prompt_content:
            logger.info(f"{message.type.capitalize()} message: {message.content}")
        response = qa_chain.invoke({"input": query, "chat_history": context})["answer"]
        self.memory.save_context({"input": query}, {"output": response})
        self.chat_history.extend(
            [
                HumanMessage(content=query),
                AIMessage(content=response),
            ]
        )
        return response
# Initialize GitHub client
# Example usage
# Process the PR data
# Create vectorstore
# Set up RAG
# Generate PR review
```

```bash
kubectl run -n genaigithub dns-test --image=busybox:1.28 --rm -i --restart=Never -- nc -zv postgres 5432
```

```bash
kubectl exec -n genaigithub deploy/genaigithub -- python3 -c "
import psycopg
import os
print(os.environ['POSTGRES_HOST'])
print(os.environ['POSTGRES_PORT'])
print(os.environ['POSTGRES_USER'])
print(os.environ['POSTGRES_PASSWORD'])

try:
    conn = psycopg.connect(
        dbname='vectorstore',
        user='vectorstore',
        password='1stAccess',
        host='postgres',
        port='5432'
    )
    print('Connection successful!')
    conn.close()
except Exception as e:
    print(f'Connection failed: {e}')
"
```
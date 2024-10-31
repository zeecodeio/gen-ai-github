apiVersion: v1
kind: Secret
namespace: genaigithub
metadata:
  name: genaigithub-secret
  labels:
    app: genaigithub
type: Opaque
data:
  POSTGRES_DB: vectorstore
  POSTGRES_USER: vectorstore
  POSTGRES_PASSWORD: op://Private/k8s-postgres/password
  OPENAI_API_KEY: op://Private/openai-api-key/password
  GITHUB_TOKEN: op://Private/github-pat/password
  POSTGRES_PORT: 5432
  POSTGRES_HOST: postgres
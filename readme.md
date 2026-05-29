# Health Monitoring System

Minimal demo project for a contract-first OpenAPI workflow.

## Run Backend and Database

From the project root:

```bash
docker compose up -d --build backend postgres
```

The backend will be available at:

```text
http://localhost:8000
```

PostgreSQL runs in Docker Compose and is reached by the backend through the Docker service name:

```text
postgres:5432
```

## Optional: Populate Demo Data

```bash
docker compose exec backend python -m app.seed
```

## Run Frontend Locally

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at the URL printed by Vite, usually:

```text
http://localhost:5173
```

## Useful Check

```bash
curl http://localhost:8000/v1/health
```

## Project Structure

```text
openapi/      OpenAPI contract used as the source of truth
generated/    Code generated from the OpenAPI contract
backend/      Real FastAPI backend implementation
frontend/     React + Vite frontend using the generated TypeScript SDK
docs/         Manual test commands and support material
compose.yaml  Docker Compose setup for backend and PostgreSQL
```

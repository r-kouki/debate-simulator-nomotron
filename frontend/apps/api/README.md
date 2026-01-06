# Debate Simulator API

Fastify + TypeScript backend for the Debate Simulator. Includes SQLite (Prisma), OpenRouter LLM proxy, SSE debate streaming, and Zod validation.

## Setup

```bash
# From repo root
cd packages/contracts
npm install
npm run build

cd ../../apps/api
npm install
cp .env.example .env
npm run prisma:generate
npm run prisma:migrate
npm run dev
```

## Environment

Required:
- `OPENROUTER_API_KEY`

Optional:
- `OPENROUTER_MODEL` (default `nvidia/nemotron-nano-9b-v2:free`)
- `OPENROUTER_SITE_URL` (sent as HTTP-Referer)
- `OPENROUTER_APP_NAME` (sent as X-Title)
- `OPENROUTER_USE_WEB` (true/false; if true uses `:online` model)
- `FRONTEND_ORIGIN` (default `http://localhost:5173`)
- `DATABASE_URL` (default `file:./dev.db`)

## Connecting the Frontend

Set the frontend base URL to the API (default `http://localhost:4000`). CORS is enabled for `FRONTEND_ORIGIN`.

## API Docs

Swagger UI at:
- `http://localhost:4000/docs`

## Mocking / Testing

To run tests, ensure the DB schema is migrated:

```bash
npm run prisma:migrate
npm run test
```

## Notes

- The API never exposes the OpenRouter key to clients.
- SSE stream: `GET /debates/:id/stream`
- Cancel AI-vs-AI: `POST /debates/:id/cancel`

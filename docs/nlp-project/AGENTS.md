# Repository Guidelines

## Project Structure & Module Organization
The core Python runtime lives in `src/` (agents, orchestration, serving, training, utils). Runnable entry points are in `scripts/` (training, evaluation, server, dataset generation). Frontend UI lives in `frontend/`, while a TypeScript API service lives in `frontend/apps/api/`. Local assets and artifacts are in `data/` (JSONL splits), `models/` (base model and LoRA adapters), and `runs/` (training, eval, debate outputs).

## Build, Test, and Development Commands
- `python -m venv .venv && source .venv/bin/activate`: create and activate a Python venv.
- `pip install -r requirements.txt`: install backend dependencies.
- `python scripts/run_server.py [--no-model]`: run the Python API server; use `--no-model` for quick startup.
- `python scripts/run_debate.py "Topic" --rounds 2`: run a local multi-agent debate.
- `cd frontend && npm install`: install UI dependencies.
- `cd frontend && npm run dev`: start the Vite UI server.
- `cd frontend/apps/api && npm install`: install API service dependencies.
- `cd frontend/apps/api && npm run dev`: run the TypeScript API service.

## Coding Style & Naming Conventions
Python follows 4-space indentation and PEP 8 style; keep modules focused (for example, `src/agents/` for agent logic). TypeScript follows ESLint and Prettier settings in `frontend/`; use PascalCase for React components and `use*` for hooks. Keep filenames aligned to their feature or module (for example, `frontend/src/features/debate/`).

## Testing Guidelines
Frontend tests use Vitest: `cd frontend && npm run test`. The API service uses Vitest too: `cd frontend/apps/api && npm run test`. There is no Python test runner configured; use `python scripts/verify_base_model.py` or `python qlora_smoke_test.py` as smoke checks when modifying training or model loading.

## Commit & Pull Request Guidelines
Git history is minimal, so no enforced commit convention exists. Use short, imperative summaries (optionally with a scope, like `frontend:`). PRs should include a clear description, linked issues when relevant, and a list of commands run. For UI changes, add screenshots or GIFs; for model/data changes, note dataset or adapter paths touched.

## Configuration & Environment Tips
The Python server expects local model files under `models/base/` and adapters under `models/adapters/`. The UI can target a live API with `VITE_API_BASE_URL` or use mocks via `VITE_USE_MOCKS=true`. The TypeScript API uses `OPENROUTER_*` and `DATABASE_URL` env vars (see `frontend/apps/api/src/utils/env.ts`).

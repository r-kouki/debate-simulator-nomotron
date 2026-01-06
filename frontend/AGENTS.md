# Repository Guidelines

This repository contains the Debate Simulator UI, a React 18 + TypeScript + Vite app
with a Windows 98-inspired interface and a mockable API layer.

## Project Structure & Module Organization
- `src/main.tsx` boots the app; `src/app/` hosts the top-level app shell.
- `src/api/` centralizes API adapters, types, and React Query hooks.
- `src/components/` and `src/features/` hold reusable UI and feature modules.
- `src/state/` stores global state (Zustand), `src/styles/` holds styling.
- `public/` stores static assets; `tests/` holds Vitest specs like `app.test.tsx`.

## Build, Test, and Development Commands
- `npm install`: install dependencies.
- `npm run dev`: start the local Vite dev server.
- `npm run build`: typecheck and build the production bundle.
- `npm run preview`: serve the production build locally.
- `npm run test`: run Vitest in CI mode.
- `npm run lint`: run ESLint for TypeScript and React rules.
- `npm run format`: apply Prettier formatting to the repo.

## Coding Style & Naming Conventions
Use TypeScript and React function components. Format with Prettier (double quotes,
semicolons, no trailing commas, 100-char lines) and follow ESLint rules.
Name components in PascalCase, hooks with a `use` prefix, and keep files aligned
with their feature or component purpose (for example, `src/features/Scoreboard/`).

## Testing Guidelines
Tests use Vitest with jsdom and Testing Library; setup lives in `vitest.setup.ts`.
Place tests in `tests/` and follow the `*.test.tsx` naming pattern. No explicit
coverage threshold is defined, so add tests for new behaviors and regressions.

## Commit & Pull Request Guidelines
No git history is available in this checkout, so no commit convention is enforced.
Use short, imperative commit summaries and keep related changes grouped together.
For PRs, include a clear description, link relevant issues, list test commands
run, and attach screenshots or GIFs for UI changes.

## Configuration & Mocking
Set `VITE_API_BASE_URL` to target a live API. Set `VITE_USE_MOCKS=true` to force
mock mode (also used when no base URL is configured). API selection lives in
`src/api/adapter.ts`.

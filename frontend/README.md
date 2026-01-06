# Debate Simulator (Win98 UI)

A Windows 98-inspired debate game UI built with React 18 + TypeScript + Vite. Includes draggable/resizable windows, start menu, taskbar, and mock API mode.

## Setup

```bash
npm install
npm run dev
```

## Env Vars

- `VITE_API_BASE_URL` - Base URL for your API.
- `VITE_USE_MOCKS` - Set to `true` to force mock adapter.

Example:

```bash
VITE_API_BASE_URL=https://api.example.com
VITE_USE_MOCKS=false
```

## Mock Mode

Mock mode is enabled when `VITE_USE_MOCKS=true` or when `VITE_API_BASE_URL` is missing. You can also toggle mock mode in the Settings window.

## API Adapter

All API calls are centralized in:

- `src/api/adapter.ts` (adapter interface + selection)
- `src/api/client.ts` (fetch wrapper)
- `src/api/mocks/mockAdapter.ts` (mock data)
- `src/api/types.ts` (OpenAPI-like TypeScript types)

Update `src/api/adapter.ts` if your endpoints differ. React Query hooks live in `src/api/hooks/*`.

## Tests

```bash
npm run test
```

### Manual Smoke Checklist

- Open Start menu, launch New Debate, start a session.
- Send a turn, observe AI response + live scoring.
- End & Score, confirm Match Results window shows.
- Search a topic in Topic Explorer and add it to a debate.
- Open Scoreboard, update username, and verify achievements list.

## Project Structure

```
src/
  app/
  api/
  components/
  features/
  state/
  styles/
  utils/
```

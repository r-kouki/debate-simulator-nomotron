# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Windows 98-inspired debate game UI built with React 18 + TypeScript + Vite. Features draggable/resizable windows, start menu, taskbar, and a mockable API layer with automatic fallback.

## Development Commands

```bash
npm install          # Install dependencies
npm run dev          # Start Vite dev server (http://localhost:5173)
npm run build        # Typecheck and build production bundle
npm run test         # Run Vitest tests
npm run lint         # Run ESLint
npm run format       # Apply Prettier formatting
```

## Connecting to Backend

The frontend can connect to two different backends:

1. **Python backend** (parent repo): `python scripts/run_server.py` runs at `http://localhost:8000`
2. **Node API** (`apps/api/`): Fastify server with Prisma/SQLite at `http://localhost:4000`

Set `VITE_API_BASE_URL` to your backend URL. Without it, mock mode is enabled.

## Architecture

```
src/
├── app/                    # App shell, QueryClient setup
├── api/
│   ├── adapter.ts          # API adapter selection + fallback logic
│   ├── client.ts           # Fetch wrapper
│   ├── types.ts            # Request/response TypeScript types
│   ├── hooks/              # React Query hooks (useTopicSearch, useStartDebate, etc.)
│   ├── mocks/mockAdapter.ts
│   └── openRouterAdapter.ts
├── components/             # Reusable UI (WindowFrame, Taskbar, Desktop, etc.)
├── features/               # Feature modules
│   ├── debate/             # NewDebateWindow, DebateSessionWindow, MatchResultsWindow
│   ├── topics/             # TopicExplorerWindow
│   ├── profile/            # ScoreboardWindow
│   └── settings/           # SettingsWindow, HelpWindow, AboutWindow
├── state/                  # Zustand stores
│   ├── windowStore.ts      # Window open/close/minimize/focus/maximize state
│   ├── debateStore.ts      # Active debate session state
│   ├── settingsStore.ts    # User preferences, mock mode toggle
│   ├── profileStore.ts     # Player profile and achievements
│   └── windowDefinitions.ts # Window types and default positions
└── utils/                  # Helpers (env.ts, windowUtils.ts)

apps/api/                   # Optional Fastify backend
├── src/
│   ├── routes/             # health, profile, topics, debates
│   ├── services/           # db, openRouterClient, debates
│   └── agents/             # researchAgent, debaterAgent, judgeAgent
└── prisma/                 # SQLite schema

packages/contracts/         # Shared Zod schemas and types
```

## Key Patterns

**API Adapter with Fallback**: `src/api/adapter.ts` wraps all API calls. When the primary API fails, it automatically falls back to mock data and opens a Connection Status window.

**Window System**: Windows are defined in `windowDefinitions.ts` with types, default rects, and icons. State is managed by `windowStore.ts` (Zustand). `WindowManager.tsx` renders open windows using `react-rnd`.

**Debate Flow**:
1. `NewDebateWindow` - Configure topic, mode, stance, difficulty
2. `DebateSessionWindow` - Live debate with timer, transcript, live scoring
3. `MatchResultsWindow` - Final scores and achievements

**State Pattern**: All global state uses Zustand stores in `src/state/`. Feature components access stores via hooks.

## Environment Variables

- `VITE_API_BASE_URL` - Backend URL (if missing, uses mocks)
- `VITE_USE_MOCKS` - Force mock mode (`true`/`false`)
- `VITE_OPENROUTER_API_KEY` - Optional OpenRouter key for direct LLM calls

## Node API Setup (apps/api)

```bash
cd packages/contracts && npm install && npm run build
cd ../../apps/api
npm install
cp .env.example .env
npm run prisma:generate
npm run prisma:migrate
npm run dev   # Runs at http://localhost:4000
```

Requires `OPENROUTER_API_KEY` in `.env`.

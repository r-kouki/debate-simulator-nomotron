# Debate Simulator XP

A nostalgic Windows XP-themed React interface for the CrewAI multi-agent debate system.

![Debate Simulator XP](./docs/screenshot.png)

## Features

- **Windows XP Desktop Environment**
  - Draggable/resizable windows
  - Start menu with programs
  - Taskbar with window management
  - Desktop icons
  - System tray with clock

- **Debate Management**
  - Create new debates with custom topics
  - Configure rounds (1-5)
  - Domain-specific adapters
  - Real-time progress tracking
  - Results viewing with export options

- **API Integration**
  - FastAPI backend with SSE streaming
  - React Query for data fetching
  - Zustand for state management

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.10+
- pnpm or npm

### Installation

1. Install frontend dependencies:
```bash
cd frontend-xp
npm install
```

2. Install backend dependencies (if not already done):
```bash
pip install fastapi uvicorn
```

### Running the Application

1. Start the backend server:
```bash
python scripts/run_xp_server.py
```
The API server runs on `http://localhost:8001`

2. Start the frontend development server:
```bash
cd frontend-xp
npm run dev
```
The frontend runs on `http://localhost:5174`

## Project Structure

```
frontend-xp/
├── src/
│   ├── api/              # API client and hooks
│   ├── components/       # React components
│   │   ├── Desktop/      # Desktop environment
│   │   ├── Window/       # Window management
│   │   ├── Taskbar/      # Taskbar components
│   │   ├── DebateCreator/
│   │   ├── DebateViewer/
│   │   ├── ResultsViewer/
│   │   ├── History/
│   │   ├── Settings/
│   │   ├── About/
│   │   ├── MyComputer/
│   │   └── Common/
│   ├── hooks/            # Custom React hooks
│   ├── stores/           # Zustand state stores
│   ├── styles/           # CSS styles
│   └── types/            # TypeScript types
├── public/               # Static assets
└── package.json
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | New Debate |
| `Ctrl+H` | Debate History |
| `Ctrl+,` | Settings |
| `Alt+F4` | Close Window |
| `Alt+Tab` | Cycle Windows |
| `Escape` | Close Menu |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/debates` | Create debate |
| GET | `/api/debates` | List debates |
| GET | `/api/debates/:id` | Get debate |
| DELETE | `/api/debates/:id` | Delete debate |
| POST | `/api/debates/:id/stop` | Stop debate |
| GET | `/api/debates/:id/stream` | SSE progress |
| GET | `/api/settings` | Get settings |
| PUT | `/api/settings` | Update settings |
| GET | `/api/adapters` | List adapters |

## Tech Stack

- **Frontend**
  - React 18
  - TypeScript
  - Vite
  - TailwindCSS
  - Zustand
  - React Query
  - Framer Motion

- **Backend**
  - FastAPI
  - Python 3.10+
  - Uvicorn
  - CrewAI (optional)

## Development

### Building for Production

```bash
cd frontend-xp
npm run build
```

### Running Tests

```bash
npm run test
```

### Linting

```bash
npm run lint
```

## Configuration

Environment variables can be set in `.env`:

```env
VITE_API_URL=http://localhost:8001/api
```

## License

MIT License - See LICENSE file for details.

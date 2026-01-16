# Debate Simulator XP - Windows XP Themed Frontend

A nostalgic Windows XP-themed frontend for the CrewAI Debate Simulator. This interface provides a retro desktop experience while running actual AI-powered debates using local LLM models.

## 🖥️ Overview

The system consists of two main components:

1. **Frontend** (`frontend-xp/`) - React + TypeScript + Vite application with Windows XP styling
2. **Backend** (`scripts/run_xp_server.py`) - FastAPI server that or
chestrates CrewAI debates

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Port 4040)                      │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐ │
│  │ New Debate  │  │Debate Viewer │  │  CrewAI Status      │ │
│  │   Window    │──│   Window     │  │     Window          │ │
│  └─────────────┘  └──────────────┘  └─────────────────────┘ │
│         │              ▲                     │              │
│         │              │ SSE Stream          │              │
│         ▼              │                     ▼              │
└─────────────────────────────────────────────────────────────┘
                    │                          │
                    ▼                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Backend (Port 5040)                        │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                   FastAPI Server                        ││
│  │  POST /api/debates        - Create new debate           ││
│  │  GET  /api/debates/{id}/stream - SSE progress stream    ││
│  │  GET  /api/crewai/status  - System status               ││
│  │  GET  /api/health         - Health check                ││
│  └─────────────────────────────────────────────────────────┘│
│                          │                                   │
│                          ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                     DebateCrew                          ││
│  │  - DualModelManager (Pro & Con models)                  ││
│  │  - Domain Router (auto-selects adapter)                 ││
│  │  - Fact Checker                                         ││
│  │  - Judge Agent                                          ││
│  └─────────────────────────────────────────────────────────┘│
│                          │                                   │
│                          ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐│
│  │           Llama 3.1 Nemotron Nano 8B                    ││
│  │           + Domain LoRA Adapters                        ││
│  │           (debate, education, medicine, ecology)        ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.12+ with virtual environment
- Node.js 18+
- NVIDIA GPU with ~14GB+ VRAM
- Base model at `models/base/llama3.1-nemotron-nano-8b-v1/`

### Start the Backend

```bash
cd /home/remote-core/project/debate-simulator-nomotron
source .venv/bin/activate
python scripts/run_xp_server.py
```

The backend will start on **port 5040** and display:
```
============================================================
Debate Simulator XP - API Server
============================================================
CrewAI Available: True
Server Port: 5040
============================================================
```

### Start the Frontend

```bash
cd /home/remote-core/project/debate-simulator-nomotron/frontend-xp
npm install  # First time only
npm run dev
```

The frontend will start on **port 4040**. Open http://localhost:4040 in your browser.

## 📁 Project Structure

### Frontend (`frontend-xp/`)

```
frontend-xp/
├── src/
│   ├── components/
│   │   ├── DebateCreator/     # New Debate window
│   │   ├── DebateViewer/      # Real-time debate display
│   │   ├── CrewAIStatus/      # System status monitor
│   │   ├── Desktop/           # XP desktop, icons, taskbar
│   │   ├── Window/            # Base window component
│   │   └── ...
│   ├── stores/                # Zustand state management
│   │   ├── debateStore.ts     # Debate state
│   │   ├── windowStore.ts     # Window management
│   │   └── uiStore.ts         # UI state, notifications
│   ├── api/                   # API client
│   ├── types/                 # TypeScript types
│   └── styles/                # Global CSS (XP theme)
├── package.json
└── vite.config.ts
```

### Backend (`scripts/run_xp_server.py`)

Key components:

| Component | Description |
|-----------|-------------|
| `DebateSession` | Pydantic model for debate state |
| `DebateArgument` | Model for individual arguments |
| `JudgeScore` | Model for judge results |
| `run_crewai_debate()` | Async function that runs CrewAI in background |
| `stream_debate_progress()` | SSE endpoint for real-time updates |

## 🔌 API Endpoints

### Create Debate
```http
POST /api/debates
Content-Type: application/json

{
  "topic": "Should AI be regulated?",
  "rounds": 2,
  "use_internet": false,
  "recommend_guests": false,
  "domain": "auto"
}
```

Response:
```json
{
  "id": "debate-abc123",
  "status": "created",
  "message": "Debate created and starting..."
}
```

### Stream Debate Progress (SSE)
```http
GET /api/debates/{debate_id}/stream
Accept: text/event-stream
```

Event types sent via SSE:
- `debate_started` - Debate initialized, includes topic
- `log` - Progress log messages
- `argument` - New argument generated (includes `side`, `content`, `round`)
- `debate_complete` - Debate finished (includes `winner`, `judgeScore`)
- `error` - Error occurred (includes `message`)

### CrewAI Status
```http
GET /api/crewai/status
```

Returns:
```json
{
  "available": true,
  "packages": {
    "crewai": {"installed": true, "version": "1.8.0"},
    "torch": {"installed": true, "version": "2.9.0"},
    ...
  },
  "gpu": {
    "name": "NVIDIA RTX A6000",
    "memory_total_mb": 49140,
    "memory_used_mb": 14036,
    "memory_free_mb": 35104
  },
  "venv_active": true,
  "python_version": "3.12.3"
}
```

## 🎨 Frontend Components

### DebateCreatorWindow
- Topic input field
- Round selector (1-5 rounds)
- Domain selector (auto-detect, education, medicine, etc.)
- Options: internet research, guest recommendations
- Creates debate via backend API

### DebateViewerWindow
- Real-time argument display (Pro vs Con columns)
- Verbose logs panel with timestamped messages
- Connection status indicator
- Winner announcement when complete

### CrewAIStatusWindow
- GPU status with VRAM usage bar
- Package versions grid
- Virtual environment status
- Setup instructions if CrewAI unavailable

## 🔄 Data Flow

1. **User creates debate** → `DebateCreatorWindow` calls `POST /api/debates`
2. **Backend creates session** → Returns debate ID, starts `run_crewai_debate()` in background
3. **Frontend connects to SSE** → `DebateViewerWindow` opens EventSource to `/api/debates/{id}/stream`
4. **CrewAI generates arguments** → Backend queues events, SSE stream delivers them
5. **Frontend updates UI** → Each event updates Zustand store, React re-renders
6. **Debate completes** → `debate_complete` event sent, winner displayed

## ⚙️ Configuration

### Frontend Environment Variables

Create `frontend-xp/.env`:
```
VITE_API_URL=http://localhost:5040/api
```

### Backend Configuration

The backend auto-detects:
- Project root path
- Model directories (`models/base/`, `models/adapters/`)
- Output directory (`runs/debates/`)

## 🐛 Troubleshooting

### "Connection Error" in Debate Viewer
1. Check backend is running: `curl http://localhost:5040/api/health`
2. Check CrewAI status: Click "Check CrewAI Status" button
3. Verify GPU has enough VRAM (needs ~14GB for both models)

### "CrewAI Not Available"
1. Ensure virtual environment is activated
2. Check packages: `pip list | grep crewai`
3. Verify model files exist in `models/base/`

### Debate Stuck on "Waiting for arguments"
1. Check backend terminal for errors
2. First debate takes ~50 seconds (model loading)
3. Subsequent debates are faster (~30 seconds)

## 📊 Typical Debate Timeline

| Time | Event |
|------|-------|
| 0s | Debate created |
| 1-15s | Pro model loading (first time) |
| 15-30s | Con model loading (first time) |
| 30-40s | Arguments generated |
| 40-45s | Fact checking |
| 45-50s | Judge scoring |
| 50s | Complete |

## 🛠️ Development

### Frontend
```bash
cd frontend-xp
npm run dev      # Development server
npm run build    # Production build
npm run test     # Run tests
```

### Backend
```bash
source .venv/bin/activate
python scripts/run_xp_server.py  # With auto-reload
```

## 📝 License

This project is part of the Debate Simulator Nomotron system.

---

Built with 💙 and nostalgia for Windows XP

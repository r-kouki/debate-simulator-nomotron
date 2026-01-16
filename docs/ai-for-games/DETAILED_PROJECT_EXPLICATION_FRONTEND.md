# FRONTEND & API DOCUMENTATION

> **Complete Technical Documentation of the Frontend System**
>
> This document covers the React frontend, Node.js API alternative, and shared contracts.

---

## TABLE OF CONTENTS

1. [Frontend Architecture Overview](#1-frontend-architecture-overview)
2. [Windows 98 Theme Components](#2-windows-98-theme-components)
3. [State Management (Zustand)](#3-state-management-zustand)
4. [API Layer & React Query](#4-api-layer--react-query)
5. [Feature Modules](#5-feature-modules)
6. [Node.js Backend Alternative](#6-nodejs-backend-alternative)
7. [Shared Contracts (Zod)](#7-shared-contracts-zod)
8. [Build & Development](#8-build--development)

---

## 1. FRONTEND ARCHITECTURE OVERVIEW

### 1.1 Technology Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| **React** | 18.x | UI framework |
| **TypeScript** | 5.x | Type safety |
| **Vite** | 5.x | Build tool & dev server |
| **Zustand** | 4.x | State management |
| **React Query** | 5.x | Data fetching & caching |
| **CSS Modules** | - | Scoped styling |
| **Vitest** | 1.x | Unit testing |
| **ESLint** | 8.x | Code quality |

### 1.2 Directory Structure

```
frontend/
├── src/
│   ├── api/                      # API layer
│   │   ├── adapters/             # API implementations
│   │   │   ├── mock.ts           # Mock adapter for testing
│   │   │   └── openRouter.ts     # OpenRouter cloud adapter
│   │   ├── hooks/                # React Query hooks
│   │   │   ├── useHealth.ts
│   │   │   ├── useStartDebate.ts
│   │   │   ├── useNextTurn.ts
│   │   │   ├── useSendTurn.ts
│   │   │   ├── useScoreDebate.ts
│   │   │   ├── useTopics.ts
│   │   │   └── useProfile.ts
│   │   └── client.ts             # Base API client
│   │
│   ├── components/               # Shared UI components
│   │   ├── WindowFrame/          # Draggable window
│   │   │   ├── WindowFrame.tsx
│   │   │   └── WindowFrame.module.css
│   │   ├── Taskbar/              # Bottom taskbar
│   │   ├── StartMenu/            # Windows start menu
│   │   ├── Desktop/              # Main canvas
│   │   ├── ContextMenu/          # Right-click menus
│   │   ├── DialogHost/           # Modal dialogs
│   │   ├── Tabs/                 # Tab navigation
│   │   └── ToastContainer/       # Notifications
│   │
│   ├── features/                 # Feature modules
│   │   ├── debate/               # Debate UI
│   │   │   ├── DebateWindow.tsx
│   │   │   ├── DebateHistory.tsx
│   │   │   ├── ArgumentCard.tsx
│   │   │   └── ScoreDisplay.tsx
│   │   ├── topics/               # Topic browser
│   │   │   ├── TopicsWindow.tsx
│   │   │   └── TopicCard.tsx
│   │   ├── profile/              # User profile
│   │   │   ├── ProfileWindow.tsx
│   │   │   └── ProfileForm.tsx
│   │   └── settings/             # Settings panel
│   │       ├── SettingsWindow.tsx
│   │       └── SettingsForm.tsx
│   │
│   ├── state/                    # Zustand stores
│   │   ├── windowStore.ts        # Window management
│   │   ├── debateStore.ts        # Debate state
│   │   ├── settingsStore.ts      # User preferences
│   │   └── profileStore.ts       # Player profile
│   │
│   ├── styles/                   # Global styles
│   │   ├── globals.css
│   │   └── win98.css             # Windows 98 theme
│   │
│   ├── types/                    # TypeScript types
│   │   └── index.ts
│   │
│   ├── App.tsx                   # Root component
│   ├── main.tsx                  # Entry point
│   └── vite-env.d.ts
│
├── apps/api/                     # Node.js backend (alternative)
│   ├── src/
│   │   ├── routes/               # Fastify routes
│   │   ├── agents/               # Simplified agents
│   │   └── index.ts
│   └── prisma/
│       └── schema.prisma         # SQLite schema
│
├── packages/contracts/           # Shared Zod schemas
│   └── src/
│       └── index.ts
│
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── vitest.config.ts
```

### 1.3 Design Philosophy

The frontend uses a **Windows 98-inspired UI** for nostalgia and distinct visual identity:

- **Draggable Windows**: Each feature opens in a movable, resizable window
- **Taskbar**: Shows open windows at the bottom
- **Start Menu**: Access to all features
- **Classic Styling**: Beveled edges, system colors, bitmap fonts

---

## 2. WINDOWS 98 THEME COMPONENTS

### 2.1 WindowFrame Component

```typescript
// components/WindowFrame/WindowFrame.tsx
import React, { useState, useRef, useCallback } from 'react';
import styles from './WindowFrame.module.css';

interface WindowFrameProps {
  title: string;
  icon?: string;
  children: React.ReactNode;
  initialPosition?: { x: number; y: number };
  initialSize?: { width: number; height: number };
  onClose?: () => void;
  onMinimize?: () => void;
  onMaximize?: () => void;
  isActive?: boolean;
  resizable?: boolean;
  minimizable?: boolean;
  maximizable?: boolean;
}

export const WindowFrame: React.FC<WindowFrameProps> = ({
  title,
  icon,
  children,
  initialPosition = { x: 100, y: 100 },
  initialSize = { width: 400, height: 300 },
  onClose,
  onMinimize,
  onMaximize,
  isActive = true,
  resizable = true,
  minimizable = true,
  maximizable = true,
}) => {
  const [position, setPosition] = useState(initialPosition);
  const [size, setSize] = useState(initialSize);
  const [isDragging, setIsDragging] = useState(false);
  const [isResizing, setIsResizing] = useState(false);
  const [isMaximized, setIsMaximized] = useState(false);

  const frameRef = useRef<HTMLDivElement>(null);
  const dragOffset = useRef({ x: 0, y: 0 });

  // Drag handling
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (e.target !== e.currentTarget) return;

    setIsDragging(true);
    dragOffset.current = {
      x: e.clientX - position.x,
      y: e.clientY - position.y,
    };
  }, [position]);

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (isDragging) {
      setPosition({
        x: e.clientX - dragOffset.current.x,
        y: e.clientY - dragOffset.current.y,
      });
    }
  }, [isDragging]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
    setIsResizing(false);
  }, []);

  // Maximize toggle
  const handleMaximize = useCallback(() => {
    if (isMaximized) {
      setIsMaximized(false);
    } else {
      setIsMaximized(true);
    }
    onMaximize?.();
  }, [isMaximized, onMaximize]);

  return (
    <div
      ref={frameRef}
      className={`${styles.window} ${isActive ? styles.active : ''} ${isMaximized ? styles.maximized : ''}`}
      style={{
        left: isMaximized ? 0 : position.x,
        top: isMaximized ? 0 : position.y,
        width: isMaximized ? '100%' : size.width,
        height: isMaximized ? '100%' : size.height,
      }}
    >
      {/* Title bar */}
      <div
        className={styles.titleBar}
        onMouseDown={handleMouseDown}
      >
        {icon && <img src={icon} alt="" className={styles.icon} />}
        <span className={styles.title}>{title}</span>

        <div className={styles.controls}>
          {minimizable && (
            <button
              className={styles.controlButton}
              onClick={onMinimize}
              title="Minimize"
            >
              _
            </button>
          )}
          {maximizable && (
            <button
              className={styles.controlButton}
              onClick={handleMaximize}
              title={isMaximized ? 'Restore' : 'Maximize'}
            >
              {isMaximized ? '❐' : '□'}
            </button>
          )}
          <button
            className={`${styles.controlButton} ${styles.closeButton}`}
            onClick={onClose}
            title="Close"
          >
            ×
          </button>
        </div>
      </div>

      {/* Content */}
      <div className={styles.content}>
        {children}
      </div>

      {/* Resize handle */}
      {resizable && !isMaximized && (
        <div className={styles.resizeHandle} />
      )}
    </div>
  );
};
```

### 2.2 WindowFrame CSS

```css
/* components/WindowFrame/WindowFrame.module.css */
.window {
  position: absolute;
  background: #c0c0c0;
  border: 2px solid;
  border-color: #ffffff #808080 #808080 #ffffff;
  box-shadow: 1px 1px 0 0 #000000;
  display: flex;
  flex-direction: column;
  min-width: 200px;
  min-height: 100px;
}

.window.maximized {
  border: none;
  box-shadow: none;
}

.titleBar {
  background: linear-gradient(90deg, #000080, #1084d0);
  color: white;
  padding: 2px 4px;
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: move;
  user-select: none;
}

.window:not(.active) .titleBar {
  background: linear-gradient(90deg, #808080, #a0a0a0);
}

.icon {
  width: 16px;
  height: 16px;
}

.title {
  flex: 1;
  font-weight: bold;
  font-size: 11px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.controls {
  display: flex;
  gap: 2px;
}

.controlButton {
  width: 16px;
  height: 14px;
  background: #c0c0c0;
  border: 1px solid;
  border-color: #ffffff #808080 #808080 #ffffff;
  font-size: 9px;
  font-weight: bold;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}

.controlButton:active {
  border-color: #808080 #ffffff #ffffff #808080;
}

.closeButton {
  color: #000000;
}

.content {
  flex: 1;
  overflow: auto;
  padding: 8px;
  background: #c0c0c0;
}

.resizeHandle {
  position: absolute;
  right: 0;
  bottom: 0;
  width: 16px;
  height: 16px;
  cursor: nwse-resize;
  background: linear-gradient(
    135deg,
    transparent 50%,
    #808080 50%,
    #808080 60%,
    transparent 60%,
    transparent 70%,
    #808080 70%,
    #808080 80%,
    transparent 80%
  );
}
```

### 2.3 Taskbar Component

```typescript
// components/Taskbar/Taskbar.tsx
import React from 'react';
import { useWindowStore } from '../../state/windowStore';
import styles from './Taskbar.module.css';

export const Taskbar: React.FC = () => {
  const { windows, activeWindow, setActiveWindow, toggleStartMenu, isStartMenuOpen } = useWindowStore();

  return (
    <div className={styles.taskbar}>
      {/* Start button */}
      <button
        className={`${styles.startButton} ${isStartMenuOpen ? styles.pressed : ''}`}
        onClick={toggleStartMenu}
      >
        <img src="/icons/windows.png" alt="" />
        <span>Start</span>
      </button>

      {/* Divider */}
      <div className={styles.divider} />

      {/* Window buttons */}
      <div className={styles.windowButtons}>
        {windows.map((window) => (
          <button
            key={window.id}
            className={`${styles.windowButton} ${window.id === activeWindow ? styles.active : ''}`}
            onClick={() => setActiveWindow(window.id)}
          >
            {window.icon && <img src={window.icon} alt="" />}
            <span>{window.title}</span>
          </button>
        ))}
      </div>

      {/* System tray */}
      <div className={styles.systemTray}>
        <span className={styles.clock}>
          {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>
    </div>
  );
};
```

### 2.4 StartMenu Component

```typescript
// components/StartMenu/StartMenu.tsx
import React from 'react';
import { useWindowStore } from '../../state/windowStore';
import styles from './StartMenu.module.css';

interface MenuItem {
  id: string;
  label: string;
  icon: string;
  action: () => void;
}

const menuItems: MenuItem[] = [
  {
    id: 'debate',
    label: 'New Debate',
    icon: '/icons/debate.png',
    action: () => {},
  },
  {
    id: 'topics',
    label: 'Browse Topics',
    icon: '/icons/folder.png',
    action: () => {},
  },
  {
    id: 'profile',
    label: 'My Profile',
    icon: '/icons/user.png',
    action: () => {},
  },
  {
    id: 'settings',
    label: 'Settings',
    icon: '/icons/settings.png',
    action: () => {},
  },
];

export const StartMenu: React.FC = () => {
  const { isStartMenuOpen, openWindow, closeStartMenu } = useWindowStore();

  if (!isStartMenuOpen) return null;

  const handleItemClick = (item: MenuItem) => {
    openWindow(item.id, item.label, item.icon);
    closeStartMenu();
  };

  return (
    <div className={styles.startMenu}>
      {/* Sidebar */}
      <div className={styles.sidebar}>
        <span className={styles.sidebarText}>Debate Simulator</span>
      </div>

      {/* Menu items */}
      <div className={styles.menuItems}>
        {menuItems.map((item) => (
          <button
            key={item.id}
            className={styles.menuItem}
            onClick={() => handleItemClick(item)}
          >
            <img src={item.icon} alt="" className={styles.menuIcon} />
            <span>{item.label}</span>
          </button>
        ))}

        <div className={styles.separator} />

        <button className={styles.menuItem}>
          <img src="/icons/shutdown.png" alt="" className={styles.menuIcon} />
          <span>Shut Down...</span>
        </button>
      </div>
    </div>
  );
};
```

### 2.5 Desktop Component

```typescript
// components/Desktop/Desktop.tsx
import React from 'react';
import { useWindowStore } from '../../state/windowStore';
import { WindowFrame } from '../WindowFrame/WindowFrame';
import { Taskbar } from '../Taskbar/Taskbar';
import { StartMenu } from '../StartMenu/StartMenu';
import { DebateWindow } from '../../features/debate/DebateWindow';
import { TopicsWindow } from '../../features/topics/TopicsWindow';
import { ProfileWindow } from '../../features/profile/ProfileWindow';
import { SettingsWindow } from '../../features/settings/SettingsWindow';
import styles from './Desktop.module.css';

const windowComponents: Record<string, React.FC> = {
  debate: DebateWindow,
  topics: TopicsWindow,
  profile: ProfileWindow,
  settings: SettingsWindow,
};

export const Desktop: React.FC = () => {
  const { windows, activeWindow, setActiveWindow, closeWindow, minimizeWindow } = useWindowStore();

  return (
    <div className={styles.desktop}>
      {/* Desktop icons */}
      <div className={styles.icons}>
        {/* Desktop shortcuts would go here */}
      </div>

      {/* Windows */}
      {windows.map((window) => {
        const Component = windowComponents[window.id];
        if (!Component || window.minimized) return null;

        return (
          <WindowFrame
            key={window.id}
            title={window.title}
            icon={window.icon}
            isActive={window.id === activeWindow}
            initialPosition={window.position}
            initialSize={window.size}
            onClose={() => closeWindow(window.id)}
            onMinimize={() => minimizeWindow(window.id)}
            onMaximize={() => {}}
          >
            <Component />
          </WindowFrame>
        );
      })}

      {/* Start menu */}
      <StartMenu />

      {/* Taskbar */}
      <Taskbar />
    </div>
  );
};
```

---

## 3. STATE MANAGEMENT (ZUSTAND)

### 3.1 Window Store

```typescript
// state/windowStore.ts
import { create } from 'zustand';

interface Window {
  id: string;
  title: string;
  icon?: string;
  position: { x: number; y: number };
  size: { width: number; height: number };
  minimized: boolean;
  maximized: boolean;
}

interface WindowState {
  windows: Window[];
  activeWindow: string | null;
  isStartMenuOpen: boolean;

  // Actions
  openWindow: (id: string, title: string, icon?: string) => void;
  closeWindow: (id: string) => void;
  minimizeWindow: (id: string) => void;
  maximizeWindow: (id: string) => void;
  setActiveWindow: (id: string) => void;
  updateWindowPosition: (id: string, position: { x: number; y: number }) => void;
  updateWindowSize: (id: string, size: { width: number; height: number }) => void;
  toggleStartMenu: () => void;
  closeStartMenu: () => void;
}

export const useWindowStore = create<WindowState>((set, get) => ({
  windows: [],
  activeWindow: null,
  isStartMenuOpen: false,

  openWindow: (id, title, icon) => {
    const { windows } = get();

    // Check if already open
    const existing = windows.find((w) => w.id === id);
    if (existing) {
      // Restore if minimized and bring to front
      set({
        windows: windows.map((w) =>
          w.id === id ? { ...w, minimized: false } : w
        ),
        activeWindow: id,
      });
      return;
    }

    // Calculate position (cascade)
    const offset = windows.length * 30;
    const newWindow: Window = {
      id,
      title,
      icon,
      position: { x: 50 + offset, y: 50 + offset },
      size: { width: 600, height: 400 },
      minimized: false,
      maximized: false,
    };

    set({
      windows: [...windows, newWindow],
      activeWindow: id,
    });
  },

  closeWindow: (id) => {
    const { windows, activeWindow } = get();
    const filtered = windows.filter((w) => w.id !== id);

    set({
      windows: filtered,
      activeWindow: activeWindow === id
        ? filtered[filtered.length - 1]?.id ?? null
        : activeWindow,
    });
  },

  minimizeWindow: (id) => {
    const { windows } = get();
    set({
      windows: windows.map((w) =>
        w.id === id ? { ...w, minimized: true } : w
      ),
    });
  },

  maximizeWindow: (id) => {
    const { windows } = get();
    set({
      windows: windows.map((w) =>
        w.id === id ? { ...w, maximized: !w.maximized } : w
      ),
    });
  },

  setActiveWindow: (id) => {
    const { windows } = get();
    const window = windows.find((w) => w.id === id);

    if (window?.minimized) {
      set({
        windows: windows.map((w) =>
          w.id === id ? { ...w, minimized: false } : w
        ),
        activeWindow: id,
      });
    } else {
      set({ activeWindow: id });
    }
  },

  updateWindowPosition: (id, position) => {
    const { windows } = get();
    set({
      windows: windows.map((w) =>
        w.id === id ? { ...w, position } : w
      ),
    });
  },

  updateWindowSize: (id, size) => {
    const { windows } = get();
    set({
      windows: windows.map((w) =>
        w.id === id ? { ...w, size } : w
      ),
    });
  },

  toggleStartMenu: () => {
    set((state) => ({ isStartMenuOpen: !state.isStartMenuOpen }));
  },

  closeStartMenu: () => {
    set({ isStartMenuOpen: false });
  },
}));
```

### 3.2 Debate Store

```typescript
// state/debateStore.ts
import { create } from 'zustand';

interface Turn {
  id: string;
  stance: 'pro' | 'con';
  content: string;
  round: number;
  timestamp: number;
}

interface Score {
  proScore: number;
  conScore: number;
  winner: 'pro' | 'con' | 'tie';
  reasoning: string;
}

interface DebateState {
  // Current debate
  debateId: string | null;
  topic: string | null;
  domain: string | null;
  totalRounds: number;
  currentRound: number;
  turns: Turn[];
  score: Score | null;
  isComplete: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  startDebate: (topic: string, rounds: number) => void;
  setDebateId: (id: string) => void;
  setDomain: (domain: string) => void;
  addTurn: (turn: Omit<Turn, 'id' | 'timestamp'>) => void;
  setScore: (score: Score) => void;
  setComplete: () => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

export const useDebateStore = create<DebateState>((set, get) => ({
  debateId: null,
  topic: null,
  domain: null,
  totalRounds: 2,
  currentRound: 0,
  turns: [],
  score: null,
  isComplete: false,
  isLoading: false,
  error: null,

  startDebate: (topic, rounds) => {
    set({
      topic,
      totalRounds: rounds,
      currentRound: 0,
      turns: [],
      score: null,
      isComplete: false,
      error: null,
    });
  },

  setDebateId: (id) => set({ debateId: id }),

  setDomain: (domain) => set({ domain }),

  addTurn: (turn) => {
    const { turns } = get();
    const newTurn: Turn = {
      ...turn,
      id: `turn-${turns.length + 1}`,
      timestamp: Date.now(),
    };

    set({
      turns: [...turns, newTurn],
      currentRound: Math.ceil((turns.length + 1) / 2),
    });
  },

  setScore: (score) => set({ score }),

  setComplete: () => set({ isComplete: true }),

  setLoading: (loading) => set({ isLoading: loading }),

  setError: (error) => set({ error }),

  reset: () => set({
    debateId: null,
    topic: null,
    domain: null,
    totalRounds: 2,
    currentRound: 0,
    turns: [],
    score: null,
    isComplete: false,
    isLoading: false,
    error: null,
  }),
}));
```

### 3.3 Settings Store

```typescript
// state/settingsStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface SettingsState {
  // API settings
  apiUrl: string;
  useMocks: boolean;

  // Debate settings
  defaultRounds: number;
  useInternet: boolean;
  autoScore: boolean;

  // UI settings
  soundEnabled: boolean;
  animationsEnabled: boolean;
  theme: 'win98' | 'modern';

  // Actions
  setApiUrl: (url: string) => void;
  setUseMocks: (value: boolean) => void;
  setDefaultRounds: (rounds: number) => void;
  setUseInternet: (value: boolean) => void;
  setAutoScore: (value: boolean) => void;
  setSoundEnabled: (value: boolean) => void;
  setAnimationsEnabled: (value: boolean) => void;
  setTheme: (theme: 'win98' | 'modern') => void;
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      // Defaults
      apiUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
      useMocks: import.meta.env.VITE_USE_MOCKS === 'true',
      defaultRounds: 2,
      useInternet: false,
      autoScore: true,
      soundEnabled: true,
      animationsEnabled: true,
      theme: 'win98',

      // Actions
      setApiUrl: (url) => set({ apiUrl: url }),
      setUseMocks: (value) => set({ useMocks: value }),
      setDefaultRounds: (rounds) => set({ defaultRounds: rounds }),
      setUseInternet: (value) => set({ useInternet: value }),
      setAutoScore: (value) => set({ autoScore: value }),
      setSoundEnabled: (value) => set({ soundEnabled: value }),
      setAnimationsEnabled: (value) => set({ animationsEnabled: value }),
      setTheme: (theme) => set({ theme }),
    }),
    {
      name: 'debate-simulator-settings',
    }
  )
);
```

### 3.4 Profile Store

```typescript
// state/profileStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface Stats {
  totalDebates: number;
  wins: number;
  losses: number;
  ties: number;
  favoriteTopics: string[];
}

interface ProfileState {
  // Profile data
  username: string;
  avatar: string | null;
  preferredStance: 'pro' | 'con' | 'random';
  stats: Stats;

  // Actions
  setUsername: (name: string) => void;
  setAvatar: (url: string | null) => void;
  setPreferredStance: (stance: 'pro' | 'con' | 'random') => void;
  recordDebate: (result: 'win' | 'loss' | 'tie', topic: string) => void;
  resetStats: () => void;
}

export const useProfileStore = create<ProfileState>()(
  persist(
    (set, get) => ({
      username: 'Debater',
      avatar: null,
      preferredStance: 'random',
      stats: {
        totalDebates: 0,
        wins: 0,
        losses: 0,
        ties: 0,
        favoriteTopics: [],
      },

      setUsername: (name) => set({ username: name }),
      setAvatar: (url) => set({ avatar: url }),
      setPreferredStance: (stance) => set({ preferredStance: stance }),

      recordDebate: (result, topic) => {
        const { stats } = get();
        const newStats = {
          ...stats,
          totalDebates: stats.totalDebates + 1,
        };

        if (result === 'win') newStats.wins++;
        else if (result === 'loss') newStats.losses++;
        else newStats.ties++;

        // Update favorite topics (keep top 5)
        const topicCounts = new Map<string, number>();
        for (const t of [...stats.favoriteTopics, topic]) {
          topicCounts.set(t, (topicCounts.get(t) || 0) + 1);
        }
        newStats.favoriteTopics = Array.from(topicCounts.entries())
          .sort((a, b) => b[1] - a[1])
          .slice(0, 5)
          .map(([t]) => t);

        set({ stats: newStats });
      },

      resetStats: () => set({
        stats: {
          totalDebates: 0,
          wins: 0,
          losses: 0,
          ties: 0,
          favoriteTopics: [],
        },
      }),
    }),
    {
      name: 'debate-simulator-profile',
    }
  )
);
```

---

## 4. API LAYER & REACT QUERY

### 4.1 Base API Client

```typescript
// api/client.ts
import { useSettingsStore } from '../state/settingsStore';

export interface ApiResponse<T> {
  data: T;
  error?: string;
}

export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl || useSettingsStore.getState().apiUrl;
  }

  async get<T>(path: string): Promise<ApiResponse<T>> {
    const response = await fetch(`${this.baseUrl}${path}`);

    if (!response.ok) {
      return { data: null as T, error: response.statusText };
    }

    const data = await response.json();
    return { data };
  }

  async post<T>(path: string, body: unknown): Promise<ApiResponse<T>> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      return { data: null as T, error: response.statusText };
    }

    const data = await response.json();
    return { data };
  }

  async *stream(path: string, body: unknown): AsyncGenerator<string> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) return;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const text = decoder.decode(value);
      const lines = text.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          yield line.slice(6);
        }
      }
    }
  }
}

export const apiClient = new ApiClient();
```

### 4.2 React Query Hooks

```typescript
// api/hooks/useStartDebate.ts
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '../client';
import { useDebateStore } from '../../state/debateStore';

interface StartDebateRequest {
  topic: string;
  rounds: number;
  useInternet: boolean;
}

interface StartDebateResponse {
  debate_id: string;
  topic: string;
  domain: string;
  status: string;
}

export const useStartDebate = () => {
  const { startDebate, setDebateId, setDomain } = useDebateStore();

  return useMutation({
    mutationFn: async (request: StartDebateRequest) => {
      const response = await apiClient.post<StartDebateResponse>('/debates', {
        topic: request.topic,
        rounds: request.rounds,
        use_internet: request.useInternet,
      });

      if (response.error) {
        throw new Error(response.error);
      }

      return response.data;
    },

    onSuccess: (data, variables) => {
      startDebate(variables.topic, variables.rounds);
      setDebateId(data.debate_id);
      setDomain(data.domain);
    },
  });
};
```

```typescript
// api/hooks/useSendTurn.ts
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '../client';
import { useDebateStore } from '../../state/debateStore';

interface SendTurnRequest {
  debateId: string;
  content?: string;
  generateAi: boolean;
}

interface SendTurnResponse {
  pro_argument: string | null;
  con_argument: string | null;
  round_num: number;
  is_complete: boolean;
}

export const useSendTurn = () => {
  const { addTurn, setComplete } = useDebateStore();

  return useMutation({
    mutationFn: async (request: SendTurnRequest) => {
      const response = await apiClient.post<SendTurnResponse>(
        `/debates/${request.debateId}/turns`,
        {
          content: request.content,
          generate_ai: request.generateAi,
        }
      );

      if (response.error) {
        throw new Error(response.error);
      }

      return response.data;
    },

    onSuccess: (data) => {
      if (data.pro_argument) {
        addTurn({
          stance: 'pro',
          content: data.pro_argument,
          round: data.round_num,
        });
      }

      if (data.con_argument) {
        addTurn({
          stance: 'con',
          content: data.con_argument,
          round: data.round_num,
        });
      }

      if (data.is_complete) {
        setComplete();
      }
    },
  });
};
```

```typescript
// api/hooks/useScoreDebate.ts
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '../client';
import { useDebateStore } from '../../state/debateStore';

interface ScoreResponse {
  pro_score: number;
  con_score: number;
  winner: 'pro' | 'con' | 'tie';
  reasoning: string;
}

export const useScoreDebate = () => {
  const { setScore } = useDebateStore();

  return useMutation({
    mutationFn: async (debateId: string) => {
      const response = await apiClient.post<ScoreResponse>(
        `/debates/${debateId}/score`,
        {}
      );

      if (response.error) {
        throw new Error(response.error);
      }

      return response.data;
    },

    onSuccess: (data) => {
      setScore({
        proScore: data.pro_score,
        conScore: data.con_score,
        winner: data.winner,
        reasoning: data.reasoning,
      });
    },
  });
};
```

```typescript
// api/hooks/useHealth.ts
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../client';

interface HealthResponse {
  status: string;
  model_loaded: boolean;
  gpu_available: boolean;
}

export const useHealth = () => {
  return useQuery({
    queryKey: ['health'],
    queryFn: async () => {
      const response = await apiClient.get<HealthResponse>('/health');
      return response.data;
    },
    refetchInterval: 30000, // Check every 30 seconds
  });
};
```

### 4.3 Mock Adapter

```typescript
// api/adapters/mock.ts
export const mockAdapter = {
  async startDebate(topic: string, rounds: number) {
    await delay(500);

    return {
      debate_id: `mock-${Date.now()}`,
      topic,
      domain: detectDomain(topic),
      status: 'created',
    };
  },

  async sendTurn(debateId: string, round: number) {
    await delay(1000);

    return {
      pro_argument: generateMockArgument('pro', round),
      con_argument: generateMockArgument('con', round),
      round_num: round,
      is_complete: round >= 2,
    };
  },

  async scoreDebate(debateId: string) {
    await delay(500);

    const proScore = 70 + Math.random() * 20;
    const conScore = 70 + Math.random() * 20;

    return {
      pro_score: Math.round(proScore),
      con_score: Math.round(conScore),
      winner: proScore > conScore ? 'pro' : conScore > proScore ? 'con' : 'tie',
      reasoning: 'Both sides presented compelling arguments.',
    };
  },
};

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function detectDomain(topic: string): string {
  const lower = topic.toLowerCase();
  if (lower.includes('school') || lower.includes('education')) return 'education';
  if (lower.includes('health') || lower.includes('medical')) return 'medicine';
  if (lower.includes('climate') || lower.includes('environment')) return 'ecology';
  if (lower.includes('ai') || lower.includes('technology')) return 'technology';
  return 'debate';
}

function generateMockArgument(stance: string, round: number): string {
  const openings = stance === 'pro'
    ? ['The benefits are clear.', 'Consider the evidence.', 'History shows us.']
    : ['But wait.', 'The risks are real.', 'We must consider.'];

  const opening = openings[round % openings.length];
  return `${opening} This is a mock ${stance} argument for round ${round}.`;
}
```

---

## 5. FEATURE MODULES

### 5.1 Debate Window

```typescript
// features/debate/DebateWindow.tsx
import React, { useState } from 'react';
import { useDebateStore } from '../../state/debateStore';
import { useSettingsStore } from '../../state/settingsStore';
import { useStartDebate } from '../../api/hooks/useStartDebate';
import { useSendTurn } from '../../api/hooks/useSendTurn';
import { useScoreDebate } from '../../api/hooks/useScoreDebate';
import { DebateHistory } from './DebateHistory';
import { ScoreDisplay } from './ScoreDisplay';
import styles from './DebateWindow.module.css';

export const DebateWindow: React.FC = () => {
  const [topic, setTopic] = useState('');
  const { defaultRounds, useInternet } = useSettingsStore();
  const {
    debateId,
    topic: currentTopic,
    turns,
    score,
    isComplete,
    isLoading,
  } = useDebateStore();

  const startDebate = useStartDebate();
  const sendTurn = useSendTurn();
  const scoreDebate = useScoreDebate();

  const handleStartDebate = () => {
    if (!topic.trim()) return;

    startDebate.mutate({
      topic: topic.trim(),
      rounds: defaultRounds,
      useInternet,
    });
  };

  const handleNextRound = () => {
    if (!debateId) return;

    sendTurn.mutate({
      debateId,
      generateAi: true,
    });
  };

  const handleScore = () => {
    if (!debateId) return;

    scoreDebate.mutate(debateId);
  };

  return (
    <div className={styles.container}>
      {/* Topic input (if no debate started) */}
      {!currentTopic && (
        <div className={styles.startSection}>
          <label className={styles.label}>Enter a debate topic:</label>
          <input
            type="text"
            className={styles.input}
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="e.g., Should college be free?"
            onKeyDown={(e) => e.key === 'Enter' && handleStartDebate()}
          />
          <button
            className={styles.button}
            onClick={handleStartDebate}
            disabled={!topic.trim() || startDebate.isPending}
          >
            {startDebate.isPending ? 'Starting...' : 'Start Debate'}
          </button>
        </div>
      )}

      {/* Debate in progress */}
      {currentTopic && (
        <>
          <div className={styles.topicBar}>
            <strong>Topic:</strong> {currentTopic}
          </div>

          <DebateHistory turns={turns} />

          {!isComplete && (
            <div className={styles.controls}>
              <button
                className={styles.button}
                onClick={handleNextRound}
                disabled={isLoading || sendTurn.isPending}
              >
                {sendTurn.isPending ? 'Generating...' : 'Next Round'}
              </button>
            </div>
          )}

          {isComplete && !score && (
            <div className={styles.controls}>
              <button
                className={styles.button}
                onClick={handleScore}
                disabled={scoreDebate.isPending}
              >
                {scoreDebate.isPending ? 'Scoring...' : 'Get Final Score'}
              </button>
            </div>
          )}

          {score && <ScoreDisplay score={score} />}
        </>
      )}
    </div>
  );
};
```

### 5.2 Argument Card

```typescript
// features/debate/ArgumentCard.tsx
import React from 'react';
import styles from './ArgumentCard.module.css';

interface ArgumentCardProps {
  stance: 'pro' | 'con';
  content: string;
  round: number;
}

export const ArgumentCard: React.FC<ArgumentCardProps> = ({
  stance,
  content,
  round,
}) => {
  return (
    <div className={`${styles.card} ${styles[stance]}`}>
      <div className={styles.header}>
        <span className={styles.stance}>
          {stance === 'pro' ? '✓ PRO' : '✗ CON'}
        </span>
        <span className={styles.round}>Round {round}</span>
      </div>
      <div className={styles.content}>{content}</div>
    </div>
  );
};
```

### 5.3 Score Display

```typescript
// features/debate/ScoreDisplay.tsx
import React from 'react';
import styles from './ScoreDisplay.module.css';

interface Score {
  proScore: number;
  conScore: number;
  winner: 'pro' | 'con' | 'tie';
  reasoning: string;
}

interface ScoreDisplayProps {
  score: Score;
}

export const ScoreDisplay: React.FC<ScoreDisplayProps> = ({ score }) => {
  return (
    <div className={styles.container}>
      <h3 className={styles.title}>Final Score</h3>

      <div className={styles.scores}>
        <div className={`${styles.scoreBox} ${score.winner === 'pro' ? styles.winner : ''}`}>
          <span className={styles.label}>PRO</span>
          <span className={styles.value}>{score.proScore}</span>
        </div>

        <div className={styles.vs}>VS</div>

        <div className={`${styles.scoreBox} ${score.winner === 'con' ? styles.winner : ''}`}>
          <span className={styles.label}>CON</span>
          <span className={styles.value}>{score.conScore}</span>
        </div>
      </div>

      <div className={styles.winner}>
        {score.winner === 'tie' ? (
          <span>🤝 It's a Tie!</span>
        ) : (
          <span>🏆 {score.winner.toUpperCase()} Wins!</span>
        )}
      </div>

      <p className={styles.reasoning}>{score.reasoning}</p>
    </div>
  );
};
```

---

## 6. NODE.JS BACKEND ALTERNATIVE

### 6.1 Overview

The Node.js backend (`frontend/apps/api/`) provides an alternative to the Python backend, using OpenRouter for LLM access instead of local models.

### 6.2 Fastify Server

```typescript
// apps/api/src/index.ts
import Fastify from 'fastify';
import cors from '@fastify/cors';
import { healthRoutes } from './routes/health';
import { debateRoutes } from './routes/debates';
import { profileRoutes } from './routes/profile';
import { topicRoutes } from './routes/topics';

const fastify = Fastify({ logger: true });

async function main() {
  // CORS
  await fastify.register(cors, {
    origin: ['http://localhost:5173', 'http://localhost:3000'],
  });

  // Routes
  await fastify.register(healthRoutes, { prefix: '/health' });
  await fastify.register(debateRoutes, { prefix: '/debates' });
  await fastify.register(profileRoutes, { prefix: '/profile' });
  await fastify.register(topicRoutes, { prefix: '/topics' });

  // Start
  const port = parseInt(process.env.PORT || '4000');
  await fastify.listen({ port, host: '0.0.0.0' });

  console.log(`Server running at http://localhost:${port}`);
}

main().catch(console.error);
```

### 6.3 OpenRouter Integration

```typescript
// apps/api/src/agents/debaterAgent.ts
import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: process.env.OPENROUTER_API_KEY,
  baseURL: 'https://openrouter.ai/api/v1',
});

const MODEL = process.env.OPENROUTER_MODEL || 'nvidia/nemotron-nano-9b-v2:free';

export async function generateArgument(
  topic: string,
  stance: 'pro' | 'con',
  research: string,
  opponentArg?: string,
): Promise<string> {
  const stanceName = stance === 'pro' ? 'FOR' : 'AGAINST';

  const messages: OpenAI.ChatCompletionMessageParam[] = [
    {
      role: 'system',
      content: `You are a skilled debater arguing ${stanceName} the topic. Be persuasive and concise (5-10 sentences).`,
    },
    {
      role: 'user',
      content: `Topic: ${topic}

Research: ${research}

${opponentArg ? `Opponent argued: ${opponentArg}` : 'This is your opening statement.'}

Generate a compelling argument ${stanceName} this topic.`,
    },
  ];

  const response = await openai.chat.completions.create({
    model: MODEL,
    messages,
    max_tokens: 300,
    temperature: 0.7,
  });

  return response.choices[0]?.message?.content || '';
}
```

### 6.4 Prisma Schema

```prisma
// apps/api/prisma/schema.prisma
datasource db {
  provider = "sqlite"
  url      = env("DATABASE_URL")
}

generator client {
  provider = "prisma-client-js"
}

model Profile {
  id              String   @id @default(uuid())
  username        String
  preferredStance String   @default("random")
  totalDebates    Int      @default(0)
  wins            Int      @default(0)
  losses          Int      @default(0)
  ties            Int      @default(0)
  createdAt       DateTime @default(now())
  updatedAt       DateTime @updatedAt
}

model Debate {
  id           String   @id @default(uuid())
  topic        String
  domain       String
  rounds       Int
  isComplete   Boolean  @default(false)
  winner       String?
  createdAt    DateTime @default(now())
  turns        Turn[]
}

model Turn {
  id        String   @id @default(uuid())
  debateId  String
  debate    Debate   @relation(fields: [debateId], references: [id])
  stance    String
  content   String
  round     Int
  createdAt DateTime @default(now())
}
```

---

## 7. SHARED CONTRACTS (ZOD)

### 7.1 Schema Definitions

```typescript
// packages/contracts/src/index.ts
import { z } from 'zod';

// Request schemas
export const startDebateRequestSchema = z.object({
  topic: z.string().min(5),
  rounds: z.number().int().min(1).max(5).default(2),
  useInternet: z.boolean().default(false),
});

export const sendTurnRequestSchema = z.object({
  content: z.string().optional(),
  generateAi: z.boolean().default(true),
});

// Response schemas
export const startDebateResponseSchema = z.object({
  debate_id: z.string(),
  topic: z.string(),
  domain: z.string(),
  status: z.string(),
});

export const sendTurnResponseSchema = z.object({
  pro_argument: z.string().nullable(),
  con_argument: z.string().nullable(),
  round_num: z.number(),
  is_complete: z.boolean(),
});

export const scoreResponseSchema = z.object({
  pro_score: z.number(),
  con_score: z.number(),
  winner: z.enum(['pro', 'con', 'tie']),
  reasoning: z.string(),
});

export const healthResponseSchema = z.object({
  status: z.string(),
  model_loaded: z.boolean(),
  gpu_available: z.boolean(),
});

// Type exports
export type StartDebateRequest = z.infer<typeof startDebateRequestSchema>;
export type StartDebateResponse = z.infer<typeof startDebateResponseSchema>;
export type SendTurnRequest = z.infer<typeof sendTurnRequestSchema>;
export type SendTurnResponse = z.infer<typeof sendTurnResponseSchema>;
export type ScoreResponse = z.infer<typeof scoreResponseSchema>;
export type HealthResponse = z.infer<typeof healthResponseSchema>;
```

---

## 8. BUILD & DEVELOPMENT

### 8.1 Development Commands

```bash
# Install dependencies
cd frontend
npm install

# Start development server
npm run dev

# Run tests
npm run test

# Run linter
npm run lint

# Type check
npm run typecheck

# Build for production
npm run build

# Preview production build
npm run preview
```

### 8.2 Environment Variables

```bash
# frontend/.env
VITE_API_BASE_URL=http://localhost:8000  # Python backend
# VITE_API_BASE_URL=http://localhost:4000  # Node.js backend

VITE_USE_MOCKS=false  # Set to true for mock mode
```

### 8.3 Vite Configuration

```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
});
```

### 8.4 TypeScript Configuration

```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

---

*Continue to [DETAILED_PROJECT_EXPLICATION_EXAMPLES.md](./DETAILED_PROJECT_EXPLICATION_EXAMPLES.md) for complete data flow examples.*

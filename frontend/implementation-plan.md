# Implementation Plan: UI Improvements, Authentication & Multiplayer Leaderboard

## Overview

Three features to implement:
1. **Softer UI + Dark Mode** - CSS variables for theming, dark mode toggle
2. **JSON-based Authentication** - Username/password auth stored in server JSON file
3. **Multiplayer Leaderboard** - Full stats display for all players

---

## Phase 1: UI Improvements (Softer Colors + Dark Mode)

### 1.1 Add CSS Custom Properties
**File**: `src/styles/index.css`

Add CSS variables at root level with softer Win98 colors:
```css
:root {
  --desktop-bg: #5f9ea0;      /* Softer teal (was #008080) */
  --surface: #d4d4d4;         /* Softer silver */
  --text-primary: #2a2a2a;    /* Softer black */
  --titlebar-start: #3d5a80;  /* Muted navy */
  --titlebar-end: #5b8dc9;    /* Softer blue */
  /* ... more variables */
}

[data-theme="dark"] {
  --desktop-bg: #1a1a2e;      /* Dark navy */
  --surface: #2d2d44;         /* Dark surface */
  --text-primary: #e2e2e2;    /* Light text */
  /* ... dark variants */
}
```

Replace all hardcoded colors with variables throughout the CSS file.

### 1.2 Create Theme Store
**New File**: `src/state/themeStore.ts`

Zustand store with localStorage persistence:
- `theme: "light" | "dark"`
- `setTheme()`, `toggleTheme()`
- Sets `data-theme` attribute on `<html>`

### 1.3 Add Theme Toggle to Settings
**File**: `src/features/settings/SettingsWindow.tsx`

Add Display fieldset with theme dropdown (Light/Dark).

### 1.4 Initialize Theme on Mount
**File**: `src/app/App.tsx`

Apply saved theme from store on app load.

---

## Phase 2: JSON-based Authentication

### 2.1 Backend User Storage
**New File**: `apps/api/src/data/users.json`
```json
{ "users": [] }
```

User structure:
```typescript
{ id, username, passwordHash, playerId, createdAt, lastLoginAt }
```

### 2.2 Auth Service
**New File**: `apps/api/src/services/auth.ts`

- `registerUser(username, password)` - Hash with bcrypt, create user
- `loginUser(username, password)` - Verify credentials
- `verifyToken(token)` - Validate JWT-like token
- `generateToken(user)` - Create signed token (HMAC-SHA256)

### 2.3 Auth Routes
**New File**: `apps/api/src/routes/auth.ts`

Endpoints:
- `POST /auth/register` - Create account
- `POST /auth/login` - Get token
- `GET /auth/me` - Verify session

### 2.4 Register Routes
**File**: `apps/api/src/server.ts`

Import and register auth routes.

### 2.5 Frontend Auth Store
**New File**: `src/state/authStore.ts`

Zustand store with persistence:
- `isAuthenticated`, `token`, `playerId`, `username`
- `login()`, `logout()`

### 2.6 Auth Hooks
**New File**: `src/api/hooks/useAuth.ts`

- `useLogin()` - Login mutation
- `useRegister()` - Register mutation

### 2.7 Login Window
**New File**: `src/features/auth/LoginWindow.tsx`

Tabbed UI for Login/Register with username, password fields.

### 2.8 Register Window Definition
**File**: `src/state/windowDefinitions.ts`

Add `"login"` to WindowType and windowDefinitions.

**File**: `src/components/WindowManager.tsx`

Register LoginWindow component.

### 2.9 Add Auth Header to API Client
**File**: `src/api/client.ts`

Include `Authorization: Bearer {token}` header when authenticated.

---

## Phase 3: Multiplayer Leaderboard

### 3.1 Leaderboard Types
**File**: `src/api/types.ts`

Add types:
```typescript
LeaderboardEntry { rank, playerId, username, avatar, level, stats, achievements }
LeaderboardResponse { players, totalPlayers, page, pageSize }
```

### 3.2 Backend Leaderboard Route
**File**: `apps/api/src/routes/profile.ts`

Enhanced `GET /leaderboard` endpoint:
- Pagination (page, pageSize)
- Sort options (xp, wins, winRate, averageScore)
- Returns full stats, achievements, recent matches

### 3.3 Update API Adapter
**File**: `src/api/adapter.ts`

Add `getLeaderboard(params)` to ApiAdapter interface and implementations.

### 3.4 Leaderboard Window
**New File**: `src/features/leaderboard/LeaderboardWindow.tsx`

Full-featured leaderboard:
- Sortable columns (dropdown)
- Pagination controls
- Table showing: Rank, Player (avatar + name + title), Level, W/L, Win%, Avg Score, Achievements

### 3.5 Register Leaderboard Window
**File**: `src/state/windowDefinitions.ts`

Add `"leaderboard"` to WindowType and windowDefinitions.

**File**: `src/components/WindowManager.tsx`

Register LeaderboardWindow component.

### 3.6 Add Desktop Icon
**File**: `src/components/DesktopIcons.tsx`

Add leaderboard icon to desktop.

---

## New Files Summary

| Path | Purpose |
|------|---------|
| `src/state/themeStore.ts` | Theme state with persistence |
| `apps/api/src/data/users.json` | User storage |
| `apps/api/src/services/auth.ts` | Auth logic (bcrypt, tokens) |
| `apps/api/src/routes/auth.ts` | Auth API endpoints |
| `src/state/authStore.ts` | Frontend auth state |
| `src/api/hooks/useAuth.ts` | Login/register hooks |
| `src/features/auth/LoginWindow.tsx` | Login/register UI |
| `src/features/leaderboard/LeaderboardWindow.tsx` | Leaderboard UI |

## Files to Modify

| Path | Changes |
|------|---------|
| `src/styles/index.css` | CSS variables, dark theme, softer colors |
| `src/app/App.tsx` | Theme initialization |
| `src/features/settings/SettingsWindow.tsx` | Theme toggle |
| `apps/api/src/server.ts` | Register auth routes |
| `src/api/client.ts` | Auth header |
| `src/state/windowDefinitions.ts` | Add login, leaderboard windows |
| `src/components/WindowManager.tsx` | Register new components |
| `src/api/types.ts` | Leaderboard types |
| `src/api/adapter.ts` | Leaderboard method |
| `apps/api/src/routes/profile.ts` | Enhanced leaderboard endpoint |
| `src/components/DesktopIcons.tsx` | Leaderboard icon |

## Implementation Order

1. Phase 1.1-1.2: CSS variables + theme store
2. Phase 1.3-1.4: Settings toggle + app init
3. Phase 2.1-2.4: Backend auth (service, routes, server)
4. Phase 2.5-2.9: Frontend auth (store, hooks, window, client)
5. Phase 3.1-3.3: Leaderboard backend + types
6. Phase 3.4-3.6: Leaderboard frontend

## Dependencies

- `bcrypt` package needed for password hashing in `apps/api`

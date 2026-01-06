import { create } from "zustand";
import { Rect } from "../utils/windowUtils";
import { WindowType, windowDefinitions } from "./windowDefinitions";

export type WindowState = {
  id: WindowType;
  title: string;
  isOpen: boolean;
  isMinimized: boolean;
  isMaximized: boolean;
  zIndex: number;
  rect: Rect;
  restoreRect?: Rect;
};

type WindowStore = {
  windows: Record<WindowType, WindowState>;
  nextZ: number;
  openWindow: (id: WindowType) => void;
  closeWindow: (id: WindowType) => void;
  minimizeWindow: (id: WindowType) => void;
  focusWindow: (id: WindowType) => void;
  setWindowRect: (id: WindowType, rect: Rect) => void;
  toggleMaximize: (id: WindowType, desktopBounds: Rect) => void;
};

const createInitialWindows = (): Record<WindowType, WindowState> => {
  const entries = Object.entries(windowDefinitions).map(([id, def]) => [
    id,
    {
      id: id as WindowType,
      title: def.title,
      isOpen: false,
      isMinimized: false,
      isMaximized: false,
      zIndex: 1,
      rect: {
        x: def.defaultRect.x,
        y: def.defaultRect.y,
        width: def.defaultRect.width,
        height: def.defaultRect.height
      }
    }
  ]);
  return Object.fromEntries(entries) as Record<WindowType, WindowState>;
};

export const useWindowStore = create<WindowStore>((set, get) => ({
  windows: createInitialWindows(),
  nextZ: 10,
  openWindow: (id) =>
    set((state) => {
      const nextZ = state.nextZ + 1;
      const current = state.windows[id];
      return {
        nextZ,
        windows: {
          ...state.windows,
          [id]: {
            ...current,
            isOpen: true,
            isMinimized: false,
            zIndex: nextZ
          }
        }
      };
    }),
  closeWindow: (id) =>
    set((state) => ({
      windows: {
        ...state.windows,
        [id]: {
          ...state.windows[id],
          isOpen: false,
          isMinimized: false,
          isMaximized: false
        }
      }
    })),
  minimizeWindow: (id) =>
    set((state) => ({
      windows: {
        ...state.windows,
        [id]: {
          ...state.windows[id],
          isMinimized: true
        }
      }
    })),
  focusWindow: (id) => {
    const state = get();
    const nextZ = state.nextZ + 1;
    set({
      nextZ,
      windows: {
        ...state.windows,
        [id]: {
          ...state.windows[id],
          zIndex: nextZ,
          isMinimized: false
        }
      }
    });
  },
  setWindowRect: (id, rect) =>
    set((state) => ({
      windows: {
        ...state.windows,
        [id]: {
          ...state.windows[id],
          rect
        }
      }
    })),
  toggleMaximize: (id, desktopBounds) =>
    set((state) => {
      const current = state.windows[id];
      if (current.isMaximized) {
        return {
          windows: {
            ...state.windows,
            [id]: {
              ...current,
              isMaximized: false,
              rect: current.restoreRect ?? current.rect,
              restoreRect: undefined
            }
          }
        };
      }
      return {
        windows: {
          ...state.windows,
          [id]: {
            ...current,
            isMaximized: true,
            restoreRect: current.rect,
            rect: {
              x: 0,
              y: 0,
              width: desktopBounds.width,
              height: desktopBounds.height
            }
          }
        }
      };
    })
}));

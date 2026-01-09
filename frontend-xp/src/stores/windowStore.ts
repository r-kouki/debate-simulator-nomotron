import { create } from 'zustand';
import { WindowState, WindowConfig, Position, Size, WindowComponent } from '@/types';

interface WindowStore {
  windows: WindowState[];
  focusedWindowId: string | null;
  nextZIndex: number;

  // Actions
  openWindow: (config: WindowConfig) => string;
  closeWindow: (id: string) => void;
  minimizeWindow: (id: string) => void;
  maximizeWindow: (id: string) => void;
  restoreWindow: (id: string) => void;
  focusWindow: (id: string) => void;
  updateWindowPosition: (id: string, position: Position) => void;
  updateWindowSize: (id: string, size: Size) => void;
  getWindowById: (id: string) => WindowState | undefined;
  isWindowOpen: (component: WindowComponent) => boolean;
}

const generateWindowId = () => `window-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;

const getDefaultPosition = (index: number): Position => ({
  x: 100 + (index * 30),
  y: 80 + (index * 30),
});

const getDefaultSize = (component: WindowComponent): Size => {
  switch (component) {
    case 'debate-creator':
      return { width: 500, height: 450 };
    case 'debate-viewer':
      return { width: 700, height: 550 };
    case 'results-viewer':
      return { width: 800, height: 600 };
    case 'history':
      return { width: 700, height: 500 };
    case 'settings':
      return { width: 480, height: 420 };
    case 'about':
      return { width: 400, height: 320 };
    case 'my-computer':
      return { width: 600, height: 450 };
    default:
      return { width: 600, height: 400 };
  }
};

export const useWindowStore = create<WindowStore>((set, get) => ({
  windows: [],
  focusedWindowId: null,
  nextZIndex: 100,

  openWindow: (config: WindowConfig) => {
    const { windows, nextZIndex } = get();
    const id = config.id || generateWindowId();

    // Check if window with same id is already open
    const existingWindow = windows.find((w) => w.id === id);
    if (existingWindow) {
      get().focusWindow(id);
      if (existingWindow.isMinimized) {
        get().restoreWindow(id);
      }
      return id;
    }

    const newWindow: WindowState = {
      id,
      title: config.title,
      icon: config.icon,
      component: config.component,
      componentProps: config.componentProps,
      position: config.initialPosition || getDefaultPosition(windows.length),
      size: config.initialSize || getDefaultSize(config.component),
      minSize: config.minSize || { width: 300, height: 200 },
      maxSize: config.maxSize,
      zIndex: nextZIndex,
      isMaximized: false,
      isMinimized: false,
      isFocused: true,
      resizable: config.resizable !== false,
    };

    set((state) => ({
      windows: [
        ...state.windows.map((w) => ({ ...w, isFocused: false })),
        newWindow,
      ],
      focusedWindowId: id,
      nextZIndex: nextZIndex + 1,
    }));

    return id;
  },

  closeWindow: (id: string) => {
    set((state) => {
      const windows = state.windows.filter((w) => w.id !== id);
      const focusedWindowId =
        state.focusedWindowId === id
          ? windows.length > 0
            ? windows[windows.length - 1].id
            : null
          : state.focusedWindowId;

      return {
        windows: windows.map((w) => ({
          ...w,
          isFocused: w.id === focusedWindowId,
        })),
        focusedWindowId,
      };
    });
  },

  minimizeWindow: (id: string) => {
    set((state) => ({
      windows: state.windows.map((w) =>
        w.id === id ? { ...w, isMinimized: true, isFocused: false } : w
      ),
      focusedWindowId:
        state.focusedWindowId === id ? null : state.focusedWindowId,
    }));
  },

  maximizeWindow: (id: string) => {
    set((state) => ({
      windows: state.windows.map((w) =>
        w.id === id ? { ...w, isMaximized: true } : w
      ),
    }));
  },

  restoreWindow: (id: string) => {
    const { nextZIndex } = get();
    set((state) => ({
      windows: state.windows.map((w) =>
        w.id === id
          ? { ...w, isMaximized: false, isMinimized: false, isFocused: true, zIndex: nextZIndex }
          : { ...w, isFocused: false }
      ),
      focusedWindowId: id,
      nextZIndex: nextZIndex + 1,
    }));
  },

  focusWindow: (id: string) => {
    const { windows, nextZIndex } = get();
    const window = windows.find((w) => w.id === id);
    if (!window || window.isFocused) return;

    set((state) => ({
      windows: state.windows.map((w) =>
        w.id === id
          ? { ...w, isFocused: true, zIndex: nextZIndex }
          : { ...w, isFocused: false }
      ),
      focusedWindowId: id,
      nextZIndex: nextZIndex + 1,
    }));
  },

  updateWindowPosition: (id: string, position: Position) => {
    set((state) => ({
      windows: state.windows.map((w) =>
        w.id === id ? { ...w, position } : w
      ),
    }));
  },

  updateWindowSize: (id: string, size: Size) => {
    set((state) => ({
      windows: state.windows.map((w) =>
        w.id === id ? { ...w, size } : w
      ),
    }));
  },

  getWindowById: (id: string) => {
    return get().windows.find((w) => w.id === id);
  },

  isWindowOpen: (component: WindowComponent) => {
    return get().windows.some((w) => w.component === component && !w.isMinimized);
  },
}));

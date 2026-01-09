import { create } from 'zustand';
import { ContextMenuItem, Notification, Position } from '@/types';

interface UIStore {
  // Start Menu
  isStartMenuOpen: boolean;

  // Context Menu
  contextMenu: {
    isOpen: boolean;
    position: Position;
    items: ContextMenuItem[];
  } | null;

  // Notifications
  notifications: Notification[];

  // Loading
  isLoading: boolean;
  loadingMessage: string;

  // Actions
  toggleStartMenu: () => void;
  closeStartMenu: () => void;
  openContextMenu: (position: Position, items: ContextMenuItem[]) => void;
  closeContextMenu: () => void;
  addNotification: (notification: Omit<Notification, 'id'>) => void;
  removeNotification: (id: string) => void;
  setLoading: (loading: boolean, message?: string) => void;
}

export const useUIStore = create<UIStore>((set) => ({
  isStartMenuOpen: false,
  contextMenu: null,
  notifications: [],
  isLoading: false,
  loadingMessage: '',

  toggleStartMenu: () =>
    set((state) => ({ isStartMenuOpen: !state.isStartMenuOpen })),

  closeStartMenu: () => set({ isStartMenuOpen: false }),

  openContextMenu: (position, items) =>
    set({
      contextMenu: { isOpen: true, position, items },
      isStartMenuOpen: false,
    }),

  closeContextMenu: () => set({ contextMenu: null }),

  addNotification: (notification) => {
    const id = `notification-${Date.now()}`;
    set((state) => ({
      notifications: [...state.notifications, { ...notification, id }],
    }));

    // Auto-remove after duration
    if (notification.duration !== 0) {
      setTimeout(() => {
        set((state) => ({
          notifications: state.notifications.filter((n) => n.id !== id),
        }));
      }, notification.duration || 5000);
    }
  },

  removeNotification: (id) =>
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    })),

  setLoading: (loading, message = '') =>
    set({ isLoading: loading, loadingMessage: message }),
}));

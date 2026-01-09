import { useEffect } from 'react';
import { useWindowStore, useUIStore } from '@/stores';

export const useKeyboardShortcuts = () => {
  const { openWindow, closeWindow, focusedWindowId, windows } = useWindowStore();
  const { toggleStartMenu, closeStartMenu } = useUIStore();

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Alt+F4: Close focused window
      if (e.altKey && e.key === 'F4') {
        e.preventDefault();
        if (focusedWindowId) {
          closeWindow(focusedWindowId);
        }
      }

      // Meta/Win key: Toggle start menu
      if (e.key === 'Meta' || e.key === 'OS') {
        e.preventDefault();
        toggleStartMenu();
      }

      // Escape: Close start menu or context menu
      if (e.key === 'Escape') {
        closeStartMenu();
      }

      // Ctrl+N: New debate
      if (e.ctrlKey && e.key === 'n') {
        e.preventDefault();
        openWindow({
          id: 'debate-creator',
          title: 'New Debate',
          icon: '💬',
          component: 'debate-creator',
        });
      }

      // Ctrl+H: History
      if (e.ctrlKey && e.key === 'h') {
        e.preventDefault();
        openWindow({
          id: 'history',
          title: 'Debate History',
          icon: '📁',
          component: 'history',
        });
      }

      // Ctrl+,: Settings
      if (e.ctrlKey && e.key === ',') {
        e.preventDefault();
        openWindow({
          id: 'settings',
          title: 'Settings',
          icon: '⚙️',
          component: 'settings',
        });
      }

      // Alt+Tab: Cycle through windows
      if (e.altKey && e.key === 'Tab') {
        e.preventDefault();
        if (windows.length > 1 && focusedWindowId) {
          const currentIndex = windows.findIndex((w) => w.id === focusedWindowId);
          const nextIndex = (currentIndex + 1) % windows.length;
          useWindowStore.getState().focusWindow(windows[nextIndex].id);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [openWindow, closeWindow, toggleStartMenu, closeStartMenu, focusedWindowId, windows]);
};

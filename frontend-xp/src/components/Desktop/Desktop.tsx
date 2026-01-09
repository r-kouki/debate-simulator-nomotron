import React, { useCallback } from 'react';
import { useSettingsStore, useUIStore, useWindowStore } from '@/stores';
import { DesktopIcons } from './DesktopIcons';
import { WindowManager } from './WindowManager';
import { ContextMenu } from './ContextMenu';

// Import wallpapers as URLs - we'll use CSS background
const wallpapers: Record<string, string> = {
  bliss: 'linear-gradient(180deg, #245EDC 0%, #3A7BD5 50%, #7EC87E 75%, #5AAB5A 100%)',
  azul: 'linear-gradient(180deg, #003087 0%, #0054E3 50%, #0078D7 100%)',
};

export const Desktop: React.FC = () => {
  const { settings } = useSettingsStore();
  const { contextMenu, closeContextMenu, closeStartMenu } = useUIStore();

  const handleDesktopClick = useCallback(() => {
    closeStartMenu();
    closeContextMenu();
  }, [closeStartMenu, closeContextMenu]);

  const handleContextMenu = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      const { openContextMenu } = useUIStore.getState();
      openContextMenu({ x: e.clientX, y: e.clientY }, [
        { id: 'refresh', label: 'Refresh', onClick: () => window.location.reload() },
        { id: 'sep1', label: '', separator: true },
        {
          id: 'new-debate',
          label: 'New Debate',
          icon: '💬',
          onClick: () => {
            const { openWindow } = useWindowStore.getState();
            openWindow({
              id: 'debate-creator',
              title: 'New Debate',
              icon: '💬',
              component: 'debate-creator',
            });
          },
        },
        { id: 'sep2', label: '', separator: true },
        {
          id: 'settings',
          label: 'Properties',
          icon: '⚙️',
          onClick: () => {
            const { openWindow } = useWindowStore.getState();
            openWindow({
              id: 'settings',
              title: 'Display Properties',
              icon: '⚙️',
              component: 'settings',
            });
          },
        },
      ]);
    },
    []
  );

  const wallpaperStyle = settings.wallpaper === 'custom' && settings.customWallpaper
    ? { backgroundImage: `url(${settings.customWallpaper})`, backgroundSize: 'cover' }
    : { background: wallpapers[settings.wallpaper] || wallpapers.bliss };

  return (
    <div
      className="relative w-full h-full overflow-hidden select-none"
      style={wallpaperStyle}
      onClick={handleDesktopClick}
      onContextMenu={handleContextMenu}
    >
      <DesktopIcons />
      <WindowManager />
      {contextMenu && (
        <ContextMenu
          position={contextMenu.position}
          items={contextMenu.items}
          onClose={closeContextMenu}
        />
      )}
    </div>
  );
};

import React, { useEffect, useRef } from 'react';
import { useUIStore, useWindowStore } from '@/stores';

interface MenuItem {
  id: string;
  label: string;
  icon: string;
  component?: 'debate-creator' | 'history' | 'settings' | 'about' | 'my-computer';
  windowTitle?: string;
  onClick?: () => void;
}

const pinnedItems: MenuItem[] = [
  {
    id: 'new-debate',
    label: 'New Debate',
    icon: '💬',
    component: 'debate-creator',
    windowTitle: 'New Debate',
  },
  {
    id: 'history',
    label: 'Debate History',
    icon: '📁',
    component: 'history',
    windowTitle: 'Debate History',
  },
];

const allProgramsItems: MenuItem[] = [
  {
    id: 'my-computer',
    label: 'My Computer',
    icon: '🖥️',
    component: 'my-computer',
    windowTitle: 'My Computer',
  },
  {
    id: 'settings',
    label: 'Settings',
    icon: '⚙️',
    component: 'settings',
    windowTitle: 'Settings',
  },
  {
    id: 'about',
    label: 'About',
    icon: 'ℹ️',
    component: 'about',
    windowTitle: 'About Debate Simulator',
  },
];

export const StartMenu: React.FC = () => {
  const menuRef = useRef<HTMLDivElement>(null);
  const { closeStartMenu } = useUIStore();
  const { openWindow } = useWindowStore();

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        // Don't close if clicking start button
        const target = e.target as HTMLElement;
        if (target.closest('.xp-start-button')) return;
        closeStartMenu();
      }
    };

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        closeStartMenu();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleEscape);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, [closeStartMenu]);

  const handleItemClick = (item: MenuItem) => {
    if (item.component && item.windowTitle) {
      openWindow({
        id: item.id,
        title: item.windowTitle,
        icon: item.icon,
        component: item.component,
      });
    } else if (item.onClick) {
      item.onClick();
    }
    closeStartMenu();
  };

  return (
    <div
      ref={menuRef}
      className="absolute bottom-[36px] left-0 w-[380px] bg-white rounded-tr-lg shadow-xl z-[9999] overflow-hidden"
      style={{
        boxShadow: '3px -3px 8px rgba(0,0,0,0.4)',
      }}
    >
      {/* Header with user */}
      <div className="h-[54px] bg-gradient-to-r from-[#1558CF] to-[#245EDC] flex items-center px-3 gap-3">
        <div className="w-[40px] h-[40px] rounded bg-white/20 flex items-center justify-center text-2xl">
          👤
        </div>
        <span className="text-white font-bold text-sm">Debate User</span>
      </div>

      {/* Content area */}
      <div className="flex">
        {/* Left column - Pinned items */}
        <div className="w-1/2 bg-white border-r border-gray-200 py-2">
          <div className="px-2 py-1 text-[11px] text-gray-500 font-bold">Pinned</div>
          {pinnedItems.map((item) => (
            <button
              key={item.id}
              onClick={() => handleItemClick(item)}
              className="w-full px-3 py-2 flex items-center gap-3 hover:bg-[#316AC5] hover:text-white text-left"
            >
              <span className="text-2xl">{item.icon}</span>
              <span className="text-sm font-semibold">{item.label}</span>
            </button>
          ))}
          
          <div className="h-px bg-gray-200 my-2 mx-3" />
          
          <div className="px-2 py-1 text-[11px] text-gray-500 font-bold">All Programs</div>
          {allProgramsItems.map((item) => (
            <button
              key={item.id}
              onClick={() => handleItemClick(item)}
              className="w-full px-3 py-2 flex items-center gap-3 hover:bg-[#316AC5] hover:text-white text-left"
            >
              <span className="text-xl">{item.icon}</span>
              <span className="text-sm">{item.label}</span>
            </button>
          ))}
        </div>

        {/* Right column - Recent/Places */}
        <div className="w-1/2 bg-[#D3E5FA] py-2">
          <div className="px-2 py-1 text-[11px] text-gray-600 font-bold">Places</div>
          <button
            onClick={() => {
              openWindow({
                id: 'my-computer',
                title: 'My Computer',
                icon: '🖥️',
                component: 'my-computer',
              });
              closeStartMenu();
            }}
            className="w-full px-3 py-2 flex items-center gap-3 hover:bg-[#316AC5] hover:text-white text-left"
          >
            <span className="text-xl">🖥️</span>
            <span className="text-sm font-semibold">My Computer</span>
          </button>
          <button
            onClick={() => {
              openWindow({
                id: 'history',
                title: 'Debate History',
                icon: '📁',
                component: 'history',
              });
              closeStartMenu();
            }}
            className="w-full px-3 py-2 flex items-center gap-3 hover:bg-[#316AC5] hover:text-white text-left"
          >
            <span className="text-xl">📁</span>
            <span className="text-sm">My Debates</span>
          </button>
          <button
            onClick={() => {
              openWindow({
                id: 'settings',
                title: 'Settings',
                icon: '⚙️',
                component: 'settings',
              });
              closeStartMenu();
            }}
            className="w-full px-3 py-2 flex items-center gap-3 hover:bg-[#316AC5] hover:text-white text-left"
          >
            <span className="text-xl">⚙️</span>
            <span className="text-sm">Control Panel</span>
          </button>
        </div>
      </div>

      {/* Footer */}
      <div className="h-[36px] bg-gradient-to-r from-[#3170DA] to-[#245EDC] flex items-center justify-end px-2 gap-2">
        <button
          onClick={() => {
            window.location.reload();
          }}
          className="px-4 py-1 text-white text-sm hover:bg-white/20 rounded flex items-center gap-2"
        >
          <span>🔄</span>
          <span>Refresh</span>
        </button>
      </div>
    </div>
  );
};

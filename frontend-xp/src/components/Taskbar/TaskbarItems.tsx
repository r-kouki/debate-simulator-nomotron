import React from 'react';
import { useWindowStore } from '@/stores';

export const TaskbarItems: React.FC = () => {
  const { windows, focusWindow, minimizeWindow, restoreWindow } = useWindowStore();

  const handleClick = (windowId: string, isMinimized: boolean, isFocused: boolean) => {
    if (isMinimized) {
      restoreWindow(windowId);
    } else if (isFocused) {
      minimizeWindow(windowId);
    } else {
      focusWindow(windowId);
    }
  };

  return (
    <div className="flex items-center h-full gap-1 px-1 overflow-x-auto">
      {windows.map((window) => (
        <button
          key={window.id}
          onClick={() => handleClick(window.id, window.isMinimized, window.isFocused)}
          className={`h-[28px] min-w-[150px] max-w-[200px] px-2 flex items-center gap-2
                      rounded-sm text-left transition-all text-sm truncate
                      ${
                        window.isFocused && !window.isMinimized
                          ? 'bg-[#1C5FBA] text-white border border-[#0A4799] shadow-inner'
                          : 'bg-gradient-to-b from-[#3C8DEE] to-[#2565C7] text-white border border-[#0A4799] hover:brightness-110'
                      }
                      ${window.isMinimized ? 'opacity-70' : ''}`}
          title={window.title}
        >
          <span className="shrink-0">{window.icon}</span>
          <span className="truncate">{window.title}</span>
        </button>
      ))}
    </div>
  );
};

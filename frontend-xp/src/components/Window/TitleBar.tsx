import React from 'react';
import { useWindowStore } from '@/stores';

interface TitleBarProps {
  title: string;
  icon: string;
  isFocused: boolean;
  isMaximized: boolean;
  windowId: string;
  onClose: () => void;
}

export const TitleBar: React.FC<TitleBarProps> = ({
  title,
  icon,
  isFocused,
  isMaximized,
  windowId,
  onClose,
}) => {
  const { minimizeWindow, maximizeWindow, restoreWindow } = useWindowStore();

  const handleMinimize = (e: React.MouseEvent) => {
    e.stopPropagation();
    minimizeWindow(windowId);
  };

  const handleMaximize = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (isMaximized) {
      restoreWindow(windowId);
    } else {
      maximizeWindow(windowId);
    }
  };

  const handleClose = (e: React.MouseEvent) => {
    e.stopPropagation();
    onClose();
  };

  return (
    <div
      className={`window-drag-handle flex items-center justify-between h-[30px] px-2 rounded-t-lg select-none ${
        isFocused ? 'xp-titlebar' : 'xp-titlebar-inactive'
      }`}
    >
      <div className="flex items-center gap-1 min-w-0">
        <span className="text-lg shrink-0">{icon}</span>
        <span className="text-white text-sm font-bold truncate text-shadow">
          {title}
        </span>
      </div>
      <div className="flex items-center gap-[2px] shrink-0">
        {/* Minimize Button */}
        <button
          onClick={handleMinimize}
          className="window-control-btn w-[21px] h-[21px] rounded-sm flex items-center justify-center 
                     bg-gradient-to-b from-[#4290F4] to-[#174FC9] 
                     hover:from-[#5CA2FF] hover:to-[#2A64D8]
                     active:from-[#174FC9] active:to-[#4290F4]
                     border border-white/30"
          title="Minimize"
        >
          <svg width="9" height="9" viewBox="0 0 9 9">
            <line x1="1" y1="7" x2="7" y2="7" stroke="white" strokeWidth="2" />
          </svg>
        </button>

        {/* Maximize/Restore Button */}
        <button
          onClick={handleMaximize}
          className="window-control-btn w-[21px] h-[21px] rounded-sm flex items-center justify-center 
                     bg-gradient-to-b from-[#4290F4] to-[#174FC9] 
                     hover:from-[#5CA2FF] hover:to-[#2A64D8]
                     active:from-[#174FC9] active:to-[#4290F4]
                     border border-white/30"
          title={isMaximized ? 'Restore' : 'Maximize'}
        >
          {isMaximized ? (
            <svg width="9" height="9" viewBox="0 0 9 9">
              <rect x="2" y="0" width="6" height="6" fill="none" stroke="white" strokeWidth="1" />
              <rect x="0" y="2" width="6" height="6" fill="none" stroke="white" strokeWidth="1" />
            </svg>
          ) : (
            <svg width="9" height="9" viewBox="0 0 9 9">
              <rect x="1" y="1" width="7" height="7" fill="none" stroke="white" strokeWidth="2" />
            </svg>
          )}
        </button>

        {/* Close Button */}
        <button
          onClick={handleClose}
          className="window-control-btn w-[21px] h-[21px] rounded-sm flex items-center justify-center 
                     bg-gradient-to-b from-[#E55B50] to-[#B41A0F] 
                     hover:from-[#FF6D63] hover:to-[#C62B20]
                     active:from-[#B41A0F] active:to-[#E55B50]
                     border border-white/30"
          title="Close"
        >
          <svg width="9" height="9" viewBox="0 0 9 9">
            <line x1="1" y1="1" x2="8" y2="8" stroke="white" strokeWidth="2" />
            <line x1="8" y1="1" x2="1" y2="8" stroke="white" strokeWidth="2" />
          </svg>
        </button>
      </div>
    </div>
  );
};

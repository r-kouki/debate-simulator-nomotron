import React from 'react';
import { useUIStore } from '@/stores';

export const StartButton: React.FC = () => {
  const { isStartMenuOpen, toggleStartMenu } = useUIStore();

  return (
    <button
      onClick={(e) => {
        e.stopPropagation();
        toggleStartMenu();
      }}
      className={`xp-start-button h-[30px] flex items-center gap-1 ml-[2px] transition-all
                  ${isStartMenuOpen ? 'brightness-90' : ''}`}
    >
      <span className="text-xl">🪟</span>
      <span className="text-[13px] italic">start</span>
    </button>
  );
};

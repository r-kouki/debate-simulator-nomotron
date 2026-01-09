import React from 'react';
import { StartButton } from './StartButton';
import { StartMenu } from './StartMenu';
import { QuickLaunch } from './QuickLaunch';
import { TaskbarItems } from './TaskbarItems';
import { SystemTray } from './SystemTray';
import { useUIStore } from '@/stores';

export const Taskbar: React.FC = () => {
  const isStartMenuOpen = useUIStore((state) => state.isStartMenuOpen);

  return (
    <>
      {isStartMenuOpen && <StartMenu />}
      <div className="absolute bottom-0 left-0 right-0 h-[36px] xp-taskbar flex items-center z-[9999]">
        <StartButton />
        <div className="h-full w-px bg-[#0E3789] mx-1" />
        <QuickLaunch />
        <div className="h-full w-px bg-[#0E3789] mx-1" />
        <TaskbarItems />
        <div className="flex-1" />
        <SystemTray />
      </div>
    </>
  );
};

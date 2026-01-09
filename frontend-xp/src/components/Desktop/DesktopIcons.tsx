import React, { useCallback } from 'react';
import { useWindowStore } from '@/stores';

interface DesktopIconData {
  id: string;
  label: string;
  icon: string;
  component: 'debate-creator' | 'history' | 'settings' | 'my-computer' | 'about';
  windowTitle: string;
}

const desktopIcons: DesktopIconData[] = [
  {
    id: 'my-computer',
    label: 'My Computer',
    icon: '🖥️',
    component: 'my-computer',
    windowTitle: 'My Computer',
  },
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
  {
    id: 'settings',
    label: 'Settings',
    icon: '⚙️',
    component: 'settings',
    windowTitle: 'Settings',
  },
];

export const DesktopIcons: React.FC = () => {
  const openWindow = useWindowStore((state) => state.openWindow);

  const handleDoubleClick = useCallback(
    (icon: DesktopIconData) => {
      openWindow({
        id: icon.id,
        title: icon.windowTitle,
        icon: icon.icon,
        component: icon.component,
      });
    },
    [openWindow]
  );

  return (
    <div className="absolute top-4 left-4 flex flex-col gap-2">
      {desktopIcons.map((icon) => (
        <DesktopIcon
          key={icon.id}
          icon={icon}
          onDoubleClick={() => handleDoubleClick(icon)}
        />
      ))}
    </div>
  );
};

interface DesktopIconProps {
  icon: DesktopIconData;
  onDoubleClick: () => void;
}

const DesktopIcon: React.FC<DesktopIconProps> = ({ icon, onDoubleClick }) => {
  const [isSelected, setIsSelected] = React.useState(false);

  return (
    <button
      className={`flex flex-col items-center justify-center w-[75px] p-2 rounded cursor-pointer
                  ${isSelected ? 'bg-[#316AC5]/50' : 'hover:bg-[#316AC5]/30'}
                  focus:outline-none focus:bg-[#316AC5]/50 transition-colors`}
      onClick={() => setIsSelected(true)}
      onDoubleClick={onDoubleClick}
      onBlur={() => setIsSelected(false)}
    >
      <span className="text-4xl drop-shadow-md">{icon.icon}</span>
      <span
        className={`text-[11px] text-center text-white mt-1 leading-tight
                    ${isSelected ? 'bg-[#316AC5]' : ''}
                    drop-shadow-[1px_1px_1px_rgba(0,0,0,0.8)]`}
        style={{
          textShadow: '1px 1px 2px rgba(0,0,0,0.8)',
        }}
      >
        {icon.label}
      </span>
    </button>
  );
};

import React from 'react';
import { useWindowStore } from '@/stores';

export const QuickLaunch: React.FC = () => {
  const openWindow = useWindowStore((state) => state.openWindow);

  const quickLaunchItems = [
    {
      id: 'quick-debate',
      icon: '💬',
      title: 'New Debate',
      component: 'debate-creator' as const,
    },
    {
      id: 'quick-history',
      icon: '📁',
      title: 'Debate History',
      component: 'history' as const,
    },
  ];

  return (
    <div className="flex items-center h-full px-1 gap-1">
      {quickLaunchItems.map((item) => (
        <button
          key={item.id}
          onClick={() =>
            openWindow({
              id: item.id.replace('quick-', ''),
              title: item.title,
              icon: item.icon,
              component: item.component,
            })
          }
          className="w-[24px] h-[24px] flex items-center justify-center text-lg
                     hover:bg-white/20 rounded transition-colors"
          title={item.title}
        >
          {item.icon}
        </button>
      ))}
    </div>
  );
};

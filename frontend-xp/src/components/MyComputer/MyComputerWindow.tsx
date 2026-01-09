import React from 'react';
import { useWindowStore, useDebateStore } from '@/stores';

interface MyComputerWindowProps {
  windowId: string;
  componentProps?: Record<string, unknown>;
}

const systemInfo = [
  { label: 'System', value: 'Debate Simulator XP' },
  { label: 'Version', value: '1.0.0' },
  { label: 'Backend', value: 'CrewAI + FastAPI' },
  { label: 'Model', value: 'Llama 3.1 Nemotron Nano 8B' },
];

export const MyComputerWindow: React.FC<MyComputerWindowProps> = () => {
  const { openWindow } = useWindowStore();
  const debates = useDebateStore((state) => state.debates);
  const adapters = useDebateStore((state) => state.adapters);

  const drives = [
    {
      id: 'debates',
      label: 'Debates (C:)',
      icon: '💾',
      description: `${debates.length} debates`,
      onClick: () => {
        openWindow({
          id: 'history',
          title: 'Debate History',
          icon: '📁',
          component: 'history',
        });
      },
    },
    {
      id: 'adapters',
      label: 'Domain Adapters (D:)',
      icon: '🔧',
      description: `${adapters.length || 4} adapters available`,
      onClick: () => {
        // Could open adapter manager
      },
    },
    {
      id: 'settings',
      label: 'Control Panel',
      icon: '⚙️',
      description: 'System settings',
      onClick: () => {
        openWindow({
          id: 'settings',
          title: 'Settings',
          icon: '⚙️',
          component: 'settings',
        });
      },
    },
  ];

  return (
    <div className="h-full flex flex-col">
      {/* Toolbar */}
      <div className="bg-xp-gray-light border-b border-gray-300 px-2 py-1 flex gap-2">
        <button className="text-xs hover:bg-gray-200 px-2 py-1 rounded">Back</button>
        <button className="text-xs hover:bg-gray-200 px-2 py-1 rounded">Forward</button>
        <div className="flex-1" />
        <button className="text-xs hover:bg-gray-200 px-2 py-1 rounded">Search</button>
      </div>

      {/* Address Bar */}
      <div className="bg-xp-gray-light border-b border-gray-300 px-2 py-1 flex items-center gap-2">
        <span className="text-xs text-gray-600">Address:</span>
        <div className="flex-1 bg-white border border-gray-400 px-2 py-0.5 text-xs flex items-center gap-1">
          <span>🖥️</span>
          <span>My Computer</span>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <div className="w-[180px] bg-[#6B89D5] p-4 text-white">
          <div className="mb-4">
            <h3 className="font-bold text-sm mb-2">System Tasks</h3>
            <button
              className="w-full text-left text-xs hover:bg-white/20 px-2 py-1 rounded flex items-center gap-2"
              onClick={() => {
                openWindow({
                  id: 'debate-creator',
                  title: 'New Debate',
                  icon: '💬',
                  component: 'debate-creator',
                });
              }}
            >
              <span>💬</span>
              <span>New Debate</span>
            </button>
            <button
              className="w-full text-left text-xs hover:bg-white/20 px-2 py-1 rounded flex items-center gap-2"
              onClick={() => {
                openWindow({
                  id: 'history',
                  title: 'Debate History',
                  icon: '📁',
                  component: 'history',
                });
              }}
            >
              <span>📁</span>
              <span>View History</span>
            </button>
          </div>

          <div>
            <h3 className="font-bold text-sm mb-2">Other Places</h3>
            <button
              className="w-full text-left text-xs hover:bg-white/20 px-2 py-1 rounded flex items-center gap-2"
              onClick={() => {
                openWindow({
                  id: 'settings',
                  title: 'Settings',
                  icon: '⚙️',
                  component: 'settings',
                });
              }}
            >
              <span>⚙️</span>
              <span>Control Panel</span>
            </button>
            <button
              className="w-full text-left text-xs hover:bg-white/20 px-2 py-1 rounded flex items-center gap-2"
              onClick={() => {
                openWindow({
                  id: 'about',
                  title: 'About',
                  icon: 'ℹ️',
                  component: 'about',
                });
              }}
            >
              <span>ℹ️</span>
              <span>About</span>
            </button>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 bg-white p-4 overflow-y-auto">
          {/* Drives */}
          <div className="mb-6">
            <h3 className="text-xs text-gray-500 border-b border-gray-200 pb-1 mb-2">
              Hard Disk Drives
            </h3>
            <div className="flex flex-wrap gap-4">
              {drives.map((drive) => (
                <button
                  key={drive.id}
                  onClick={drive.onClick}
                  className="flex flex-col items-center p-3 rounded hover:bg-blue-50 w-[100px] text-center"
                >
                  <span className="text-4xl mb-1">{drive.icon}</span>
                  <span className="text-xs font-bold">{drive.label}</span>
                  <span className="text-[10px] text-gray-500">{drive.description}</span>
                </button>
              ))}
            </div>
          </div>

          {/* System Info */}
          <div>
            <h3 className="text-xs text-gray-500 border-b border-gray-200 pb-1 mb-2">
              System Information
            </h3>
            <div className="bg-xp-gray-light p-3 rounded border border-gray-300">
              {systemInfo.map((info) => (
                <div key={info.label} className="flex text-sm mb-1 last:mb-0">
                  <span className="w-24 text-gray-600">{info.label}:</span>
                  <span className="font-medium">{info.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Status Bar */}
      <div className="bg-xp-gray-light border-t border-gray-300 px-2 py-1 text-xs text-gray-600">
        {drives.length} items
      </div>
    </div>
  );
};

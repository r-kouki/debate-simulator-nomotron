import React from 'react';
import { useWindowStore } from '@/stores';

interface AboutWindowProps {
  windowId: string;
  componentProps?: Record<string, unknown>;
}

export const AboutWindow: React.FC<AboutWindowProps> = ({ windowId }) => {
  const { closeWindow } = useWindowStore();

  return (
    <div className="p-6 h-full flex flex-col items-center justify-center text-center">
      <div className="text-6xl mb-4">🎯</div>
      <h1 className="text-xl font-bold mb-2">Debate Simulator XP</h1>
      <p className="text-sm text-gray-600 mb-4">Version 1.0.0</p>

      <div className="bg-xp-gray-light p-4 rounded border border-gray-300 mb-4 max-w-sm">
        <p className="text-sm mb-2">
          A Windows XP-themed interface for the CrewAI multi-agent debate system.
        </p>
        <p className="text-xs text-gray-500">
          Features AI-powered debates with domain-specific adapters, fact-checking, and intelligent
          judging.
        </p>
      </div>

      <div className="text-xs text-gray-500 mb-4">
        <p>Built with React, TypeScript, and TailwindCSS</p>
        <p>Powered by CrewAI and local LLMs</p>
      </div>

      <button className="xp-button px-8" onClick={() => closeWindow(windowId)}>
        OK
      </button>
    </div>
  );
};

import React, { useState } from 'react';
import { useWindowStore, useDebateStore, useUIStore } from '@/stores';
import { DebateConfig } from '@/types';
import { debateApi } from '@/api/debateApi';

interface DebateCreatorWindowProps {
  windowId: string;
  componentProps?: Record<string, unknown>;
}

export const DebateCreatorWindow: React.FC<DebateCreatorWindowProps> = ({ windowId }) => {
  const { openWindow, closeWindow } = useWindowStore();
  const { addDebate, setActiveDebate } = useDebateStore();
  const { addNotification } = useUIStore();

  const [config, setConfig] = useState<DebateConfig>({
    topic: '',
    rounds: 2,
    useInternet: false,
    recommendGuests: false,
    domain: 'auto',
    adapter: 'auto',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!config.topic.trim()) {
      addNotification({
        title: 'Error',
        message: 'Please enter a debate topic',
        type: 'error',
      });
      return;
    }

    setIsSubmitting(true);

    try {
      // Always require backend API - no simulation mode
      console.log('[CrewAI] Creating debate via backend API...');
      const response = await debateApi.createDebate(config);
      const debateId = response.id;
      console.log('[CrewAI] Backend debate created:', response);
      
      // Create local state for the debate
      const debate = {
        id: debateId,
        topic: config.topic,
        domain: config.domain || 'general',
        rounds: config.rounds,
        status: 'pending' as const,  // Use 'pending' - backend will update to 'running'
        startTime: new Date().toISOString(),
        currentRound: 0,
        currentStep: 'Connecting to CrewAI...',
        progress: 0,
        proArguments: [],
        conArguments: [],
      };

      addDebate(debate);
      setActiveDebate(debateId);
      
      // Close creator and open viewer
      closeWindow(windowId);
      openWindow({
        id: `debate-viewer-${debateId}`,
        title: `🎭 Debate: ${config.topic.slice(0, 30)}...`,
        icon: '🎭',
        component: 'debate-viewer',
        componentProps: { debateId },
      });

      addNotification({
        title: 'Debate Started',
        message: `CrewAI debate started: ${config.topic}`,
        type: 'success',
      });
    } catch (error) {
      console.error('[CrewAI] Failed to create debate:', error);
      addNotification({
        title: 'CrewAI Error',
        message: 'Failed to connect to CrewAI backend. Make sure the server is running on port 5040.',
        type: 'error',
      });
      
      // Open the status window so user can check
      openWindow({
        id: 'crewai-status-check',
        title: '🔧 CrewAI Status',
        icon: '🔧',
        component: 'crewai-status',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="p-4 h-full flex flex-col">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4 flex-1">
        {/* Topic Input */}
        <div className="flex flex-col gap-1">
          <label className="text-sm font-bold">Debate Topic:</label>
          <textarea
            className="xp-input w-full h-[80px] resize-none"
            placeholder="Enter the topic or question to debate..."
            value={config.topic}
            onChange={(e) => setConfig({ ...config, topic: e.target.value })}
          />
        </div>

        {/* Rounds Selector */}
        <div className="flex items-center gap-4">
          <label className="text-sm font-bold">Rounds:</label>
          <div className="flex gap-2">
            {[1, 2, 3, 4, 5].map((num) => (
              <button
                key={num}
                type="button"
                onClick={() => setConfig({ ...config, rounds: num })}
                className={`w-8 h-8 rounded ${
                  config.rounds === num
                    ? 'bg-[#316AC5] text-white'
                    : 'xp-button'
                }`}
              >
                {num}
              </button>
            ))}
          </div>
        </div>

        {/* Domain Selector */}
        <div className="flex items-center gap-4">
          <label className="text-sm font-bold">Domain:</label>
          <select
            className="xp-select flex-1"
            value={config.domain}
            onChange={(e) => setConfig({ ...config, domain: e.target.value })}
          >
            <option value="auto">Auto-detect</option>
            <option value="general">General</option>
            <option value="education">Education</option>
            <option value="medicine">Medicine</option>
            <option value="ecology">Ecology</option>
            <option value="debate">Debate/Philosophy</option>
          </select>
        </div>

        {/* Options */}
        <fieldset className="border-2 border-gray-300 p-3 rounded">
          <legend className="px-2 text-sm font-bold">Options</legend>
          <div className="flex flex-col gap-2">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                className="xp-checkbox"
                checked={config.useInternet}
                onChange={(e) => setConfig({ ...config, useInternet: e.target.checked })}
              />
              <span className="text-sm">Enable internet research</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                className="xp-checkbox"
                checked={config.recommendGuests}
                onChange={(e) => setConfig({ ...config, recommendGuests: e.target.checked })}
              />
              <span className="text-sm">Recommend guest experts</span>
            </label>
          </div>
        </fieldset>

        {/* CrewAI Info */}
        <div className="bg-blue-50 border border-blue-200 p-3 rounded text-xs">
          <p className="font-bold text-blue-800 mb-1">🤖 CrewAI Mode</p>
          <p className="text-blue-600">
            Debates use CrewAI agents with the local Llama model. 
            Make sure the backend server is running on port 5040.
          </p>
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-2 mt-auto pt-4 border-t border-gray-300">
          <button
            type="button"
            className="xp-button px-6"
            onClick={() => closeWindow(windowId)}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="xp-button px-6"
            disabled={isSubmitting || !config.topic.trim()}
          >
            {isSubmitting ? 'Creating...' : 'Start Debate'}
          </button>
        </div>
      </form>
    </div>
  );
};

import { useEffect, useState } from 'react';
import { useDebateStore, useWindowStore, useUIStore } from '@/stores';

interface DebateViewerWindowProps {
  windowId: string;
  componentProps?: Record<string, unknown>;
}

const DEBATE_STEPS = [
  { id: 'routing', label: 'Routing to Domain', icon: '🔀' },
  { id: 'research', label: 'Research Phase', icon: '🔍' },
  { id: 'pro-argument', label: 'Pro Argument', icon: '✅' },
  { id: 'con-argument', label: 'Con Argument', icon: '❌' },
  { id: 'fact-check', label: 'Fact Checking', icon: '📋' },
  { id: 'judge', label: 'Judge Evaluation', icon: '⚖️' },
];

export const DebateViewerWindow: React.FC<DebateViewerWindowProps> = ({
  windowId,
  componentProps,
}) => {
  const debateId = componentProps?.debateId as string;
  const debate = useDebateStore((state) => state.debates.find((d) => d.id === debateId));
  const { updateDebate } = useDebateStore();
  const { openWindow, closeWindow } = useWindowStore();
  const { addNotification } = useUIStore();
  
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [, setIsSimulating] = useState(false);

  // Simulate debate progress (in real implementation, this would connect to backend SSE)
  useEffect(() => {
    if (!debate || debate.status !== 'pending') return;

    setIsSimulating(true);
    updateDebate(debateId, { status: 'running' });

    const simulateDebate = async () => {
      for (let round = 1; round <= (debate.rounds || 2); round++) {
        for (let stepIdx = 0; stepIdx < DEBATE_STEPS.length; stepIdx++) {
          const step = DEBATE_STEPS[stepIdx];
          setCurrentStepIndex(stepIdx);

          updateDebate(debateId, {
            currentRound: round,
            currentStep: step.label,
            progress: ((round - 1) * DEBATE_STEPS.length + stepIdx + 1) / 
                      (debate.rounds * DEBATE_STEPS.length) * 100,
          });

          // Simulate argument generation
          if (step.id === 'pro-argument') {
            await new Promise((r) => setTimeout(r, 1500));
            updateDebate(debateId, {
              currentArgument: `Pro argument for round ${round}: This is a simulated argument supporting the topic...`,
              proArguments: [
                ...(debate.proArguments || []),
                {
                  side: 'pro',
                  round,
                  content: `Pro argument for round ${round}: The evidence strongly supports this position because...`,
                  timestamp: new Date().toISOString(),
                },
              ],
            });
          } else if (step.id === 'con-argument') {
            await new Promise((r) => setTimeout(r, 1500));
            updateDebate(debateId, {
              currentArgument: `Con argument for round ${round}: This is a simulated argument opposing the topic...`,
              conArguments: [
                ...(debate.conArguments || []),
                {
                  side: 'con',
                  round,
                  content: `Con argument for round ${round}: However, we must consider the opposing view that...`,
                  timestamp: new Date().toISOString(),
                },
              ],
            });
          }

          await new Promise((r) => setTimeout(r, 1000));
        }
      }

      // Complete the debate
      updateDebate(debateId, {
        status: 'completed',
        endTime: new Date().toISOString(),
        progress: 100,
        currentStep: 'Completed',
        judgeScore: {
          winner: Math.random() > 0.5 ? 'pro' : 'con',
          proScore: Math.floor(Math.random() * 30) + 70,
          conScore: Math.floor(Math.random() * 30) + 70,
          reasoning: 'Based on the quality of arguments presented, logical consistency, and evidence provided...',
          factCheckPassed: true,
        },
      });

      addNotification({
        title: 'Debate Complete',
        message: `The debate on "${debate.topic}" has concluded!`,
        type: 'success',
      });

      setIsSimulating(false);
    };

    simulateDebate();
  }, [debate?.id]);

  if (!debate) {
    return (
      <div className="p-4 text-center">
        <p>Debate not found</p>
      </div>
    );
  }

  const handleViewResults = () => {
    openWindow({
      id: `results-${debateId}`,
      title: `Results: ${debate.topic.slice(0, 25)}...`,
      icon: '📊',
      component: 'results-viewer',
      componentProps: { debateId },
    });
    closeWindow(windowId);
  };

  const handleStop = () => {
    updateDebate(debateId, { status: 'stopped' });
    setIsSimulating(false);
    addNotification({
      title: 'Debate Stopped',
      message: 'The debate has been stopped.',
      type: 'warning',
    });
  };

  return (
    <div className="p-4 h-full flex flex-col gap-4">
      {/* Topic */}
      <div className="bg-xp-gray-light p-3 rounded border border-gray-300">
        <h2 className="font-bold text-sm mb-1">Topic:</h2>
        <p className="text-sm">{debate.topic}</p>
      </div>

      {/* Progress Bar */}
      <div className="flex flex-col gap-1">
        <div className="flex justify-between text-xs">
          <span>Progress</span>
          <span>{Math.round(debate.progress || 0)}%</span>
        </div>
        <div className="h-5 bg-white border-2 border-gray-400 rounded overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-[#00A000] to-[#00D000] transition-all duration-300"
            style={{ width: `${debate.progress || 0}%` }}
          />
        </div>
      </div>

      {/* Steps Indicator */}
      <div className="flex flex-col gap-1">
        <h3 className="font-bold text-xs">Steps:</h3>
        <div className="flex gap-1">
          {DEBATE_STEPS.map((step, idx) => (
            <div
              key={step.id}
              className={`flex-1 text-center py-1 px-1 rounded text-[10px] border
                ${idx < currentStepIndex
                  ? 'bg-green-100 border-green-400 text-green-700'
                  : idx === currentStepIndex
                  ? 'bg-blue-100 border-blue-400 text-blue-700 animate-pulse'
                  : 'bg-gray-100 border-gray-300 text-gray-500'
                }`}
              title={step.label}
            >
              {step.icon}
            </div>
          ))}
        </div>
      </div>

      {/* Round Info */}
      <div className="flex gap-4 text-sm">
        <span>
          <strong>Round:</strong> {debate.currentRound || 0} / {debate.rounds}
        </span>
        <span>
          <strong>Status:</strong>{' '}
          <span
            className={`${
              debate.status === 'running'
                ? 'text-blue-600'
                : debate.status === 'completed'
                ? 'text-green-600'
                : debate.status === 'error'
                ? 'text-red-600'
                : 'text-gray-600'
            }`}
          >
            {debate.status}
          </span>
        </span>
      </div>

      {/* Current Step */}
      <div className="bg-white border-2 border-gray-300 p-2 rounded">
        <p className="text-sm text-gray-600">
          <strong>Current:</strong> {debate.currentStep || 'Waiting...'}
        </p>
      </div>

      {/* Arguments Display */}
      <div className="flex-1 flex gap-2 min-h-0 overflow-hidden">
        {/* Pro Arguments */}
        <div className="flex-1 flex flex-col border border-green-400 rounded overflow-hidden">
          <div className="bg-green-100 px-2 py-1 font-bold text-xs text-green-800 border-b border-green-400">
            ✅ Pro Arguments
          </div>
          <div className="flex-1 overflow-y-auto p-2 bg-white">
            {debate.proArguments?.map((arg, idx) => (
              <div key={idx} className="text-xs mb-2 p-2 bg-green-50 rounded">
                <div className="text-[10px] text-gray-500 mb-1">Round {arg.round}</div>
                {arg.content}
              </div>
            ))}
          </div>
        </div>

        {/* Con Arguments */}
        <div className="flex-1 flex flex-col border border-red-400 rounded overflow-hidden">
          <div className="bg-red-100 px-2 py-1 font-bold text-xs text-red-800 border-b border-red-400">
            ❌ Con Arguments
          </div>
          <div className="flex-1 overflow-y-auto p-2 bg-white">
            {debate.conArguments?.map((arg, idx) => (
              <div key={idx} className="text-xs mb-2 p-2 bg-red-50 rounded">
                <div className="text-[10px] text-gray-500 mb-1">Round {arg.round}</div>
                {arg.content}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex justify-end gap-2 pt-2 border-t border-gray-300">
        {debate.status === 'running' && (
          <button className="xp-button px-4" onClick={handleStop}>
            Stop Debate
          </button>
        )}
        {debate.status === 'completed' && (
          <button className="xp-button px-4" onClick={handleViewResults}>
            View Results
          </button>
        )}
        <button className="xp-button px-4" onClick={() => closeWindow(windowId)}>
          Close
        </button>
      </div>
    </div>
  );
};

import React from 'react';
import { useDebateStore, useWindowStore } from '@/stores';

interface ResultsViewerWindowProps {
  windowId: string;
  componentProps?: Record<string, unknown>;
}

export const ResultsViewerWindow: React.FC<ResultsViewerWindowProps> = ({
  windowId,
  componentProps,
}) => {
  const debateId = componentProps?.debateId as string;
  const debate = useDebateStore((state) => state.debates.find((d) => d.id === debateId));
  const { closeWindow } = useWindowStore();

  if (!debate) {
    return (
      <div className="p-4 text-center">
        <p>Debate results not found</p>
      </div>
    );
  }

  const handleExportJSON = () => {
    const data = JSON.stringify(debate, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `debate-${debate.id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleExportText = () => {
    let text = `DEBATE RESULTS\n`;
    text += `=============\n\n`;
    text += `Topic: ${debate.topic}\n`;
    text += `Domain: ${debate.domain}\n`;
    text += `Rounds: ${debate.rounds}\n`;
    text += `Status: ${debate.status}\n\n`;

    if (debate.judgeScore) {
      text += `VERDICT\n-------\n`;
      text += `Winner: ${debate.judgeScore.winner.toUpperCase()}\n`;
      text += `Pro Score: ${debate.judgeScore.proScore}\n`;
      text += `Con Score: ${debate.judgeScore.conScore}\n`;
      text += `Reasoning: ${debate.judgeScore.reasoning}\n\n`;
    }

    text += `PRO ARGUMENTS\n-------------\n`;
    debate.proArguments?.forEach((arg) => {
      text += `\nRound ${arg.round}:\n${arg.content}\n`;
    });

    text += `\nCON ARGUMENTS\n-------------\n`;
    debate.conArguments?.forEach((arg) => {
      text += `\nRound ${arg.round}:\n${arg.content}\n`;
    });

    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `debate-${debate.id}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="p-4 h-full flex flex-col gap-4">
      {/* Topic */}
      <div className="bg-xp-gray-light p-3 rounded border border-gray-300">
        <h2 className="font-bold text-sm mb-1">Topic:</h2>
        <p className="text-sm">{debate.topic}</p>
      </div>

      {/* Verdict */}
      {debate.judgeScore && (
        <div
          className={`p-4 rounded border-2 ${
            debate.judgeScore.winner === 'pro'
              ? 'bg-green-50 border-green-400'
              : debate.judgeScore.winner === 'con'
              ? 'bg-red-50 border-red-400'
              : 'bg-yellow-50 border-yellow-400'
          }`}
        >
          <h3 className="font-bold text-lg mb-2 flex items-center gap-2">
            ⚖️ Verdict:{' '}
            <span
              className={
                debate.judgeScore.winner === 'pro'
                  ? 'text-green-700'
                  : debate.judgeScore.winner === 'con'
                  ? 'text-red-700'
                  : 'text-yellow-700'
              }
            >
              {debate.judgeScore.winner === 'pro'
                ? 'PRO WINS'
                : debate.judgeScore.winner === 'con'
                ? 'CON WINS'
                : 'TIE'}
            </span>
          </h3>
          <div className="flex gap-4 mb-2">
            <div className="text-center p-2 bg-white rounded border">
              <div className="text-2xl font-bold text-green-600">{debate.judgeScore.proScore}</div>
              <div className="text-xs text-gray-500">Pro Score</div>
            </div>
            <div className="text-center p-2 bg-white rounded border">
              <div className="text-2xl font-bold text-red-600">{debate.judgeScore.conScore}</div>
              <div className="text-xs text-gray-500">Con Score</div>
            </div>
            <div className="flex-1 flex items-center">
              {debate.judgeScore.factCheckPassed && (
                <span className="text-green-600 text-sm">✅ Fact Check Passed</span>
              )}
            </div>
          </div>
          <p className="text-sm text-gray-700">{debate.judgeScore.reasoning}</p>
        </div>
      )}

      {/* Arguments Comparison */}
      <div className="flex-1 flex gap-2 min-h-0 overflow-hidden">
        {/* Pro Arguments */}
        <div className="flex-1 flex flex-col border border-green-400 rounded overflow-hidden">
          <div className="bg-green-100 px-3 py-2 font-bold text-sm text-green-800 border-b border-green-400">
            ✅ Pro Arguments
          </div>
          <div className="flex-1 overflow-y-auto p-3 bg-white">
            {debate.proArguments?.map((arg, idx) => (
              <div key={idx} className="text-sm mb-3 p-3 bg-green-50 rounded border border-green-200">
                <div className="text-xs text-gray-500 mb-1 font-bold">Round {arg.round}</div>
                <p>{arg.content}</p>
              </div>
            ))}
            {(!debate.proArguments || debate.proArguments.length === 0) && (
              <p className="text-gray-400 text-sm">No arguments recorded</p>
            )}
          </div>
        </div>

        {/* Con Arguments */}
        <div className="flex-1 flex flex-col border border-red-400 rounded overflow-hidden">
          <div className="bg-red-100 px-3 py-2 font-bold text-sm text-red-800 border-b border-red-400">
            ❌ Con Arguments
          </div>
          <div className="flex-1 overflow-y-auto p-3 bg-white">
            {debate.conArguments?.map((arg, idx) => (
              <div key={idx} className="text-sm mb-3 p-3 bg-red-50 rounded border border-red-200">
                <div className="text-xs text-gray-500 mb-1 font-bold">Round {arg.round}</div>
                <p>{arg.content}</p>
              </div>
            ))}
            {(!debate.conArguments || debate.conArguments.length === 0) && (
              <p className="text-gray-400 text-sm">No arguments recorded</p>
            )}
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="flex gap-4 text-sm bg-xp-gray-light p-2 rounded border border-gray-300">
        <span>
          <strong>Domain:</strong> {debate.domain}
        </span>
        <span>
          <strong>Rounds:</strong> {debate.rounds}
        </span>
        <span>
          <strong>Started:</strong> {new Date(debate.startTime).toLocaleString()}
        </span>
        {debate.endTime && (
          <span>
            <strong>Ended:</strong> {new Date(debate.endTime).toLocaleString()}
          </span>
        )}
      </div>

      {/* Actions */}
      <div className="flex justify-end gap-2 pt-2 border-t border-gray-300">
        <button className="xp-button px-4" onClick={handleExportJSON}>
          Export JSON
        </button>
        <button className="xp-button px-4" onClick={handleExportText}>
          Export Text
        </button>
        <button className="xp-button px-4" onClick={() => closeWindow(windowId)}>
          Close
        </button>
      </div>
    </div>
  );
};

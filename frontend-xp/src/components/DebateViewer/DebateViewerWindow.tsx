import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useDebateStore, useWindowStore } from '@/stores';
import { DebateArgument } from '@/types';

interface LogEntry {
  timestamp: string;
  message: string;
  type: 'info' | 'success' | 'error' | 'warning';
}

interface DebateViewerWindowProps {
  windowId: string;
  componentProps?: {
    debateId?: string;
  };
}

export const DebateViewerWindow: React.FC<DebateViewerWindowProps> = ({ 
  componentProps 
}) => {
  const { activeDebateId, updateDebate, getDebateById } = useDebateStore();
  const { openWindow } = useWindowStore();
  
  // Get the debate - either from props or active debate
  const debateId = componentProps?.debateId || activeDebateId;
  const activeDebate = debateId ? getDebateById(debateId) : undefined;
  
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'error' | 'idle'>('idle');
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [showLogs, setShowLogs] = useState(true);
  
  const eventSourceRef = useRef<EventSource | null>(null);
  const logsEndRef = useRef<HTMLDivElement>(null);
  
  // Add log entry helper
  const addLog = useCallback((message: string, type: LogEntry['type'] = 'info') => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs(prev => [...prev, { timestamp, message, type }]);
  }, []);
  
  // Auto-scroll logs
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);
  
  // Connect to SSE stream when debate starts
  useEffect(() => {
    if (!activeDebate) {
      return;
    }
    
    // Only connect if we have a proper backend ID (not a local one)
    if (!activeDebate.id || activeDebate.id.startsWith('debate-')) {
      addLog('Waiting for backend debate ID...', 'warning');
      return;
    }
    
    // Only connect if status is in_progress or running
    if (activeDebate.status !== 'running' && activeDebate.status !== 'pending') {
      addLog(`Debate status: ${activeDebate.status}`, 'info');
      return;
    }
    
    addLog(`Connecting to CrewAI backend for debate: ${activeDebate.id}`, 'info');
    setConnectionStatus('connecting');
    
    const sseUrl = `http://localhost:5040/api/debates/${activeDebate.id}/stream`;
    addLog(`SSE URL: ${sseUrl}`, 'info');
    
    const eventSource = new EventSource(sseUrl);
    eventSourceRef.current = eventSource;
    
    eventSource.onopen = () => {
      addLog('✓ Connected to CrewAI stream', 'success');
      setConnectionStatus('connected');
    };
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        addLog(`Received: ${data.type}`, 'info');
        
        switch (data.type) {
          case 'debate_started':
            addLog(`Debate started: "${data.topic}"`, 'success');
            updateDebate(activeDebate.id, { status: 'running' });
            break;
            
          case 'round_start':
            addLog(`Round ${data.round} beginning...`, 'info');
            updateDebate(activeDebate.id, { currentRound: data.round });
            break;
            
          case 'argument': {
            addLog(`${data.side.toUpperCase()} argument (Round ${data.round}): ${data.content.substring(0, 50)}...`, 'success');
            
            const newArg: DebateArgument = {
              side: data.side,
              content: data.content,
              round: data.round,
              timestamp: new Date().toISOString(),
            };
            
            const debate = getDebateById(activeDebate.id);
            if (debate) {
              if (data.side === 'pro') {
                updateDebate(activeDebate.id, {
                  proArguments: [...debate.proArguments, newArg],
                  currentArgument: data.content,
                });
              } else {
                updateDebate(activeDebate.id, {
                  conArguments: [...debate.conArguments, newArg],
                  currentArgument: data.content,
                });
              }
            }
            break;
          }
            
          case 'round_end':
            addLog(`Round ${data.round} complete`, 'info');
            break;
            
          case 'debate_complete':
            addLog(`Debate complete! Winner: ${data.winner || 'Draw'}`, 'success');
            updateDebate(activeDebate.id, { 
              status: 'completed',
              judgeScore: data.judgeScore,
            });
            eventSource.close();
            setConnectionStatus('idle');
            break;
            
          case 'error':
            addLog(`Error: ${data.message}`, 'error');
            updateDebate(activeDebate.id, { 
              status: 'error',
              error: data.message,
            });
            eventSource.close();
            setConnectionStatus('error');
            break;
            
          case 'log':
            // Verbose log from backend
            addLog(`[CrewAI] ${data.message}`, 'info');
            break;
            
          default:
            addLog(`Unknown event type: ${data.type}`, 'warning');
        }
      } catch (e) {
        addLog(`Parse error: ${event.data}`, 'error');
      }
    };
    
    eventSource.onerror = (error) => {
      console.error('SSE Error:', error);
      addLog('Connection error - CrewAI may not be running', 'error');
      setConnectionStatus('error');
      eventSource.close();
    };
    
    return () => {
      eventSource.close();
      eventSourceRef.current = null;
    };
  }, [activeDebate?.id, activeDebate?.status, updateDebate, getDebateById, addLog]);
  
  const handleOpenCrewAIStatus = () => {
    openWindow({
      id: 'crewai-status-check',
      title: '🔧 CrewAI Status',
      icon: '🔧',
      component: 'crewai-status',
    });
  };
  
  const handleClearLogs = () => {
    setLogs([]);
  };
  
  if (!activeDebate) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8 text-center">
        <div className="text-5xl mb-4">🎭</div>
        <p className="text-gray-600 mb-2">No active debate</p>
        <p className="text-sm text-gray-400 mb-4">Use "New Debate" to start a CrewAI debate</p>
        <button className="xp-button" onClick={handleOpenCrewAIStatus}>
          Check CrewAI Status
        </button>
      </div>
    );
  }
  
  const { topic, proArguments, conArguments, status, judgeScore } = activeDebate;
  
  // Combine and sort arguments by round
  const allArguments = [...proArguments, ...conArguments].sort((a, b) => {
    if (a.round !== b.round) return a.round - b.round;
    return new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime();
  });
  
  // Group arguments by round
  const argumentsByRound: Record<number, typeof allArguments> = {};
  allArguments.forEach(arg => {
    if (!argumentsByRound[arg.round]) {
      argumentsByRound[arg.round] = [];
    }
    argumentsByRound[arg.round].push(arg);
  });
  
  return (
    <div className="debate-viewer">
      {/* Status Bar */}
      <div className="debate-header">
        <div className="debate-topic">
          <strong>Topic:</strong> {topic}
        </div>
        <div className="debate-meta">
          <span className={`connection-status ${connectionStatus}`}>
            {connectionStatus === 'connecting' && '🔄 Connecting...'}
            {connectionStatus === 'connected' && '🟢 Connected to CrewAI'}
            {connectionStatus === 'error' && '🔴 Connection Error'}
            {connectionStatus === 'idle' && '⚪ Idle'}
          </span>
          <span className="debate-mode">Mode: AI vs AI (CrewAI)</span>
          <span className={`debate-status ${status}`}>
            {status === 'running' || status === 'pending' ? '🔄 In Progress' : 
             status === 'completed' ? '✅ Completed' : '❌ Error'}
          </span>
        </div>
      </div>
      
      {/* Main Content Area */}
      <div className="debate-content-area">
        {/* Arguments Panel */}
        <div className="arguments-panel">
          <div className="arguments-header">
            <div className="side-label pro">🟢 PRO</div>
            <div className="side-label con">🔴 CON</div>
          </div>
          
          <div className="arguments-container">
            {Object.keys(argumentsByRound).length === 0 ? (
              <div className="waiting-for-arguments">
                <div className="spinner"></div>
                <p>Waiting for CrewAI arguments...</p>
                <p className="hint">Make sure the backend server is running on port 5040</p>
              </div>
            ) : (
              Object.entries(argumentsByRound).map(([round, args]) => (
                <div key={round} className="round-section">
                  <div className="round-header">Round {round}</div>
                  <div className="round-arguments">
                    {args.map((arg, idx) => (
                      <div key={`${arg.side}-${arg.round}-${idx}`} className={`argument-card ${arg.side}`}>
                        <div className="argument-header">
                          <span className="side-badge">{arg.side.toUpperCase()}</span>
                          <span className="timestamp">
                            {new Date(arg.timestamp).toLocaleTimeString()}
                          </span>
                        </div>
                        <div className="argument-content">{arg.content}</div>
                      </div>
                    ))}
                  </div>
                </div>
              ))
            )}
          </div>
          
          {/* Winner Display */}
          {status === 'completed' && judgeScore && (
            <div className="winner-display">
              <div className="winner-banner">
                🏆 Winner: <strong>{judgeScore.winner.toUpperCase()}</strong>
                <div className="scores">
                  Pro: {judgeScore.proScore} | Con: {judgeScore.conScore}
                </div>
              </div>
            </div>
          )}
        </div>
        
        {/* Logs Panel */}
        {showLogs && (
          <div className="logs-panel">
            <div className="logs-header">
              <span>📋 Verbose Logs</span>
              <div className="logs-actions">
                <button className="xp-button-small" onClick={handleClearLogs}>Clear</button>
                <button className="xp-button-small" onClick={() => setShowLogs(false)}>Hide</button>
              </div>
            </div>
            <div className="logs-content">
              {logs.map((log, idx) => (
                <div key={idx} className={`log-entry ${log.type}`}>
                  <span className="log-time">[{log.timestamp}]</span>
                  <span className="log-message">{log.message}</span>
                </div>
              ))}
              <div ref={logsEndRef} />
            </div>
          </div>
        )}
      </div>
      
      {/* Footer Actions */}
      <div className="debate-footer">
        <button className="xp-button" onClick={handleOpenCrewAIStatus}>
          Check CrewAI Status
        </button>
        {!showLogs && (
          <button className="xp-button" onClick={() => setShowLogs(true)}>
            Show Logs
          </button>
        )}
        {connectionStatus === 'error' && (
          <span className="error-hint">
            ⚠️ Connection failed. Check if backend is running on port 5040.
          </span>
        )}
      </div>
    </div>
  );
};

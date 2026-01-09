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
  const { activeDebateId, updateDebate } = useDebateStore();
  const { openWindow } = useWindowStore();

  // Get the debate - either from props or active debate
  const debateId = componentProps?.debateId || activeDebateId;

  // Subscribe to the specific debate so component re-renders when it updates
  const activeDebate = useDebateStore(state =>
    debateId ? state.debates.find(d => d.id === debateId) : undefined
  );
  
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
    
    // Must have a valid debate ID
    if (!activeDebate.id) {
      addLog('No debate ID available', 'warning');
      return;
    }
    
    // Only connect if status is pending or running
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
        console.log('[SSE Event]', data); // Debug: log all events
        addLog(`Received: ${data.type}`, 'info');

        // Special logging for argument events
        if (data.type === 'argument') {
          console.log('[SSE Argument]', {
            type: data.type,
            side: data.side,
            round: data.round,
            hasContent: !!data.content,
            contentLength: data.content?.length
          });
        }

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
            try {
              addLog(`${data.side?.toUpperCase() || 'UNKNOWN'} argument (Round ${data.round}): ${data.content?.substring(0, 50) || 'NO CONTENT'}...`, 'success');

              if (!data.side || !data.content || !data.round) {
                console.error('[SSE] Invalid argument data:', data);
                addLog(`Invalid argument data received`, 'error');
                break;
              }

              const newArg: DebateArgument = {
                side: data.side,
                content: data.content,
                round: data.round,
                timestamp: new Date().toISOString(),
              };

              // Get fresh debate state from store
              const debate = useDebateStore.getState().getDebateById(activeDebate.id);
              console.log('[SSE] Current debate state:', {
                debateId: activeDebate.id,
                found: !!debate,
                proArgsCount: debate?.proArguments?.length || 0,
                conArgsCount: debate?.conArguments?.length || 0
              });

              if (debate) {
                if (data.side === 'pro') {
                  const updated = {
                    proArguments: [...debate.proArguments, newArg],
                    currentArgument: data.content,
                  };
                  console.log('[SSE] Updating PRO arguments:', updated.proArguments.length);
                  updateDebate(activeDebate.id, updated);
                } else {
                  const updated = {
                    conArguments: [...debate.conArguments, newArg],
                    currentArgument: data.content,
                  };
                  console.log('[SSE] Updating CON arguments:', updated.conArguments.length);
                  updateDebate(activeDebate.id, updated);
                }
              } else {
                console.error('[SSE] Debate not found in store:', activeDebate.id);
                addLog(`Error: Debate ${activeDebate.id} not found`, 'error');
              }
            } catch (err) {
              console.error('[SSE] Error handling argument:', err);
              addLog(`Error processing argument: ${err}`, 'error');
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
  }, [activeDebate?.id, activeDebate?.status, updateDebate, addLog]);
  
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

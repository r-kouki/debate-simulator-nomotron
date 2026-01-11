import React, { useState, useEffect, useRef, useCallback } from 'react';

interface LogEntry {
    timestamp: string;
    message: string;
    type: 'info' | 'success' | 'error' | 'warning';
}

interface LessonContent {
    overview: string;
    key_concepts: string[];
    examples: string[];
    further_reading: { title: string }[];
    quiz_questions: string[];
}

interface LessonViewerWindowProps {
    windowId: string;
    componentProps?: {
        lessonId?: string;
    };
}

export const LessonViewerWindow: React.FC<LessonViewerWindowProps> = ({
    componentProps
}) => {
    const lessonId = componentProps?.lessonId;

    const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'error' | 'idle'>('idle');
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const [showLogs, setShowLogs] = useState(false);
    const [lesson, setLesson] = useState<LessonContent | null>(null);
    const [topic, setTopic] = useState<string>('');
    const [status, setStatus] = useState<string>('pending');
    const [progress, setProgress] = useState<number>(0);
    const [currentStep, setCurrentStep] = useState<string>('Initializing');

    const eventSourceRef = useRef<EventSource | null>(null);
    const logsEndRef = useRef<HTMLDivElement>(null);

    const addLog = useCallback((message: string, type: LogEntry['type'] = 'info') => {
        const timestamp = new Date().toLocaleTimeString();
        setLogs(prev => [...prev, { timestamp, message, type }]);
    }, []);

    useEffect(() => {
        logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [logs]);

    // Connect to SSE stream
    useEffect(() => {
        if (!lessonId) return;

        addLog(`Connecting to lesson stream: ${lessonId}`, 'info');
        setConnectionStatus('connecting');

        const sseUrl = `http://localhost:5040/api/lessons/${lessonId}/stream`;
        const eventSource = new EventSource(sseUrl);
        eventSourceRef.current = eventSource;

        eventSource.onopen = () => {
            addLog('✓ Connected to teaching stream', 'success');
            setConnectionStatus('connected');
        };

        eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log('[Lesson SSE]', data);

                switch (data.type) {
                    case 'lesson_started':
                        addLog(`Lesson started: "${data.topic}"`, 'success');
                        setTopic(data.topic);
                        setStatus('running');
                        break;

                    case 'lesson_progress':
                        addLog(`[${data.step}] ${data.message}`, 'info');
                        setCurrentStep(data.step);
                        setProgress(data.progress);
                        break;

                    case 'lesson_complete':
                        addLog('Lesson generated!', 'success');
                        setStatus('completed');
                        if (data.lesson) {
                            setLesson(data.lesson);
                        }
                        eventSource.close();
                        setConnectionStatus('idle');
                        break;

                    case 'error':
                        addLog(`Error: ${data.message}`, 'error');
                        setStatus('error');
                        eventSource.close();
                        setConnectionStatus('error');
                        break;

                    default:
                        addLog(`Unknown event: ${data.type}`, 'warning');
                }
            } catch (e) {
                addLog(`Parse error: ${event.data}`, 'error');
            }
        };

        eventSource.onerror = (error) => {
            console.error('SSE Error:', error);
            addLog('Connection error', 'error');
            setConnectionStatus('error');
            eventSource.close();
        };

        return () => {
            eventSource.close();
            eventSourceRef.current = null;
        };
    }, [lessonId, addLog]);

    // Fetch lesson if already complete
    useEffect(() => {
        if (!lessonId || lesson) return;

        const fetchLesson = async () => {
            try {
                const response = await fetch(`http://localhost:5040/api/lessons/${lessonId}`);
                if (response.ok) {
                    const data = await response.json();
                    if (data.status === 'completed' && data.lesson) {
                        setLesson(data.lesson);
                        setTopic(data.topic);
                        setStatus('completed');
                    }
                }
            } catch (e) {
                // Ignore - will use SSE
            }
        };
        fetchLesson();
    }, [lessonId, lesson]);

    if (!lessonId) {
        return (
            <div className="flex flex-col items-center justify-center h-full p-8 text-center">
                <div className="text-5xl mb-4">📚</div>
                <p className="text-gray-600 mb-2">No active lesson</p>
                <p className="text-sm text-gray-400">Use "New Lesson" to start learning</p>
            </div>
        );
    }

    return (
        <div className="lesson-viewer" style={{ display: 'flex', flexDirection: 'column', height: '100%', backgroundColor: '#1e1e2e', color: '#e0e0e0' }}>
            {/* Header */}
            <div style={{ padding: '12px 16px', borderBottom: '1px solid #333', backgroundColor: '#252536' }}>
                <div style={{ fontWeight: 'bold', fontSize: '16px', marginBottom: '4px' }}>
                    📚 {topic || 'Loading...'}
                </div>
                <div style={{ display: 'flex', gap: '16px', fontSize: '12px', color: '#888' }}>
                    <span>Status: {status === 'running' ? '⏳ Generating...' : status === 'completed' ? '✅ Complete' : status}</span>
                    {status === 'running' && <span>Progress: {progress.toFixed(0)}% ({currentStep})</span>}
                </div>
            </div>

            {/* Content Area */}
            <div style={{ flex: 1, overflow: 'auto', padding: '16px' }}>
                {status === 'running' && !lesson && (
                    <div style={{ textAlign: 'center', padding: '40px' }}>
                        <div className="spinner" style={{ width: '40px', height: '40px', border: '4px solid #333', borderTop: '4px solid #8b5cf6', borderRadius: '50%', animation: 'spin 1s linear infinite', margin: '0 auto 16px' }}></div>
                        <p style={{ color: '#888' }}>Generating lesson...</p>
                        <p style={{ color: '#666', fontSize: '12px', marginTop: '8px' }}>{currentStep}</p>
                    </div>
                )}

                {lesson && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                        {/* Overview */}
                        <section>
                            <h2 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '12px', color: '#8b5cf6' }}>📖 Overview</h2>
                            <div style={{ backgroundColor: '#252536', padding: '16px', borderRadius: '8px', lineHeight: '1.6', whiteSpace: 'pre-wrap' }}>
                                {lesson.overview}
                            </div>
                        </section>

                        {/* Key Concepts */}
                        {lesson.key_concepts?.length > 0 && (
                            <section>
                                <h2 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '12px', color: '#10b981' }}>💡 Key Concepts</h2>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                    {lesson.key_concepts.map((concept, idx) => (
                                        <div key={idx} style={{ backgroundColor: '#252536', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #10b981' }}>
                                            {concept}
                                        </div>
                                    ))}
                                </div>
                            </section>
                        )}

                        {/* Examples */}
                        {lesson.examples?.length > 0 && (
                            <section>
                                <h2 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '12px', color: '#f59e0b' }}>🔍 Examples</h2>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                    {lesson.examples.map((example, idx) => (
                                        <div key={idx} style={{ backgroundColor: '#252536', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #f59e0b' }}>
                                            {example}
                                        </div>
                                    ))}
                                </div>
                            </section>
                        )}

                        {/* Quiz Questions */}
                        {lesson.quiz_questions?.length > 0 && (
                            <section>
                                <h2 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '12px', color: '#3b82f6' }}>❓ Review Questions</h2>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                    {lesson.quiz_questions.map((question, idx) => (
                                        <div key={idx} style={{ backgroundColor: '#252536', padding: '12px', borderRadius: '6px', borderLeft: '3px solid #3b82f6' }}>
                                            <span style={{ fontWeight: 'bold', marginRight: '8px' }}>{idx + 1}.</span>
                                            {question}
                                        </div>
                                    ))}
                                </div>
                            </section>
                        )}

                        {/* Further Reading */}
                        {lesson.further_reading?.length > 0 && (
                            <section>
                                <h2 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '12px', color: '#ec4899' }}>📚 Further Reading</h2>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                    {lesson.further_reading.map((item, idx) => (
                                        <div key={idx} style={{ backgroundColor: '#252536', padding: '12px', borderRadius: '6px' }}>
                                            • {item.title}
                                        </div>
                                    ))}
                                </div>
                            </section>
                        )}
                    </div>
                )}
            </div>

            {/* Footer with logs toggle */}
            <div style={{ borderTop: '1px solid #333', padding: '8px 16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: '#252536' }}>
                <button
                    onClick={() => setShowLogs(!showLogs)}
                    style={{ background: 'none', border: 'none', color: '#888', cursor: 'pointer', fontSize: '12px' }}
                >
                    {showLogs ? 'Hide Logs' : 'Show Logs'}
                </button>
                <span style={{ fontSize: '11px', color: '#666' }}>
                    {connectionStatus === 'connected' ? '🟢 Connected' : connectionStatus === 'error' ? '🔴 Error' : '⚪ Idle'}
                </span>
            </div>

            {/* Logs Panel */}
            {showLogs && (
                <div style={{ maxHeight: '150px', overflow: 'auto', borderTop: '1px solid #333', backgroundColor: '#1a1a1a', padding: '8px', fontSize: '11px', fontFamily: 'monospace' }}>
                    {logs.map((log, idx) => (
                        <div key={idx} style={{ color: log.type === 'error' ? '#f87171' : log.type === 'success' ? '#34d399' : '#888' }}>
                            [{log.timestamp}] {log.message}
                        </div>
                    ))}
                    <div ref={logsEndRef} />
                </div>
            )}

            <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
        </div>
    );
};

import { useEffect, useRef, useState } from 'react';
import { debateApi } from '@/api';
import { DebateProgress } from '@/types';
import { useDebateStore } from '@/stores';

export const useDebateStream = (debateId: string | null) => {
  const [progress, setProgress] = useState<DebateProgress | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const cleanupRef = useRef<(() => void) | null>(null);
  const { updateDebateProgress } = useDebateStore();

  useEffect(() => {
    if (!debateId) {
      return;
    }

    // Clean up previous connection
    if (cleanupRef.current) {
      cleanupRef.current();
    }

    setIsConnected(true);
    setError(null);

    const cleanup = debateApi.streamDebateProgress(
      debateId,
      (data) => {
        setProgress(data);
        updateDebateProgress(data);

        // Disconnect when debate is complete
        if (data.status === 'completed' || data.status === 'error' || data.status === 'stopped') {
          setIsConnected(false);
        }
      },
      (err) => {
        console.error('Stream error:', err);
        setError('Connection lost');
        setIsConnected(false);
      }
    );

    cleanupRef.current = cleanup;

    return () => {
      if (cleanupRef.current) {
        cleanupRef.current();
        cleanupRef.current = null;
      }
      setIsConnected(false);
    };
  }, [debateId, updateDebateProgress]);

  return { progress, isConnected, error };
};

import React, { useEffect, useState } from 'react';
import { useWindowStore } from '@/stores';
import { apiClient } from '@/api/client';

interface CrewAIStatusWindowProps {
  windowId: string;
}

interface PackageInfo {
  installed: boolean;
  version: string | null;
}

interface GPUInfo {
  name: string;
  memory_total_mb: number;
  memory_used_mb: number;
  memory_free_mb: number;
}

interface CrewAIStatus {
  available: boolean;
  error: string | null;
  packages: Record<string, PackageInfo>;
  packages_error?: string;
  gpu: GPUInfo | null;
  venv_active: boolean;
  python_version: string;
  vllm_server_running: boolean;
}

export const CrewAIStatusWindow: React.FC<CrewAIStatusWindowProps> = ({ windowId }) => {
  const { closeWindow } = useWindowStore();
  
  const [status, setStatus] = useState<CrewAIStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchStatus = async () => {
    setRefreshing(true);
    try {
      const response = await apiClient.get('/crewai/status');
      setStatus(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to connect to backend server. Make sure it is running on port 5040.');
      setStatus(null);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const formatMemory = (mb: number) => {
    if (mb >= 1024) {
      return `${(mb / 1024).toFixed(1)} GB`;
    }
    return `${mb} MB`;
  };

  const memoryPercent = status?.gpu 
    ? ((status.gpu.memory_used_mb / status.gpu.memory_total_mb) * 100).toFixed(0)
    : 0;

  return (
    <div className="p-4 h-full flex flex-col gap-4 overflow-y-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="font-bold text-lg flex items-center gap-2">
          🤖 CrewAI System Status
        </h2>
        <button 
          className="xp-button px-3"
          onClick={fetchStatus}
          disabled={refreshing}
        >
          {refreshing ? '⏳' : '🔄'} Refresh
        </button>
      </div>

      {loading ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="text-4xl animate-spin mb-2">⏳</div>
            <p>Checking CrewAI status...</p>
          </div>
        </div>
      ) : error ? (
        <div className="bg-red-100 border-2 border-red-400 p-4 rounded">
          <h3 className="font-bold text-red-800 mb-2">❌ Connection Error</h3>
          <p className="text-sm text-red-700">{error}</p>
          <div className="mt-4 p-3 bg-white rounded border border-red-300 text-xs font-mono">
            <p className="font-bold mb-2">To start the backend:</p>
            <code className="block">cd /home/remote-core/project/debate-simulator-nomotron</code>
            <code className="block">source .venv/bin/activate</code>
            <code className="block">python scripts/run_xp_server.py</code>
          </div>
        </div>
      ) : status && (
        <>
          {/* Main Status */}
          <div className={`p-4 rounded border-2 ${
            status.available 
              ? 'bg-green-100 border-green-400' 
              : 'bg-red-100 border-red-400'
          }`}>
            <div className="flex items-center gap-3">
              <span className="text-3xl">{status.available ? '✅' : '❌'}</span>
              <div>
                <h3 className="font-bold text-lg">
                  CrewAI is {status.available ? 'Available' : 'Not Available'}
                </h3>
                {status.error && (
                  <p className="text-sm text-red-700 mt-1">{status.error}</p>
                )}
              </div>
            </div>
          </div>

          {/* vLLM Server Warning */}
          {status.vllm_server_running && (
            <div className="bg-yellow-100 border-2 border-yellow-400 p-3 rounded">
              <p className="text-sm text-yellow-800">
                <strong>⚠️ Warning:</strong> vLLM server is running on port 8000. 
                This may cause GPU memory conflicts. Stop it with:
              </p>
              <code className="text-xs bg-white px-2 py-1 rounded mt-1 inline-block">
                pkill -f 'vllm.entrypoints.openai.api_server'
              </code>
            </div>
          )}

          {/* GPU Status */}
          <fieldset className="border-2 border-gray-300 p-3 rounded">
            <legend className="px-2 text-sm font-bold">🎮 GPU Status</legend>
            {status.gpu ? (
              <div className="space-y-2">
                <p className="text-sm"><strong>GPU:</strong> {status.gpu.name}</p>
                <div className="flex flex-col gap-1">
                  <div className="flex justify-between text-xs">
                    <span>VRAM Usage</span>
                    <span>{memoryPercent}%</span>
                  </div>
                  <div className="h-5 bg-gray-200 border border-gray-400 rounded overflow-hidden">
                    <div 
                      className={`h-full transition-all ${
                        Number(memoryPercent) > 80 
                          ? 'bg-red-500' 
                          : Number(memoryPercent) > 50 
                          ? 'bg-yellow-500' 
                          : 'bg-green-500'
                      }`}
                      style={{ width: `${memoryPercent}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-xs text-gray-600">
                    <span>Used: {formatMemory(status.gpu.memory_used_mb)}</span>
                    <span>Free: {formatMemory(status.gpu.memory_free_mb)}</span>
                    <span>Total: {formatMemory(status.gpu.memory_total_mb)}</span>
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-sm text-gray-500">No GPU detected or nvidia-smi not available</p>
            )}
          </fieldset>

          {/* Package Status */}
          <fieldset className="border-2 border-gray-300 p-3 rounded">
            <legend className="px-2 text-sm font-bold">📦 Required Packages</legend>
            {status.packages_error ? (
              <p className="text-sm text-red-600">{status.packages_error}</p>
            ) : (
              <div className="grid grid-cols-2 gap-2">
                {Object.entries(status.packages).map(([pkg, info]) => (
                  <div 
                    key={pkg}
                    className={`text-xs p-2 rounded ${
                      info.installed 
                        ? 'bg-green-50 border border-green-200' 
                        : 'bg-red-50 border border-red-200'
                    }`}
                  >
                    <span className="mr-1">{info.installed ? '✅' : '❌'}</span>
                    <strong>{pkg}</strong>
                    {info.version && (
                      <span className="text-gray-500 ml-1">v{info.version}</span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </fieldset>

          {/* Environment Info */}
          <fieldset className="border-2 border-gray-300 p-3 rounded">
            <legend className="px-2 text-sm font-bold">🐍 Environment</legend>
            <div className="space-y-1 text-sm">
              <p>
                <strong>Virtual Env:</strong>{' '}
                <span className={status.venv_active ? 'text-green-600' : 'text-red-600'}>
                  {status.venv_active ? '✅ Active' : '❌ Not Active'}
                </span>
              </p>
              <p className="text-xs text-gray-600 truncate">
                <strong>Python:</strong> {status.python_version.split(' ')[0]}
              </p>
            </div>
          </fieldset>

          {/* Instructions */}
          {!status.available && (
            <div className="bg-blue-50 border border-blue-300 p-3 rounded">
              <h4 className="font-bold text-blue-800 mb-2">📋 Setup Instructions</h4>
              <ol className="text-xs space-y-1 list-decimal list-inside text-blue-900">
                <li>Activate the virtual environment: <code className="bg-white px-1">source .venv/bin/activate</code></li>
                <li>Install dependencies: <code className="bg-white px-1">pip install -r requirements.txt</code></li>
                <li>Restart the backend server</li>
              </ol>
            </div>
          )}
        </>
      )}

      {/* Actions */}
      <div className="flex justify-end gap-2 pt-2 border-t border-gray-300 mt-auto">
        <button 
          className="xp-button px-4"
          onClick={() => closeWindow(windowId)}
        >
          Close
        </button>
      </div>
    </div>
  );
};

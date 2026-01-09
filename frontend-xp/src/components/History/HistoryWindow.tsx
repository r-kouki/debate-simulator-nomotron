import React, { useState } from 'react';
import { useDebateStore, useWindowStore, useUIStore } from '@/stores';
import { DebateSession, DebateStatus } from '@/types';

interface HistoryWindowProps {
  windowId: string;
  componentProps?: Record<string, unknown>;
}

export const HistoryWindow: React.FC<HistoryWindowProps> = ({ windowId }) => {
  const debates = useDebateStore((state) => state.debates);
  const { removeDebate } = useDebateStore();
  const { openWindow, closeWindow } = useWindowStore();
  const { addNotification } = useUIStore();

  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<DebateStatus | 'all'>('all');
  const [sortBy, setSortBy] = useState<'date' | 'topic'>('date');

  const filteredDebates = debates
    .filter((d) => {
      if (searchTerm && !d.topic.toLowerCase().includes(searchTerm.toLowerCase())) {
        return false;
      }
      if (statusFilter !== 'all' && d.status !== statusFilter) {
        return false;
      }
      return true;
    })
    .sort((a, b) => {
      if (sortBy === 'date') {
        return new Date(b.startTime).getTime() - new Date(a.startTime).getTime();
      }
      return a.topic.localeCompare(b.topic);
    });

  const handleViewDebate = (debate: DebateSession) => {
    if (debate.status === 'completed') {
      openWindow({
        id: `results-${debate.id}`,
        title: `Results: ${debate.topic.slice(0, 25)}...`,
        icon: '📊',
        component: 'results-viewer',
        componentProps: { debateId: debate.id },
      });
    } else {
      openWindow({
        id: `viewer-${debate.id}`,
        title: `Debate: ${debate.topic.slice(0, 25)}...`,
        icon: '🎯',
        component: 'debate-viewer',
        componentProps: { debateId: debate.id },
      });
    }
  };

  const handleDeleteDebate = (debate: DebateSession) => {
    if (window.confirm(`Delete debate: "${debate.topic}"?`)) {
      removeDebate(debate.id);
      addNotification({
        title: 'Deleted',
        message: 'Debate has been deleted',
        type: 'info',
      });
    }
  };

  const getStatusIcon = (status: DebateStatus) => {
    switch (status) {
      case 'pending':
        return '⏳';
      case 'running':
        return '▶️';
      case 'completed':
        return '✅';
      case 'error':
        return '❌';
      case 'stopped':
        return '⏹️';
      default:
        return '❓';
    }
  };

  const getStatusColor = (status: DebateStatus) => {
    switch (status) {
      case 'pending':
        return 'text-yellow-600';
      case 'running':
        return 'text-blue-600';
      case 'completed':
        return 'text-green-600';
      case 'error':
        return 'text-red-600';
      case 'stopped':
        return 'text-gray-600';
      default:
        return 'text-gray-500';
    }
  };

  return (
    <div className="p-4 h-full flex flex-col gap-4">
      {/* Search and Filters */}
      <div className="flex gap-2">
        <input
          type="text"
          className="xp-input flex-1"
          placeholder="Search debates..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
        <select
          className="xp-select"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as DebateStatus | 'all')}
        >
          <option value="all">All Status</option>
          <option value="completed">Completed</option>
          <option value="running">Running</option>
          <option value="pending">Pending</option>
          <option value="error">Error</option>
          <option value="stopped">Stopped</option>
        </select>
        <select
          className="xp-select"
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as 'date' | 'topic')}
        >
          <option value="date">Sort by Date</option>
          <option value="topic">Sort by Topic</option>
        </select>
      </div>

      {/* Debate List */}
      <div className="flex-1 overflow-y-auto border-2 border-gray-300 bg-white rounded">
        {filteredDebates.length === 0 ? (
          <div className="p-4 text-center text-gray-500">
            {debates.length === 0 ? (
              <>
                <p className="text-lg mb-2">No debates yet</p>
                <p className="text-sm">Create your first debate to get started!</p>
              </>
            ) : (
              <p>No debates match your search</p>
            )}
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {filteredDebates.map((debate) => (
              <div
                key={debate.id}
                className="p-3 hover:bg-blue-50 cursor-pointer flex items-center gap-3"
                onClick={() => handleViewDebate(debate)}
              >
                <span className="text-2xl">{getStatusIcon(debate.status)}</span>
                <div className="flex-1 min-w-0">
                  <h4 className="font-bold text-sm truncate">{debate.topic}</h4>
                  <div className="flex gap-3 text-xs text-gray-500">
                    <span className={getStatusColor(debate.status)}>{debate.status}</span>
                    <span>Domain: {debate.domain}</span>
                    <span>Rounds: {debate.rounds}</span>
                    <span>{new Date(debate.startTime).toLocaleDateString()}</span>
                  </div>
                </div>
                {debate.judgeScore && (
                  <div className="text-center px-2">
                    <div
                      className={`text-xs font-bold ${
                        debate.judgeScore.winner === 'pro'
                          ? 'text-green-600'
                          : debate.judgeScore.winner === 'con'
                          ? 'text-red-600'
                          : 'text-yellow-600'
                      }`}
                    >
                      {debate.judgeScore.winner.toUpperCase()}
                    </div>
                    <div className="text-[10px] text-gray-400">Winner</div>
                  </div>
                )}
                <button
                  className="xp-button text-xs px-2 py-1"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDeleteDebate(debate);
                  }}
                >
                  Delete
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Stats */}
      <div className="flex gap-4 text-sm bg-xp-gray-light p-2 rounded border border-gray-300">
        <span>
          <strong>Total:</strong> {debates.length}
        </span>
        <span>
          <strong>Completed:</strong> {debates.filter((d) => d.status === 'completed').length}
        </span>
        <span>
          <strong>Running:</strong> {debates.filter((d) => d.status === 'running').length}
        </span>
      </div>

      {/* Actions */}
      <div className="flex justify-end gap-2 pt-2 border-t border-gray-300">
        <button
          className="xp-button px-4"
          onClick={() => {
            openWindow({
              id: 'debate-creator',
              title: 'New Debate',
              icon: '💬',
              component: 'debate-creator',
            });
          }}
        >
          New Debate
        </button>
        <button className="xp-button px-4" onClick={() => closeWindow(windowId)}>
          Close
        </button>
      </div>
    </div>
  );
};

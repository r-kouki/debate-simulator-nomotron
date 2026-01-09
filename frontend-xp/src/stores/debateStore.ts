import { create } from 'zustand';
import { DebateSession, DebateProgress, AdapterInfo } from '@/types';

interface DebateStore {
  // State
  debates: DebateSession[];
  activeDebateId: string | null;
  isCreating: boolean;
  adapters: AdapterInfo[];

  // Actions
  setDebates: (debates: DebateSession[]) => void;
  addDebate: (debate: DebateSession) => void;
  updateDebate: (id: string, updates: Partial<DebateSession>) => void;
  removeDebate: (id: string) => void;
  setActiveDebate: (id: string | null) => void;
  setIsCreating: (isCreating: boolean) => void;
  setAdapters: (adapters: AdapterInfo[]) => void;
  getDebateById: (id: string) => DebateSession | undefined;
  
  // Progress updates
  updateDebateProgress: (progress: DebateProgress) => void;
}

export const useDebateStore = create<DebateStore>((set, get) => ({
  debates: [],
  activeDebateId: null,
  isCreating: false,
  adapters: [],

  setDebates: (debates) => set({ debates }),

  addDebate: (debate) =>
    set((state) => ({
      debates: [debate, ...state.debates],
    })),

  updateDebate: (id, updates) =>
    set((state) => ({
      debates: state.debates.map((d) =>
        d.id === id ? { ...d, ...updates } : d
      ),
    })),

  removeDebate: (id) =>
    set((state) => ({
      debates: state.debates.filter((d) => d.id !== id),
      activeDebateId: state.activeDebateId === id ? null : state.activeDebateId,
    })),

  setActiveDebate: (id) => set({ activeDebateId: id }),

  setIsCreating: (isCreating) => set({ isCreating }),

  setAdapters: (adapters) => set({ adapters }),

  getDebateById: (id) => get().debates.find((d) => d.id === id),

  updateDebateProgress: (progress) => {
    const { debates } = get();
    const debate = debates.find((d) => d.id === progress.debateId);
    
    if (!debate) return;

    const updates: Partial<DebateSession> = {
      status: progress.status,
      currentStep: progress.step,
      currentRound: progress.round,
      progress: progress.progress,
    };

    if (progress.argument) {
      const newArgument = {
        side: progress.argument.side,
        round: progress.round,
        content: progress.argument.content,
        timestamp: new Date().toISOString(),
      };

      if (progress.argument.side === 'pro') {
        updates.proArguments = [...(debate.proArguments || []), newArgument];
      } else {
        updates.conArguments = [...(debate.conArguments || []), newArgument];
      }
      updates.currentArgument = progress.argument.content;
    }

    set((state) => ({
      debates: state.debates.map((d) =>
        d.id === progress.debateId ? { ...d, ...updates } : d
      ),
    }));
  },
}));

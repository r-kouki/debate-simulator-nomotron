import { apiClient } from './client';
import { DebateConfig, DebateSession, DebateProgress, AdapterInfo } from '@/types';

export interface CreateDebateResponse {
  id: string;
  status: string;
  message: string;
}

export const debateApi = {
  /**
   * Create a new debate
   */
  createDebate: async (config: DebateConfig): Promise<CreateDebateResponse> => {
    const response = await apiClient.post<CreateDebateResponse>('/debates', {
      topic: config.topic,
      rounds: config.rounds,
      use_internet: config.useInternet,
      recommend_guests: config.recommendGuests,
      domain: config.domain,
      adapter: config.adapter,
      mode: config.mode || 'ai_vs_ai',
      human_side: config.humanSide,
    });
    return response.data;
  },

  /**
   * Get a specific debate by ID
   */
  getDebate: async (id: string): Promise<DebateSession> => {
    const response = await apiClient.get<DebateSession>(`/debates/${id}`);
    return mapApiDebate(response.data);
  },

  /**
   * List all debates
   */
  listDebates: async (params?: { limit?: number; offset?: number }): Promise<DebateSession[]> => {
    const response = await apiClient.get<DebateSession[]>('/debates', { params });
    return response.data.map(mapApiDebate);
  },

  /**
   * Delete a debate
   */
  deleteDebate: async (id: string): Promise<void> => {
    await apiClient.delete(`/debates/${id}`);
  },

  /**
   * Stop a running debate
   */
  stopDebate: async (id: string): Promise<void> => {
    await apiClient.post(`/debates/${id}/stop`);
  },

  /**
   * Submit a human's debate turn (for human_vs_ai mode)
   */
  submitHumanTurn: async (debateId: string, argument: string): Promise<{ status: string; message: string }> => {
    const response = await apiClient.post(`/debates/${debateId}/human-turn`, { argument });
    return response.data;
  },

  /**
   * Subscribe to debate progress updates via SSE
   */
  streamDebateProgress: (
    id: string,
    onProgress: (data: DebateProgress) => void,
    onError?: (error: Event) => void
  ): (() => void) => {
    const baseUrl = import.meta.env.VITE_API_URL || '/api';
    const eventSource = new EventSource(`${baseUrl}/debates/${id}/stream`);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onProgress(mapApiProgress(data));
      } catch (e) {
        console.error('Error parsing SSE message:', e);
      }
    };

    eventSource.onerror = (error) => {
      console.error('SSE Error:', error);
      if (onError) onError(error);
      eventSource.close();
    };

    return () => eventSource.close();
  },

  /**
   * List available adapters
   */
  listAdapters: async (): Promise<AdapterInfo[]> => {
    const response = await apiClient.get<AdapterInfo[]>('/adapters');
    return response.data;
  },

  /**
   * Health check
   */
  healthCheck: async (): Promise<{ status: string; crewai_available: boolean }> => {
    const response = await apiClient.get('/health');
    return response.data;
  },
};

// Map API response to frontend types (handle snake_case to camelCase)
function mapApiDebate(data: any): DebateSession {
  return {
    id: data.id,
    topic: data.topic,
    domain: data.domain,
    rounds: data.rounds,
    status: data.status,
    startTime: data.start_time,
    endTime: data.end_time,
    currentRound: data.current_round,
    currentStep: data.current_step,
    progress: data.progress,
    proArguments: data.pro_arguments?.map(mapApiArgument) || [],
    conArguments: data.con_arguments?.map(mapApiArgument) || [],
    currentArgument: data.current_argument,
    judgeScore: data.judge_score ? {
      winner: data.judge_score.winner,
      proScore: data.judge_score.pro_score,
      conScore: data.judge_score.con_score,
      reasoning: data.judge_score.reasoning,
      factCheckPassed: data.judge_score.fact_check_passed,
    } : undefined,
    error: data.error,
  };
}

function mapApiArgument(data: any) {
  return {
    side: data.side,
    round: data.round,
    content: data.content,
    timestamp: data.timestamp,
  };
}

function mapApiProgress(data: any): DebateProgress {
  // Extract argument data if this is an argument event
  let argument = undefined;
  if (data.type === 'argument' && data.side && data.content) {
    argument = {
      side: data.side,
      content: data.content,
      round: data.round,
    };
  } else if (data.argument) {
    // Fallback for nested argument object
    argument = data.argument;
  }

  return {
    debateId: data.debate_id,
    status: data.status,
    step: data.step,
    round: data.round,
    progress: data.progress,
    message: data.message,
    argument,
  };
}

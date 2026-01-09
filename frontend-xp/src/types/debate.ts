export type DebateStatus = 'pending' | 'running' | 'completed' | 'error' | 'stopped';

export interface DebateConfig {
  topic: string;
  rounds: number;
  useInternet: boolean;
  recommendGuests: boolean;
  domain?: string;
  adapter?: string;
}

export interface JudgeScore {
  winner: 'pro' | 'con' | 'tie';
  proScore: number;
  conScore: number;
  reasoning: string;
  factCheckPassed: boolean;
}

export interface DebateArgument {
  side: 'pro' | 'con';
  round: number;
  content: string;
  timestamp: string;
  isHuman?: boolean;
}

export interface DebateSession {
  id: string;
  topic: string;
  domain: string;
  rounds: number;
  status: DebateStatus;
  startTime: string;
  endTime?: string;
  currentRound: number;
  currentStep: string;
  progress: number;
  proArguments: DebateArgument[];
  conArguments: DebateArgument[];
  currentArgument?: string;
  judgeScore?: JudgeScore;
  artifacts?: {
    json: string;
    transcript: string;
  };
  error?: string;
  humanMode?: boolean;
  humanSide?: 'pro' | 'con';
}

export interface DebateProgress {
  debateId: string;
  status: DebateStatus;
  step: string;
  round: number;
  progress: number;
  message: string;
  argument?: {
    side: 'pro' | 'con';
    content: string;
  };
}

export interface AdapterInfo {
  id: string;
  name: string;
  domain: string;
  description: string;
  path: string;
}

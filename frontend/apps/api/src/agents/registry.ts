/**
 * Agent Registry - Extensible agent framework
 *
 * To add a new agent:
 * 1. Create an agent file (e.g., myAgent.ts) that exports an AgentHandler
 * 2. Import and register it in this file: registerAgent("my-agent", myAgentHandler)
 * 3. The agent will be available at POST /api/agents/my-agent
 */

import type { AgentRequest, AgentResponse } from "@debate/contracts";

export type AgentHandler = (request: AgentRequest) => Promise<AgentResponse>;

const agentRegistry = new Map<string, AgentHandler>();

export const registerAgent = (agentId: string, handler: AgentHandler): void => {
  if (agentRegistry.has(agentId)) {
    throw new Error(`Agent "${agentId}" is already registered`);
  }
  agentRegistry.set(agentId, handler);
};

export const getAgent = (agentId: string): AgentHandler | undefined => {
  return agentRegistry.get(agentId);
};

export const getRegisteredAgentIds = (): string[] => {
  return Array.from(agentRegistry.keys());
};

export const hasAgent = (agentId: string): boolean => {
  return agentRegistry.has(agentId);
};

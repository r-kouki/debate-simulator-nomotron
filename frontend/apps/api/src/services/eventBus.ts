import type { ServerResponse } from "node:http";

export type EventPayload = {
  type: string;
  data: unknown;
  time: string;
};

export class EventBus {
  private streams: Map<string, Set<ServerResponse>> = new Map();

  subscribe(debateId: string, res: ServerResponse) {
    const current = this.streams.get(debateId) ?? new Set();
    current.add(res);
    this.streams.set(debateId, current);
  }

  unsubscribe(debateId: string, res: ServerResponse) {
    const current = this.streams.get(debateId);
    if (!current) {
      return;
    }
    current.delete(res);
    if (current.size === 0) {
      this.streams.delete(debateId);
    }
  }

  emit(debateId: string, type: string, data: unknown) {
    const payload: EventPayload = { type, data, time: new Date().toISOString() };
    const message = `event: ${type}\ndata: ${JSON.stringify(payload)}\n\n`;
    const current = this.streams.get(debateId);
    if (!current) {
      return;
    }
    current.forEach((res) => {
      res.write(message);
    });
  }
}

export const eventBus = new EventBus();

export interface CouncilEvent {
  id: string;
  topic: string;
  payload: any;
  timestamp: string;
}

export interface CouncilBus {
  publish: (topic: string, payload: any) => CouncilEvent | undefined;
  subscribe: (topic: string, listener: (event: CouncilEvent) => void) => () => void;
  subscribeAll?: (listener: (event: { topic: string; payload: any; ts: number; id: string; timestamp: string }) => void) => () => void;
  getRecentEvents: (topic?: string | null, limit?: number) => CouncilEvent[];
  agentHealth?: Map<string, any>;
  reportAgentHealth?: (agentId: string, status: any) => void;
  getAgentHealth?: (agentId?: string | null) => any;
}

export const councilBus: CouncilBus;

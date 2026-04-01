export interface EventBus {
  subscribe: (event: string, handler: (data: any) => void) => void;
  publish: (event: string, data: any) => void;
}

export const eventBus: EventBus;

// Central Tick Dispatcher - Core Game Spine
// Bridges symbolic ΞΘΛΔ_tick operations to literal game loop execution

export type TickChannel = 'idle' | 'fast' | 'combat' | 'ui' | 'simulation';
export type TickCallback = (deltaTime: number) => void;

export interface TickStats {
  channel: TickChannel;
  rate_hz: number;
  last_tick: number;
  total_ticks: number;
  avg_delta: number;
  subscribers: number;
  paused: boolean;
}

export class TickBus {
  private channels = new Map<TickChannel, {
    rate_hz: number;
    subscribers: Set<TickCallback>;
    last_tick: number;
    total_ticks: number;
    paused: boolean;
    interval_id: NodeJS.Timeout | null;
    delta_history: number[];
  }>();

  private receiptCounter = 0;

  constructor() {
    this.initializeChannels();
    this.startHeartbeat();
    console.log('[TickBus] Central tick dispatcher initialized');
  }

  private initializeChannels() {
    const defaultChannels: Array<{channel: TickChannel, rate: number}> = [
      { channel: 'idle', rate: 1 },        // 1 Hz - slow background ticks
      { channel: 'fast', rate: 10 },       // 10 Hz - normal gameplay
      { channel: 'combat', rate: 30 },     // 30 Hz - real-time combat
      { channel: 'ui', rate: 60 },         // 60 Hz - UI updates
      { channel: 'simulation', rate: 100 } // 100 Hz - physics simulation
    ];

    for (const {channel, rate} of defaultChannels) {
      this.channels.set(channel, {
        rate_hz: rate,
        subscribers: new Set(),
        last_tick: performance.now(),
        total_ticks: 0,
        paused: false,
        interval_id: null,
        delta_history: []
      });
    }
  }

  subscribe(channel: TickChannel, callback: TickCallback): () => void {
    const channelData = this.channels.get(channel);
    if (!channelData) {
      throw new Error(`Invalid tick channel: ${channel}`);
    }

    channelData.subscribers.add(callback);
    this.updateChannelTimer(channel);

    console.log(`[TickBus] Subscribed to ${channel} channel (${channelData.subscribers.size} subscribers)`);

    // Return unsubscribe function
    return () => {
      channelData.subscribers.delete(callback);
      if (channelData.subscribers.size === 0) {
        this.pauseChannel(channel);
      }
    };
  }

  setRate(channel: TickChannel, hz: number): void {
    const channelData = this.channels.get(channel);
    if (!channelData) return;

    channelData.rate_hz = Math.max(0.1, Math.min(1000, hz)); // Clamp between 0.1-1000 Hz
    this.updateChannelTimer(channel);
    
    console.log(`[TickBus] ${channel} rate set to ${hz} Hz`);
    this.emitReceipt('tick_rate_change', { channel, old_rate: channelData.rate_hz, new_rate: hz });
  }

  pause(channel: TickChannel): void {
    this.pauseChannel(channel);
    console.log(`[TickBus] ${channel} channel paused`);
    this.emitReceipt('tick_pause', { channel });
  }

  resume(channel: TickChannel): void {
    const channelData = this.channels.get(channel);
    if (!channelData) return;

    channelData.paused = false;
    this.updateChannelTimer(channel);
    console.log(`[TickBus] ${channel} channel resumed`);
    this.emitReceipt('tick_resume', { channel });
  }

  private pauseChannel(channel: TickChannel): void {
    const channelData = this.channels.get(channel);
    if (!channelData) return;

    channelData.paused = true;
    if (channelData.interval_id) {
      clearInterval(channelData.interval_id);
      channelData.interval_id = null;
    }
  }

  private updateChannelTimer(channel: TickChannel): void {
    const channelData = this.channels.get(channel);
    if (!channelData || channelData.paused) return;

    // Clear existing timer
    if (channelData.interval_id) {
      clearInterval(channelData.interval_id);
    }

    // Only start timer if there are subscribers
    if (channelData.subscribers.size === 0) return;

    const intervalMs = 1000 / channelData.rate_hz;
    
    channelData.interval_id = setInterval(() => {
      this.tickChannel(channel);
    }, intervalMs);
  }

  private tickChannel(channel: TickChannel): void {
    const channelData = this.channels.get(channel);
    if (!channelData || channelData.paused) return;

    const now = performance.now();
    const deltaTime = (now - channelData.last_tick) / 1000; // Convert to seconds
    
    // Update channel stats
    channelData.last_tick = now;
    channelData.total_ticks++;
    channelData.delta_history.push(deltaTime);
    
    // Keep only last 60 deltas for averaging
    if (channelData.delta_history.length > 60) {
      channelData.delta_history.shift();
    }

    // Call all subscribers
    for (const callback of channelData.subscribers) {
      try {
        callback(deltaTime);
      } catch (error) {
        console.error(`[TickBus] Error in ${channel} subscriber:`, error);
      }
    }

    // Emit heartbeat receipt every 100 ticks
    if (channelData.total_ticks % 100 === 0) {
      this.emitHeartbeatReceipt(channel, channelData);
    }
  }

  getStats(channel?: TickChannel): TickStats | TickStats[] {
    if (channel) {
      const channelData = this.channels.get(channel);
      if (!channelData) throw new Error(`Invalid channel: ${channel}`);
      
      return {
        channel,
        rate_hz: channelData.rate_hz,
        last_tick: channelData.last_tick,
        total_ticks: channelData.total_ticks,
        avg_delta: channelData.delta_history.reduce((a, b) => a + b, 0) / channelData.delta_history.length || 0,
        subscribers: channelData.subscribers.size,
        paused: channelData.paused
      };
    }

    // Return stats for all channels
    return Array.from(this.channels.keys()).map(ch => this.getStats(ch) as TickStats);
  }

  private startHeartbeat(): void {
    // Meta-heartbeat to ensure the system stays alive
    setInterval(() => {
      const activeChannels = Array.from(this.channels.values()).filter(ch => !ch.paused && ch.subscribers.size > 0);
      if (activeChannels.length === 0) {
        console.log('[TickBus] No active channels - system idle');
      }
    }, 10000); // Check every 10 seconds
  }

  private async emitHeartbeatReceipt(channel: TickChannel, channelData: any): Promise<void> {
    const receipt = {
      action: 'tick_heartbeat',
      channel,
      timestamp: Date.now(),
      total_ticks: channelData.total_ticks,
      rate_hz: channelData.rate_hz,
      subscribers: channelData.subscribers.size,
      avg_delta: channelData.delta_history.reduce((a, b) => a + b, 0) / channelData.delta_history.length || 0
    };

    try {
      const { promises: fs } = await import('node:fs');
      await fs.mkdir('SystemDev/receipts/ticks', { recursive: true });
      await fs.appendFile(
        `SystemDev/receipts/ticks/${channel}_heartbeat.jsonl`,
        JSON.stringify(receipt) + '\n'
      );
    } catch (error) {
      // Fail silently - receipts are nice-to-have
    }
  }

  private async emitReceipt(action: string, data: any): Promise<void> {
    const receipt = {
      action,
      timestamp: Date.now(),
      receipt_id: `tick_${this.receiptCounter++}`,
      ...data
    };

    try {
      const { promises: fs } = await import('node:fs');
      await fs.mkdir('SystemDev/receipts/ticks', { recursive: true });
      await fs.writeFile(
        `SystemDev/receipts/ticks/${action}_${Date.now()}.json`,
        JSON.stringify(receipt, null, 2)
      );
    } catch (error) {
      // Fail silently
    }
  }

  // Msg⛛ command interface for symbolic integration
  processMsgCommand(command: string): boolean {
    const parts = command.split(' ');
    
    if (parts[0] === 'Tick:Rate' && parts.length === 3) {
      const channel = parts[1] as TickChannel;
      const rate = parseFloat(parts[2]);
      if (this.channels.has(channel) && !isNaN(rate)) {
        this.setRate(channel, rate);
        return true;
      }
    } else if (parts[0] === 'Tick:Pause' && parts.length === 2) {
      const channel = parts[1] as TickChannel;
      if (this.channels.has(channel)) {
        this.pause(channel);
        return true;
      }
    } else if (parts[0] === 'Tick:Resume' && parts.length === 2) {
      const channel = parts[1] as TickChannel;
      if (this.channels.has(channel)) {
        this.resume(channel);
        return true;
      }
    }
    
    return false;
  }

  // Destroy tick bus cleanly
  destroy(): void {
    for (const channelData of this.channels.values()) {
      if (channelData.interval_id) {
        clearInterval(channelData.interval_id);
      }
    }
    this.channels.clear();
    console.log('[TickBus] Destroyed');
  }
}

export const tickBus = new TickBus();
---
source: kb/kb/specs/event-bus-architecture.md
updated: 2025-08-30T05:30:30.631Z
tags: [corelink, ]
---

# Event Bus Architecture

**Status**: Implemented  
**Date**: 2025-08-27  
**Version**: 1.0  

## Overview

The KPulse event bus is the central nervous system of our integrated ecosystem, enabling real-time communication between all subsystems through WebSocket JSON-RPC.

## Design Principles

1. **Single Source of Truth**: All state changes flow through the bus
2. **No Hidden Side-Effects**: Every interaction is observable
3. **Event-First Architecture**: UI actions become events, not direct calls
4. **Validation at Boundaries**: All events validated against schemas

## Components

### Event Types
- `TICK` - Engine heartbeat (250ms intervals)
- `UI.CLICK` - User interface interactions
- `STORY.EVENT` - Narrative system events
- `DIRECTIVE.SPAWNED` - Self-building content creation
- `TIER.ADVANCE` - Civilization progression
- `METRICS.RESOURCE` - Resource tracking

### RPC Methods
- `engine.getState()` - Retrieve current game state
- `story.next()` - Generate narrative content
- `repopilot.ask()` - Query LLM for assistance
- `directive.spawn()` - Create new game content

## Integration Points

- **Engine**: Core game loop broadcasts TICK events
- **Storyteller**: Responds to state changes with narrative
- **RepoPilot**: Analyzes event streams for insights
- **UI Systems**: All interactions converted to events
- **Analytics**: Passive event consumption for metrics

## Benefits

- Real-time debugging through event stream monitoring
- Perfect audit trail of all system interactions
- Loose coupling between subsystems
- Easy integration of new components
- Automated testing through event replay

## Next Steps

- Add event persistence for historical analysis
- Implement event filtering and routing
- Create dashboard for real-time monitoring
- Add performance metrics collection
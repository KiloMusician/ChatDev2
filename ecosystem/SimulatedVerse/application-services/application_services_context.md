# Application Services Suite

**Purpose**: Collection of specialized application services including game engine, development assistant, storytelling, and web interface.

## Directory Structure

### `/engine/`
**Context**: Core game engine and simulation systems
- Game loop and state management
- Resource calculation and progression mechanics
- Real-time simulation and automation systems

### `/repopilot/`
**Context**: Replit development assistant and automation
- Development workflow automation
- Code assistance and intelligent suggestions
- Integration with Replit development environment

### `/storyteller/`
**Context**: Narrative generation and progression systems
- Story beat generation and management
- Character development and plot progression
- Integration with ΞNuSyQ consciousness for narrative decisions

### `/web/`
**Context**: Web application interface and visualization
- **`src/engine/`** - Web-facing game engine interface
- **`src/modules/`** - Modular web components
- **`src/render/`** - Rendering and visualization systems
- **`src/views/`** - Game view management (city, colony, microbe, planet, space, system)
- **`main.ts`** - Web application entry point
- **`index.html`** - Web interface HTML
- **`package.json`** - Web application dependencies
- **`vite.config.ts`** - Vite build configuration

## Integration Points

- **ΞNuSyQ Consciousness** - Storyteller integrates with consciousness for narrative decisions
- **Game Engine** - Core simulation engine powers all gameplay mechanics
- **Web Interface** - Real-time visualization of game state and progression
- **Development Tools** - RepoPilot assists with code generation and maintenance

## Key Features

- **Multi-Scale Views** - From microbe to cosmic scale simulation
- **Real-time Visualization** - Live updating web interface
- **Intelligent Assistance** - AI-powered development automation
- **Narrative Integration** - Story-driven gameplay progression
- **Modular Architecture** - Loosely coupled service components

## Service Architecture

Each service operates independently while sharing common infrastructure:
- **Engine** - Core game simulation and mechanics
- **RepoPilot** - Development workflow automation
- **Storyteller** - Narrative generation and management  
- **Web** - User interface and visualization layer

**Last Renamed**: August 2025 - Repository cleanup initiative
**Formerly**: apps/ (renamed for descriptive clarity)
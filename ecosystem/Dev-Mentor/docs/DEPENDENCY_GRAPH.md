# Dependency Graph — DevMentor Colony

Visual map of service and agent dependencies within the colony.
Generated as part of Phase 0: Inventory & Mapping.

---

## Core Service Dependencies

```mermaid
graph TB
    subgraph REPLIT["Replit Surface (Primary)"]
        API["FastAPI Server\n:5000"]
        GAME["Terminal Depths\nGame Engine"]
        SERENA["Serena ΨΞΦΩ\nConvergence Layer"]
        SCHED["Content Scheduler"]
        NUSYQ["NuSyQ-Hub Bridge"]
    end

    subgraph AGENTS["Agent Layer"]
        GORDON["Gordon\nAutonomous Player"]
        ORACLE["Oracle"]
        ARCHITECT["Architect"]
        SENTINEL["Sentinel"]
        CHRONICLER["Chronicler"]
        BRIDGE["Surface Bridge"]
    end

    subgraph MEMORY["Memory Layer"]
        SQLITE["SQLite\nagent_memory.db"]
        PALACE["Memory Palace\nserena_memory.db"]
        MANIFEST["Agent Manifest\nstate/agent_manifest.json"]
    end

    subgraph LLM["LLM Layer"]
        REPLIT_AI["Replit AI Proxy\nmodelfarm/openai"]
        OLLAMA["Ollama\n:11434"]
        STUB["Stub/Fallback"]
    end

    subgraph EXTERNAL["External"]
        GITHUB["GitHub\nKiloMusician/Dev-Mentor"]
        AGNO["Agno Framework\n(future)"]
        N8N["n8n\n:5678 (future)"]
    end

    %% Core flow
    API --> GAME
    API --> SERENA
    API --> NUSYQ
    API --> SCHED

    %% Serena internals
    SERENA --> PALACE
    SERENA --> |"walk/index"| PALACE
    SERENA --> |"policy gate"| PALACE

    %% Game ↔ Memory
    GAME --> SQLITE
    SCHED --> SQLITE
    NUSYQ --> MANIFEST

    %% Agent → API
    GORDON --> |"REST /api/game/command"| API
    GORDON --> |"REST /api/serena/*"| SERENA
    ORACLE  --> API
    ARCHITECT --> API

    %% LLM routing
    API --> REPLIT_AI
    API --> OLLAMA
    API --> STUB

    %% External
    SCHED --> |"auto-git"| GITHUB
    NUSYQ --> |"mirror"| GITHUB

    %% Agno bridge
    SERENA --> |"toolkit manifest"| AGNO
```

---

## Serena ΨΞΦΩ Internal Architecture

```mermaid
graph LR
    subgraph PSI["Ψ — Walker (Signal Intake)"]
        WALKER["RepoWalker\nwalker.py"]
        FAST["fast_walk()\ngame scope 5.5s"]
        FULL["walk_full()\nentire repo ~30s"]
    end

    subgraph OMEGA["Ω — Memory Palace (Compression)"]
        DB["SQLite\ncode_chunks\nobservations\nrelationships"]
        PURGE["purge_stale()\nclean .pythonlibs etc"]
    end

    subgraph XI["Ξ — Ask / Find (Refinement)"]
        ASK["ask()\nfuzzy keyword search"]
        FIND["find()\nsymbol-level lookup"]
        EXPLAIN["explain()\nfile/function Φ-map"]
    end

    subgraph PHI["Φ — Relate / Sync"]
        RELATE["relate()\ncross-layer relationships"]
        DIFF["diff()\ngit-changed files"]
    end

    subgraph DRIFT["⟁ Drift Detection"]
        DETECTOR["DriftDetector\ndrift.py"]
        ALIGN["align_check()\nMladenc score"]
    end

    subgraph GATE["🔒 Consent Gate"]
        POLICY["ConsentGate\npolicy.yaml"]
        L0["L0 READ_ONLY"]
        L2["L2 AUTOMATIC"]
        L3["L3 CONFIRM"]
        L4["L4 DENY"]
    end

    WALKER --> OMEGA
    FAST --> WALKER
    FULL --> WALKER
    PURGE --> OMEGA

    OMEGA --> XI
    OMEGA --> PHI
    OMEGA --> DRIFT

    DETECTOR --> ALIGN
    PSI --> DRIFT

    POLICY --> L0
    POLICY --> L2
    POLICY --> L3
    POLICY --> L4
```

---

## Agent Communication Flow

```mermaid
sequenceDiagram
    participant H as Human/Browser
    participant API as FastAPI :5000
    participant GAME as Game Engine
    participant SERENA as Serena ΨΞΦΩ
    participant GORDON as Gordon Agent
    participant DB as Memory Palace

    H->>API: POST /api/game/command (serena drift)
    API->>GAME: dispatch_command("serena drift")
    GAME->>SERENA: serena.drift(fast=True)
    SERENA->>DB: detect_all() [SQLite read]
    DB-->>SERENA: drift signals
    SERENA-->>GAME: DriftSignal list
    GAME-->>API: formatted output lines
    API-->>H: [{t:"system", s:"⟁ Drift..."}]

    GORDON->>API: GET /api/serena/align
    API->>SERENA: serena.align()
    SERENA->>DB: align_check()
    DB-->>SERENA: check results
    SERENA-->>API: {score:1.0, aligned:true}
    API-->>GORDON: alignment briefing

    GORDON->>API: POST /api/game/command (serena walk)
    API->>GAME: dispatch_command("serena walk")
    GAME->>SERENA: serena.fast_walk()
    SERENA->>DB: index chunks
    DB-->>SERENA: stats
    SERENA-->>GAME: walk summary
    GAME-->>API: output
    API-->>GORDON: walk complete
```

---

## Data Flow: Colony → GitHub

```mermaid
flowchart LR
    A[Content Scheduler\nevery 60 min] -->|generate| B[Challenges\nLore\nStory Beats]
    B --> C[SQLite\nagent_memory.db]
    C --> D[git_auto_push.py]
    D -->|reads| E[.env.local or\nGITHUB_TOKEN]
    E --> F[GitHub\nKiloMusician/Dev-Mentor]
    F --> G[NuSyQ-Hub Mirror]

    H[NuSyQ Bridge] -->|manifest| I[state/agent_manifest.json]
    I --> F

    J[Serena\nMemory Palace] -->|observations| C
    J -->|drift signals| K[Observations Table]
```

---

## Trust Level Flow (L0-L4)

```mermaid
graph TD
    REQ["Action Request"] --> CHECK["ConsentGate.check(action)"]
    CHECK --> L0{"L0?"}
    L0 -->|yes| AUTO0["Auto-proceed\n(read-only)"]
    L0 -->|no| L2{"L1/L2?"}
    L2 -->|yes| AUTO2["Auto-proceed\nlog to Memory Palace"]
    L2 -->|no| L3{"L3?"}
    L3 -->|yes| CONFIRM["await human\napproval (60s)"]
    CONFIRM --> TIMEOUT{"timed out?"}
    TIMEOUT -->|yes| SUGGEST["downgrade to\nL1 suggestion"]
    TIMEOUT -->|no| APPROVED["proceed + log"]
    L3 -->|no| L4{"L4?"}
    L4 -->|yes| DENY["DENY — immutable\nregardless of trust"]
```

---

*Last updated: auto-generated by diagnostics.py. Run `make diagnose` to refresh.*

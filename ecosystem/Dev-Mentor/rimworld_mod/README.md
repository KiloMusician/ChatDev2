# TerminalKeeper Event Bridge

Minimal RimWorld mod skeleton that:

- depends on Harmony
- patches pawn death, incidents, caravan creation, and trade session startup
- publishes those events to a local HTTP bridge on port `9000`
- polls the bridge for queued commands

## Layout

```text
rimworld_mod/
├── About/About.xml
├── LoadFolders.xml
├── Config/BridgeSettings.xml
├── Assemblies/
├── Source/
│   ├── Bridge/
│   ├── Core/
│   └── Patches/
└── server/http_event_server.py
```

## Build

1. Open `Source/TerminalKeeper.EventBridge.csproj` in Visual Studio or Rider on Windows.
2. Set `RimWorldDir` if your RimWorld install is not at `C:\Program Files (x86)\Steam\steamapps\common\RimWorld`.
3. Build the project.
4. The DLL is copied into `rimworld_mod/Assemblies/`.

Direct smoke-build from this workspace also works with the installed Windows SDK:

```bash
'/mnt/c/Program Files/dotnet/dotnet.exe' build \
  'C:\Users\keath\Dev-Mentor\rimworld_mod\Source\TerminalKeeper.EventBridge.csproj' \
  -c Debug
```

## Install

1. Copy `rimworld_mod/` into a RimWorld local mods folder.
2. Enable `TerminalKeeper Event Bridge` in the RimWorld mod list.
3. Ensure Harmony is enabled above it.

## Server

Start the local bridge:

```bash
python rimworld_mod/server/http_event_server.py
```

Default bind is `127.0.0.1:9000`. For local validation on a different port:

```bash
TK_EVENT_BRIDGE_PORT=9001 python rimworld_mod/server/http_event_server.py
```

Endpoints:

- `GET /health`
- `POST /api/events`
- `GET /api/events`
- `POST /api/commands`
- `GET /api/commands/next`

Example command enqueue:

```bash
curl -X POST http://127.0.0.1:9000/api/commands \
  -H 'Content-Type: application/json' \
  -d '{"command":"ping"}'
```

## Config

Edit `Config/BridgeSettings.xml`:

- `ServerBaseUrl`
- `EventFlushIntervalTicks`
- `CommandPollIntervalTicks`
- `EnableBootstrapEvent`

## Notes

- The included ChatDev stub was invoked for patch/server generation, but it only emitted task envelopes in this repo state, so the scaffold code was completed manually.
- The patch targets are intentionally conservative and string-reflection based to reduce signature drift against the active mod stack.

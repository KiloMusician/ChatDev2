This folder contains lightweight deployment/dev scaffolding.

deploy/docker-compose.yml

- Minimal development docker-compose for `NuSyQ-Hub`.
- Builds the repository root Dockerfile and mounts the repo for
  edit-in-container workflows.

How to use (PowerShell):

```powershell
# from repo root
docker compose -f deploy/docker-compose.yml up --build
```

Notes:

- This compose file is intentionally small and designed as a starting point. Add
  services (DBs, caches, local model services) under `services:` as needed.
- If you prefer the old `docker-compose` binary:

```powershell
docker-compose -f deploy/docker-compose.yml up --build
```

## Optional full dev stack

An opt-in, fuller development stack is available at
`deploy/docker-compose.dev.yml` and is designed to be safe by default (minimal)
and enable optional services via the `full` profile.

Examples (PowerShell):

```powershell
# Minimal (app container only)
docker compose -f deploy/docker-compose.dev.yml up --build

# Full stack (app + Postgres + Redis + Ollama-mock)
docker compose -f deploy/docker-compose.dev.yml --profile full up --build

# Helper script (convenience)
.\scripts\dev_up.ps1 -Profile full -Build
```

The file `deploy/.env.example` shows common environment variables you may want
to copy to `deploy/.env` and tweak locally. Do NOT commit your `.env` with
secrets.

## Helper scripts

Two helper scripts are included under `scripts/`:

- `scripts/dev_up.ps1` - convenience wrapper to bring up the minimal or full dev
  stack.
- `scripts/dev_stop.ps1` - convenience wrapper to stop the stack and optionally
  prune volumes/images.

- `scripts/dev_prune.ps1` - safer prune helper that only removes named dev
  volumes used by the stack (`nusyq_pgdata`, `nusyq_redisdata`).

## Database migrations

An optional one-shot migration runner is provided as the `db_migrate` service in
the `full` profile (`deploy/docker-compose.dev.yml`). It runs
`./scripts/db_migrate.sh` inside the `nusyq-hub:dev` image. The script will
attempt to run `alembic upgrade head` if an Alembic configuration or migrations
are present. If you use a different migration tool, adapt
`scripts/db_migrate.sh` accordingly.

## Mediator end-to-end test

There is a convenience PowerShell script `scripts/mediator_e2e.ps1` which will:

- Start the mediator via `scripts/start_powershell_mediator.ps1` (it assumes a
  Windows pwsh environment)
- Wait for the mediator control port file
  (`.vscode/mediator/mediator.http.port`)
- GET `/status`, POST `/stop-child`, and verify `child.pid` / `mediator.pid`
  removal

Run it from the repository root:

```powershell
.
# from repo root
.\scripts\mediator_e2e.ps1
```

The script is intended as a best-effort smoke test for the mediator control path
and should be run in a local development environment where starting background
processes is supported.

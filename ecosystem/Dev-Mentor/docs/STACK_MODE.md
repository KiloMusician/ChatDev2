# Stack Mode (Backend + Middleware + Frontend + CLI)

DevMentor’s **primary** runtime is VS Code tasks + tutorials.

Stack Mode is an **additional core component** for environments like Replit:
- Backend: FastAPI (local)
- Middleware: event bus + tool registry (local)
- Frontend: static UI served by backend
- CLI: Typer (`python -m cli.devmentor ...`)

## Design rules
- No mandatory cloud services.
- All state is file-based and portable.
- UI is an optional accelerator and “teaching instrument”.
- Deterministic tools first; AI is optional.

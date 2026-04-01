Docker build & run notes for NuSyQ

Build image (from repository root):

```bash
docker build -t nusyq-root:local .
```

Run (example):

```bash
docker run --rm -p 8765:8765 \
  -v /path/to/models:/app/models \
  -e SOME_SECRET_VAR=REPLACE nusyq-root:local
```

Notes:
- Do NOT include local virtual environments or model binaries in the build context; use `.dockerignore` (already configured).
- Mount large model directories as volumes instead of baking into the image.
- Set secrets via environment variables or Docker secrets in production.

ChatDev Docker notes

Build and run locally (avoid including model binaries or venvs):

```bash
cd ChatDev
docker build -t chatdev:local .

# Run interactively and mount models at runtime
docker run --rm -it -p 8000:8000 \
  -v /path/to/models:/app/WareHouse \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  chatdev:local
```

Guidelines:
- `.dockerignore` excludes `WareHouse/`, model binaries and venvs. Do not copy models into the image.
- Do not set secrets via `ENV` in the Dockerfile; provide them at runtime.

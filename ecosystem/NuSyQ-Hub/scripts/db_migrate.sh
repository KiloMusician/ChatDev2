#!/usr/bin/env sh
set -e

echo "Running db_migrate helper (one-shot)."

# Wait for Postgres to be reachable
POSTGRES_HOST=${POSTGRES_HOST:-postgres}
POSTGRES_PORT=${POSTGRES_PORT:-5432}
MAX_WAIT=30
WAITED=0

echo "Waiting for Postgres at ${POSTGRES_HOST}:${POSTGRES_PORT}"
python - <<'PY'
import socket, os, time
host = os.environ.get('POSTGRES_HOST', 'postgres')
port = int(os.environ.get('POSTGRES_PORT', '5432'))
max_wait = 30
waited = 0
while waited < max_wait:
    s = socket.socket()
    s.settimeout(1.0)
    try:
        s.connect((host, port))
        s.close()
        print('Postgres is reachable')
        break
    except Exception:
        time.sleep(1)
        waited += 1
else:
    print('Timed out waiting for Postgres')
    raise SystemExit(1)
PY

if [ -d "migrations" ] || [ -f "alembic.ini" ]; then
  echo "Detected migrations; ensuring alembic is installed and running migrations."
  if ! command -v alembic >/dev/null 2>&1; then
    echo "alembic not found; installing into container (pip)."
    pip install --no-cache-dir alembic
  fi
  echo "Running: alembic upgrade head"
  alembic upgrade head || echo "alembic finished with non-zero exit"
else
  echo "No migrations found in repository. If you have application-level migrations, add them to 'migrations/' or provide an alembic.ini."
fi

echo "db_migrate completed."
#!/usr/bin/env sh
set -e

echo "Running db_migrate helper (one-shot)."
# Simple helper: wait a bit for postgres to accept connections (best-effort)
sleep 3

if [ -d "migrations" ] || [ -f "alembic.ini" ]; then
  echo "Detected migrations directory or alembic.ini; attempting to run 'alembic upgrade head'."
  if command -v alembic >/dev/null 2>&1; then
    alembic upgrade head
  else
    echo "alembic not installed in image. To run migrations, install alembic or run migrations locally."
  fi
else
  echo "No migrations found in repository. If you have application-level migrations, add them to 'migrations/' or provide an alembic.ini."
fi

echo "db_migrate completed."

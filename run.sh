#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required but was not found."
  exit 1
fi

if [ -d ".venv" ] && { [ ! -x ".venv/bin/python" ] || [ ! -x ".venv/bin/pip" ]; }; then
  echo "Removing incomplete .venv directory."
  rm -rf .venv
fi

if [ ! -d ".venv" ]; then
  if ! python3 -m venv .venv; then
    rm -rf .venv
    echo
    echo "Failed to create a Python virtual environment."
    echo "On Ubuntu/WSL, install the venv package first:"
    echo
    echo "  sudo apt update"
    echo "  sudo apt install -y python3.10-venv"
    echo
    echo "Then run ./run.sh again."
    exit 1
  fi
fi

source .venv/bin/activate

INSTALL_STAMP=".venv/.auto_blog_installed"
if [ ! -f "$INSTALL_STAMP" ] || [ "pyproject.toml" -nt "$INSTALL_STAMP" ]; then
  python -m pip install -U pip
  python -m pip install -e .
  touch "$INSTALL_STAMP"
fi

if [ ! -f ".env" ] && [ -f ".env.example" ]; then
  cp .env.example .env
  echo "Created .env from .env.example. Check credentials before generating content."
fi

export AUTO_BLOG_HOST="${AUTO_BLOG_HOST:-127.0.0.1}"
if [ -z "${AUTO_BLOG_PORT:-}" ]; then
  AUTO_BLOG_PORT="$(python - "$AUTO_BLOG_HOST" <<'PY'
import socket
import sys

host = sys.argv[1]
for port in range(8000, 8100):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind((host, port))
        except OSError:
            continue
        print(port)
        break
else:
    raise SystemExit("No available port found between 8000 and 8099.")
PY
)"
  export AUTO_BLOG_PORT
fi

echo "Starting auto_blog web UI at http://${AUTO_BLOG_HOST}:${AUTO_BLOG_PORT}"
exec autoblog-web "$@"

#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

if ! command -v node >/dev/null 2>&1; then
  echo "Node.js is required. Install Node.js 20+ first."
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "npm is required. Install npm first."
  exit 1
fi

npm install

if [[ ! -f ".env" ]]; then
  cp .env.example .env
  echo "Created .env from .env.example. Fill TELEGRAM_BOT_TOKEN before starting the bot."
fi

mkdir -p data/users storage
chmod 700 data/users storage || true

echo "Install complete."

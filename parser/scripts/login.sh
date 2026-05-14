#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

PID_FILE="${ROOT_DIR}/storage/obscura.pid"
PORT="${OBSCURA_PORT:-9222}"
if (echo >"/dev/tcp/127.0.0.1/${PORT}") >/dev/null 2>&1; then
  :
elif [[ ! -f "${PID_FILE}" ]] || ! kill -0 "$(cat "${PID_FILE}" 2>/dev/null)" >/dev/null 2>&1; then
  rm -f "${PID_FILE}"
  bash "${ROOT_DIR}/scripts/start-obscura.sh"
fi

node src/login.mjs

#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_ROOT="$(cd "${ROOT_DIR}/.." && pwd)"
OBSCURA_BIN="${PROJECT_ROOT}/obscura"
PID_FILE="${ROOT_DIR}/storage/obscura.pid"

if [[ ! -x "${OBSCURA_BIN}" ]]; then
  echo "obscura binary not found: ${OBSCURA_BIN}"
  exit 1
fi

mkdir -p "${ROOT_DIR}/storage" "${ROOT_DIR}/data"

if [[ -f "${PID_FILE}" ]]; then
  EXISTING_PID="$(cat "${PID_FILE}")"
  if kill -0 "${EXISTING_PID}" >/dev/null 2>&1; then
    echo "obscura already running with PID ${EXISTING_PID}"
    exit 0
  fi
  rm -f "${PID_FILE}"
fi

PORT="${OBSCURA_PORT:-9222}"
STEALTH_FLAG=""
if [[ "${OBSCURA_STEALTH:-false}" == "true" ]]; then
  STEALTH_FLAG="--stealth"
fi

"${OBSCURA_BIN}" serve --port "${PORT}" ${STEALTH_FLAG} >/tmp/obscura-e-klase.log 2>&1 &
echo $! > "${PID_FILE}"

for _ in $(seq 1 20); do
  if ! kill -0 "$(cat "${PID_FILE}")" >/dev/null 2>&1; then
    echo "obscura failed to start. Log:"
    tail -n 80 /tmp/obscura-e-klase.log || true
    rm -f "${PID_FILE}"
    exit 1
  fi

  if (echo >"/dev/tcp/127.0.0.1/${PORT}") >/dev/null 2>&1; then
    echo "obscura started on port ${PORT}, PID $(cat "${PID_FILE}")"
    exit 0
  fi

  sleep 0.5
done

echo "obscura did not become ready on port ${PORT}. Log:"
tail -n 80 /tmp/obscura-e-klase.log || true
exit 1

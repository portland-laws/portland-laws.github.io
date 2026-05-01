#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PID_FILE="$ROOT/ppd/daemon/ppd-daemon.pid"
OUT_FILE="$ROOT/ppd/daemon/ppd-daemon.out"
STATUS_FILE="$ROOT/ppd/daemon/status.json"

start() {
  if [[ -f "$PID_FILE" ]]; then
    local old_pid
    old_pid="$(cat "$PID_FILE" 2>/dev/null || true)"
    if [[ -n "$old_pid" ]] && ps -p "$old_pid" >/dev/null 2>&1; then
      echo "PP&D daemon already running: $old_pid"
      return 0
    fi
  fi

  setsid -f bash -c "cd '$ROOT' && PYTHONPATH=ipfs_datasets_py IPFS_DATASETS_PY_CODEX_SANDBOX=read-only exec python3 ppd/daemon/ppd_daemon.py --apply --watch --iterations 0 --interval 60 --llm-timeout 300 --provider codex_cli > '$OUT_FILE' 2>&1"
  sleep 1
  local pid
  pid="$(pgrep -f "python3 ppd/daemon/ppd_daemon.py --apply --watch" | tail -n 1 || true)"
  if [[ -z "$pid" ]]; then
    echo "PP&D daemon did not start; see $OUT_FILE" >&2
    return 1
  fi
  echo "$pid" > "$PID_FILE"
  echo "PP&D daemon started: $pid"
}

stop() {
  if [[ ! -f "$PID_FILE" ]]; then
    echo "No PID file at $PID_FILE"
    return 0
  fi
  local pid
  pid="$(cat "$PID_FILE")"
  if ps -p "$pid" >/dev/null 2>&1; then
    kill "$pid"
    echo "PP&D daemon stopped: $pid"
  else
    echo "PP&D daemon not running: $pid"
  fi
}

status() {
  if [[ -f "$PID_FILE" ]]; then
    local pid
    pid="$(cat "$PID_FILE")"
    ps -p "$pid" -o pid,ppid,sid,etime,cmd || true
  fi
  if [[ -f "$STATUS_FILE" ]]; then
    cat "$STATUS_FILE"
  fi
}

case "${1:-status}" in
  start) start ;;
  stop) stop ;;
  restart) stop; start ;;
  status) status ;;
  logs) tail -f "$OUT_FILE" ;;
  *)
    echo "Usage: $0 {start|stop|restart|status|logs}" >&2
    exit 2
    ;;
esac

#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PID_FILE="$ROOT/ppd/daemon/ppd-daemon.pid"
OUT_FILE="$ROOT/ppd/daemon/ppd-daemon.out"
STATUS_FILE="$ROOT/ppd/daemon/status.json"
SUPERVISOR_PID_FILE="$ROOT/ppd/daemon/ppd-supervisor.pid"
SUPERVISOR_OUT_FILE="$ROOT/ppd/daemon/ppd-supervisor.out"
SUPERVISOR_STATUS_FILE="$ROOT/ppd/daemon/supervisor-status.json"

start() {
  if [[ -f "$PID_FILE" ]]; then
    local old_pid
    old_pid="$(cat "$PID_FILE" 2>/dev/null || true)"
    if [[ -n "$old_pid" ]] && ps -p "$old_pid" >/dev/null 2>&1; then
      echo "PP&D daemon already running: $old_pid"
      return 0
    fi
  fi

  local existing_pid
  existing_pid="$(pgrep -f "python3 ppd/daemon/ppd_daemon.py --apply --watch" | tail -n 1 || true)"
  if [[ -n "$existing_pid" ]]; then
    echo "$existing_pid" > "$PID_FILE"
    echo "PP&D daemon already running: $existing_pid"
    return 0
  fi

  setsid -f bash -c "cd '$ROOT' && PYTHONPATH=ipfs_datasets_py IPFS_DATASETS_PY_CODEX_SANDBOX=read-only exec python3 ppd/daemon/ppd_daemon.py --apply --watch --iterations 0 --interval 0 --llm-timeout 300 --provider codex_cli --revisit-blocked > '$OUT_FILE' 2>&1"
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

supervisor_start() {
  if [[ -f "$SUPERVISOR_PID_FILE" ]]; then
    local old_pid
    old_pid="$(cat "$SUPERVISOR_PID_FILE" 2>/dev/null || true)"
    if [[ -n "$old_pid" ]] && ps -p "$old_pid" >/dev/null 2>&1; then
      echo "PP&D supervisor already running: $old_pid"
      return 0
    fi
  fi

  setsid -f bash -c "cd '$ROOT' && PYTHONPATH=ipfs_datasets_py IPFS_DATASETS_PY_CODEX_SANDBOX=read-only exec python3 ppd/daemon/ppd_supervisor.py --watch --interval 120 --apply --self-heal --restart-daemon --llm-timeout 300 --provider codex_cli > '$SUPERVISOR_OUT_FILE' 2>&1"
  sleep 1
  local pid
  pid="$(pgrep -f "python3 ppd/daemon/ppd_supervisor.py --watch" | tail -n 1 || true)"
  if [[ -z "$pid" ]]; then
    echo "PP&D supervisor did not start; see $SUPERVISOR_OUT_FILE" >&2
    return 1
  fi
  echo "$pid" > "$SUPERVISOR_PID_FILE"
  echo "PP&D supervisor started: $pid"
}

supervisor_stop() {
  if [[ ! -f "$SUPERVISOR_PID_FILE" ]]; then
    echo "No supervisor PID file at $SUPERVISOR_PID_FILE"
    return 0
  fi
  local pid
  pid="$(cat "$SUPERVISOR_PID_FILE")"
  if ps -p "$pid" >/dev/null 2>&1; then
    kill "$pid"
    echo "PP&D supervisor stopped: $pid"
  else
    echo "PP&D supervisor not running: $pid"
  fi
}

supervisor_status() {
  if [[ -f "$SUPERVISOR_PID_FILE" ]]; then
    local pid
    pid="$(cat "$SUPERVISOR_PID_FILE")"
    ps -p "$pid" -o pid,ppid,sid,etime,cmd || true
  fi
  if [[ -f "$SUPERVISOR_STATUS_FILE" ]]; then
    cat "$SUPERVISOR_STATUS_FILE"
  fi
}

case "${1:-status}" in
  start) start ;;
  stop) stop ;;
  restart) stop; start ;;
  status) status ;;
  logs) tail -f "$OUT_FILE" ;;
  doctor) python3 "$ROOT/ppd/daemon/ppd_supervisor.py" --once --apply --self-heal --restart-daemon --llm-timeout 300 --provider codex_cli ;;
  supervisor-start) supervisor_start ;;
  supervisor-stop) supervisor_stop ;;
  supervisor-restart) supervisor_stop; supervisor_start ;;
  supervisor-status) supervisor_status ;;
  supervisor-logs) tail -f "$SUPERVISOR_OUT_FILE" ;;
  *)
    echo "Usage: $0 {start|stop|restart|status|logs|doctor|supervisor-start|supervisor-stop|supervisor-restart|supervisor-status|supervisor-logs}" >&2
    exit 2
    ;;
esac

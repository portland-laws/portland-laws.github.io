#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PID_FILE="$ROOT/ppd/daemon/ppd-daemon.pid"
CHILD_PID_FILE="$ROOT/ppd/daemon/ppd-daemon.child.pid"
OUT_FILE="$ROOT/ppd/daemon/ppd-daemon.out"
STATUS_FILE="$ROOT/ppd/daemon/status.json"
LIFECYCLE_LOG="$ROOT/ppd/daemon/ppd-daemon-lifecycle.jsonl"
SUPERVISOR_PID_FILE="$ROOT/ppd/daemon/ppd-supervisor.pid"
SUPERVISOR_CHILD_PID_FILE="$ROOT/ppd/daemon/ppd-supervisor.child.pid"
SUPERVISOR_OUT_FILE="$ROOT/ppd/daemon/ppd-supervisor.out"
SUPERVISOR_STATUS_FILE="$ROOT/ppd/daemon/supervisor-status.json"
SUPERVISOR_LIFECYCLE_LOG="$ROOT/ppd/daemon/ppd-supervisor-lifecycle.jsonl"
WATCHDOG_SCRIPT="$ROOT/ppd/daemon/watchdog.sh"
DAEMON_UNIT="ppd-daemon.service"
SUPERVISOR_UNIT="ppd-supervisor.service"

systemd_available() {
  command -v systemd-run >/dev/null 2>&1 && systemctl --user is-system-running >/dev/null 2>&1
}

systemd_unit_active() {
  local unit="$1"
  systemctl --user is-active --quiet "$unit" >/dev/null 2>&1
}

stop_systemd_unit() {
  local unit="$1"
  if systemd_available; then
    systemctl --user stop "$unit" >/dev/null 2>&1 || true
    systemctl --user reset-failed "$unit" >/dev/null 2>&1 || true
  fi
}

collect_descendant_pids() {
  local parent="$1"
  local child
  while IFS= read -r child; do
    [[ -z "$child" ]] && continue
    echo "$child"
    collect_descendant_pids "$child"
  done < <(pgrep -P "$parent" 2>/dev/null || true)
}

process_group_for_pid() {
  local pid="$1"
  ps -o pgid= -p "$pid" 2>/dev/null | tr -d '[:space:]'
}

terminate_process_family() {
  local root_pid="$1"
  local label="$2"
  local -a family_pids=()
  local -a process_groups=()
  local pid
  local pgid

  if [[ -z "$root_pid" ]] || ! ps -p "$root_pid" >/dev/null 2>&1; then
    echo "$label not running: ${root_pid:-unknown}"
    return 0
  fi

  mapfile -t family_pids < <(
    {
      echo "$root_pid"
      collect_descendant_pids "$root_pid"
    } | awk 'NF && !seen[$0]++'
  )

  for pid in "${family_pids[@]}"; do
    pgid="$(process_group_for_pid "$pid")"
    [[ -n "$pgid" ]] && process_groups+=("$pgid")
  done
  mapfile -t process_groups < <(printf '%s\n' "${process_groups[@]}" | awk 'NF && !seen[$0]++')

  for pgid in "${process_groups[@]}"; do
    kill -TERM -- "-$pgid" 2>/dev/null || true
  done
  sleep 2
  for pgid in "${process_groups[@]}"; do
    kill -KILL -- "-$pgid" 2>/dev/null || true
  done

  echo "$label stopped: $root_pid"
}

sweep_orphaned_ppd_llm_children() {
  local pid
  local ppid
  while read -r pid ppid; do
    [[ -z "$pid" ]] && continue
    if [[ "$ppid" == "1" ]]; then
      terminate_process_family "$pid" "Orphaned PP&D LLM child"
    fi
  done < <(
    ps -eo pid=,ppid=,args= |
      awk '/python3 -c/ && /PPD_LLM_PROMPT_FILE/ && /ipfs_datasets_py/ {print $1, $2}'
  )
}

start() {
  sweep_orphaned_ppd_llm_children

  if [[ -f "$PID_FILE" ]]; then
    local old_pid
    old_pid="$(cat "$PID_FILE" 2>/dev/null || true)"
    if [[ -n "$old_pid" ]] && ps -p "$old_pid" >/dev/null 2>&1; then
      echo "PP&D daemon watchdog already running: $old_pid"
      return 0
    fi
    rm -f "$PID_FILE" "$CHILD_PID_FILE" "$PID_FILE.stop"
  fi

  local existing_pid
  existing_pid="$(pgrep -f "^python3 ppd/daemon/ppd_daemon.py --apply --watch" | tail -n 1 || true)"
  if [[ -n "$existing_pid" ]]; then
    echo "Stopping unwatched PP&D daemon before watchdog start: $existing_pid"
    terminate_process_family "$existing_pid" "Unwatched PP&D daemon"
  fi

  if systemd_available; then
    stop_systemd_unit "$DAEMON_UNIT"
    systemd-run --user --unit="$DAEMON_UNIT" --collect --property=Restart=always --property=RestartSec=5 --working-directory="$ROOT" \
      bash -lc "exec bash '$WATCHDOG_SCRIPT' daemon '$PID_FILE' '$CHILD_PID_FILE' '$LIFECYCLE_LOG' 5 env PYTHONPATH=ipfs_datasets_py PPD_LLM_BACKEND=llm_router IPFS_DATASETS_PY_CODEX_SANDBOX=read-only python3 ppd/daemon/ppd_daemon.py --apply --watch --iterations 0 --interval 0 --llm-timeout 300 --crash-backoff 5 --revisit-blocked --repair-validation-failures >> '$OUT_FILE' 2>&1" >/dev/null
  else
    setsid -f bash -c "cd '$ROOT' && exec bash '$WATCHDOG_SCRIPT' daemon '$PID_FILE' '$CHILD_PID_FILE' '$LIFECYCLE_LOG' 5 env PYTHONPATH=ipfs_datasets_py PPD_LLM_BACKEND=llm_router IPFS_DATASETS_PY_CODEX_SANDBOX=read-only python3 ppd/daemon/ppd_daemon.py --apply --watch --iterations 0 --interval 0 --llm-timeout 300 --crash-backoff 5 --revisit-blocked --repair-validation-failures >> '$OUT_FILE' 2>&1"
  fi
  sleep 1
  local pid
  pid="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [[ -z "$pid" ]] || ! ps -p "$pid" >/dev/null 2>&1; then
    echo "PP&D daemon did not start; see $OUT_FILE" >&2
    return 1
  fi
  echo "PP&D daemon watchdog started: $pid"
  if [[ -f "$CHILD_PID_FILE" ]]; then
    echo "PP&D daemon child started: $(cat "$CHILD_PID_FILE")"
  fi
}

stop() {
  if [[ ! -f "$PID_FILE" ]]; then
    if [[ -f "$CHILD_PID_FILE" ]]; then
      local child_pid
      child_pid="$(cat "$CHILD_PID_FILE" 2>/dev/null || true)"
      [[ -n "$child_pid" ]] && terminate_process_family "$child_pid" "PP&D daemon child"
      rm -f "$CHILD_PID_FILE" "$PID_FILE.stop"
    fi
    sweep_orphaned_ppd_llm_children
    echo "No PID file at $PID_FILE"
    return 0
  fi
  local pid
  pid="$(cat "$PID_FILE")"
  touch "$PID_FILE.stop"
  stop_systemd_unit "$DAEMON_UNIT"
  terminate_process_family "$pid" "PP&D daemon"
  if [[ -f "$CHILD_PID_FILE" ]]; then
    local child_pid
    child_pid="$(cat "$CHILD_PID_FILE" 2>/dev/null || true)"
    [[ -n "$child_pid" ]] && terminate_process_family "$child_pid" "PP&D daemon child"
  fi
  sweep_orphaned_ppd_llm_children
  rm -f "$PID_FILE" "$CHILD_PID_FILE" "$PID_FILE.stop"
}

status() {
  if [[ -f "$PID_FILE" ]]; then
    local pid
    pid="$(cat "$PID_FILE")"
    echo "watchdog:"
    ps -p "$pid" -o pid,ppid,sid,etime,cmd || true
  fi
  if systemd_available && systemd_unit_active "$DAEMON_UNIT"; then
    echo "systemd:"
    systemctl --user --no-pager --plain status "$DAEMON_UNIT" | sed -n '1,8p' || true
  fi
  if [[ -f "$CHILD_PID_FILE" ]]; then
    local child_pid
    child_pid="$(cat "$CHILD_PID_FILE")"
    echo "child:"
    ps -p "$child_pid" -o pid,ppid,sid,etime,cmd || true
  fi
  if [[ -f "$STATUS_FILE" ]]; then
    cat "$STATUS_FILE"
  fi
  if [[ -f "$LIFECYCLE_LOG" ]]; then
    echo
    echo "recent lifecycle:"
    tail -n 5 "$LIFECYCLE_LOG"
  fi
}

supervisor_start() {
  if [[ -f "$SUPERVISOR_PID_FILE" ]]; then
    local old_pid
    old_pid="$(cat "$SUPERVISOR_PID_FILE" 2>/dev/null || true)"
    if [[ -n "$old_pid" ]] && ps -p "$old_pid" >/dev/null 2>&1; then
      echo "PP&D supervisor watchdog already running: $old_pid"
      return 0
    fi
    rm -f "$SUPERVISOR_PID_FILE" "$SUPERVISOR_CHILD_PID_FILE" "$SUPERVISOR_PID_FILE.stop"
  fi

  local existing_pid
  existing_pid="$(pgrep -f "python3 ppd/daemon/ppd_supervisor.py --watch" | tail -n 1 || true)"
  if [[ -n "$existing_pid" ]]; then
    echo "Stopping unwatched PP&D supervisor before watchdog start: $existing_pid"
    terminate_process_family "$existing_pid" "Unwatched PP&D supervisor"
  fi

  if systemd_available; then
    stop_systemd_unit "$SUPERVISOR_UNIT"
    systemd-run --user --unit="$SUPERVISOR_UNIT" --collect --property=Restart=always --property=RestartSec=5 --working-directory="$ROOT" \
      bash -lc "exec bash '$WATCHDOG_SCRIPT' supervisor '$SUPERVISOR_PID_FILE' '$SUPERVISOR_CHILD_PID_FILE' '$SUPERVISOR_LIFECYCLE_LOG' 5 env PYTHONPATH=ipfs_datasets_py PPD_LLM_BACKEND=llm_router IPFS_DATASETS_PY_CODEX_SANDBOX=read-only python3 ppd/daemon/ppd_supervisor.py --watch --interval 120 --exception-backoff 5 --apply --self-heal --restart-daemon --llm-timeout 300 >> '$SUPERVISOR_OUT_FILE' 2>&1" >/dev/null
  else
    setsid -f bash -c "cd '$ROOT' && exec bash '$WATCHDOG_SCRIPT' supervisor '$SUPERVISOR_PID_FILE' '$SUPERVISOR_CHILD_PID_FILE' '$SUPERVISOR_LIFECYCLE_LOG' 5 env PYTHONPATH=ipfs_datasets_py PPD_LLM_BACKEND=llm_router IPFS_DATASETS_PY_CODEX_SANDBOX=read-only python3 ppd/daemon/ppd_supervisor.py --watch --interval 120 --exception-backoff 5 --apply --self-heal --restart-daemon --llm-timeout 300 >> '$SUPERVISOR_OUT_FILE' 2>&1"
  fi
  sleep 1
  local pid
  pid="$(cat "$SUPERVISOR_PID_FILE" 2>/dev/null || true)"
  if [[ -z "$pid" ]] || ! ps -p "$pid" >/dev/null 2>&1; then
    echo "PP&D supervisor did not start; see $SUPERVISOR_OUT_FILE" >&2
    return 1
  fi
  echo "PP&D supervisor watchdog started: $pid"
  if [[ -f "$SUPERVISOR_CHILD_PID_FILE" ]]; then
    echo "PP&D supervisor child started: $(cat "$SUPERVISOR_CHILD_PID_FILE")"
  fi
}

supervisor_stop() {
  if [[ ! -f "$SUPERVISOR_PID_FILE" ]]; then
    if [[ -f "$SUPERVISOR_CHILD_PID_FILE" ]]; then
      local child_pid
      child_pid="$(cat "$SUPERVISOR_CHILD_PID_FILE" 2>/dev/null || true)"
      [[ -n "$child_pid" ]] && terminate_process_family "$child_pid" "PP&D supervisor child"
      rm -f "$SUPERVISOR_CHILD_PID_FILE" "$SUPERVISOR_PID_FILE.stop"
    fi
    echo "No supervisor PID file at $SUPERVISOR_PID_FILE"
    return 0
  fi
  local pid
  pid="$(cat "$SUPERVISOR_PID_FILE")"
  touch "$SUPERVISOR_PID_FILE.stop"
  stop_systemd_unit "$SUPERVISOR_UNIT"
  terminate_process_family "$pid" "PP&D supervisor"
  if [[ -f "$SUPERVISOR_CHILD_PID_FILE" ]]; then
    local child_pid
    child_pid="$(cat "$SUPERVISOR_CHILD_PID_FILE" 2>/dev/null || true)"
    [[ -n "$child_pid" ]] && terminate_process_family "$child_pid" "PP&D supervisor child"
  fi
  rm -f "$SUPERVISOR_PID_FILE" "$SUPERVISOR_CHILD_PID_FILE" "$SUPERVISOR_PID_FILE.stop"
}

supervisor_status() {
  if [[ -f "$SUPERVISOR_PID_FILE" ]]; then
    local pid
    pid="$(cat "$SUPERVISOR_PID_FILE")"
    echo "watchdog:"
    ps -p "$pid" -o pid,ppid,sid,etime,cmd || true
  fi
  if systemd_available && systemd_unit_active "$SUPERVISOR_UNIT"; then
    echo "systemd:"
    systemctl --user --no-pager --plain status "$SUPERVISOR_UNIT" | sed -n '1,8p' || true
  fi
  if [[ -f "$SUPERVISOR_CHILD_PID_FILE" ]]; then
    local child_pid
    child_pid="$(cat "$SUPERVISOR_CHILD_PID_FILE")"
    echo "child:"
    ps -p "$child_pid" -o pid,ppid,sid,etime,cmd || true
  fi
  if [[ -f "$SUPERVISOR_STATUS_FILE" ]]; then
    cat "$SUPERVISOR_STATUS_FILE"
  fi
  if [[ -f "$SUPERVISOR_LIFECYCLE_LOG" ]]; then
    echo
    echo "recent lifecycle:"
    tail -n 5 "$SUPERVISOR_LIFECYCLE_LOG"
  fi
}

case "${1:-status}" in
  start) start ;;
  stop) stop ;;
  restart) stop; start ;;
  status) status ;;
  logs) tail -f "$OUT_FILE" ;;
  doctor) python3 "$ROOT/ppd/daemon/ppd_supervisor.py" --once --apply --self-heal --restart-daemon --llm-timeout 300 ;;
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

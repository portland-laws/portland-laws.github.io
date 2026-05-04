#!/usr/bin/env bash
set -euo pipefail

if [[ "$#" -lt 6 ]]; then
  echo "Usage: $0 ROLE PID_FILE CHILD_PID_FILE LIFECYCLE_LOG RESTART_DELAY COMMAND..." >&2
  exit 2
fi

ROLE="$1"
PID_FILE="$2"
CHILD_PID_FILE="$3"
LIFECYCLE_LOG="$4"
RESTART_DELAY="$5"
STOP_FILE="${PID_FILE}.stop"
shift 5

mkdir -p "$(dirname "$PID_FILE")" "$(dirname "$CHILD_PID_FILE")" "$(dirname "$LIFECYCLE_LOG")"

child_pid=""

utc_now() {
  date -u '+%Y-%m-%dT%H:%M:%SZ'
}

json_escape() {
  local text="${1:-}"
  text="${text//\\/\\\\}"
  text="${text//\"/\\\"}"
  text="${text//$'\n'/ }"
  text="${text//$'\r'/ }"
  printf '%s' "$text"
}

append_event() {
  local event="$1"
  local started_at="${2:-}"
  local ended_at="${3:-}"
  local pid="${4:-0}"
  local exit_code="${5:-0}"
  local signal_number="${6:-}"
  local message="${7:-}"
  {
    printf '{"event":"%s","role":"%s","updated_at":"%s"' \
      "$(json_escape "$event")" "$(json_escape "$ROLE")" "$(utc_now)"
    [[ -n "$started_at" ]] && printf ',"started_at":"%s"' "$(json_escape "$started_at")"
    [[ -n "$ended_at" ]] && printf ',"ended_at":"%s"' "$(json_escape "$ended_at")"
    [[ "$pid" =~ ^[0-9]+$ ]] && printf ',"pid":%s' "$pid"
    [[ "$exit_code" =~ ^[0-9]+$ ]] && printf ',"exit_code":%s' "$exit_code"
    [[ -n "$signal_number" && "$signal_number" =~ ^[0-9]+$ ]] && printf ',"signal":%s' "$signal_number"
    [[ -n "$message" ]] && printf ',"message":"%s"' "$(json_escape "$message")"
    printf '}\n'
  } >> "$LIFECYCLE_LOG"
}

terminate_child() {
  local pid="${child_pid:-}"
  [[ -z "$pid" ]] && return 0
  if ! kill -0 "$pid" 2>/dev/null; then
    return 0
  fi
  kill -TERM "$pid" 2>/dev/null || true
  for _ in 1 2 3 4 5; do
    if ! kill -0 "$pid" 2>/dev/null; then
      break
    fi
    sleep 1
  done
  kill -KILL "$pid" 2>/dev/null || true
  wait "$pid" 2>/dev/null || true
}

cleanup() {
  append_event "watchdog_stop" "" "" "${child_pid:-0}" 0 "" "watchdog received termination signal"
  terminate_child
  rm -f "$PID_FILE" "$CHILD_PID_FILE" "$STOP_FILE"
  exit 0
}

handle_signal() {
  local signal_name="$1"
  if [[ -f "$STOP_FILE" ]]; then
    cleanup
  fi
  append_event "watchdog_signal_ignored" "" "" "${child_pid:-0}" 0 "" "ignored ${signal_name}; stop sentinel was absent"
}

trap 'handle_signal TERM' TERM
trap 'handle_signal INT' INT
trap 'handle_signal HUP' HUP

rm -f "$STOP_FILE"
echo "$$" > "$PID_FILE"
append_event "watchdog_start" "" "" "$$" 0 "" "watchdog started"

while true; do
  started_at="$(utc_now)"
  "$@" &
  child_pid="$!"
  echo "$child_pid" > "$CHILD_PID_FILE"
  append_event "child_start" "$started_at" "" "$child_pid" 0 "" "child process started"

  while true; do
    set +e
    wait "$child_pid"
    rc="$?"
    set -e
    if [[ "$rc" -gt 128 ]] && kill -0 "$child_pid" 2>/dev/null; then
      append_event "child_wait_interrupted" "$started_at" "" "$child_pid" "$rc" "$((rc - 128))" "wait interrupted while child remained alive"
      continue
    fi
    break
  done

  ended_at="$(utc_now)"
  signal_number=""
  if [[ "$rc" -gt 128 ]]; then
    signal_number="$((rc - 128))"
  fi
  append_event "child_exit" "$started_at" "$ended_at" "$child_pid" "$rc" "$signal_number" "child process exited"
  child_pid=""
  rm -f "$CHILD_PID_FILE"

  if [[ "${PPD_WATCHDOG_ONESHOT:-}" == "1" ]]; then
    rm -f "$PID_FILE" "$CHILD_PID_FILE" "$STOP_FILE"
    exit "$rc"
  fi

  sleep "$RESTART_DELAY" &
  sleep_pid="$!"
  wait "$sleep_pid" || true
done

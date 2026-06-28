#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  sudo -E bash scripts/setup-voice-proxy-digitalocean.sh

Optional environment variables:
  VOICE_PROXY_API_KEY=optional-upstream-key
  VOICE_PROXY_PORT=8790
  VOICE_PROXY_HOST=127.0.0.1
  VOICE_PROXY_UPSTREAM_URL=http://10.8.0.99:8000/infer
  VOICE_PROXY_TTS_UPSTREAM_URL=http://10.8.0.99:8000/tts
  VOICE_PROXY_STT_UPSTREAM_URL=http://10.8.0.99:8000/stt
  VOICE_PROXY_ALLOWED_ORIGINS=https://portland-laws.github.io,https://211-ai.github.io,http://localhost:5173
  VOICE_PROXY_PUBLIC_ORIGIN=https://animegf.chat
  VOICE_PROXY_OPEN_FIREWALL=1
  SERVICE_NAME=portland-voice-proxy

After setup, expose the service over HTTPS and call:
  https://animegf.chat:8790/api/voice/infer
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ "${EUID}" -ne 0 ]]; then
  echo "Please run as root, for example: sudo -E bash scripts/setup-voice-proxy-digitalocean.sh" >&2
  exit 1
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
REPO_DIR="$(cd -- "${SCRIPT_DIR}/.." >/dev/null 2>&1 && pwd)"
SERVICE_NAME="${SERVICE_NAME:-portland-voice-proxy}"
SERVICE_USER="${SUDO_USER:-${USER:-root}}"
SERVICE_GROUP="$(id -gn "${SERVICE_USER}" 2>/dev/null || echo "${SERVICE_USER}")"
PORT="${VOICE_PROXY_PORT:-8790}"
HOST="${VOICE_PROXY_HOST:-127.0.0.1}"
PUBLIC_ORIGIN="${VOICE_PROXY_PUBLIC_ORIGIN:-https://animegf.chat}"
UPSTREAM_URL="${VOICE_PROXY_UPSTREAM_URL:-http://10.8.0.99:8000/infer}"
TTS_UPSTREAM_URL="${VOICE_PROXY_TTS_UPSTREAM_URL:-http://10.8.0.99:8000/tts}"
STT_UPSTREAM_URL="${VOICE_PROXY_STT_UPSTREAM_URL:-http://10.8.0.99:8000/stt}"
ENV_FILE="/etc/${SERVICE_NAME}.env"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

DEFAULT_ALLOWED_ORIGINS="https://portland-laws.github.io,https://211-ai.github.io,http://localhost:5173,http://127.0.0.1:5173"
if [[ -n "${PUBLIC_ORIGIN}" ]]; then
  DEFAULT_ALLOWED_ORIGINS+=",${PUBLIC_ORIGIN}"
fi
ALLOWED_ORIGINS="${VOICE_PROXY_ALLOWED_ORIGINS:-${DEFAULT_ALLOWED_ORIGINS}}"

if ! command -v node >/dev/null 2>&1; then
  echo "Installing Node.js from the Ubuntu/Debian package repositories..."
  apt-get update
  apt-get install -y nodejs npm
fi

NODE_MAJOR="$(node -p "Number(process.versions.node.split('.')[0])")"
if [[ "${NODE_MAJOR}" -lt 18 ]]; then
  echo "Node.js 18+ is required for built-in fetch. Current version: $(node --version)" >&2
  echo "Install Node.js 20 LTS, then rerun this script." >&2
  exit 1
fi

echo "Skipping npm install for proxy setup; the voice proxy only uses built-in Node modules."
cd "${REPO_DIR}"

if command -v ufw >/dev/null 2>&1 && [[ "${VOICE_PROXY_OPEN_FIREWALL:-1}" == "1" ]]; then
  echo "Opening TCP port ${PORT} in UFW..."
  ufw allow "${PORT}/tcp" || true
fi

echo "Writing ${ENV_FILE}..."
cat > "${ENV_FILE}" <<EOF
VOICE_PROXY_PORT=${PORT}
VOICE_PROXY_HOST=${HOST}
VOICE_PROXY_UPSTREAM_URL=${UPSTREAM_URL}
VOICE_PROXY_TTS_UPSTREAM_URL=${TTS_UPSTREAM_URL}
VOICE_PROXY_STT_UPSTREAM_URL=${STT_UPSTREAM_URL}
VOICE_PROXY_ALLOWED_ORIGINS=${ALLOWED_ORIGINS}
EOF
if [[ -n "${VOICE_PROXY_API_KEY:-}" ]]; then
  echo "VOICE_PROXY_API_KEY=${VOICE_PROXY_API_KEY}" >> "${ENV_FILE}"
fi
chmod 600 "${ENV_FILE}"
chown root:root "${ENV_FILE}"

echo "Writing ${SERVICE_FILE}..."
cat > "${SERVICE_FILE}" <<EOF
[Unit]
Description=Portland Laws voice proxy
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=${REPO_DIR}
EnvironmentFile=${ENV_FILE}
ExecStart=$(command -v node) ${REPO_DIR}/scripts/voice-proxy-server.mjs
Restart=always
RestartSec=3
User=${SERVICE_USER}
Group=${SERVICE_GROUP}
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ProtectHome=false

[Install]
WantedBy=multi-user.target
EOF

chmod +x "${REPO_DIR}/scripts/voice-proxy-server.mjs"
systemctl daemon-reload
systemctl enable --now "${SERVICE_NAME}"

echo
echo "Service status:"
systemctl --no-pager --full status "${SERVICE_NAME}" || true

echo
echo "Health check:"
curl -fsS "http://127.0.0.1:${PORT}/health" || true
echo

cat <<EOF

Voice proxy setup complete.

Local endpoint:
  http://127.0.0.1:${PORT}/api/voice/infer

Expose this service through TLS before calling it from a github.io page.
Recommended browser URL:
  https://animegf.chat:${PORT}/api/voice/infer

Useful commands:
  sudo systemctl status ${SERVICE_NAME}
  sudo journalctl -u ${SERVICE_NAME} -f
  sudo systemctl restart ${SERVICE_NAME}
EOF
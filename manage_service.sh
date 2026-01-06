#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="sora2api"
WORKDIR="/root/sora2api"
START_SCRIPT="${WORKDIR}/start.sh"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

usage() {
  cat <<'EOF'
Usage: manage_service.sh <install|update|restart|status|logs|disable>
  install : create+enable the systemd service and start it
  update  : git pull, install deps, restart service
  restart : restart the running service
  status  : show systemd status
  logs    : follow service logs
  disable : stop and disable the service
EOF
}

require_root() {
  if [[ $(id -u) -ne 0 ]]; then
    echo "Please run as root (sudo)." >&2
    exit 1
  fi
}

install_service() {
  require_root
  chmod +x "$START_SCRIPT"

  cat >"$SERVICE_FILE" <<EOF
[Unit]
Description=sora2api service
After=network.target

[Service]
Type=simple
WorkingDirectory=${WORKDIR}
ExecStart=/bin/bash ${START_SCRIPT}
Restart=on-failure
RestartSec=5s
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

  systemctl daemon-reload
  systemctl enable "$SERVICE_NAME"
  systemctl restart "$SERVICE_NAME"
  systemctl status --no-pager "$SERVICE_NAME"
}

update_code() {
  require_root
  if [[ -d "$WORKDIR/.git" ]]; then
    git -C "$WORKDIR" pull --ff-only
  else
    echo "Warning: no git repo found, skipping pull." >&2
  fi
  if [[ -f "$WORKDIR/venv/bin/pip" && -f "$WORKDIR/requirements.txt" ]]; then
    "$WORKDIR/venv/bin/pip" install -r "$WORKDIR/requirements.txt"
  fi
  systemctl restart "$SERVICE_NAME"
}

case "${1:-}" in
  install) install_service ;;
  update)  update_code ;;
  restart) require_root; systemctl restart "$SERVICE_NAME" ;;
  status)  require_root; systemctl status --no-pager "$SERVICE_NAME" ;;
  logs)    require_root; journalctl -u "$SERVICE_NAME" -f ;;
  disable) require_root; systemctl disable --now "$SERVICE_NAME" ;;
  *) usage; exit 1 ;;
esac

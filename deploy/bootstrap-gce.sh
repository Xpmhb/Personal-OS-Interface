#!/usr/bin/env bash
# Bootstrap the Hermes Chief-of-Staff pilot host on Debian-based Compute Engine VMs.
# This script intentionally contains no credentials. Populate /opt/hermes/.env
# with production secrets before activating model-backed Hermes, Cognee, or ClickUp work.
set -euo pipefail

REPO_URL="https://github.com/Xpmhb/Personal-OS-Interface.git"
APP_DIR="/opt/hermes"
LOG_FILE="/var/log/hermes-bootstrap.log"

exec > >(tee -a "${LOG_FILE}") 2>&1

echo "[$(date --iso-8601=seconds)] Starting Hermes bootstrap"
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends git docker.io docker-compose ca-certificates
systemctl enable --now docker

if [[ -d "${APP_DIR}/.git" ]]; then
  git -C "${APP_DIR}" fetch --depth=1 origin main
  git -C "${APP_DIR}" reset --hard origin/main
else
  rm -rf "${APP_DIR}"
  git clone --depth=1 --branch main "${REPO_URL}" "${APP_DIR}"
fi

cd "${APP_DIR}"
if [[ ! -f .env ]]; then
  cp .env.example .env
  chmod 600 .env
fi

# The web edge can start without provider credentials. Agent tools and incoming
# ClickUp events remain inert until real values replace placeholders in .env.
if docker compose version >/dev/null 2>&1; then
  COMPOSE=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE=(docker-compose)
else
  echo "Docker Compose is unavailable after package installation" >&2
  exit 1
fi
"${COMPOSE[@]}" -f docker-compose.yml -f docker-compose.prod.yml up -d --build

echo "[$(date --iso-8601=seconds)] Hermes bootstrap completed"

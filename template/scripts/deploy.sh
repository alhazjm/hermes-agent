#!/usr/bin/env bash
# Deploy the hosted demo to a $5 VPS.
#
# Prereqs on the VPS: docker, docker-compose-plugin, git.
# Run on your laptop:  REMOTE=user@vps.example.com ./scripts/deploy.sh
#
# What it does:
#   1. Rsync the template/ directory to the VPS.
#   2. SSH in, build the image, and start docker compose.
#   3. Tail the logs once so you can confirm cron registered.
#
# Cost shape: ~$5/mo VPS + ~$5–20/mo OpenRouter at default model and
# session cap. Hard cap on spend lives in the container, not here.

set -euo pipefail

REMOTE="${REMOTE:?Set REMOTE=user@host}"
REMOTE_DIR="${REMOTE_DIR:-/opt/agentic-template}"
ENV_FILE="${ENV_FILE:-.env.production}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing $ENV_FILE — copy .env.example and fill in production values." >&2
  exit 1
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "==> Syncing template to $REMOTE:$REMOTE_DIR"
ssh "$REMOTE" "mkdir -p $REMOTE_DIR"
rsync -az --delete \
  --exclude='.env' --exclude='.env.production' --exclude='out/' \
  "$ROOT/" "$REMOTE:$REMOTE_DIR/"

echo "==> Pushing $ENV_FILE as .env"
scp "$ENV_FILE" "$REMOTE:$REMOTE_DIR/.env"

echo "==> Building and starting"
ssh "$REMOTE" "cd $REMOTE_DIR && docker compose build && docker compose up -d"

echo "==> Recent logs (Ctrl-C to stop following)"
ssh "$REMOTE" "cd $REMOTE_DIR && docker compose logs --tail=80 -f"

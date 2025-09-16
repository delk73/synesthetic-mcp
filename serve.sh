#!/usr/bin/env bash
set -euo pipefail

SERVICE=serve
CLEANED=0

cleanup() {
  if [ "$CLEANED" -eq 1 ]; then
    return
  fi
  CLEANED=1
  docker compose stop "$SERVICE" >/dev/null 2>&1 || true
  docker compose rm -f "$SERVICE" >/dev/null 2>&1 || true
}

trap cleanup EXIT
trap 'cleanup; exit 130' INT TERM

echo "🚀 Building image for '$SERVICE'..."
docker compose build "$SERVICE"

echo "🚀 Starting '$SERVICE' in detached mode..."
docker compose up -d "$SERVICE"

container_id=$(docker compose ps -q "$SERVICE")
if [ -z "$container_id" ]; then
  echo "Unable to find container id for '$SERVICE'" >&2
  exit 1
fi

echo "⏳ Waiting for '$SERVICE' to report healthy..."
while true; do
  status=$(docker inspect --format='{{.State.Health.Status}}' "$container_id" 2>/dev/null || echo "starting")
  if [ "$status" = "healthy" ]; then
    break
  fi
  if [ "$status" = "unhealthy" ]; then
    docker compose logs "$SERVICE"
    echo "'$SERVICE' reported unhealthy" >&2
    exit 1
  fi
  sleep 2
done

echo "✅ '$SERVICE' is healthy. Attaching logs (Ctrl+C to stop)..."
docker compose logs -f "$SERVICE"

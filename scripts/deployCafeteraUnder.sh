#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
IMAGE="edokope/cafetera-under-backend:latest"
NAME="cafeteraUnder"
MEMORY_LIMIT="512m"
ENV_FILE="$SCRIPT_DIR/.env-cafetera-under"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Falta $ENV_FILE"
  exit 1
fi
if [[ ! -f "$ROOT/secrets/firebase.json" ]]; then
  echo "Falta $ROOT/secrets/firebase.json"
  exit 1
fi

oldImageId=""
if docker inspect "$NAME" >/dev/null 2>&1; then
  oldImageId="$(docker inspect "$NAME" --format '{{.Image}}')"
fi
docker pull "$IMAGE"
docker rm -f "$NAME" >/dev/null 2>&1 || true
docker run -d \
  --name "$NAME" \
  --restart unless-stopped \
  --memory="$MEMORY_LIMIT" \
  --env-file "$ENV_FILE" \
  -v "$ROOT/secrets/firebase.json:/run/secrets/firebase.json:ro" \
  "$IMAGE"

newImageId="$(docker inspect "$NAME" --format '{{.Image}}')"
if [[ -n "$oldImageId" && "$oldImageId" != "$newImageId" ]]; then
  docker rmi "$oldImageId" >/dev/null 2>&1 || true
fi
echo "Deploy OK: $NAME en marcha. Se conecta al broker MQTT y no abre puertos."

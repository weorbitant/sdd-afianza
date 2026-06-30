#!/usr/bin/env bash
# Usage: connect.sh <service-alias> <env> [psql-args...]
#   service-alias: pgi-api | pc-api | obligations | data-factory
#   env:           local | dev | prod
#
# Called by Claude after prompting via AskUserQuestion.
# Extra args after env are forwarded to psql (e.g. -c "SELECT 1;")

set -euo pipefail

WORKSPACE_ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"

SERVICE_ALIAS="${1:-}"
ENV="${2:-}"

if [[ -z "$SERVICE_ALIAS" || -z "$ENV" ]]; then
  echo "Usage: $0 <service-alias> <env> [psql-args...]"
  echo "  aliases: pgi-api | pc-api | obligations | data-factory"
  echo "  env:     local | dev | prod"
  exit 1
fi

shift 2
EXTRA_ARGS=("$@")

case "$SERVICE_ALIAS" in
  pgi-api)
    ENV_FILE="$WORKSPACE_ROOT/pgi-service-pgi-api/.env"
    DB_NAME="pd-service-backoffice-api-$ENV"
    ;;
  pc-api)
    ENV_FILE="$WORKSPACE_ROOT/pc-service-portalcliente-api/.env"
    DB_NAME="pc-service-portalcliente-api-$ENV"
    ;;
  obligations)
    ENV_FILE="$WORKSPACE_ROOT/pd-service-obligations-api/.env-sample"
    DB_NAME="mp-service-obligations-api-$ENV"
    ;;
  data-factory)
    ENV_FILE="$WORKSPACE_ROOT/pd-service-data-factory/.env"
    DB_NAME="pd-service-data-factory-$ENV"
    ;;
  *)
    echo "Unknown alias: $SERVICE_ALIAS"
    exit 1
    ;;
esac

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Error: credentials file not found at $ENV_FILE"
  echo ""
  echo "Possible reasons:"
  echo "  - The repo/.env may not exist locally (e.g. data-factory has no local .env)"
  echo "  - The .env file may not exist yet (copy from .env.example or .env-sample)"
  echo ""
  echo "Alternative: read credentials from k8s:"
  echo "  kubectl get secret <service>-secret -n <env> -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 -d"
  exit 1
fi

parse_env() {
  local key="$1"
  grep -E "^${key}=" "$ENV_FILE" | tail -1 | sed "s/^${key}=//;s/^['\"]//;s/['\"]$//"
}

PG_HOST=$(parse_env "POSTGRES_HOST")
PG_USER=$(parse_env "POSTGRES_USER")
PG_PASS=$(parse_env "POSTGRES_PASSWORD")
PG_PORT=$(parse_env "POSTGRES_PORT")
PG_PORT="${PG_PORT:-5432}"

if [[ "$ENV" == "local" ]]; then
  PG_HOST="localhost"
fi

if [[ "$ENV" != "local" ]] && grep -qE "^POSTGRES_CONNECTION_STRING=" "$ENV_FILE"; then
  CONN_STR=$(parse_env "POSTGRES_CONNECTION_STRING")
  echo "Connecting to $SERVICE_ALIAS ($ENV)..."
  PGPASSWORD="$PG_PASS" psql "$CONN_STR" "${EXTRA_ARGS[@]+"${EXTRA_ARGS[@]}"}"
else
  echo "Connecting to $SERVICE_ALIAS ($ENV) → $PG_HOST:$PG_PORT/$DB_NAME as $PG_USER"
  PGPASSWORD="$PG_PASS" psql -h "$PG_HOST" -p "$PG_PORT" -U "$PG_USER" -d "$DB_NAME" "${EXTRA_ARGS[@]+"${EXTRA_ARGS[@]}"}"
fi

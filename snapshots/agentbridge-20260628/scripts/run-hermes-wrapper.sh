#!/bin/sh
set -eu

SECRET_PATH="/run/secrets/provider_api_key"

if [ ! -f "${SECRET_PATH}" ]; then
  echo "Missing provider secret at ${SECRET_PATH}" >&2
  exit 1
fi

PROVIDER_API_KEY="$(tr -d '\r\n' < "${SECRET_PATH}")"

if [ -z "${PROVIDER_API_KEY}" ]; then
  echo "Provider secret is empty" >&2
  exit 1
fi

export HERMES_PROVIDER_API_KEY="${PROVIDER_API_KEY}"
export OPENAI_API_KEY="${PROVIDER_API_KEY}"
export HERMES_INFERENCE_MODEL="${HERMES_INFERENCE_MODEL:-${HERMES_MODEL_PRIMARY:-gpt-5.5}}"
export HERMES_INFERENCE_PROVIDER="${HERMES_INFERENCE_PROVIDER:-openai-api}"

if [ -n "${HERMES_PROVIDER_BASE_URL:-}" ]; then
  export OPENAI_BASE_URL="${HERMES_PROVIDER_BASE_URL}"
fi

export AGENTBRIDGE_ROOT="${AGENTBRIDGE_ROOT:-/bridge}"
export HERMES_DATA_DIR="${HERMES_DATA_DIR:-/opt/data}"
export HERMES_APPROVALS_MODE="${HERMES_APPROVALS_MODE:-manual}"

RUN_LOG_DIR="${HERMES_RUN_LOG_DIR:-/bridge/logs/hermes-runs}"
COST_LOG_DIR="${HERMES_COST_LOG_DIR:-/bridge/logs/cost-rollups}"

mkdir -p "${RUN_LOG_DIR}"
mkdir -p "${COST_LOG_DIR}"

timestamp_utc() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}

json_escape() {
  printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'
}

cd "${AGENTBRIDGE_ROOT}"

STARTED_AT="$(timestamp_utc)"
RUN_DAY="$(date -u +%F)"
RUN_MONTH="$(date -u +%Y-%m)"
SESSION_ID="${HERMES_SESSION_ID:-$(date -u +%Y%m%dT%H%M%SZ)-$$}"
COMMAND_NAME="${1:-chat}"
MODEL_NAME="${HERMES_INFERENCE_MODEL:-${HERMES_MODEL_PRIMARY:-gpt-5.5}}"
PROVIDER_LABEL="${HERMES_PROVIDER_LABEL:-third-party-openai-compatible}"

set +e
hermes "$@"
EXIT_CODE=$?
set -e

ENDED_AT="$(timestamp_utc)"
if [ "${EXIT_CODE}" -eq 0 ]; then
  RUN_STATUS="succeeded"
else
  RUN_STATUS="failed"
fi

RUN_LOG_FILE="${RUN_LOG_DIR}/${RUN_DAY}.jsonl"
COST_LOG_FILE="${COST_LOG_DIR}/${RUN_MONTH}.jsonl"
RUN_NOTES="wrapper log only; token and cost fields unavailable; command=${COMMAND_NAME}; exit_code=${EXIT_CODE}"
ROLLUP_NOTES="wrapper rollup only; aggregate cost unavailable without provider telemetry"

printf '{"started_at":"%s","ended_at":"%s","session_id":"%s","task_id":null,"runtime":"hermes","model":"%s","provider":"%s","prompt_tokens":null,"completion_tokens":null,"reasoning_tokens":null,"cost_usd_est":null,"status":"%s","notes":"%s"}\n' \
  "$(json_escape "${STARTED_AT}")" \
  "$(json_escape "${ENDED_AT}")" \
  "$(json_escape "${SESSION_ID}")" \
  "$(json_escape "${MODEL_NAME}")" \
  "$(json_escape "${PROVIDER_LABEL}")" \
  "$(json_escape "${RUN_STATUS}")" \
  "$(json_escape "${RUN_NOTES}")" >> "${RUN_LOG_FILE}" || {
    echo "[wrapper] warning: failed to append run log to ${RUN_LOG_FILE}" >&2
  }

printf '{"month":"%s","session_id":"%s","model":"%s","provider":"%s","cost_usd_est":null,"notes":"%s"}\n' \
  "$(json_escape "${RUN_MONTH}")" \
  "$(json_escape "${SESSION_ID}")" \
  "$(json_escape "${MODEL_NAME}")" \
  "$(json_escape "${PROVIDER_LABEL}")" \
  "$(json_escape "${ROLLUP_NOTES}")" >> "${COST_LOG_FILE}" || {
    echo "[wrapper] warning: failed to append cost log to ${COST_LOG_FILE}" >&2
  }

exit "${EXIT_CODE}"

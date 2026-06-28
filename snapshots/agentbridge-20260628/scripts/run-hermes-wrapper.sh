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
export HERMES_INFERENCE_MODEL="${HERMES_INFERENCE_MODEL:-${HERMES_MODEL_PRIMARY:-gpt-5.4}}"
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
PROVIDER_LABEL="${HERMES_PROVIDER_LABEL:-third-party-openai-compatible}"

# Hermes upstream oneshot bug: when HERMES_INFERENCE_MODEL is present and the
# caller did not explicitly pass --model/--provider, `hermes -z` treats the env
# model as an explicit override, auto-detects bare OpenAI-family models like
# gpt-5.4 to the non-routable group alias "openai", then fails with
# "Unknown provider 'openai'". In that narrow case, let oneshot fall back to
# config.yaml's persisted model/provider pair instead of the session env pair.
IS_ONESHOT_COMMAND=0
HAS_EXPLICIT_MODEL_FLAG=0
HAS_EXPLICIT_PROVIDER_FLAG=0
EXPECT_MODEL_VALUE=0
EXPECT_PROVIDER_VALUE=0

for ARG in "$@"; do
  if [ "${EXPECT_MODEL_VALUE}" -eq 1 ]; then
    HAS_EXPLICIT_MODEL_FLAG=1
    EXPECT_MODEL_VALUE=0
    continue
  fi

  if [ "${EXPECT_PROVIDER_VALUE}" -eq 1 ]; then
    HAS_EXPLICIT_PROVIDER_FLAG=1
    EXPECT_PROVIDER_VALUE=0
    continue
  fi

  case "${ARG}" in
    -z|--oneshot|--oneshot=*)
      IS_ONESHOT_COMMAND=1
      ;;
  esac

  case "${ARG}" in
    -m|--model)
      EXPECT_MODEL_VALUE=1
      ;;
    --model=*)
      HAS_EXPLICIT_MODEL_FLAG=1
      ;;
    --provider)
      EXPECT_PROVIDER_VALUE=1
      ;;
    --provider=*)
      HAS_EXPLICIT_PROVIDER_FLAG=1
      ;;
  esac
done

if [ "${IS_ONESHOT_COMMAND}" -eq 1 ] && [ "${HAS_EXPLICIT_MODEL_FLAG}" -eq 0 ] && [ "${HAS_EXPLICIT_PROVIDER_FLAG}" -eq 0 ]; then
  unset HERMES_INFERENCE_MODEL
  unset HERMES_INFERENCE_PROVIDER
fi

MODEL_NAME="${HERMES_INFERENCE_MODEL:-${HERMES_MODEL_PRIMARY:-gpt-5.4}}"

IS_INTERACTIVE_COMMAND=0
if [ "${COMMAND_NAME}" = "chat" ] || [ "${COMMAND_NAME}" = "auth" ] || [ "${COMMAND_NAME}" = "model" ] || [ "${COMMAND_NAME}" = "setup" ]; then
  if [ "${IS_ONESHOT_COMMAND}" -eq 0 ]; then
    IS_INTERACTIVE_COMMAND=1
  fi
fi

if [ "${IS_INTERACTIVE_COMMAND}" -eq 1 ] && [ -t 0 ] && [ -t 1 ]; then
  exec hermes "$@"
fi

set +e
HERMES_OUTPUT="$(hermes "$@" 2>&1)"
EXIT_CODE=$?
set -e

printf '%s\n' "${HERMES_OUTPUT}"

ENDED_AT="$(timestamp_utc)"
if [ "${EXIT_CODE}" -eq 0 ] && printf '%s' "${HERMES_OUTPUT}" | grep -Eq '(^|\n)(❌|Error: HTTP |API call failed after [0-9]+ retries:|Billing or credits exhausted:|hermes -z: agent failed:)'; then
  EXIT_CODE=1
fi

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

#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PYTHON="${PYTHON:-$REPO_ROOT/.venv/bin/python}"
if [[ ! -x "$PYTHON" ]]; then
  PYTHON="${PYTHON:-python3}"
fi

if [[ -z "${SECURE_CODE_HUNT_ROOT:-}" ]]; then
  echo "SECURE_CODE_HUNT_ROOT must point to the external secure-code-hunt corpus root." >&2
  exit 2
fi

if [[ -z "${CODEGOPHER_PROXY_ADMIN_URL:-}" ]]; then
  echo "CODEGOPHER_PROXY_ADMIN_URL is required so the benchmark can create a fresh proxy run." >&2
  exit 2
fi

MODEL_ALIAS="Qwen 3.5 35B"
API_KEY_ENV_NAME="CODEGOPHER_LOCAL_API_KEY"
export CODEGOPHER_LOCAL_API_KEY="${CODEGOPHER_LOCAL_API_KEY:-dummy-local-key}"

configured_base_url() {
  "$PYTHON" - <<'PY'
from codegopher.config.loader import load_settings

settings = load_settings()
entries = settings.providers.get(settings.model.provider, ())
selected = None
for entry in entries:
    if entry.id == settings.model.name or entry.name == settings.model.name:
        selected = entry
        break
if selected is None and entries:
    selected = entries[0]
print(selected.base_url if selected and selected.base_url else "")
PY
}

BASE_URL="${CODEGOPHER_LOCAL_BASE_URL:-$(configured_base_url)}"
if [[ -z "$BASE_URL" ]]; then
  echo "CODEGOPHER_LOCAL_BASE_URL is unset and no base_url was found in CodeGopher settings." >&2
  exit 2
fi

find_app_dir() {
  local app_key="$1"
  local match
  match="$(find "$SECURE_CODE_HUNT_ROOT/apps" -type d -name "${app_key}-*" | sort | head -n 1)"
  if [[ -z "$match" ]]; then
    echo "Could not find sanitized source app for ${app_key} under the configured corpus root." >&2
    exit 2
  fi
  if [[ ! -f "$match/.vulns" ]]; then
    echo "Could not find evaluator manifest for ${app_key}; expected hidden manifest beside the app." >&2
    exit 2
  fi
  printf '%s\n' "$match"
}

APP05="$(find_app_dir app-05)"
APP10="$(find_app_dir app-10)"
APP14="$(find_app_dir app-14)"

STAMP="$(date -u +%Y%m%d-%H%M%S)"
RUN_ROOT="${TMPDIR:-/tmp}/codegopher-v016-local-qwen-${STAMP}"
OUTPUT_ROOT="$RUN_ROOT/output"
TEMP_ROOT="$RUN_ROOT/temp"
mkdir -p "$OUTPUT_ROOT" "$TEMP_ROOT"

echo "Starting v0.16 local Qwen focused validation."
echo "Raw benchmark output: $OUTPUT_ROOT"
echo "Sanitized workspaces: $TEMP_ROOT"

"$PYTHON" -m codegopher.devtools.benchmark \
  --app "app-05|app-05|$APP05|$APP05/.vulns" \
  --app "app-10|app-10|$APP10|$APP10/.vulns" \
  --app "app-14|app-14|$APP14|$APP14/.vulns" \
  --output-dir "$OUTPUT_ROOT" \
  --temp-root "$TEMP_ROOT" \
  --cgopher "$PYTHON" \
  --cgopher-arg=-m \
  --cgopher-arg=codegopher \
  --provider openai \
  --model "$MODEL_ALIAS" \
  --base-url "$BASE_URL" \
  --api-family responses \
  --api-key-env "$API_KEY_ENV_NAME" \
  --api-key-value "$CODEGOPHER_LOCAL_API_KEY" \
  --proxy-admin-url "$CODEGOPHER_PROXY_ADMIN_URL" \
  --proxy-run-name "CodeGopher v0.16 local Qwen focused validation" \
  --proxy-run-notes "Focused sanitized validation for app-05, app-10, and app-14." \
  --sanitize-source-hints \
  --timeout-seconds 3600 \
  --max-output-tokens 16384

echo "Completed v0.16 local Qwen focused validation."
echo "Raw benchmark output: $OUTPUT_ROOT"
echo "Sanitized workspaces: $TEMP_ROOT"

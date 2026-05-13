#!/usr/bin/env bash
# Source this file to inject plugin userConfig values as env vars before running scripts.
#
# Usage:
#   source "${CLAUDE_PLUGIN_ROOT}/scripts/init-env.sh"
#   uv run enrich.py resolve
#
# The camelCase variables ($paperlessUrl etc.) are set by the plugin runtime from
# your userConfig. The SCREAMING_SNAKE_CASE versions are what the scripts consume.
# This mapping lets you also override from a shell profile or secret manager.

export PAPERLESS_URL="${PAPERLESS_URL:-${paperlessUrl:-}}"
export PAPERLESS_TOKEN="${PAPERLESS_TOKEN:-${paperlessToken:-}}"
export CAR_INVOICE_VEHICLES_PATH="${CAR_INVOICE_VEHICLES_PATH:-${vehiclesConfigPath:-}}"

if [ -n "${pipelineStateDir:-}" ]; then
  export CAR_INVOICE_STATE_DIR="${CAR_INVOICE_STATE_DIR:-$pipelineStateDir}"
fi

# Validate required vars
_missing=()
[ -z "$PAPERLESS_URL" ]             && _missing+=("PAPERLESS_URL (set paperlessUrl in plugin config)")
[ -z "$PAPERLESS_TOKEN" ]           && _missing+=("PAPERLESS_TOKEN (set paperlessToken in plugin config)")
[ -z "$CAR_INVOICE_VEHICLES_PATH" ] && _missing+=("CAR_INVOICE_VEHICLES_PATH (set vehiclesConfigPath in plugin config)")

if [ ${#_missing[@]} -gt 0 ]; then
  echo "ERROR: Required environment variables are not set:" >&2
  for v in "${_missing[@]}"; do echo "  - $v" >&2; done
  return 1
fi

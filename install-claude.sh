#!/usr/bin/env bash
set -euo pipefail

token=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --token)
      if [[ $# -lt 2 || -z "${2:-}" ]]; then
        echo "Error: --token requires a value." >&2
        exit 1
      fi
      token="$2"
      shift 2
      ;;
    *)
      echo "Error: unknown argument '$1'." >&2
      echo "Usage: $0 --token <api-token>" >&2
      exit 1
      ;;
  esac
done

if [[ -z "$token" ]]; then
  echo "Error: missing required --token argument." >&2
  echo "Usage: $0 --token <api-token>" >&2
  exit 1
fi

uv run fastmcp install claude-desktop main.py \
  --project . \
  --env "API_TOKEN=$token"
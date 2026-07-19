#!/usr/bin/env bash
# Thin wrapper around the cross-platform installer. Windows users run:
#   uv run python install_claude.py --token <api-token>
set -euo pipefail
cd "$(dirname "$0")"
exec uv run python install_claude.py "$@"

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

# fastmcp writes a bare `uv` as the command. Claude Desktop is a GUI app with a
# minimal PATH (no Homebrew), so it can't find `uv` and the server fails to
# launch. Rewrite the command to the absolute uv path.
uv_bin="$(command -v uv)"
cfg="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
python3 - "$cfg" "$uv_bin" <<'PY'
import json, sys
cfg, uv_bin = sys.argv[1], sys.argv[2]
with open(cfg) as f:
    data = json.load(f)
data["mcpServers"]["darus-mcp"]["command"] = uv_bin
with open(cfg, "w") as f:
    json.dump(data, f, indent=2)
print(f"Patched darus-mcp command -> {uv_bin}")
PY
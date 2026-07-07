"""Smoke tests for the DaRUS MCP server.

No pytest dependency on purpose: run it directly.

    uv run python test_smoke.py

Covers two of CI's three checks (the third, a locked build, is `uv sync`):
  1. The module imports without a token and registers its tools.
  2. Running the server without a token fails loud instead of starting.
"""

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent


def test_imports_and_registers_tools():
    """Importing must succeed with no API_TOKEN and register the tools."""
    os.environ.pop("API_TOKEN", None)
    import main  # noqa: PLC0415 - deferred so the pop above takes effect

    tools = main.app._tool_manager._tools
    assert len(tools) > 0, f"expected tools to register, got {len(tools)}"
    print(f"[ok] import clean, {len(tools)} tools registered")


def test_run_without_token_fails_loud():
    """`python main.py` with no token must exit non-zero and name the token."""
    env = {k: v for k, v in os.environ.items() if k != "API_TOKEN"}
    proc = subprocess.run(
        [sys.executable, "main.py"],
        cwd=HERE,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode != 0, "server started without a token — guard is broken"
    assert "API_TOKEN" in proc.stderr, f"expected API_TOKEN error, got:\n{proc.stderr}"
    print("[ok] no-token run failed loud")


if __name__ == "__main__":
    test_imports_and_registers_tools()
    test_run_without_token_fails_loud()
    print("all smoke tests passed")

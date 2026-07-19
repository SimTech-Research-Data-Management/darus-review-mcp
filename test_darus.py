"""Tests for the DaRUS MCP server and its Claude Desktop installer.

No pytest dependency on purpose: run it directly.

    uv run python test_darus.py

Covers (alongside `uv sync --locked` in CI):
  - the server imports without a token and serves its tools over MCP,
  - running the server without a token fails loud instead of starting,
  - the Claude Desktop installer builds the right entry, resolves the config
    path per OS, and merges into the config without clobbering other servers.
"""

import asyncio
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).parent


def test_serves_tools_over_mcp():
    """Import must succeed with no API_TOKEN, and the server must actually serve
    its tools over the MCP protocol (not just hold them in a private registry).
    Uses fastmcp's in-process client — the same protocol Claude Desktop speaks."""
    os.environ.pop("API_TOKEN", None)
    from fastmcp import Client  # noqa: PLC0415

    import main  # noqa: PLC0415 - deferred so the pop above takes effect

    async def list_tools():
        async with Client(main.app) as client:
            return await client.list_tools()

    tools = asyncio.run(list_tools())
    assert len(tools) == 12, f"expected 12 tools served, got {len(tools)}"
    print(f"[ok] import clean, {len(tools)} tools served over MCP")


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


def test_install_entry_shape():
    """The generated Claude Desktop entry uses an absolute uv path and the fast,
    self-healing launch command (no --with, no --no-sync)."""
    import install_claude as ic

    entry = ic.build_entry("/abs/path/to/uv", "my-token")
    assert entry["command"] == "/abs/path/to/uv", "must use the absolute uv path"
    assert entry["args"][:3] == ["run", "--project", str(ic.REPO)]
    assert entry["args"][-3:] == ["fastmcp", "run", str(ic.REPO / "main.py")]
    assert "--with" not in entry["args"], "the --with overlay is what made startup ~48s"
    assert "--no-sync" not in entry["args"], "keep self-healing sync on"
    assert entry["env"] == {"API_TOKEN": "my-token"}
    print("[ok] install entry shape")


def test_install_merge_preserves_other_servers():
    """Installing us must never clobber a user's other MCP servers."""
    import install_claude as ic

    existing = {"mcpServers": {"neo4j-database": {"command": "uvx"}}}
    merged = ic.with_server(existing, ic.SERVER_NAME, {"command": "uv"})
    assert "neo4j-database" in merged["mcpServers"], "clobbered another server!"
    assert ic.SERVER_NAME in merged["mcpServers"]
    # original input must be untouched (pure function)
    assert existing == {"mcpServers": {"neo4j-database": {"command": "uvx"}}}
    print("[ok] install merge preserves other servers")


def test_install_config_path_per_os():
    """Config path resolves correctly on each supported OS."""
    import install_claude as ic

    orig_platform, orig_appdata = sys.platform, os.environ.get("APPDATA")
    try:
        sys.platform = "darwin"
        assert (
            ic.claude_desktop_config_path()
            .as_posix()
            .endswith("Library/Application Support/Claude/claude_desktop_config.json")
        )
        sys.platform = "win32"
        os.environ["APPDATA"] = str(Path.home() / "AppData" / "Roaming")
        assert (
            ic.claude_desktop_config_path()
            .as_posix()
            .endswith("Claude/claude_desktop_config.json")
        )
        sys.platform = "linux"
        assert (
            ic.claude_desktop_config_path()
            .as_posix()
            .endswith("Claude/claude_desktop_config.json")
        )
    finally:
        sys.platform = orig_platform
        if orig_appdata is None:
            os.environ.pop("APPDATA", None)
        else:
            os.environ["APPDATA"] = orig_appdata
    print("[ok] install config path per OS")


def test_install_writes_and_merges_on_disk():
    """Writing the config to a real file must create missing parents, handle an
    empty file, and preserve any pre-existing servers."""
    import install_claude as ic  # noqa: PLC0415

    # Case 1: merge into an existing config that already has another server.
    with tempfile.TemporaryDirectory() as d:
        cfg = Path(d) / "claude_desktop_config.json"
        cfg.write_text(
            json.dumps({"mcpServers": {"neo4j-database": {"command": "uvx"}}})
        )
        ic.write_config(cfg, ic.SERVER_NAME, ic.build_entry("/abs/uv", "tok"))
        data = json.loads(cfg.read_text())
        assert set(data["mcpServers"]) == {"neo4j-database", ic.SERVER_NAME}
        assert data["mcpServers"][ic.SERVER_NAME]["env"]["API_TOKEN"] == "tok"

    # Case 2: no file and a missing parent directory -> created from scratch.
    with tempfile.TemporaryDirectory() as d:
        cfg = Path(d) / "Claude" / "claude_desktop_config.json"  # parent doesn't exist
        ic.write_config(cfg, ic.SERVER_NAME, ic.build_entry("/abs/uv", "t"))
        assert cfg.exists()
        assert json.loads(cfg.read_text())["mcpServers"][ic.SERVER_NAME]
    print("[ok] install writes & merges on disk")


if __name__ == "__main__":
    test_serves_tools_over_mcp()
    test_run_without_token_fails_loud()
    test_install_entry_shape()
    test_install_merge_preserves_other_servers()
    test_install_config_path_per_os()
    test_install_writes_and_merges_on_disk()
    print("all tests passed")

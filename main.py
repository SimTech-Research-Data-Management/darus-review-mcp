"""
DaRUS MCP Server

This module provides a Model Context Protocol (MCP) server for interacting with the
DaRUS (Data Repository of the University of Stuttgart) Dataverse instance.

The server exposes Dataverse functionality through MCP tools, allowing AI assistants
to search, retrieve, and interact with datasets and metadata stored in DaRUS.

Features:
    - Search datasets and dataverses in DaRUS
    - Retrieve dataset metadata and files
    - Access publication information

Usage:
    Run this server to expose DaRUS functionality via MCP:

    $ python main.py

    The server will start on http://0.0.0.0:8000 and provide MCP tools for:
    - Dataverse operations (search, metadata retrieval)

Dependencies:
    - fastmcp: MCP server framework
    - pyDataverse: Dataverse API client
    - python-dotenv: loads API_TOKEN from a local .env file
"""

import os
import tomllib
from pathlib import Path

from dotenv import load_dotenv
from fastmcp import FastMCP
from pyDataverse import Dataverse
from pyDataverse.mcp import DataverseMCP

load_dotenv()

# Load the API token from the environment variable.
api_token = os.environ.get("API_TOKEN")

# Initialize connection to the DaRUS Dataverse instance
# DaRUS is the institutional data repository of the University of Stuttgart
darus = Dataverse(
    base_url="https://darus.uni-stuttgart.de",
    api_token=api_token,
    verbose=0,
)


# Create the FastMCP application
# This serves as the main MCP server instance that will expose tools to clients
# ponytail: single source of truth for the version; assumes pyproject.toml sits
# next to this file (true when run in-place, as uv/fastmcp do). Switch to
# importlib.metadata if this ever ships as an installed package.
_version = tomllib.loads((Path(__file__).parent / "pyproject.toml").read_text())["project"]["version"]
app = FastMCP(name="darus-mcp", version=_version)

# Register Dataverse MCP tools with the application
# This adds all Dataverse-related tools (search, metadata, files) to the MCP server
DataverseMCP(dataverse=darus).to_mcp(app)

if __name__ == "__main__":
    """
    Main entry point for the DaRUS MCP server.
    
    Starts the MCP server using streamable HTTP transport on all interfaces
    at port 8000. The server will handle MCP requests and provide access to
    the DaRUS Dataverse tools.
    
    Server Configuration:
        - Transport: streamable-http (compatible with MCP clients)
        - Host: 0.0.0.0 (accepts connections from any interface)
        - Port: 8000 (standard development port)
    """
    if not api_token:
        raise ValueError("API_TOKEN environment variable is not set")

    # Start the MCP server
    app.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=8000,
    )

# DaRUS Review MCP

`darus-review-mcp` is a Model Context Protocol (MCP) server that connects LLM assistants to the [DaRUS Dataverse](https://darus.uni-stuttgart.de) API.

It enables AI clients (for example Claude Desktop via MCP) to search datasets, inspect metadata, and retrieve repository context that can be used during scientific or data-quality reviews.

## What It Is

This project provides a lightweight MCP wrapper around Dataverse capabilities using:

- `fastmcp` for exposing tools to MCP-compatible clients
- `pydataverse[mcp]` for Dataverse API and MCP tool integration
- a DaRUS-targeted configuration (`https://darus.uni-stuttgart.de`)

## What It Does

When running, the server exposes Dataverse-backed MCP tools that allow an LLM client to:

- search datasets and dataverses in DaRUS
- retrieve structured dataset metadata
- access publication and file-level repository context
- use repository evidence as context during review workflows

In practice, this turns DaRUS into a live, queryable context source for AI-assisted review tasks.

## Using LLMs to Conduct Reviews

LLMs are most useful for review workflows when they can access repository-grounded facts instead of relying only on prompts.

With this MCP server:

1. the assistant can discover candidate datasets and related metadata in DaRUS,
2. inspect the relevant context (publication details, files, descriptive metadata),
3. generate review feedback based on that retrieved evidence.

Typical outcomes include:

- consistency checks between metadata fields
- completeness checks for dataset documentation
- structured review notes and suggested follow-ups
- faster triage across many records before manual expert review

## Installation

### Prerequisites

- Python `3.12+`
- [`uv`](https://docs.astral.sh/uv/) for environment and dependency execution
- A DaRUS API token

### Why the token is required

Your API token is passed to the MCP server as `API_TOKEN`.
It is used to authenticate against DaRUS and allows access to restricted or unpublished datasets that are not publicly visible.

Without a valid token, the server cannot query protected repository content.

### Install for Claude Desktop (MCP)

From the repository root:

```bash
chmod +x install-claude.sh
./install-claude.sh --token "<your-darus-api-token>"
```

The installer registers this MCP server and injects the token as:

```bash
--env API_TOKEN=<your-darus-api-token>
```

### Run locally

```bash
API_TOKEN="<your-darus-api-token>" uv run python main.py
```

The server starts on `http://0.0.0.0:8000` using `streamable-http` transport.

## Security Notes

- Treat your API token as a secret.
- Do not commit tokens to version control.
- Prefer passing credentials via environment variables or secure secret stores.

## Project Layout

- `main.py` - MCP server bootstrap and DaRUS tool registration
- `install-claude.sh` - helper for Claude Desktop MCP installation with token injection
- `pyproject.toml` - project metadata and dependencies

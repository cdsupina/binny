# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with
code in this repository.

## Project Overview

Binny is a CLI application built with the Claude Agent SDK that provides an
inventory management chatbot. The application uses a multi-agent architecture
with specialized sub-agents for different tasks.

## Architecture

### Package Structure

Binny uses a standard Python package layout:

```
binny/
├── binny/                    # Main package
│   ├── __init__.py
│   ├── main.py              # Entry point and agent setup
│   ├── cli_tools.py         # CLI interface and Rich formatting
│   ├── part_namer_tools.py  # MCP tools for part naming
│   └── part_namer_mcp/      # Utility library for part naming
│       ├── models.py
│       ├── file_manager.py
│       └── approval_workflow.py
├── system_prompts/          # Agent system prompts
├── .claude/                 # Slash commands
└── pyproject.toml          # Package configuration with entry point
```

### Main Agent Structure (binny/main.py)

- **Primary agent**: "Binny" - main conversational interface
- **Sub-agents**:
  - `part-namer`: Generates names for physical parts in mechanical/electrical
    assemblies
  - `mmc-searcher`: Handles McMaster-Carr catalog operations including searching
    for parts, retrieving specifications, and managing subscriptions
  - `inventory-manager`: Manages inventory files stored in location specified
    by `BINNY_INVENTORY_DIR` environment variable

System prompts are loaded from `system_prompts/` directory:

- `binny_prompt.md` - main agent prompt
- `part_namer_prompt.md` - part naming agent prompt
- `mmc_searcher_prompt.md` - McMaster-Carr search agent prompt
- `inventory_manager_prompt.md` - inventory management agent prompt

### CLI Interface (binny/cli_tools.py)

Provides Rich-based terminal UI with:

- Color-coded message panels (user/yellow, assistant/green, tool_use/blue,
  tool_result/magenta, system/cyan)
- JSON syntax highlighting for tool results
- Debug mode (`--debug` or `-d` flag) to show tool use, tool results, and
  session statistics
- Message parsing for different Claude SDK message types: `AssistantMessage`,
  `UserMessage`, `SystemMessage`, `ResultMessage`

## Development Commands

### Running the Application

**Development mode:**
```bash
uv run binny
```

**Installed with uv tool:**
```bash
uv tool install .
binny
```

**Reinstall after making changes:**
```bash
uv tool install --reinstall .
```

**Debug mode:**
```bash
uv run binny --debug
```

### Dependencies

Uses `uv` for dependency management. Dependencies are:

- `asyncio>=4.0.0`
- `claude-agent-sdk>=0.1.4`
- `rich>=14.2.0`
- `python-dotenv>=1.0.0`

Python version: `>=3.13`

Build system: `hatchling` (configured in `[build-system]` section of pyproject.toml)

### Environment Variables

- `BINNY_INVENTORY_DIR` - required by inventory-manager sub-agent to specify
  inventory file location
- `BINNY_PREFIXES_FILE` - path to prefixes.md (typically
  `~/.config/binny/part_namer/prefixes.md`)
- `BINNY_MATERIALS_FILE` - path to materials.md (typically
  `~/.config/binny/part_namer/materials.md`)
- `MMC_SUBSCRIBED_PARTS_FILE` - path to McMaster-Carr subscribed parts file
- `MCMASTER_USERNAME` - McMaster-Carr account email
- `MCMASTER_PASSWORD` - McMaster-Carr account password
- `MCMASTER_CERT_PATH` - path to McMaster-Carr certificate file (.pfx)
- `MCMASTER_CERT_PASSWORD` - certificate password

Environment variables are loaded via `python-dotenv` in main.py:12

### Part Namer MCP Server

The `binny/part_namer_mcp/` directory contains utility code for managing part
naming with a proposal-based workflow. MCP tools are defined in
`binny/part_namer_tools.py` and run as an embedded SDK MCP server.

**Architecture:**

- `part_namer_tools.py` - 10 MCP tools using @tool decorator (embedded server)
- `part_namer_mcp/models.py` - TypedDicts for PrefixProposal and MaterialProposal
- `part_namer_mcp/file_manager.py` - Parse/write H2-based markdown files
- `part_namer_mcp/approval_workflow.py` - Rich panel formatting for proposals

**Workflow:**

1. Part-namer sub-agent checks if prefix/material exists via MCP tools
2. If missing, creates proposal using `propose_prefix` or `propose_material`
3. User approves/rejects via immediate prompt or `/review-prefixes` /
   `/review-materials` commands
4. Approved items are written to respective markdown files in H2 format

**File Format:**

Prefixes and materials are stored as H2 headers with structured fields:

```markdown
## PREFIX_CODE

**Description:** Description text

**Format:** `PREFIX-{PLACEHOLDER}-{PLACEHOLDER}`
```

**MCP Tools:**

- `read_prefixes` / `read_materials` - Get tracked items
- `propose_prefix` / `propose_material` - Create proposals
- `approve_prefix` / `approve_material` - Approve and write to files
- `reject_prefix` / `reject_material` - Reject proposals
- `list_prefix_proposals` / `list_material_proposals` - List pending

**Slash Commands:**

- `/review-prefixes` - Review pending prefix proposals
- `/review-materials` - Review pending material proposals

## Agent SDK Integration

The application uses Claude Agent SDK's async client pattern:

1. Initialize `ClaudeAgentOptions` with model, system prompt, and agent
   definitions
2. Create `ClaudeSDKClient` context manager
3. Loop: get user input → `client.query()` → iterate `client.receive_response()`
4. Parse and display messages using Rich console

Sub-agents are registered in the `agents` dict of `ClaudeAgentOptions` in
`binny/main.py`, each with description, prompt, and model specification.

The embedded MCP server is created with `create_sdk_mcp_server` and added to
`mcp_servers` alongside external MCP servers like mcmaster and excel.

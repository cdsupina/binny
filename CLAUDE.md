# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with
code in this repository.

## Project Overview

Binny is a CLI application built with the Claude Agent SDK that provides an
inventory management chatbot. The application uses a multi-agent architecture
with specialized sub-agents for different tasks.

## Architecture

### Main Agent Structure (main.py:8-56)

- **Primary agent**: "Binny" - main conversational interface
- **Sub-agents**:
  - `part-namer`: Generates names for physical parts in mechanical/electrical
    assemblies
  - `inventory-manager`: Manages inventory files stored in location specified
    by `INVENTORY_SUBAGENT_DIRECTORY` environment variable

System prompts are loaded from `system_prompts/` directory:

- `binny_prompt.md` - main agent prompt
- `part_namer_prompt.md` - part naming agent prompt
- `inventory_manager_prompt.md` - inventory management agent prompt

### CLI Interface (cli_tools.py)

Provides Rich-based terminal UI with:

- Color-coded message panels (user/yellow, assistant/green, tool_use/blue,
  tool_result/magenta, system/cyan)
- JSON syntax highlighting for tool results
- Session statistics display (when enabled with `--stats`)
- Message parsing for different Claude SDK message types: `AssistantMessage`,
  `UserMessage`, `SystemMessage`, `ResultMessage`

## Development Commands

### Running the Application

```bash
uv run main.py
```

Note: cli_tools.py defines CLI argument flags (--stats, --model,
--output-style, --print-raw) but they are not currently wired up in main.py

### Dependencies

Uses `uv` for dependency management. Dependencies are:

- `asyncio>=4.0.0`
- `claude-agent-sdk>=0.1.4`
- `rich>=14.2.0`

Python version: `>=3.13`

### Environment Variables

- `INVENTORY_SUBAGENT_DIRECTORY` - required by inventory-manager sub-agent to
  specify inventory file location
- API credentials loaded via `dotenv` in cli_tools.py:28

## Agent SDK Integration

The application uses Claude Agent SDK's async client pattern:

1. Initialize `ClaudeAgentOptions` with model, system prompt, and agent
   definitions
2. Create `ClaudeSDKClient` context manager
3. Loop: get user input → `client.query()` → iterate `client.receive_response()`
4. Parse and display messages using Rich console

Sub-agents are registered in the `agents` dict of `ClaudeAgentOptions`
(main.py:28-39), each with description, prompt, and model specification.

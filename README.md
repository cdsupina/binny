# Binny

An intelligent CLI inventory management chatbot built with the Claude Agent SDK.

## Overview

Binny is a conversational interface for managing inventory through natural
language. Built on a multi-agent architecture, Binny uses specialized
sub-agents to handle different aspects of inventory management, from naming
physical parts to tracking inventory files.

## Features

- **Natural Language Interface**: Chat with your inventory system using plain English
- **Multi-Agent Architecture**: Specialized sub-agents for different tasks
  - **Part Namer**: Generates standardized names for mechanical and electrical components
  - **McMaster-Carr Searcher**: Search and retrieve parts from McMaster-Carr catalog
  - **Inventory Manager**: Manages inventory files and tracks stock levels
- **Rich Terminal UI**: Color-coded output with syntax highlighting
- **Debug Mode**: View tool usage and session statistics with `--debug` flag

## Prerequisites

- Python 3.13 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Claude Code

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/cdsupina/binny.git
   cd binny
   ```

2. Install dependencies using uv:

   ```bash
   uv sync
   ```

3. Set up your environment variables:

   ```bash
   cp .env.example .env
   ```

4. Edit `.env` and configure required variables (see `.env.example` for all options):

   ```bash
   # Required: Set the directory for inventory files
   BINNY_INVENTORY_DIR=/path/to/your/inventory/files

   # Required: Part namer configuration files
   BINNY_MATERIALS_FILE=/path/to/.config/binny/part_namer/materials.md
   BINNY_PREFIXES_FILE=/path/to/.config/binny/part_namer/prefixes.md

   # Optional: McMaster-Carr integration (if using mmc-searcher)
   # MCMASTER_USERNAME=your-email@example.com
   # MCMASTER_PASSWORD=your-password
   ```

## Usage

Run the application in development mode:

```bash
uv run binny
```

Run with debug mode (shows tool usage and session statistics):

```bash
uv run binny --debug
```

Or install as a global tool:

```bash
uv tool install .
binny
```

To reinstall after making changes:

```bash
uv tool install --reinstall .
```

### Example Interactions

```text
You: I need to add 50 units of M3x10mm screws to inventory
Binny: [Uses inventory-manager to update your inventory files]

You: What should I call this 3-pin connector with 2.54mm pitch?
Binny: [Uses part-namer to suggest a standardized name]
```

## Architecture

### Agent Structure

- **Main Agent (Binny)**: Orchestrates conversations and delegates to sub-agents
- **Sub-agents**:
  - `part-namer`: Specialized in naming physical components following
    engineering conventions
  - `mmc-searcher`: Searches McMaster-Carr catalog for parts and specifications
  - `inventory-manager`: Handles CRUD operations on inventory files

### System Prompts

Custom prompts for each agent are stored in `system_prompts/`:

- `binny_prompt.md` - Main conversational agent
- `part_namer_prompt.md` - Part naming specialist
- `mmc_searcher_prompt.md` - McMaster-Carr catalog search
- `inventory_manager_prompt.md` - Inventory operations

## Development

### Project Structure

```text
binny/
├── binny/                    # Main package
│   ├── __init__.py
│   ├── main.py              # Entry point and agent setup
│   ├── cli_tools.py         # CLI interface and Rich formatting
│   ├── part_namer_tools.py  # MCP tools for part naming
│   └── part_namer_mcp/      # Utility library for part naming
├── system_prompts/          # Agent system prompts
├── .claude/                 # Slash commands
├── pyproject.toml           # Package configuration with entry point
└── CLAUDE.md                # Developer guidance for Claude Code
```

### Dependencies

- `asyncio` - Async runtime
- `claude-agent-sdk` - Claude Agent SDK
- `rich` - Terminal formatting
- `python-dotenv` - Environment variable management

Build system: `hatchling` (configured in `[build-system]` section of pyproject.toml)

## License

MIT License - see [LICENSE](LICENSE) for details

## Acknowledgments

Built with the [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk)
by Anthropic.

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
  - **Inventory Manager**: Manages inventory files and tracks stock levels
- **Rich Terminal UI**: Color-coded output with syntax highlighting
- **Session Statistics**: Track token usage and API calls (optional)

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

4. Edit `.env` and configure:

   ```bash
   # Set the directory for inventory files
   INVENTORY_SUBAGENT_DIRECTORY=/path/to/your/inventory/files
   ```

## Usage

Run the application:

```bash
uv run main.py
```

Run with debug mode:

```bash
uv run main.py --debug
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
  - `inventory-manager`: Handles CRUD operations on inventory files

### System Prompts

Custom prompts for each agent are stored in `system_prompts/`:

- `binny_prompt.md` - Main conversational agent
- `part_namer_prompt.md` - Part naming specialist
- `inventory_manager_prompt.md` - Inventory operations

## Development

### Project Structure

```text
binny/
   main.py              # Main application entry point
   cli_tools.py         # Rich-based CLI interface
   system_prompts/      # Agent system prompts
   pyproject.toml       # Project dependencies
   CLAUDE.md           # Developer guidance for Claude Code
```

### Dependencies

- `asyncio` - Async runtime
- `claude-agent-sdk` - Claude Agent SDK
- `rich` - Terminal formatting

## License

MIT License - see [LICENSE](LICENSE) for details

## Acknowledgments

Built with the [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk)
by Anthropic.

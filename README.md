# Binny

An intelligent TUI inventory management chatbot built with the Claude Agent SDK and Textual.

## Overview

Binny is a conversational interface for managing inventory through natural
language. Built on a multi-agent architecture with a modern terminal user interface,
Binny uses specialized sub-agents to handle different aspects of inventory management,
from naming physical parts to tracking inventory files.

## Features

- **Modern Terminal UI**: Interactive Textual-based TUI with status bar, chat view, and modal dialogs
- **Natural Language Interface**: Chat with your inventory system using plain English
- **Multi-Agent Architecture**: Specialized sub-agents for different tasks
  - **Part Namer**: Generates standardized names with proposal-based approval workflow
  - **McMaster-Carr Searcher**: Search and retrieve parts from McMaster-Carr catalog
  - **Inventory Manager**: Manages inventory files and tracks stock levels
- **Deterministic Approval Workflow**: Interactive modals for approving/rejecting part naming proposals
- **Clipboard Support**: Copy assistant responses or entire chat with keyboard shortcuts
- **Color-Coded Output**: Rich formatting with syntax highlighting
- **Debug Mode**: View tool usage and session statistics with `Ctrl+D` toggle

### Keyboard Shortcuts

- **`Ctrl+C`**: Quit (clean exit)
- **`Ctrl+Y`**: Copy last assistant response to clipboard
- **`Ctrl+L`**: Copy entire chat to clipboard
- **`Ctrl+D`**: Toggle debug mode
- **`Ctrl+R`**: Review all pending proposals

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

You: Name this M8x20mm socket head cap screw in 18-8 stainless steel
Binny: [Uses part-namer to generate standardized name]
      [If prefix/material not tracked, shows interactive approval modal]
      [User approves via modal buttons: Approve/Reject/Edit/Defer]
      Result: SCREW-SS118-M8-20

You: Search McMaster-Carr for metric washers
Binny: [Uses mmc-searcher to find parts and specifications]
```

### UI Features

- **Status Bar**: Shows pending proposal count (clickable to review)
- **Chat View**: Scrollable color-coded message panels
- **Proposal Modals**: Interactive dialogs with button navigation
- **System Messages**: Confirmation messages for all actions
- **Welcome Screen**: Displays help and keyboard shortcuts on startup

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
│   ├── main.py              # Entry point - launches TUI
│   ├── cli_tools.py         # CLI utilities (arg parsing)
│   ├── part_namer_tools.py  # MCP tools for part naming
│   ├── part_namer_mcp/      # Utility library for part naming
│   │   ├── models.py        # TypedDicts for proposals
│   │   └── file_manager.py  # File I/O for prefixes/materials
│   ├── tui/                 # Textual TUI components
│   │   ├── app.py           # Main TUI application
│   │   ├── status_bar.py    # Pending proposal status
│   │   ├── chat_view.py     # Message display
│   │   └── proposal_modal.py # Approval modal dialog
│   └── system_prompts/      # Agent system prompts
├── .claude/                 # Slash commands
├── pyproject.toml           # Package configuration with entry point
└── CLAUDE.md                # Developer guidance for Claude Code
```

### Dependencies

- `asyncio` - Async runtime
- `claude-agent-sdk` - Claude Agent SDK
- `textual` - Modern TUI framework
- `rich` - Terminal formatting
- `python-dotenv` - Environment variable management

Build system: `hatchling` (configured in `[build-system]` section of pyproject.toml)

### Part Naming Workflow

The part-namer agent uses a rigidly controlled naming system:

1. **Validation**: Checks if prefix/material exists in tracking files
2. **Proposal Creation**: If missing, creates a proposal (returns JSON)
3. **TUI Detection**: TUI detects proposal in tool result
4. **Interactive Modal**: Shows modal with Approve/Reject/Edit/Defer buttons
5. **Deterministic Action**: User clicks button → TUI calls MCP tool directly
6. **File Update**: Approved items written to markdown files in H2 format

**Key Features:**
- No agent interpretation of approval responses
- All approval logic handled by TUI
- Proposals stored in JSONL files
- Can review pending proposals with `Ctrl+R` or click status bar

## License

MIT License - see [LICENSE](LICENSE) for details

## Acknowledgments

Built with the [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk)
by Anthropic.

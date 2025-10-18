# Part Namer MCP Library

Utility library for managing part naming with a proposal-based approval workflow.

## Overview

This library provides the core functionality for rigidly tracking part prefixes and materials used in the Binny part naming system. It implements a proposal workflow where new prefixes and materials must be approved before being added to the tracking files.

The MCP tools are defined in `part_namer_tools.py` (in the main Binny directory) and run as an **embedded SDK MCP server** within the Binny application process.

## Architecture

- **models.py** - TypedDict definitions for proposals and parsed data
- **file_manager.py** - Parse and write H2-based markdown files
- **approval_workflow.py** - Rich panel formatting for proposals

**MCP Tools** (defined in `../part_namer_tools.py`):
- 10 tools using the `@tool` decorator for embedded SDK MCP server

## File Format

### Prefixes File

```markdown
## SCREW

**Description:** Socket head cap screws for mechanical assemblies

**Format:** `SCREW-{MATERIAL}-{THREAD}-{LENGTH}`
```

### Materials File

```markdown
## SS118

**Description:** 18-8 Stainless Steel
```

## MCP Tools

### Read Tools
- `read_prefixes` - Get all tracked prefixes
- `read_materials` - Get all tracked materials

### Proposal Tools
- `propose_prefix` - Create new prefix proposal
- `propose_material` - Create new material proposal

### Approval Tools
- `approve_prefix` - Approve prefix and write to file
- `approve_material` - Approve material and write to file
- `reject_prefix` - Reject prefix proposal
- `reject_material` - Reject material proposal

### List Tools
- `list_prefix_proposals` - List pending prefix proposals
- `list_material_proposals` - List pending material proposals

## Workflow

1. **Part-namer agent** receives part specs from other agents
2. Calls `read_prefixes` to check if prefix exists
3. If missing, calls `propose_prefix` to create proposal
4. User approves/rejects via immediate prompt or `/review-prefixes` command
5. On approval, `approve_prefix` writes to prefixes.md
6. Same process for materials

## Setup

1. **Environment variables** (set in `.env`):
   ```bash
   BINNY_PREFIXES_FILE=~/.config/binny/part_namer/prefixes.md
   BINNY_MATERIALS_FILE=~/.config/binny/part_namer/materials.md
   ```

2. **Config files** (initialized automatically):
   - `~/.config/binny/part_namer/prefixes.md`
   - `~/.config/binny/part_namer/materials.md`
   - `~/.config/binny/part_namer/proposals_prefix.jsonl`
   - `~/.config/binny/part_namer/proposals_material.jsonl`

3. **Run Binny:**
   ```bash
   uv run main.py
   ```

   The embedded MCP server starts automatically with Binny.

## Integration with Binny

The part-namer sub-agent uses these MCP tools to:
1. Validate prefixes/materials exist before generating part names
2. Create proposals when encountering new part types or materials
3. Never invent codes - always check MCP first

Slash commands (`/review-prefixes`, `/review-materials`) allow users to review pending proposals at any time.

## Proposal Storage

Proposals are stored as JSONL files in the same directory as prefixes/materials:
- `proposals_prefix.jsonl` - Pending prefix proposals
- `proposals_material.jsonl` - Pending material proposals

Each proposal includes:
- Unique proposal_id
- Timestamp
- All required fields (prefix/material code, description, reasoning)
- Format template (prefixes only)

## Future Enhancements

- Drive types tracking (same H2 format as materials)
- Bulk import/export tools
- Proposal versioning

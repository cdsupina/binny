"""Part Namer MCP Tools for embedded SDK MCP server.

Provides tools for managing part prefixes and materials with a proposal workflow.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any
import uuid

from claude_agent_sdk import tool

from .part_namer_mcp.models import (
    PrefixProposal,
    MaterialProposal,
)
from .part_namer_mcp.file_manager import (
    parse_prefixes_file,
    parse_materials_file,
    append_prefix_to_file,
    append_material_to_file,
)
from .part_namer_mcp.approval_workflow import (
    format_prefix_proposal,
    format_material_proposal,
    format_approval_prompt,
)

# Get file paths from environment variables with XDG defaults
_default_config_dir = Path.home() / ".config/binny/part_namer"
PREFIXES_FILE = Path(os.getenv("BINNY_PREFIXES_FILE") or _default_config_dir / "prefixes.md")
MATERIALS_FILE = Path(os.getenv("BINNY_MATERIALS_FILE") or _default_config_dir / "materials.md")

# Proposal storage files
PROPOSALS_DIR = PREFIXES_FILE.parent
PREFIX_PROPOSALS_FILE = PROPOSALS_DIR / "proposals_prefix.jsonl"
MATERIAL_PROPOSALS_FILE = PROPOSALS_DIR / "proposals_material.jsonl"


def load_prefix_proposals() -> list[PrefixProposal]:
    """Load all pending prefix proposals from JSONL file."""
    if not PREFIX_PROPOSALS_FILE.exists():
        return []

    proposals = []
    with open(PREFIX_PROPOSALS_FILE, 'r') as f:
        for line in f:
            if line.strip():
                proposals.append(json.loads(line))
    return proposals


def save_prefix_proposal(proposal: PrefixProposal) -> None:
    """Save a prefix proposal to JSONL file."""
    PREFIX_PROPOSALS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PREFIX_PROPOSALS_FILE, 'a') as f:
        f.write(json.dumps(proposal) + '\n')


def remove_prefix_proposal(proposal_id: str) -> bool:
    """Remove a prefix proposal by ID."""
    if not PREFIX_PROPOSALS_FILE.exists():
        return False

    proposals = load_prefix_proposals()
    filtered = [p for p in proposals if p['proposal_id'] != proposal_id]

    if len(filtered) == len(proposals):
        return False

    with open(PREFIX_PROPOSALS_FILE, 'w') as f:
        for proposal in filtered:
            f.write(json.dumps(proposal) + '\n')

    return True


def load_material_proposals() -> list[MaterialProposal]:
    """Load all pending material proposals from JSONL file."""
    if not MATERIAL_PROPOSALS_FILE.exists():
        return []

    proposals = []
    with open(MATERIAL_PROPOSALS_FILE, 'r') as f:
        for line in f:
            if line.strip():
                proposals.append(json.loads(line))
    return proposals


def save_material_proposal(proposal: MaterialProposal) -> None:
    """Save a material proposal to JSONL file."""
    MATERIAL_PROPOSALS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(MATERIAL_PROPOSALS_FILE, 'a') as f:
        f.write(json.dumps(proposal) + '\n')


def remove_material_proposal(proposal_id: str) -> bool:
    """Remove a material proposal by ID."""
    if not MATERIAL_PROPOSALS_FILE.exists():
        return False

    proposals = load_material_proposals()
    filtered = [p for p in proposals if p['proposal_id'] != proposal_id]

    if len(filtered) == len(proposals):
        return False

    with open(MATERIAL_PROPOSALS_FILE, 'w') as f:
        for proposal in filtered:
            f.write(json.dumps(proposal) + '\n')

    return True


# Define tools using the @tool decorator

@tool("read_prefixes", "Read all prefixes from the prefixes file", {})
async def read_prefixes_tool(args: dict[str, Any]) -> dict:
    """Read all tracked prefixes."""
    prefixes = parse_prefixes_file(PREFIXES_FILE)
    return {
        "content": [
            {"type": "text", "text": json.dumps(prefixes, indent=2)}
        ]
    }


@tool("read_materials", "Read all materials from the materials file", {})
async def read_materials_tool(args: dict[str, Any]) -> dict:
    """Read all tracked materials."""
    materials = parse_materials_file(MATERIALS_FILE)
    return {
        "content": [
            {"type": "text", "text": json.dumps(materials, indent=2)}
        ]
    }


@tool(
    "propose_prefix",
    "Create a new prefix proposal",
    {
        "prefix": str,
        "description": str,
        "format_template": str,
        "reasoning": str,
    }
)
async def propose_prefix_tool(args: dict[str, Any]) -> dict:
    """Create a new prefix proposal."""
    proposal_id = f"prefix_{uuid.uuid4().hex[:8]}"
    proposal = PrefixProposal(
        prefix=args["prefix"],
        description=args["description"],
        format_template=args["format_template"],
        reasoning=args["reasoning"],
        timestamp=datetime.now().isoformat(),
        proposal_id=proposal_id,
    )
    save_prefix_proposal(proposal)

    panel_text = format_prefix_proposal(proposal)

    # Add clear marker for proposals
    marker = "🔔 PROPOSAL REQUIRES APPROVAL 🔔\n\n"

    return {
        "content": [
            {"type": "text", "text": f"{marker}{panel_text}"}
        ]
    }


@tool(
    "propose_material",
    "Create a new material proposal",
    {
        "material_code": str,
        "description": str,
        "reasoning": str,
    }
)
async def propose_material_tool(args: dict[str, Any]) -> dict:
    """Create a new material proposal."""
    proposal_id = f"material_{uuid.uuid4().hex[:8]}"
    proposal = MaterialProposal(
        material_code=args["material_code"],
        description=args["description"],
        reasoning=args["reasoning"],
        timestamp=datetime.now().isoformat(),
        proposal_id=proposal_id,
    )
    save_material_proposal(proposal)

    panel_text = format_material_proposal(proposal)

    # Add clear marker for proposals
    marker = "🔔 PROPOSAL REQUIRES APPROVAL 🔔\n\n"

    return {
        "content": [
            {"type": "text", "text": f"{marker}{panel_text}"}
        ]
    }


@tool(
    "approve_prefix",
    "Approve a prefix proposal and add it to the prefixes file",
    {"proposal_id": str}
)
async def approve_prefix_tool(args: dict[str, Any]) -> dict:
    """Approve a prefix proposal."""
    proposal_id = args["proposal_id"]
    proposals = load_prefix_proposals()

    proposal = next((p for p in proposals if p['proposal_id'] == proposal_id), None)
    if not proposal:
        return {
            "content": [
                {"type": "text", "text": f"Error: Proposal {proposal_id} not found"}
            ]
        }

    success = append_prefix_to_file(PREFIXES_FILE, proposal)
    if not success:
        return {
            "content": [
                {"type": "text", "text": "Error: Failed to write to prefixes file"}
            ]
        }

    remove_prefix_proposal(proposal_id)

    return {
        "content": [
            {"type": "text", "text": f"✓ Prefix '{proposal['prefix']}' approved and added to {PREFIXES_FILE}"}
        ]
    }


@tool(
    "approve_material",
    "Approve a material proposal and add it to the materials file",
    {"proposal_id": str}
)
async def approve_material_tool(args: dict[str, Any]) -> dict:
    """Approve a material proposal."""
    proposal_id = args["proposal_id"]
    proposals = load_material_proposals()

    proposal = next((p for p in proposals if p['proposal_id'] == proposal_id), None)
    if not proposal:
        return {
            "content": [
                {"type": "text", "text": f"Error: Proposal {proposal_id} not found"}
            ]
        }

    success = append_material_to_file(MATERIALS_FILE, proposal)
    if not success:
        return {
            "content": [
                {"type": "text", "text": "Error: Failed to write to materials file"}
            ]
        }

    remove_material_proposal(proposal_id)

    return {
        "content": [
            {"type": "text", "text": f"✓ Material '{proposal['material_code']}' approved and added to {MATERIALS_FILE}"}
        ]
    }


@tool(
    "reject_prefix",
    "Reject a prefix proposal",
    {"proposal_id": str}
)
async def reject_prefix_tool(args: dict[str, Any]) -> dict:
    """Reject a prefix proposal."""
    proposal_id = args["proposal_id"]
    success = remove_prefix_proposal(proposal_id)

    if success:
        return {
            "content": [
                {"type": "text", "text": f"✓ Prefix proposal {proposal_id} rejected"}
            ]
        }
    else:
        return {
            "content": [
                {"type": "text", "text": f"Error: Proposal {proposal_id} not found"}
            ]
        }


@tool(
    "reject_material",
    "Reject a material proposal",
    {"proposal_id": str}
)
async def reject_material_tool(args: dict[str, Any]) -> dict:
    """Reject a material proposal."""
    proposal_id = args["proposal_id"]
    success = remove_material_proposal(proposal_id)

    if success:
        return {
            "content": [
                {"type": "text", "text": f"✓ Material proposal {proposal_id} rejected"}
            ]
        }
    else:
        return {
            "content": [
                {"type": "text", "text": f"Error: Proposal {proposal_id} not found"}
            ]
        }


@tool("list_prefix_proposals", "List all pending prefix proposals", {})
async def list_prefix_proposals_tool(args: dict[str, Any]) -> dict:
    """List all pending prefix proposals."""
    proposals = load_prefix_proposals()

    if not proposals:
        return {
            "content": [
                {"type": "text", "text": "No pending prefix proposals"}
            ]
        }

    formatted = []
    for proposal in proposals:
        formatted.append(format_prefix_proposal(proposal))

    return {
        "content": [
            {"type": "text", "text": "\n\n".join(formatted)}
        ]
    }


@tool("list_material_proposals", "List all pending material proposals", {})
async def list_material_proposals_tool(args: dict[str, Any]) -> dict:
    """List all pending material proposals."""
    proposals = load_material_proposals()

    if not proposals:
        return {
            "content": [
                {"type": "text", "text": "No pending material proposals"}
            ]
        }

    formatted = []
    for proposal in proposals:
        formatted.append(format_material_proposal(proposal))

    return {
        "content": [
            {"type": "text", "text": "\n\n".join(formatted)}
        ]
    }


# Export all tool functions for create_sdk_mcp_server
PART_NAMER_TOOLS = [
    read_prefixes_tool,
    read_materials_tool,
    propose_prefix_tool,
    propose_material_tool,
    approve_prefix_tool,
    approve_material_tool,
    reject_prefix_tool,
    reject_material_tool,
    list_prefix_proposals_tool,
    list_material_proposals_tool,
]

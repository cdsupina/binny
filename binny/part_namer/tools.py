"""Part Namer MCP Tools for embedded SDK MCP server.

Provides tools for managing part prefixes and materials with a proposal workflow.
Uses a registry pattern and tool factory to eliminate code duplication.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, TypeVar, Generic, Callable
from enum import Enum
import uuid

from claude_agent_sdk import tool

from .models import (
    PrefixProposal,
    MaterialProposal,
    Prefix,
    Material,
)
from .file_manager import (
    parse_prefixes_file,
    parse_materials_file,
    append_prefix_to_file,
    append_material_to_file,
)

# Get file paths from environment variables with XDG defaults
_default_config_dir = Path.home() / ".config/binny/part_namer"
PREFIXES_FILE = Path(os.getenv("BINNY_PREFIXES_FILE") or _default_config_dir / "prefixes.md")
MATERIALS_FILE = Path(os.getenv("BINNY_MATERIALS_FILE") or _default_config_dir / "materials.md")

# Proposal storage files
PROPOSALS_DIR = PREFIXES_FILE.parent
PREFIX_PROPOSALS_FILE = PROPOSALS_DIR / "proposals_prefix.jsonl"
MATERIAL_PROPOSALS_FILE = PROPOSALS_DIR / "proposals_material.jsonl"


# Proposal type enumeration
class ProposalType(Enum):
    """Types of proposals supported by the system."""
    PREFIX = "prefix"
    MATERIAL = "material"


# Generic proposal manager
T = TypeVar('T', PrefixProposal, MaterialProposal)


class ProposalManager(Generic[T]):
    """Generic manager for proposal CRUD operations."""

    def __init__(
        self,
        proposal_type: str,
        proposals_file: Path,
        data_file: Path,
        parse_fn: Callable[[Path], list],
        append_fn: Callable[[Path, T], bool],
        id_field: str,  # 'prefix' or 'material_code'
    ):
        self.type = proposal_type
        self.proposals_file = proposals_file
        self.data_file = data_file
        self.parse_fn = parse_fn
        self.append_fn = append_fn
        self.id_field = id_field

    def load_proposals(self) -> list[T]:
        """Load all pending proposals from JSONL file."""
        if not self.proposals_file.exists():
            return []

        proposals = []
        with open(self.proposals_file, 'r') as f:
            for line in f:
                if line.strip():
                    proposals.append(json.loads(line))
        return proposals

    def save_proposal(self, proposal: T) -> None:
        """Save a proposal to JSONL file."""
        self.proposals_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.proposals_file, 'a') as f:
            f.write(json.dumps(proposal) + '\n')

    def remove_proposal(self, proposal_id: str) -> bool:
        """Remove a proposal by ID."""
        if not self.proposals_file.exists():
            return False

        proposals = self.load_proposals()
        filtered = [p for p in proposals if p['proposal_id'] != proposal_id]

        if len(filtered) == len(proposals):
            return False

        with open(self.proposals_file, 'w') as f:
            for proposal in filtered:
                f.write(json.dumps(proposal) + '\n')

        return True

    def update_proposal(self, proposal_id: str, updates: dict) -> T | None:
        """Update a proposal by ID with new field values."""
        if not self.proposals_file.exists():
            return None

        proposals = self.load_proposals()
        updated_proposal = None

        for proposal in proposals:
            if proposal['proposal_id'] == proposal_id:
                # Update fields that are provided
                for key, value in updates.items():
                    if key in proposal:
                        proposal[key] = value

                # Update timestamp
                proposal['timestamp'] = datetime.now().isoformat()
                updated_proposal = proposal
                break

        if not updated_proposal:
            return None

        # Write back all proposals
        with open(self.proposals_file, 'w') as f:
            for proposal in proposals:
                f.write(json.dumps(proposal) + '\n')

        return updated_proposal

    def approve_proposal(self, proposal_id: str) -> tuple[bool, str, dict | None]:
        """Approve a proposal and add it to the data file.

        Returns:
            (success, message, proposal)
        """
        proposals = self.load_proposals()

        proposal = next((p for p in proposals if p['proposal_id'] == proposal_id), None)
        if not proposal:
            return False, f"Error: Proposal {proposal_id} not found", None

        success = self.append_fn(self.data_file, proposal)
        if not success:
            return False, f"Error: Failed to write to {self.type} file", None

        self.remove_proposal(proposal_id)

        item_id = proposal.get(self.id_field, 'unknown')
        return True, f"✓ {self.type.capitalize()} '{item_id}' approved and added to {self.data_file}", proposal

    def reject_proposal(self, proposal_id: str) -> tuple[bool, str]:
        """Reject a proposal.

        Returns:
            (success, message)
        """
        success = self.remove_proposal(proposal_id)
        if not success:
            return False, f"Error: Proposal {proposal_id} not found"
        return True, f"✓ {self.type.capitalize()} proposal rejected"

    def read_data(self) -> list:
        """Read all tracked items from the data file."""
        return self.parse_fn(self.data_file)


# Manager configuration registry
MANAGER_CONFIG = {
    ProposalType.PREFIX: {
        "proposals_file": PREFIX_PROPOSALS_FILE,
        "data_file": PREFIXES_FILE,
        "parse_fn": parse_prefixes_file,
        "append_fn": append_prefix_to_file,
        "id_field": "prefix",
        "proposal_class": PrefixProposal,
        "schema": {
            "prefix": str,
            "description": str,
            "format_template": str,
            "reasoning": str,
        },
        "valid_update_fields": {'prefix', 'description', 'format_template', 'reasoning'},
    },
    ProposalType.MATERIAL: {
        "proposals_file": MATERIAL_PROPOSALS_FILE,
        "data_file": MATERIALS_FILE,
        "parse_fn": parse_materials_file,
        "append_fn": append_material_to_file,
        "id_field": "material_code",
        "proposal_class": MaterialProposal,
        "schema": {
            "material_code": str,
            "description": str,
            "reasoning": str,
        },
        "valid_update_fields": {'material_code', 'description', 'reasoning'},
    },
}

# Create manager instances
MANAGERS = {
    proposal_type: ProposalManager(
        proposal_type=proposal_type.value,
        proposals_file=config["proposals_file"],
        data_file=config["data_file"],
        parse_fn=config["parse_fn"],
        append_fn=config["append_fn"],
        id_field=config["id_field"],
    )
    for proposal_type, config in MANAGER_CONFIG.items()
}


def create_tools_for_type(proposal_type: ProposalType) -> dict[str, Any]:
    """Factory function to create all MCP tools for a proposal type.

    Args:
        proposal_type: The type of proposal (PREFIX or MATERIAL)

    Returns:
        Dictionary mapping tool names to tool objects
    """
    manager = MANAGERS[proposal_type]
    config = MANAGER_CONFIG[proposal_type]
    type_name = proposal_type.value

    # Read tool
    @tool(f"read_{type_name}s", f"Read all {type_name}s from the {type_name}s file", {})
    async def read_tool(args: dict[str, Any]) -> dict:
        items = manager.read_data()
        return {"content": [{"type": "text", "text": json.dumps(items, indent=2)}]}

    # Propose tool
    @tool(f"propose_{type_name}", f"Create a new {type_name} proposal", config["schema"])
    async def propose_tool(args: dict[str, Any]) -> dict:
        proposal_id = f"{type_name}_{uuid.uuid4().hex[:8]}"
        proposal = config["proposal_class"](
            **args,
            timestamp=datetime.now().isoformat(),
            proposal_id=proposal_id,
            status="pending",
        )
        manager.save_proposal(proposal)
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "type": "proposal",
                    "proposal_type": type_name,
                    "data": proposal
                }, indent=2)
            }]
        }

    # Approve tool
    @tool(f"approve_{type_name}", f"Approve a {type_name} proposal and add it to the {type_name}s file", {"proposal_id": str})
    async def approve_tool(args: dict[str, Any]) -> dict:
        success, message, _ = manager.approve_proposal(args["proposal_id"])
        return {"content": [{"type": "text", "text": message}]}

    # Reject tool
    @tool(f"reject_{type_name}", f"Reject a {type_name} proposal", {"proposal_id": str})
    async def reject_tool(args: dict[str, Any]) -> dict:
        success, message = manager.reject_proposal(args["proposal_id"])
        return {"content": [{"type": "text", "text": message}]}

    # Update tool
    @tool(
        f"update_{type_name}_proposal",
        f"Update a {type_name} proposal with new field values",
        {"proposal_id": str, "updates": dict}
    )
    async def update_tool(args: dict[str, Any]) -> dict:
        proposal_id = args["proposal_id"]
        updates = args["updates"]

        # Validate updates contain only valid fields
        valid_fields = config["valid_update_fields"]
        invalid_fields = set(updates.keys()) - valid_fields
        if invalid_fields:
            return {
                "content": [{
                    "type": "text",
                    "text": f"Error: Invalid fields in updates: {', '.join(invalid_fields)}"
                }]
            }

        updated_proposal = manager.update_proposal(proposal_id, updates)
        if not updated_proposal:
            return {"content": [{"type": "text", "text": f"Error: Proposal {proposal_id} not found"}]}

        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "type": "proposal",
                    "proposal_type": type_name,
                    "data": updated_proposal
                }, indent=2)
            }]
        }

    # List tool
    @tool(f"list_{type_name}_proposals", f"List all pending {type_name} proposals", {})
    async def list_tool(args: dict[str, Any]) -> dict:
        proposals = manager.load_proposals()
        return {"content": [{"type": "text", "text": json.dumps(proposals, indent=2)}]}

    return {
        "read": read_tool,
        "propose": propose_tool,
        "approve": approve_tool,
        "reject": reject_tool,
        "update": update_tool,
        "list": list_tool,
    }


# Generate all tools
_prefix_tools = create_tools_for_type(ProposalType.PREFIX)
_material_tools = create_tools_for_type(ProposalType.MATERIAL)

# Export individual tool objects (for TUI to call .handler() on them)
read_prefixes_tool = _prefix_tools["read"]
propose_prefix_tool = _prefix_tools["propose"]
approve_prefix_tool = _prefix_tools["approve"]
reject_prefix_tool = _prefix_tools["reject"]
update_prefix_tool = _prefix_tools["update"]
list_prefix_proposals_tool = _prefix_tools["list"]

read_materials_tool = _material_tools["read"]
propose_material_tool = _material_tools["propose"]
approve_material_tool = _material_tools["approve"]
reject_material_tool = _material_tools["reject"]
update_material_tool = _material_tools["update"]
list_material_proposals_tool = _material_tools["list"]

# Collect all tools for MCP server registration
PART_NAMER_TOOLS = [
    read_prefixes_tool,
    read_materials_tool,
    propose_prefix_tool,
    propose_material_tool,
    approve_prefix_tool,
    approve_material_tool,
    reject_prefix_tool,
    reject_material_tool,
    update_prefix_tool,
    update_material_tool,
    list_prefix_proposals_tool,
    list_material_proposals_tool,
]

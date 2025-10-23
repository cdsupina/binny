"""Part Namer package for managing part prefixes and materials.

Provides MCP tools and utilities for the part naming workflow with proposal-based
approval system.
"""

__version__ = "0.1.0"

from .tools import (
    # Core registry
    ProposalType,
    MANAGERS,
    PART_NAMER_TOOLS,
    # Individual tool objects (for calling .handler() directly)
    approve_prefix_tool,
    approve_material_tool,
    reject_prefix_tool,
    reject_material_tool,
    read_prefixes_tool,
    read_materials_tool,
    propose_prefix_tool,
    propose_material_tool,
    update_prefix_tool,
    update_material_tool,
    list_prefix_proposals_tool,
    list_material_proposals_tool,
)

from .models import (
    PrefixProposal,
    MaterialProposal,
    Prefix,
    Material,
)

__all__ = [
    "__version__",
    # Registry and enum
    "ProposalType",
    "MANAGERS",
    "PART_NAMER_TOOLS",
    # Tool objects
    "approve_prefix_tool",
    "approve_material_tool",
    "reject_prefix_tool",
    "reject_material_tool",
    "read_prefixes_tool",
    "read_materials_tool",
    "propose_prefix_tool",
    "propose_material_tool",
    "update_prefix_tool",
    "update_material_tool",
    "list_prefix_proposals_tool",
    "list_material_proposals_tool",
    # Models
    "PrefixProposal",
    "MaterialProposal",
    "Prefix",
    "Material",
]

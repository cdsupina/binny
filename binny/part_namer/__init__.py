"""Part Namer package for managing part prefixes and materials.

Provides MCP tools and utilities for the part naming workflow with proposal-based
approval system.
"""

__version__ = "0.1.0"

from .tools import (
    PART_NAMER_TOOLS,
    load_prefix_proposals,
    load_material_proposals,
    approve_prefix_tool,
    approve_material_tool,
    reject_prefix_tool,
    reject_material_tool,
)

from .models import (
    PrefixProposal,
    MaterialProposal,
    Prefix,
    Material,
)

__all__ = [
    "__version__",
    "PART_NAMER_TOOLS",
    "load_prefix_proposals",
    "load_material_proposals",
    "approve_prefix_tool",
    "approve_material_tool",
    "reject_prefix_tool",
    "reject_material_tool",
    "PrefixProposal",
    "MaterialProposal",
    "Prefix",
    "Material",
]

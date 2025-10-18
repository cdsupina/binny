"""Type definitions for the part namer MCP server."""

from typing import TypedDict, Literal


class PrefixProposal(TypedDict):
    """Proposal for a new part prefix.

    Prefixes are stored as H2 headers in the prefixes file.
    """
    prefix: str              # e.g., "SCREW"
    description: str         # Brief description of the part type
    format_template: str     # Format string, e.g., "SCREW-{MATERIAL}-{THREAD}-{LENGTH}"
    reasoning: str          # Why this prefix is needed
    timestamp: str
    proposal_id: str        # Unique identifier for this proposal


class MaterialProposal(TypedDict):
    """Proposal for a new material code.

    Materials are stored as H2 headers in the materials file.
    """
    material_code: str       # e.g., "SS118", "ALU6061"
    description: str         # Full name and description
    reasoning: str          # Why this material is needed
    timestamp: str
    proposal_id: str        # Unique identifier for this proposal


class Prefix(TypedDict):
    """A parsed prefix from the prefixes file."""
    prefix: str
    description: str
    format_template: str


class Material(TypedDict):
    """A parsed material from the materials file."""
    material_code: str
    description: str


# Type alias for approval actions
ApprovalAction = Literal['approve', 'reject', 'defer']

"""Approval workflow UI for proposals using Rich formatting."""

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich import box

from .models import PrefixProposal, MaterialProposal

console = Console()


def format_prefix_proposal(proposal: PrefixProposal) -> str:
    """Format a prefix proposal as a Rich panel string.

    Args:
        proposal: The prefix proposal to format

    Returns:
        Markdown-formatted string for Rich display
    """
    content = f"""**Prefix:** `{proposal['prefix']}`

**Description:** {proposal['description']}

**Format Template:** `{proposal['format_template']}`

**Reasoning:**
{proposal['reasoning']}

**Proposal ID:** `{proposal['proposal_id']}`
"""

    panel = Panel(
        Markdown(content),
        title="[bold cyan]Prefix Proposal[/bold cyan]",
        border_style="cyan",
        box=box.ROUNDED
    )

    # Render to string using console
    with console.capture() as capture:
        console.print(panel)

    return capture.get()


def format_material_proposal(proposal: MaterialProposal) -> str:
    """Format a material proposal as a Rich panel string.

    Args:
        proposal: The material proposal to format

    Returns:
        Markdown-formatted string for Rich display
    """
    content = f"""**Material Code:** `{proposal['material_code']}`

**Description:** {proposal['description']}

**Reasoning:**
{proposal['reasoning']}

**Proposal ID:** `{proposal['proposal_id']}`
"""

    panel = Panel(
        Markdown(content),
        title="[bold cyan]Material Proposal[/bold cyan]",
        border_style="cyan",
        box=box.ROUNDED
    )

    # Render to string using console
    with console.capture() as capture:
        console.print(panel)

    return capture.get()


def format_approval_prompt() -> str:
    """Format the approval prompt text.

    Returns:
        Formatted prompt string
    """
    prompt = """
[bold yellow]Actions:[/bold yellow]
  [green]approve[/green] - Add this entry to the file
  [red]reject[/red]  - Discard this proposal
  [dim]defer[/dim]   - Save for later review

What would you like to do? (approve/reject/defer)
"""
    return prompt

"""Proposal modal for interactive approval workflow."""

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Static, Label
from textual.containers import Container, Horizontal, Vertical
from textual.binding import Binding
from rich.panel import Panel
from rich.markdown import Markdown


class ProposalModal(ModalScreen[str]):
    """Modal dialog for approving/rejecting/editing/deferring proposals."""

    BINDINGS = [
        Binding("escape", "dismiss_defer", "Defer", show=False),
    ]

    DEFAULT_CSS = """
    ProposalModal {
        align: center middle;
    }

    #proposal-container {
        width: 80;
        height: auto;
        max-height: 90%;
        background: $surface;
        border: thick $accent;
        padding: 1;
    }

    #proposal-content {
        width: 100%;
        height: auto;
        max-height: 15;
        overflow-y: auto;
        margin-bottom: 1;
        padding: 1;
        background: $panel;
        border: round $primary;
    }

    #button-container {
        width: 100%;
        height: auto;
        align: center middle;
    }

    #button-container Horizontal {
        width: auto;
        height: auto;
        align: center middle;
    }

    Button {
        margin: 0 1;
        min-width: 10;
    }
    """

    def __init__(self, proposal_data: dict, proposal_type: str):
        """Initialize the proposal modal.

        Args:
            proposal_data: The proposal data dictionary
            proposal_type: Either "prefix" or "material"
        """
        super().__init__()
        self.proposal_data = proposal_data
        self.proposal_type = proposal_type

    def compose(self) -> ComposeResult:
        """Compose the modal content."""
        with Container(id="proposal-container"):
            yield Static(Markdown(self._format_proposal()), id="proposal-content")
            with Horizontal(id="button-container"):
                yield Button("Approve", id="approve", variant="success")
                yield Button("Reject", id="reject", variant="error")
                yield Button("Edit", id="edit", variant="primary")
                yield Button("Defer", id="defer", variant="default")

    def _format_proposal(self) -> str:
        """Format the proposal data for display."""
        if self.proposal_type == "prefix":
            return self._format_prefix_proposal()
        else:
            return self._format_material_proposal()

    def _format_prefix_proposal(self) -> str:
        """Format a prefix proposal."""
        content = f"""**Prefix Proposal**

**Prefix:** `{self.proposal_data['prefix']}`

**Description:** {self.proposal_data['description']}

**Format Template:** `{self.proposal_data['format_template']}`

**Reasoning:**
{self.proposal_data['reasoning']}

**Proposal ID:** `{self.proposal_data['proposal_id']}`
"""
        return content

    def _format_material_proposal(self) -> str:
        """Format a material proposal."""
        content = f"""**Material Proposal**

**Material Code:** `{self.proposal_data['material_code']}`

**Description:** {self.proposal_data['description']}

**Reasoning:**
{self.proposal_data['reasoning']}

**Proposal ID:** `{self.proposal_data['proposal_id']}`
"""
        return content

    def on_mount(self) -> None:
        """Set initial focus when modal mounts."""
        # Focus the first button (Approve) by default
        approve_button = self.query_one("#approve", Button)
        approve_button.focus()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        if button_id:
            self.dismiss(button_id)

    def key_left(self) -> None:
        """Move focus to previous button with left arrow."""
        self.focus_previous()

    def key_right(self) -> None:
        """Move focus to next button with right arrow."""
        self.focus_next()

    def key_space(self) -> None:
        """Activate focused button with space bar."""
        # Get the currently focused widget
        focused = self.focused
        if isinstance(focused, Button):
            # Trigger the button press
            self.post_message(Button.Pressed(focused))

    def action_dismiss_defer(self) -> None:
        """Dismiss modal with defer action on Escape key."""
        self.dismiss("defer")

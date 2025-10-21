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
        border: none;
        outline: none;
    }

    #proposal-container {
        width: 90;
        height: auto;
        max-height: 90%;
        background: $surface;
        border: round $accent;
        padding: 1;
    }

    #proposal-header {
        width: 100%;
        text-align: center;
        margin-bottom: 1;
        color: $accent;
    }

    #proposal-content {
        width: 100%;
        height: auto;
        max-height: 15;
        overflow-y: auto;
        margin-bottom: 1;
        padding: 1;
        background: $panel;
    }

    #button-container {
        width: 100%;
        height: auto;
        align: center middle;
        margin-bottom: 1;
    }

    #button-container Horizontal {
        width: auto;
        height: auto;
    }

    #button-container Button {
        margin: 0 5;
        min-width: 14;
        max-width: 14;
        content-align: center middle;
        text-align: center;
    }

    #button-container Button:first-of-type {
        margin-left: 0;
    }

    #button-container Button:last-of-type {
        margin-right: 0;
    }

    #confirm-button {
        content-align: center middle;
        text-align: center;
    }

    .action-selected {
        text-style: bold;
        border: thick $accent;
    }

    #shortcuts-footer {
        width: 100%;
        height: auto;
        text-align: center;
        color: $text-muted;
        border-top: solid $primary;
        padding-top: 1;
    }
    """

    def __init__(
        self,
        proposal_data: dict,
        proposal_type: str,
        all_proposals: list[tuple[str, dict]] | None = None,
        current_index: int = 0,
    ):
        """Initialize the proposal modal.

        Args:
            proposal_data: The proposal data dictionary
            proposal_type: Either "prefix" or "material"
            all_proposals: List of all (type, data) tuples for navigation
            current_index: Current index in all_proposals list
        """
        super().__init__()
        self.proposal_data = proposal_data
        self.proposal_type = proposal_type
        self.all_proposals = all_proposals or [(proposal_type, proposal_data)]
        self.current_index = current_index
        # Track actions for each proposal (index -> action)
        self.proposal_actions: dict[int, str] = {}

    def compose(self) -> ComposeResult:
        """Compose the modal content."""
        with Container(id="proposal-container"):
            # Show proposal counter if multiple proposals
            if len(self.all_proposals) > 1:
                yield Static(
                    self._format_header(),
                    id="proposal-header"
                )
            yield Static(Markdown(self._format_proposal()), id="proposal-content")
            with Container(id="button-container"):
                with Horizontal():
                    yield Button("Approve", id="approve", variant="success")
                    yield Button("Reject", id="reject", variant="error")
                    yield Button("Edit", id="edit", variant="warning")
                    # Confirm button for multiple proposals
                    if len(self.all_proposals) > 1:
                        yield Button("Confirm", id="confirm-button", variant="primary")
            # Footer with shortcuts for multiple proposals
            if len(self.all_proposals) > 1:
                yield Static(
                    "↑↓: Navigate | Tab/←→: Select | Space/Enter: Mark | Esc: Cancel All",
                    id="shortcuts-footer"
                )

    def _format_header(self) -> str:
        """Format the header with proposal count and current action."""
        header = f"Proposal {self.current_index + 1} of {len(self.all_proposals)}"
        if self.current_index in self.proposal_actions:
            action = self.proposal_actions[self.current_index]
            header += f" - Action: {action.upper()}"
        return header

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
        # Update action button states
        self.update_action_buttons()

        # Focus the first button (Approve) by default
        approve_button = self.query_one("#approve", Button)
        approve_button.focus()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        # Handle confirm button
        if button_id == "confirm-button":
            # Submit all actions
            self.dismiss(self.proposal_actions)
        elif button_id in ["approve", "reject", "edit"]:
            # For single proposal, dismiss immediately
            if len(self.all_proposals) == 1:
                self.dismiss(button_id)
            else:
                # For multiple proposals, mark the action
                self.mark_action(button_id)
        elif button_id:
            self.dismiss(button_id)

    def mark_action(self, action: str) -> None:
        """Mark an action for the current proposal."""
        # Store the action
        self.proposal_actions[self.current_index] = action

        # Update visual feedback
        self.update_action_buttons()

        # Update the header
        try:
            header = self.query_one("#proposal-header", Static)
            header.update(self._format_header())
        except:
            pass

    def update_action_buttons(self) -> None:
        """Update the visual state of action buttons."""
        current_action = self.proposal_actions.get(self.current_index)

        for action_id in ["approve", "reject", "edit"]:
            try:
                button = self.query_one(f"#{action_id}", Button)
                if action_id == current_action:
                    button.add_class("action-selected")
                else:
                    button.remove_class("action-selected")
            except:
                pass

    def navigate_previous(self) -> None:
        """Navigate to the previous proposal."""
        if self.current_index > 0:
            self.current_index -= 1
            self.update_proposal()

    def navigate_next(self) -> None:
        """Navigate to the next proposal."""
        if self.current_index < len(self.all_proposals) - 1:
            self.current_index += 1
            self.update_proposal()

    def update_proposal(self) -> None:
        """Update the modal to show the current proposal."""
        # Get the current proposal
        self.proposal_type, self.proposal_data = self.all_proposals[self.current_index]

        # Update the header if it exists
        try:
            header = self.query_one("#proposal-header", Static)
            header.update(self._format_header())
        except:
            pass

        # Update the proposal content
        content_widget = self.query_one("#proposal-content", Static)
        content_widget.update(Markdown(self._format_proposal()))

        # Update action button states
        self.update_action_buttons()

    def key_left(self) -> None:
        """Move focus to previous button with left arrow."""
        self.focus_previous()

    def key_right(self) -> None:
        """Move focus to next button with right arrow."""
        self.focus_next()

    def key_up(self) -> None:
        """Navigate to previous proposal with up arrow."""
        if len(self.all_proposals) > 1:
            self.navigate_previous()
        else:
            self.focus_previous()

    def key_down(self) -> None:
        """Navigate to next proposal with down arrow."""
        if len(self.all_proposals) > 1:
            self.navigate_next()
        else:
            self.focus_next()

    def key_space(self) -> None:
        """Activate focused button with space bar."""
        # Get the currently focused widget
        focused = self.focused
        if isinstance(focused, Button):
            # Trigger the button press
            self.post_message(Button.Pressed(focused))

    def action_dismiss_defer(self) -> None:
        """Dismiss modal on Escape key."""
        # For single proposal, defer it
        if len(self.all_proposals) == 1:
            self.dismiss("defer")
        else:
            # For multiple proposals, cancel the entire batch review
            self.dismiss(None)

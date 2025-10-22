"""Proposal modal for interactive approval workflow."""

import os
import re
from pathlib import Path

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Static, Label, Input
from textual.widgets import Markdown as MarkdownWidget
from textual.containers import Container, Horizontal, Vertical
from textual.binding import Binding
from textual.reactive import reactive


class ProposalModal(ModalScreen[str]):
    """Modal dialog for approving/rejecting/editing/deferring proposals."""

    BINDINGS = [
        Binding("escape", "dismiss_defer", "Defer", show=False),
        Binding("r", "toggle_reference", "Reference", show=True),
        Binding("ctrl+f", "toggle_search", "Find", show=True),
    ]

    # Reactive attributes for reference viewer
    show_reference: reactive[bool] = reactive(False)
    show_search: reactive[bool] = reactive(False)

    DEFAULT_CSS = """
    ProposalModal {
        align: center middle;
        border: none;
        outline: none;
    }

    #main-layout {
        width: 100%;
        height: 100%;
        align: center middle;
        padding: 0 2;
    }

    #proposal-container {
        width: 50%;
        min-width: 40;
        height: 90%;
        background: $surface;
        border: round $accent;
        padding: 1;
    }

    /* When reference is shown, adjust proposal container */
    ProposalModal.show-reference #main-layout {
        align: left middle;
    }

    ProposalModal.show-reference #proposal-container {
        margin-right: 2;
    }

    /* Reference container - hidden by default */
    #reference-container {
        display: none;
    }

    /* When reference is shown, display it */
    ProposalModal.show-reference #reference-container {
        display: block;
        width: 50%;
        min-width: 30;
        max-width: 50%;
        height: 90%;
        margin-left: 3;
        background: $surface;
        border: round $accent;
        padding: 1;
    }

    #reference-header {
        width: 100%;
        text-align: center;
        margin-bottom: 1;
        color: $accent;
        height: auto;
    }

    #reference-markdown {
        width: 100%;
        height: 1fr;
        overflow-y: auto;
        margin-bottom: 1;
        background: $panel;
        padding: 1;
    }

    #match-counter {
        display: none;
        width: 100%;
        text-align: right;
        color: $text-muted;
        margin-bottom: 1;
        height: auto;
    }

    #reference-search {
        display: none;
        width: 100%;
        margin-bottom: 0;
        height: auto;
    }

    #reference-shortcuts {
        width: 100%;
        text-align: center;
        color: $text-muted;
        border-top: solid $primary;
        padding-top: 1;
        margin-top: 1;
        height: auto;
    }

    /* Show search box and match counter when search is active */
    ProposalModal.show-search #match-counter {
        display: block;
    }

    ProposalModal.show-search #reference-search {
        display: block;
    }

    #proposal-header {
        width: 100%;
        text-align: center;
        margin-bottom: 1;
        color: $accent;
    }

    #decision-summary {
        width: 100%;
        height: auto;
        text-align: center;
        content-align: center middle;
        margin-bottom: 1;
        color: $text-muted;
    }

    #proposal-content {
        width: 100%;
        height: 1fr;
        overflow-y: auto;
        margin-bottom: 1;
        padding: 1;
        background: $panel;
    }

    #button-container {
        width: 100%;
        height: auto;
        align: center middle;
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
        margin-top: 1;
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
        # Reference viewer state
        self.reference_matches: list[dict] = []
        self.current_match_index: int = 0
        self.reference_content: str = ""
        self.reference_title: str = ""

    def compose(self) -> ComposeResult:
        """Compose the modal content."""
        with Horizontal(id="main-layout"):
            # Left side: Proposal container
            with Vertical(id="proposal-container"):
                # Show proposal counter if multiple proposals
                if len(self.all_proposals) > 1:
                    yield Static(
                        self._format_decision_summary(),
                        id="decision-summary"
                    )
                    yield Static(
                        self._format_header(),
                        id="proposal-header"
                    )
                yield MarkdownWidget(self._format_proposal(), id="proposal-content")
                with Container(id="button-container"):
                    with Horizontal():
                        yield Button("Approve", id="approve", variant="success")
                        yield Button("Reject", id="reject", variant="error")
                        yield Button("Edit", id="edit", variant="warning")
                        # Confirm button for multiple proposals
                        if len(self.all_proposals) > 1:
                            yield Button("Confirm", id="confirm-button", variant="primary")
                # Footer with shortcuts
                if len(self.all_proposals) > 1:
                    yield Static(
                        "↑↓: Navigate | Tab/←→: Select | Space/Enter: Mark | R: Reference | Esc: Cancel",
                        id="shortcuts-footer"
                    )
                else:
                    yield Static(
                        "R: Reference | Esc: Defer",
                        id="shortcuts-footer"
                    )

            # Right side: Reference viewer container
            with Vertical(id="reference-container"):
                yield Static(
                    "",
                    id="reference-header"
                )
                yield MarkdownWidget("", id="reference-markdown")
                yield Static("", id="match-counter")
                yield Input(
                    placeholder="Search...",
                    id="reference-search"
                )
                yield Static(
                    "Ctrl+F: Find | Ctrl+J: Next | Ctrl+K: Prev",
                    id="reference-shortcuts"
                )

    def _format_header(self) -> str:
        """Format the header with proposal count and current action."""
        header = f"Proposal {self.current_index + 1} of {len(self.all_proposals)}"
        if self.current_index in self.proposal_actions:
            action = self.proposal_actions[self.current_index]
            header += f" - Action: {action.upper()}"
        return header

    def _format_decision_summary(self) -> str:
        """Format the decision summary line with smart windowing."""
        total = len(self.all_proposals)

        # Action symbols with colors
        symbols = {
            "approve": ("✓", "green"),
            "reject": ("✗", "red"),
            "edit": ("✎", "yellow"),
            None: ("-", "dim")
        }

        # For ≤10 proposals, show all
        if total <= 10:
            parts = []
            for i in range(total):
                action = self.proposal_actions.get(i)
                symbol, color = symbols.get(action, symbols[None])
                if i == self.current_index:
                    parts.append(f"[reverse bold {color}][{i+1}:{symbol}][/reverse bold {color}]")
                else:
                    parts.append(f"[{color}][{i+1}:{symbol}][/{color}]")
            return " ".join(parts)

        # For >10 proposals, show 7 items with current centered when possible
        parts = []
        current = self.current_index
        window_size = 7
        half_window = 3

        # Calculate window bounds, keeping current centered when possible
        start = current - half_window
        end = current + half_window

        # Adjust if window goes out of bounds
        if start < 0:
            start = 0
            end = min(total - 1, window_size - 1)
        elif end >= total:
            end = total - 1
            start = max(0, end - window_size + 1)

        # Show ellipsis at start if there are items before the window
        if start > 0:
            parts.append("[dim]...[/dim]")

        # Show the 7-item window
        for i in range(start, end + 1):
            action = self.proposal_actions.get(i)
            symbol, color = symbols.get(action, symbols[None])
            if i == current:
                parts.append(f"[reverse bold {color}][{i+1}:{symbol}][/reverse bold {color}]")
            else:
                parts.append(f"[{color}][{i+1}:{symbol}][/{color}]")

        # Show ellipsis at end if there are items after the window
        if end < total - 1:
            parts.append("[dim]...[/dim]")

        return " ".join(parts)

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
        """Mark an action for the current proposal (toggle if already set)."""
        # If the same action is already selected, deselect it
        current_action = self.proposal_actions.get(self.current_index)
        if current_action == action:
            # Remove the action (deselect)
            del self.proposal_actions[self.current_index]
        else:
            # Set the new action
            self.proposal_actions[self.current_index] = action

        # Update visual feedback
        self.update_action_buttons()

        # Update the header
        try:
            header = self.query_one("#proposal-header", Static)
            header.update(self._format_header())
        except:
            pass

        # Update the decision summary
        try:
            summary = self.query_one("#decision-summary", Static)
            summary.update(self._format_decision_summary())
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
        # Store previous type to detect changes
        previous_type = self.proposal_type

        # Get the current proposal
        self.proposal_type, self.proposal_data = self.all_proposals[self.current_index]

        # Update the header if it exists
        try:
            header = self.query_one("#proposal-header", Static)
            header.update(self._format_header())
        except:
            pass

        # Update the decision summary
        try:
            summary = self.query_one("#decision-summary", Static)
            summary.update(self._format_decision_summary())
        except:
            pass

        # Update the proposal content
        content_widget = self.query_one("#proposal-content", MarkdownWidget)
        content_widget.update(self._format_proposal())

        # Update action button states
        self.update_action_buttons()

        # If reference panel is shown and proposal type changed, reload the reference file
        if self.show_reference and previous_type != self.proposal_type:
            self.load_reference_file()

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

    def action_toggle_reference(self) -> None:
        """Toggle reference viewer panel."""
        self.show_reference = not self.show_reference

    def watch_show_reference(self, show: bool) -> None:
        """Update UI when reference panel visibility changes."""
        # Update CSS classes
        if show:
            self.add_class("show-reference")
            # Load the reference file
            self.load_reference_file()
        else:
            self.remove_class("show-reference")
            # Hide search when closing reference panel
            self.show_search = False

    def action_toggle_search(self) -> None:
        """Toggle search box visibility (only works when reference is shown)."""
        # Only allow search if reference is shown
        if self.show_reference:
            self.show_search = not self.show_search

    def watch_show_search(self, show: bool) -> None:
        """Update UI when search box visibility changes."""
        if show:
            self.add_class("show-search")
            # Focus the search input
            try:
                search_input = self.query_one("#reference-search", Input)
                search_input.focus()
            except:
                pass
        else:
            self.remove_class("show-search")
            # Clear search and reset view
            try:
                search_input = self.query_one("#reference-search", Input)
                search_input.value = ""
                # Reset to full content view
                self._update_reference_ui(
                    self.reference_title,
                    self.reference_content,
                    ""
                )
                self.reference_matches = []
            except:
                pass
            # Return focus to approve button
            try:
                approve_button = self.query_one("#approve", Button)
                approve_button.focus()
            except:
                pass

    def load_reference_file(self) -> None:
        """Load appropriate markdown file based on proposal type."""
        # Determine which env variable to use
        if self.proposal_type == "prefix":
            env_var = "BINNY_PREFIXES_FILE"
            title = "Prefixes Reference"
        else:
            env_var = "BINNY_MATERIALS_FILE"
            title = "Materials Reference"

        # Store title for later use
        self.reference_title = title

        # Get file path from environment
        file_path_str = os.getenv(env_var)

        if not file_path_str:
            error_msg = f"# Error\n\nEnvironment variable `{env_var}` is not set."
            self.reference_content = error_msg
            self._update_reference_ui(title, error_msg, "")
            return

        file_path = Path(file_path_str)

        if not file_path.exists():
            error_msg = f"# Error\n\nFile not found: `{file_path}`"
            self.reference_content = error_msg
            self._update_reference_ui(title, error_msg, "")
            return

        try:
            content = file_path.read_text()
            self.reference_content = content
            self._update_reference_ui(title, content, "")
            # Parse H2 sections for search
            self.reference_matches = self.parse_h2_sections(content)
        except Exception as e:
            error_msg = f"# Error\n\nFailed to read file: {str(e)}"
            self.reference_content = error_msg
            self._update_reference_ui(title, error_msg, "")

    def _update_reference_ui(self, title: str, content: str, match_info: str) -> None:
        """Update reference viewer UI elements."""
        try:
            header = self.query_one("#reference-header", Static)
            header.update(f"[bold]{title}[/bold]")
        except:
            pass

        try:
            markdown = self.query_one("#reference-markdown", MarkdownWidget)
            markdown.update(content)
        except:
            pass

        try:
            counter = self.query_one("#match-counter", Static)
            counter.update(match_info)
        except:
            pass

    def parse_h2_sections(self, content: str) -> list[dict]:
        """Extract H2 sections for searching.

        Returns list of: {'header': 'SHAFT', 'anchor': 'shaft', 'content': '...'}
        """
        sections = []

        # Split by H2 headers
        parts = re.split(r'^## (.+)$', content, flags=re.MULTILINE)

        # parts[0] is content before first H2 (usually empty or H1)
        # Then alternating: header1, content1, header2, content2, ...
        for i in range(1, len(parts), 2):
            if i + 1 < len(parts):
                header = parts[i].strip()
                section_content = parts[i + 1].strip()

                # Create anchor (lowercase, spaces to hyphens)
                anchor = header.lower().replace(' ', '-')

                sections.append({
                    'header': header,
                    'anchor': anchor,
                    'content': section_content
                })

        return sections

    async def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        # Only handle reference search input
        if event.input.id != "reference-search":
            return

        query = event.value.strip().lower()

        if not query:
            # No search query, show all content
            self._update_reference_ui(
                self.reference_title,
                self.reference_content,
                ""
            )
            return

        # Find all sections matching the query
        all_sections = self.parse_h2_sections(self.reference_content)
        matched_sections = [
            section for section in all_sections
            if query in section['header'].lower() or query in section['content'].lower()
        ]

        if not matched_sections:
            # No matches found
            self._update_reference_ui(
                self.reference_title,
                self.reference_content,
                "[dim]No matches[/dim]"
            )
            self.reference_matches = []
            return

        # Store matches and jump to first one
        self.reference_matches = matched_sections
        self.current_match_index = 0
        self.navigate_to_match(0)

    def navigate_to_match(self, direction: int) -> None:
        """Navigate to next/prev match (direction: +1 for next, -1 for prev, 0 for current)."""
        if not self.reference_matches:
            return

        # Update index
        if direction != 0:
            self.current_match_index = (self.current_match_index + direction) % len(self.reference_matches)

        # Get current match
        match = self.reference_matches[self.current_match_index]

        # Update match counter
        match_info = f"Match {self.current_match_index + 1} of {len(self.reference_matches)}"
        try:
            counter = self.query_one("#match-counter", Static)
            counter.update(match_info)
        except:
            pass

        # Jump to anchor
        try:
            markdown = self.query_one("#reference-markdown", MarkdownWidget)
            markdown.goto_anchor(match['anchor'])
        except Exception:
            pass

    async def on_key(self, event) -> None:
        """Handle keyboard shortcuts globally and for search navigation."""
        # Handle Ctrl+F globally - toggle search when reference is open
        if event.key == "ctrl+f":
            if self.show_reference:
                self.show_search = not self.show_search
                event.prevent_default()
                event.stop()
            return

        # Handle Ctrl+J and Ctrl+K for navigating search results
        if event.key == "ctrl+j":
            if self.reference_matches and self.show_search:
                self.navigate_to_match(1)
                event.prevent_default()
                event.stop()
            return
        elif event.key == "ctrl+k":
            if self.reference_matches and self.show_search:
                self.navigate_to_match(-1)
                event.prevent_default()
                event.stop()
            return

        # Handle Escape when search is focused - close search box
        focused = self.focused
        if isinstance(focused, Input) and focused.id == "reference-search":
            if event.key == "escape":
                self.show_search = False
                event.prevent_default()
                event.stop()

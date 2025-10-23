"""Edit Proposal Modal with mini-chat interface."""

import asyncio
import json
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Static, Input, Label
from textual.widgets import Markdown as MarkdownWidget
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.binding import Binding
from textual.reactive import reactive
from claude_agent_sdk import (
    ClaudeAgentOptions,
    AgentDefinition,
    create_sdk_mcp_server,
)
from claude_agent_sdk.client import ClaudeSDKClient

from ..part_namer import PART_NAMER_TOOLS, __version__ as part_namer_version


class MiniChatMessage(Static):
    """A single message in the mini-chat."""

    def __init__(self, role: str, content: str, **kwargs):
        super().__init__(**kwargs)
        self.role = role
        self.content = content

    def render(self) -> str:
        """Render the message."""
        if self.role == "user":
            return f"[bold yellow]You:[/bold yellow] {self.content}"
        elif self.role == "assistant":
            return f"[bold green]Assistant:[/bold green] {self.content}"
        else:
            return f"[dim]{self.content}[/dim]"


class EditProposalModal(ModalScreen[dict | None]):
    """Modal for editing a proposal with dedicated chat interface."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=True),
    ]

    CSS_PATH = "styles/edit_proposal_modal.tcss"

    def __init__(
        self,
        proposal_data: dict,
        proposal_type: str,
        edit_assistant_prompt: str,
    ):
        """Initialize the edit modal.

        Args:
            proposal_data: The proposal data dictionary
            proposal_type: Either "prefix" or "material"
            edit_assistant_prompt: System prompt for edit assistant
        """
        super().__init__()
        self.proposal_data = proposal_data
        self.proposal_type = proposal_type
        self.proposal_id = proposal_data["proposal_id"]
        self.edit_assistant_prompt = edit_assistant_prompt
        self.client = None
        self.has_updates = False
        self.updated_proposal = None

    def compose(self) -> ComposeResult:
        """Compose the modal content."""
        with Vertical(id="edit-container"):
            # Proposal details section (using Static instead of Markdown for better visibility)
            with ScrollableContainer(id="proposal-details"):
                yield Static(
                    self._format_proposal_details_static(),
                    id="proposal-details-content"
                )

            # Chat area
            with ScrollableContainer(id="chat-area"):
                yield Vertical(id="chat-messages")

            # Input field
            with Container(id="input-container"):
                yield Input(
                    placeholder="Describe what you'd like to change...",
                    id="edit-input"
                )

            # Buttons
            with Container(id="button-container"):
                with Horizontal():
                    yield Button(
                        "Apply Changes",
                        id="apply-button",
                        variant="success",
                        disabled=True
                    )
                    yield Button("Cancel", id="cancel-button", variant="error")

    def _format_proposal_details_static(self) -> str:
        """Format the proposal details for Static widget (with Rich markup)."""
        if self.proposal_type == "prefix":
            return f"""[bold cyan]Editing Prefix Proposal[/bold cyan]

[dim]Proposal ID:[/dim] [yellow]{self.proposal_id}[/yellow]

[bold]Current Values:[/bold]
  [bold green]Prefix:[/bold green] {self.proposal_data['prefix']}
  [bold green]Description:[/bold green] {self.proposal_data['description']}
  [bold green]Format:[/bold green] {self.proposal_data['format_template']}
  [bold green]Reasoning:[/bold green] {self.proposal_data['reasoning']}
"""
        else:
            return f"""[bold cyan]Editing Material Proposal[/bold cyan]

[dim]Proposal ID:[/dim] [yellow]{self.proposal_id}[/yellow]

[bold]Current Values:[/bold]
  [bold green]Material Code:[/bold green] {self.proposal_data['material_code']}
  [bold green]Description:[/bold green] {self.proposal_data['description']}
  [bold green]Reasoning:[/bold green] {self.proposal_data['reasoning']}
"""

    def _format_proposal_details(self) -> str:
        """Format the proposal details for display (kept for backwards compatibility)."""
        if self.proposal_type == "prefix":
            return f"""**Editing Prefix Proposal**

**Proposal ID:** `{self.proposal_id}`

**Current Values:**
- **Prefix:** `{self.proposal_data['prefix']}`
- **Description:** {self.proposal_data['description']}
- **Format:** `{self.proposal_data['format_template']}`
- **Reasoning:** {self.proposal_data['reasoning']}
"""
        else:
            return f"""**Editing Material Proposal**

**Proposal ID:** `{self.proposal_id}`

**Current Values:**
- **Material Code:** `{self.proposal_data['material_code']}`
- **Description:** {self.proposal_data['description']}
- **Reasoning:** {self.proposal_data['reasoning']}
"""

    async def on_mount(self) -> None:
        """Initialize the edit assistant SDK client."""
        try:
            # Create part_namer MCP server
            part_namer_mcp = create_sdk_mcp_server(
                name="part_namer",
                version=part_namer_version,
                tools=PART_NAMER_TOOLS,
            )

            # Build context message with proposal details
            if self.proposal_type == "prefix":
                context = f"""Editing Prefix Proposal (ID: {self.proposal_id})
- Prefix: {self.proposal_data['prefix']}
- Description: {self.proposal_data['description']}
- Format: {self.proposal_data['format_template']}
- Reasoning: {self.proposal_data['reasoning']}
"""
            else:
                context = f"""Editing Material Proposal (ID: {self.proposal_id})
- Material Code: {self.proposal_data['material_code']}
- Description: {self.proposal_data['description']}
- Reasoning: {self.proposal_data['reasoning']}
"""

            # Create SDK client for edit assistant
            full_prompt = self.edit_assistant_prompt + f"\n\n## Current Proposal Context\n\n{context}"

            # Log prompt length for debugging
            prompt_length = len(full_prompt)
            if prompt_length > 10000:
                self.add_chat_message("system", f"Warning: System prompt is {prompt_length} characters (may be too long)")

            options = ClaudeAgentOptions(
                model="haiku",
                system_prompt=full_prompt,
                allowed_tools=[
                    "mcp__part_namer__update_prefix_proposal",
                    "mcp__part_namer__update_material_proposal",
                ],
                mcp_servers={
                    "part_namer": part_namer_mcp,
                },
                env={
                    "MAX_THINKING_TOKENS": "1500",  # Must be >= 1024
                },
            )

            self.client = ClaudeSDKClient(options=options)
            await self.client.__aenter__()

            # Show greeting
            self.add_chat_message("assistant", "How would you like to edit this proposal?")

        except Exception as e:
            import traceback
            error_msg = f"Error initializing: {str(e)}\n{traceback.format_exc()}"
            self.add_chat_message("system", error_msg)

        # Focus the input
        self.query_one("#edit-input", Input).focus()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle user input submission."""
        if event.input.id != "edit-input":
            return

        user_input = event.value
        if not user_input.strip():
            return

        # Clear input
        event.input.value = ""

        # Add user message to chat
        self.add_chat_message("user", user_input)

        # Send to edit assistant
        try:
            if not self.client:
                self.add_chat_message("system", "Error: Edit assistant not initialized")
                return

            await self.client.query(user_input)

            # Process response
            message_count = 0
            async for message in self.client.receive_response():
                message_count += 1
                await self.handle_assistant_message(message)

            # If no messages received, show warning
            if message_count == 0:
                self.add_chat_message("system", "Warning: No response received from assistant")

        except Exception as e:
            import traceback
            error_msg = f"Error sending message:\n{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            self.add_chat_message("system", error_msg)

    async def handle_assistant_message(self, message) -> None:
        """Handle a message from the edit assistant."""
        try:
            # Import message types
            from claude_agent_sdk import AssistantMessage, ResultMessage

            if isinstance(message, AssistantMessage):
                # Extract text content
                content = ""
                if isinstance(message.content, list):
                    for item in message.content:
                        # Handle both dict and TextBlock objects
                        if isinstance(item, dict) and item.get("type") == "text":
                            content += item.get("text", "")
                        elif hasattr(item, 'text'):
                            # Handle TextBlock objects
                            content += item.text
                        elif hasattr(item, '__dict__'):
                            # Try to get text from object dict
                            item_dict = item.__dict__
                            if 'text' in item_dict:
                                content += item_dict['text']
                elif isinstance(message.content, str):
                    content = message.content

                if content.strip():
                    self.add_chat_message("assistant", content)

            elif isinstance(message, ResultMessage):
                # Check if this is an updated proposal
                proposal_info = self.detect_updated_proposal(message)
                if proposal_info:
                    # Proposal was updated!
                    self.has_updates = True
                    self.updated_proposal = proposal_info["data"]

                    # Enable the Apply Changes button
                    apply_button = self.query_one("#apply-button", Button)
                    apply_button.disabled = False

                    # Add confirmation message
                    self.add_chat_message(
                        "system",
                        "✓ Proposal updated. Click 'Apply Changes' to save."
                    )
        except Exception as e:
            import traceback
            error_msg = f"Error: {str(e)}\n{traceback.format_exc()}"
            self.add_chat_message("system", error_msg)

    def detect_updated_proposal(self, message) -> dict | None:
        """Detect if a result message contains an updated proposal."""
        try:
            if message.content:
                content_text = ""
                if isinstance(message.content, list):
                    for item in message.content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            content_text = item.get("text", "")
                            break
                elif isinstance(message.content, str):
                    content_text = message.content

                if content_text:
                    data = json.loads(content_text)
                    if isinstance(data, dict) and data.get("type") == "proposal":
                        # Check if this is our proposal being updated
                        if data.get("data", {}).get("proposal_id") == self.proposal_id:
                            return {
                                "proposal_type": data.get("proposal_type"),
                                "data": data.get("data")
                            }
        except (json.JSONDecodeError, AttributeError, TypeError):
            pass

        return None

    def add_chat_message(self, role: str, content: str) -> None:
        """Add a message to the chat area."""
        messages_container = self.query_one("#chat-messages", Vertical)
        messages_container.mount(MiniChatMessage(role, content))

        # Scroll to bottom
        chat_area = self.query_one("#chat-area", ScrollableContainer)
        chat_area.scroll_end(animate=False)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "apply-button":
            if self.has_updates and self.updated_proposal:
                # Return the updated proposal
                await self.cleanup_client()
                self.dismiss(self.updated_proposal)
        elif event.button.id == "cancel-button":
            await self.cleanup_client()
            self.dismiss(None)

    def action_cancel(self) -> None:
        """Handle escape key."""
        asyncio.create_task(self.cleanup_and_dismiss())

    async def cleanup_and_dismiss(self) -> None:
        """Clean up client and dismiss."""
        await self.cleanup_client()
        self.dismiss(None)

    async def cleanup_client(self) -> None:
        """Clean up the SDK client."""
        if self.client:
            try:
                await self.client.__aexit__(None, None, None)
            except:
                pass

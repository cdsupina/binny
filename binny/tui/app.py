"""Main Textual TUI application for Binny."""

import json
import asyncio
import sys
from pathlib import Path
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Header, Footer, Input
from textual.containers import Container, Vertical
from textual import work
from claude_agent_sdk.client import ClaudeSDKClient
from claude_agent_sdk import (
    AgentDefinition,
    ClaudeAgentOptions,
    create_sdk_mcp_server,
    AssistantMessage,
    UserMessage,
    SystemMessage,
    ResultMessage,
)

from .chat_view import ChatView
from .proposal_modal import ProposalModal
from ..part_namer import (
    PART_NAMER_TOOLS,
    ProposalType,
    MANAGERS,
    approve_prefix_tool,
    approve_material_tool,
    reject_prefix_tool,
    reject_material_tool,
    __version__ as part_namer_version,
)


class BinnyApp(App):
    """Binny inventory management TUI application."""

    TITLE = "Binny - Inventory Management Assistant"
    CSS_PATH = "styles/app.tcss"

    BINDINGS = [
        Binding("ctrl+d", "toggle_debug", "Toggle Debug", priority=True),
        Binding("ctrl+r", "review_proposals", "Review Proposals", priority=True),
        Binding("ctrl+y", "copy_last_response", "Copy Last Response", priority=True),
        Binding("ctrl+l", "copy_all_chat", "Copy All Chat", priority=True),
    ]

    def __init__(
        self,
        binny_system_prompt: str,
        part_namer_system_prompt: str,
        inventory_manager_system_prompt: str,
        mmc_searcher_system_prompt: str,
        edit_assistant_system_prompt: str,
        inventory_dir: str,
        debug_enabled: bool = False,
    ):
        super().__init__()
        self.binny_system_prompt = binny_system_prompt
        self.part_namer_system_prompt = part_namer_system_prompt
        self.inventory_manager_system_prompt = inventory_manager_system_prompt
        self.mmc_searcher_system_prompt = mmc_searcher_system_prompt
        self.edit_assistant_system_prompt = edit_assistant_system_prompt
        self.inventory_dir = inventory_dir
        self.debug_enabled = debug_enabled
        self.client = None
        self.pending_proposals = []

    def compose(self) -> ComposeResult:
        """Compose the TUI layout."""
        yield Header()
        with Vertical(id="main-container"):
            with Container(id="chat-container"):
                yield ChatView(debug_enabled=self.debug_enabled)
            with Container(id="input-container"):
                yield Input(placeholder="Type your message...")
        yield Footer()

    async def on_mount(self) -> None:
        """Initialize the Claude SDK client on mount."""
        # Initialize Claude SDK client
        part_namer_mcp = create_sdk_mcp_server(
            name="part_namer",
            version=part_namer_version,
            tools=PART_NAMER_TOOLS,
        )

        options = ClaudeAgentOptions(
            model="haiku",
            system_prompt=self.binny_system_prompt,
            add_dirs=[self.inventory_dir],
            allowed_tools=[
                "mcp__excel__read_data_from_excel",
                "mcp__mcmaster__mmc_get_specifications",
                "mcp__mcmaster__mmc_get_price",
                "mcp__mcmaster__mmc_get_status",
                "mcp__mcmaster__mmc_login",
                "mcp__mcmaster__mmc_remove_product",
                "mcp__mcmaster__mmc_get_changes",
                "mcp__mcmaster__mmc_add_product",
                "mcp__mcmaster__mmc_get_description",
                "mcp__mcmaster__mmc_logout",
                "mcp__mcmaster__mmc_get_product",
                "mcp__part_namer__approve_prefix",
                "mcp__part_namer__approve_material",
                "mcp__part_namer__reject_prefix",
                "mcp__part_namer__reject_material",
                "mcp__part_namer__update_prefix_proposal",
                "mcp__part_namer__update_material_proposal",
                "mcp__part_namer__list_prefix_proposals",
                "mcp__part_namer__list_material_proposals",
                "mcp__part_namer__read_prefixes",
                "mcp__part_namer__read_materials",
                "mcp__part_namer__propose_prefix",
                "mcp__part_namer__propose_material",
            ],
            agents={
                "part-namer": AgentDefinition(
                    description="An agent to generate names for parts.",
                    prompt=self.part_namer_system_prompt,
                    model="haiku",
                    tools=[
                        "mcp__part_namer__read_prefixes",
                        "mcp__part_namer__read_materials",
                        "mcp__part_namer__propose_prefix",
                        "mcp__part_namer__propose_material",
                        "mcp__part_namer__update_prefix_proposal",
                        "mcp__part_namer__update_material_proposal",
                    ],
                ),
                "mmc-searcher": AgentDefinition(
                    description="Use this agent for all McMaster-Carr catalog operations including searching for parts, retrieving part information and specifications, managing part subscriptions, and accessing the McMaster-Carr product database.",
                    prompt=self.mmc_searcher_system_prompt,
                    model="haiku",
                    tools=[
                        "mcp__mcmaster__mmc_get_specifications",
                        "mcp__mcmaster__mmc_get_price",
                        "mcp__mcmaster__mmc_get_status",
                        "mcp__mcmaster__mmc_login",
                        "mcp__mcmaster__mmc_remove_product",
                        "mcp__mcmaster__mmc_get_changes",
                        "mcp__mcmaster__mmc_add_product",
                        "mcp__mcmaster__mmc_get_description",
                        "mcp__mcmaster__mmc_logout",
                        "mcp__mcmaster__mmc_get_product",
                    ],
                ),
                "inventory-manager": AgentDefinition(
                    description="Use this agent to query, search, and report on inventory levels, stock counts, and item availability.",
                    prompt=self.inventory_manager_system_prompt,
                    model="haiku",
                    tools=["mcp__excel__read_data_from_excel"],
                ),
            },
            mcp_servers={
                "excel": {"command": "uvx", "args": ["excel-mcp-server", "stdio"]},
                "mcmaster": {"type": "stdio", "command": "mmc-mcp", "args": []},
                "part_namer": part_namer_mcp,
            },
            env={
                "MAX_THINKING_TOKENS": "1500",
            },
        )

        self.client = ClaudeSDKClient(options=options)
        await self.client.__aenter__()

        # Show welcome message
        chat_view = self.query_one(ChatView)
        chat_view.add_system_message(
            "Welcome to Binny! I'm ready to help with inventory management, part naming, and McMaster-Carr lookups.\n\n"
            "Type your message below and press Enter to chat.\n\n"
            "💡 To copy text:\n"
            "  • Ctrl+Y: Copy last assistant response to clipboard\n"
            "  • Ctrl+L: Copy entire chat to clipboard\n\n"
            "Other shortcuts:\n"
            "  • Ctrl+C: Quit\n"
            "  • Ctrl+D: Toggle debug mode\n"
            "  • Ctrl+R: Review pending proposals"
        )

        # Focus the input field
        self.query_one(Input).focus()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle user input submission."""
        user_input = event.value
        if not user_input.strip():
            return

        # Clear the input
        event.input.value = ""

        # Add user message to chat
        chat_view = self.query_one(ChatView)
        chat_view.add_user_message(user_input)

        # Send to Claude SDK
        try:
            if not self.client:
                chat_view.add_system_message("Error: Claude SDK client not initialized")
                return

            await self.client.query(user_input)

            # Process response
            async for message in self.client.receive_response():
                await self.handle_message(message)

        except Exception as e:
            import traceback
            chat_view.add_system_message(f"Error: {str(e)}\n{traceback.format_exc()}")

    async def handle_message(self, message) -> None:
        """Handle a message from Claude SDK."""
        chat_view = self.query_one(ChatView)

        # Check if this is a proposal in a tool result
        if isinstance(message, ResultMessage):
            proposal_info = self.detect_proposal(message)
            if proposal_info:
                await self.show_proposal_modal(
                    proposal_info["data"],
                    proposal_info["proposal_type"]
                )
                # Still add to chat view in debug mode
                if self.debug_enabled:
                    chat_view.add_message(message)
                return

        # Add message to chat view
        chat_view.add_message(message)

    def detect_proposal(self, message: ResultMessage) -> dict | None:
        """Detect if a result message contains a proposal.

        Args:
            message: The result message to check

        Returns:
            Dictionary with proposal data if found, None otherwise
        """
        try:
            # Try to parse the result content as JSON
            if message.content:
                # Handle different content formats
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
                        return {
                            "proposal_type": data.get("proposal_type"),
                            "data": data.get("data")
                        }
        except (json.JSONDecodeError, AttributeError, TypeError):
            pass

        return None

    async def show_proposal_modal(
        self,
        proposal_data: dict,
        proposal_type: str,
        all_proposals: list[tuple[str, dict]] | None = None,
        current_index: int = 0,
    ) -> None:
        """Show the proposal approval modal.

        Args:
            proposal_data: The proposal data
            proposal_type: Either "prefix" or "material"
            all_proposals: Optional list of all proposals for navigation
            current_index: Current index in the all_proposals list
        """
        # Show modal and get user's choice
        result = await self.push_screen_wait(
            ProposalModal(proposal_data, proposal_type, all_proposals, current_index)
        )

        chat_view = self.query_one(ChatView)

        # Handle the user's choice
        # If result is None, user cancelled (Escape on batch review)
        if result is None:
            chat_view.add_system_message("Proposal review cancelled.")
            return
        # If result is a dict, it's multiple actions from batch review
        elif isinstance(result, dict):
            await self.process_batch_actions(result, all_proposals or [(proposal_type, proposal_data)])
        # Single action
        elif result == "approve":
            await self.approve_proposal(proposal_data, proposal_type)
            chat_view.add_system_message(
                f"✓ {proposal_type.capitalize()} proposal approved!"
            )
        elif result == "reject":
            await self.reject_proposal(proposal_data, proposal_type)
            chat_view.add_system_message(
                f"✗ {proposal_type.capitalize()} proposal rejected."
            )
        elif result == "edit":
            await self.edit_proposal(proposal_data, proposal_type)
        elif result == "defer":
            chat_view.add_system_message(
                f"Proposal deferred. Use Ctrl+R to review later."
            )

    async def process_batch_actions(
        self,
        actions: dict[int, str],
        all_proposals: list[tuple[str, dict]]
    ) -> None:
        """Process batch actions for multiple proposals.

        Args:
            actions: Dict mapping proposal index to action (approve/reject/edit/defer)
            all_proposals: List of all (type, data) tuples
        """
        chat_view = self.query_one(ChatView)

        # Process approve/reject actions first
        approved = []
        rejected = []
        deferred = []
        edit_proposals = []  # Store proposals marked for editing

        for index, action in actions.items():
            if index >= len(all_proposals):
                continue

            prop_type, prop_data = all_proposals[index]
            prop_name = prop_data.get('prefix') or prop_data.get('material_code')

            if action == "approve":
                await self.approve_proposal(prop_data, prop_type)
                approved.append(f"{prop_type}:{prop_name}")
            elif action == "reject":
                await self.reject_proposal(prop_data, prop_type)
                rejected.append(f"{prop_type}:{prop_name}")
            elif action == "defer":
                deferred.append(f"{prop_type}:{prop_name}")
            elif action == "edit":
                # Store for sequential editing
                edit_proposals.append((prop_type, prop_data, prop_name))

        # Show summary of approve/reject actions
        summary = []
        if approved:
            summary.append(f"✓ Approved: {', '.join(approved)}")
        if rejected:
            summary.append(f"✗ Rejected: {', '.join(rejected)}")
        if deferred:
            summary.append(f"⊙ Deferred: {', '.join(deferred)}")

        # Show what wasn't acted on
        unprocessed_count = len(all_proposals) - len(actions)
        if unprocessed_count > 0:
            summary.append(f"⊙ {unprocessed_count} proposal(s) left without action (deferred)")

        if summary:
            chat_view.add_system_message("Batch actions:\n" + "\n".join(summary))

        # Process edit proposals sequentially
        if edit_proposals:
            chat_view.add_system_message(
                f"\nProcessing {len(edit_proposals)} proposal(s) marked for editing..."
            )

            for prop_type, prop_data, prop_name in edit_proposals:
                # Open edit modal for each proposal
                # This will block until user clicks Apply or Cancel
                await self.edit_proposal(prop_data, prop_type)

        # Final summary
        if not summary and not edit_proposals:
            chat_view.add_system_message("No actions were selected.")
        elif edit_proposals:
            chat_view.add_system_message(f"Finished processing {len(edit_proposals)} edit session(s).")

    async def approve_proposal(self, proposal_data: dict, proposal_type: str) -> None:
        """Approve a proposal by calling the appropriate MCP tool."""
        tool_name = f"approve_{proposal_type}"
        proposal_id = proposal_data["proposal_id"]

        # Call the approval tool directly using the SDK client
        # Note: This is a simplified approach - in production you might want
        # to call the MCP tool more directly
        if proposal_type == "prefix":
            await approve_prefix_tool.handler({"proposal_id": proposal_id})
        else:
            await approve_material_tool.handler({"proposal_id": proposal_id})

    async def reject_proposal(self, proposal_data: dict, proposal_type: str) -> None:
        """Reject a proposal by calling the appropriate MCP tool."""
        proposal_id = proposal_data["proposal_id"]

        if proposal_type == "prefix":
            await reject_prefix_tool.handler({"proposal_id": proposal_id})
        else:
            await reject_material_tool.handler({"proposal_id": proposal_id})

    async def edit_proposal(self, proposal_data: dict, proposal_type: str) -> None:
        """Handle editing a proposal - open edit modal with mini-chat."""
        from .edit_proposal_modal import EditProposalModal

        # Open the edit modal
        result = await self.push_screen_wait(
            EditProposalModal(
                proposal_data,
                proposal_type,
                self.edit_assistant_system_prompt
            )
        )

        chat_view = self.query_one(ChatView)

        # Handle result
        if result is None:
            # User cancelled
            chat_view.add_system_message("Editing cancelled.")
        else:
            # User applied changes - result is the updated proposal
            # Show the updated proposal in the review modal
            await self.show_proposal_modal(result, proposal_type)


    def action_toggle_debug(self) -> None:
        """Toggle debug mode."""
        self.debug_enabled = not self.debug_enabled

        chat_view = self.query_one(ChatView)
        chat_view.debug_enabled = self.debug_enabled

        # Show confirmation message
        if self.debug_enabled:
            chat_view.add_system_message("✓ Debug mode enabled - tool use and results will now be shown")
        else:
            chat_view.add_system_message("✓ Debug mode disabled")

    @work
    async def action_review_proposals(self) -> None:
        """Review all pending proposals via interactive modals."""
        # Load all pending proposals
        prefix_proposals = MANAGERS[ProposalType.PREFIX].load_proposals()
        material_proposals = MANAGERS[ProposalType.MATERIAL].load_proposals()

        all_proposals = [
            ("prefix", p) for p in prefix_proposals
        ] + [
            ("material", p) for p in material_proposals
        ]

        if not all_proposals:
            chat_view = self.query_one(ChatView)
            chat_view.add_system_message("No pending proposals to review.")
            return

        chat_view = self.query_one(ChatView)
        chat_view.add_system_message(
            f"Reviewing {len(all_proposals)} pending proposal(s)..."
        )

        # Show single modal with all proposals (user can navigate through them)
        first_type, first_data = all_proposals[0]
        await self.show_proposal_modal(first_data, first_type, all_proposals, 0)

        chat_view.add_system_message("Proposal review complete!")

    def action_copy_last_response(self) -> None:
        """Copy the last assistant response to clipboard."""
        chat_view = self.query_one(ChatView)
        last_msg = chat_view.get_last_assistant_message()

        if last_msg:
            self.copy_to_clipboard(last_msg)
            chat_view.add_system_message("✓ Last response copied to clipboard!")
        else:
            chat_view.add_system_message("No assistant response to copy yet.")

    def action_copy_all_chat(self) -> None:
        """Copy all chat messages to clipboard."""
        chat_view = self.query_one(ChatView)
        all_messages = chat_view.get_all_messages()

        if all_messages:
            self.copy_to_clipboard(all_messages)
            chat_view.add_system_message("✓ Entire chat copied to clipboard!")
        else:
            chat_view.add_system_message("No messages to copy yet.")

    async def on_unmount(self) -> None:
        """Clean up the Claude SDK client on unmount."""
        # Don't manually clean up the client here - it causes shutdown errors
        # The client will be cleaned up automatically when the app exits
        pass

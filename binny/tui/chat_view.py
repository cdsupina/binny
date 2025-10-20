"""Chat view component for displaying messages."""

from textual.widgets import RichLog
from rich.panel import Panel
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich import box
from claude_agent_sdk import (
    AssistantMessage,
    UserMessage,
    SystemMessage,
    ResultMessage,
)
import json


class ChatView(RichLog):
    """Scrollable chat area for displaying conversation messages."""

    DEFAULT_CSS = """
    ChatView {
        background: $surface;
        border: none;
        padding: 0;
        scrollbar-gutter: stable;
    }

    ChatView:focus {
        border: none;
    }
    """

    can_focus = True

    def __init__(self, debug_enabled: bool = False):
        super().__init__(wrap=True, markup=True, auto_scroll=True)
        self.debug_enabled = debug_enabled
        self.messages_plain = []  # Store plain text messages for copying

    def _create_panel(self, content, title: str, color: str) -> Panel:
        """Helper method to create a panel with consistent styling.

        Args:
            content: The content to display (can be string, Markdown, Syntax, etc.)
            title: The title text (without markup)
            color: The color for both title and border

        Returns:
            A configured Panel object
        """
        return Panel(
            content,
            title=f"[bold {color}]{title}[/bold {color}]",
            title_align="left",
            border_style=color,
            expand=False,
            box=box.HORIZONTALS,
        )

    def add_user_message(self, content: str) -> None:
        """Add a user message to the chat."""
        panel = self._create_panel(content, "You", "yellow")
        self.write(panel)
        self.write("")  # Add spacing
        self.messages_plain.append(f"You: {content}")

    def add_assistant_message(self, content: str) -> None:
        """Add an assistant message to the chat."""
        panel = self._create_panel(Markdown(content), "Binny", "green")
        self.write(panel)
        self.write("")
        self.messages_plain.append(f"Binny: {content}")

    def add_tool_use(self, tool_name: str, tool_input: dict) -> None:
        """Add a tool use message (only in debug mode)."""
        if not self.debug_enabled:
            return

        syntax = Syntax(
            json.dumps(tool_input, indent=2),
            "json",
            theme="monokai",
            line_numbers=False,
        )
        panel = self._create_panel(syntax, f"Tool Use: {tool_name}", "blue")
        self.write(panel)
        self.write("")

    def add_tool_result(self, tool_name: str, result: str) -> None:
        """Add a tool result message (only in debug mode)."""
        if not self.debug_enabled:
            return

        # Try to parse as JSON for pretty printing
        try:
            parsed = json.loads(result)
            content = Syntax(
                json.dumps(parsed, indent=2),
                "json",
                theme="monokai",
                line_numbers=False,
            )
        except (json.JSONDecodeError, TypeError):
            content = result

        panel = self._create_panel(content, f"Tool Result: {tool_name}", "magenta")
        self.write(panel)
        self.write("")

    def add_system_message(self, content: str, debug_only: bool = False) -> None:
        """Add a system message to the chat.

        Args:
            content: The message content
            debug_only: If True, only show in debug mode. If False, always show.
        """
        if debug_only and not self.debug_enabled:
            return

        panel = self._create_panel(content, "System", "cyan")
        self.write(panel)
        self.write("")

        # Store plain text
        if not debug_only:
            self.messages_plain.append(f"System: {content}")

    def get_last_assistant_message(self) -> str:
        """Get the last assistant message in plain text."""
        for msg in reversed(self.messages_plain):
            if msg.startswith("Binny: "):
                return msg[7:]  # Remove "Binny: " prefix
        return ""

    def get_all_messages(self) -> str:
        """Get all messages as plain text."""
        return "\n\n".join(self.messages_plain)

    def add_message(self, message) -> None:
        """Add a message to the chat based on its type."""
        from claude_agent_sdk import TextBlock, ToolUseBlock, ThinkingBlock, ToolResultBlock

        if isinstance(message, UserMessage):
            # UserMessage has content blocks (can include ToolResultBlock)
            for block in message.content:
                if isinstance(block, ToolResultBlock) and self.debug_enabled:
                    # Tool result in user message
                    content = str(block.content) if block.content else ""
                    self.add_tool_result(block.tool_use_id, content)
                # Regular user content is already displayed when user types

        elif isinstance(message, AssistantMessage):
            # AssistantMessage has content blocks
            for block in message.content:
                if isinstance(block, TextBlock):
                    self.add_assistant_message(block.text)
                elif isinstance(block, ToolUseBlock) and self.debug_enabled:
                    self.add_tool_use(block.name, block.input)
                elif isinstance(block, ThinkingBlock):
                    if self.debug_enabled:
                        self.add_system_message("Assistant is thinking...", debug_only=True)

        elif isinstance(message, ResultMessage):
            # ResultMessage contains session stats
            if self.debug_enabled:
                stats = {
                    "Session ID": message.session_id,
                    "Result": message.subtype,
                    "Duration": f"{message.duration_ms / 1000:.2f}s",
                    "Cost": f"${message.total_cost_usd:.4f}" if message.total_cost_usd else "N/A",
                    "Input Tokens": message.usage["input_tokens"],
                    "Output Tokens": message.usage["output_tokens"],
                }
                import json
                self.add_system_message(json.dumps(stats, indent=2), debug_only=True)

        elif isinstance(message, SystemMessage):
            # SystemMessage has .data and .subtype, not .content
            if self.debug_enabled:
                import json
                if message.subtype == "compact_boundary":
                    compact_msg = (
                        f"Compaction completed\n"
                        f"Pre-compaction tokens: {message.data.get('compact_metadata', {}).get('pre_tokens', 'N/A')}\n"
                        f"Trigger: {message.data.get('compact_metadata', {}).get('trigger', 'N/A')}"
                    )
                    self.add_system_message(compact_msg, debug_only=True)
                else:
                    self.add_system_message(json.dumps(message.data, indent=2), debug_only=True)

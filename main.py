from claude_agent_sdk.client import ClaudeSDKClient
from dotenv import load_dotenv
from rich.console import Console
from claude_agent_sdk import AgentDefinition, ClaudeAgentOptions
from cli_tools import get_user_input, parse_and_print_message, parse_args
from pathlib import Path
import os

_ = load_dotenv()
inventory_dir = os.getenv("INVENTORY_SUBAGENT_DIRECTORY")

# Parse CLI arguments and set debug mode
args = parse_args()
debug_enabled = args.debug


async def main():
    console = Console()

    # Load Binny system prompt from file
    binny_system_prompt_path = Path(__file__).parent / "system_prompts/binny_prompt.md"
    binny_system_prompt = binny_system_prompt_path.read_text().strip()

    # Load part-namer system prompt from file
    part_namer_system_prompt_path = (
        Path(__file__).parent / "system_prompts/part_namer_prompt.md"
    )
    part_namer_system_prompt = part_namer_system_prompt_path.read_text().strip()

    # Load inventory-manager system prompt from file
    inventory_manager_system_prompt_path = (
        Path(__file__).parent / "system_prompts/inventory_manager_prompt.md"
    )
    inventory_manager_system_prompt = (
        inventory_manager_system_prompt_path.read_text().strip()
    )

    # Initialize Claude options
    options = ClaudeAgentOptions(
        model="haiku",
        system_prompt=binny_system_prompt,
        add_dirs=[inventory_dir],
        allowed_tools=["mcp__excel__read_data_from_excel"],
        agents={
            "part-namer": AgentDefinition(
                description="An agent to generate names for parts.",
                prompt=part_namer_system_prompt,
                model="haiku",
            ),
            "inventory-manager": AgentDefinition(
                description="Use this agent to query, search, and report on inventory levels, stock counts, and item availability.",
                prompt=inventory_manager_system_prompt,
                model="haiku",
                tools=["mcp__excel__read_data_from_excel"],
            ),
        },
        mcp_servers={
            "excel": {"command": "uvx", "args": ["excel-mcp-server", "stdio"]}
        },
        env={
            "MAX_THINKING_TOKENS": "1500",
        },
    )

    # Run the agent loop with the Claude SDK client
    async with ClaudeSDKClient(options=options) as client:
        while True:
            input_prompt = get_user_input(console)

            await client.query(input_prompt)

            async for message in client.receive_response():
                parse_and_print_message(message, console, debug_enabled)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

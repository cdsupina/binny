from claude_agent_sdk.client import ClaudeSDKClient
from dotenv import load_dotenv
from rich.console import Console
from claude_agent_sdk import AgentDefinition, ClaudeAgentOptions, create_sdk_mcp_server
from .cli_tools import get_user_input, parse_and_print_message, parse_args
from pathlib import Path
import os

from .part_namer_tools import PART_NAMER_TOOLS
from .part_namer_mcp import __version__ as part_namer_version

_ = load_dotenv()
inventory_dir = os.getenv("BINNY_INVENTORY_DIR")

# Parse CLI arguments and set debug mode
args = parse_args()
debug_enabled = args.debug


async def async_main():
    console = Console()

    # Load Binny system prompt from file
    binny_system_prompt_path = Path(__file__).parent.parent / "system_prompts/binny_prompt.md"
    binny_system_prompt = binny_system_prompt_path.read_text().strip()

    # Load part-namer system prompt from file
    part_namer_system_prompt_path = (
        Path(__file__).parent.parent / "system_prompts/part_namer_prompt.md"
    )
    part_namer_system_prompt = part_namer_system_prompt_path.read_text().strip()

    # Load inventory-manager system prompt from file
    inventory_manager_system_prompt_path = (
        Path(__file__).parent.parent / "system_prompts/inventory_manager_prompt.md"
    )
    inventory_manager_system_prompt = (
        inventory_manager_system_prompt_path.read_text().strip()
    )

    # Load mmc-searcher system prompt from file
    mmc_searcher_system_prompt_path = (
        Path(__file__).parent.parent / "system_prompts/mmc_searcher_prompt.md"
    )
    mmc_searcher_system_prompt = mmc_searcher_system_prompt_path.read_text().strip()

    # Create SDK MCP server for part namer tools
    part_namer_mcp = create_sdk_mcp_server(
        name="part_namer",
        version=part_namer_version,
        tools=PART_NAMER_TOOLS,
    )

    # Initialize Claude options
    options = ClaudeAgentOptions(
        model="haiku",
        system_prompt=binny_system_prompt,
        add_dirs=[inventory_dir],
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
                prompt=part_namer_system_prompt,
                model="haiku",
                tools=[
                    "mcp__part_namer__read_prefixes",
                    "mcp__part_namer__read_materials",
                    "mcp__part_namer__propose_prefix",
                    "mcp__part_namer__propose_material",
                ],
            ),
            "mmc-searcher": AgentDefinition(
                description="Use this agent for all McMaster-Carr catalog operations including searching for parts, retrieving part information and specifications, managing part subscriptions, and accessing the McMaster-Carr product database.",
                prompt=mmc_searcher_system_prompt,
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
                prompt=inventory_manager_system_prompt,
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

    # Run the agent loop with the Claude SDK client
    async with ClaudeSDKClient(options=options) as client:
        while True:
            input_prompt = get_user_input(console)

            await client.query(input_prompt)

            async for message in client.receive_response():
                parse_and_print_message(message, console, debug_enabled)


def main():
    """Entry point for the binny CLI tool."""
    import asyncio
    asyncio.run(async_main())


if __name__ == "__main__":
    main()

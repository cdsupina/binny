from dotenv import load_dotenv
from pathlib import Path
import os

from .cli_tools import parse_args
from .tui.app import BinnyApp

_ = load_dotenv()
inventory_dir = os.getenv("BINNY_INVENTORY_DIR")

# Parse CLI arguments and set debug mode
args = parse_args()
debug_enabled = args.debug


async def async_main():
    import sys
    import io
    import asyncio

    # Load system prompts from files
    binny_system_prompt_path = Path(__file__).parent / "system_prompts/binny_prompt.md"
    binny_system_prompt = binny_system_prompt_path.read_text().strip()

    part_namer_system_prompt_path = (
        Path(__file__).parent / "system_prompts/part_namer_prompt.md"
    )
    part_namer_system_prompt = part_namer_system_prompt_path.read_text().strip()

    inventory_manager_system_prompt_path = (
        Path(__file__).parent / "system_prompts/inventory_manager_prompt.md"
    )
    inventory_manager_system_prompt = (
        inventory_manager_system_prompt_path.read_text().strip()
    )

    mmc_searcher_system_prompt_path = (
        Path(__file__).parent / "system_prompts/mmc_searcher_prompt.md"
    )
    mmc_searcher_system_prompt = mmc_searcher_system_prompt_path.read_text().strip()

    edit_assistant_system_prompt_path = (
        Path(__file__).parent / "system_prompts/edit_assistant_prompt.md"
    )
    edit_assistant_system_prompt = edit_assistant_system_prompt_path.read_text().strip()

    # Create and run the TUI app
    app = BinnyApp(
        binny_system_prompt=binny_system_prompt,
        part_namer_system_prompt=part_namer_system_prompt,
        inventory_manager_system_prompt=inventory_manager_system_prompt,
        mmc_searcher_system_prompt=mmc_searcher_system_prompt,
        edit_assistant_system_prompt=edit_assistant_system_prompt,
        inventory_dir=inventory_dir,
        debug_enabled=debug_enabled,
    )

    # Redirect stderr during shutdown to suppress asyncio warnings
    original_stderr = sys.stderr
    try:
        await app.run_async()
    except Exception as e:
        # Only print stack trace for actual errors, not clean exits
        print(f"\nError: {e}", file=sys.stderr)
        raise
    finally:
        # Suppress stderr during final cleanup to hide shutdown warnings
        sys.stderr = io.StringIO()
        try:
            # Give asyncio a moment to clean up
            await asyncio.sleep(0.01)
        finally:
            sys.stderr = original_stderr


def main():
    """Entry point for the binny CLI tool."""
    import asyncio
    import sys
    import warnings

    # Suppress specific warnings during shutdown
    warnings.filterwarnings("ignore", category=RuntimeWarning,
                          message=".*Attempted to exit cancel scope.*")

    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        # Clean exit on Ctrl+C (shouldn't happen if Textual handles it, but just in case)
        sys.exit(0)
    except SystemExit:
        # Clean exit from app.exit()
        pass
    except Exception:
        # Only show stack trace for unexpected errors
        import traceback
        print("\n" + "="*60, file=sys.stderr)
        print("UNEXPECTED ERROR - Please report this:", file=sys.stderr)
        print("="*60, file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

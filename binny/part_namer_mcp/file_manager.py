"""File management for prefixes and materials files.

Handles parsing and writing H2-based markdown files.
"""

import re
from pathlib import Path
from typing import List

from .models import Prefix, Material, PrefixProposal, MaterialProposal


def parse_prefixes_file(file_path: Path) -> List[Prefix]:
    """Parse prefixes from H2-based markdown file.

    Expected format:
    ## PREFIX_CODE

    **Description:** Description text

    **Format:** `PREFIX-{PLACEHOLDER}-{PLACEHOLDER}`

    Args:
        file_path: Path to prefixes.md file

    Returns:
        List of parsed Prefix objects
    """
    if not file_path.exists():
        return []

    content = file_path.read_text()
    prefixes = []

    # Split by H2 headers
    sections = re.split(r'^## ', content, flags=re.MULTILINE)

    for section in sections[1:]:  # Skip the first empty section before first H2
        lines = section.strip().split('\n')
        if not lines:
            continue

        prefix_code = lines[0].strip()

        # Extract description and format
        description = ""
        format_template = ""

        for line in lines[1:]:
            if line.startswith('**Description:**'):
                description = line.replace('**Description:**', '').strip()
            elif line.startswith('**Format:**'):
                # Extract format from backticks
                match = re.search(r'`([^`]+)`', line)
                if match:
                    format_template = match.group(1)

        if prefix_code and description and format_template:
            prefixes.append(Prefix(
                prefix=prefix_code,
                description=description,
                format_template=format_template
            ))

    return prefixes


def parse_materials_file(file_path: Path) -> List[Material]:
    """Parse materials from H2-based markdown file.

    Expected format:
    ## MATERIAL_CODE

    **Description:** Description text

    Args:
        file_path: Path to materials.md file

    Returns:
        List of parsed Material objects
    """
    if not file_path.exists():
        return []

    content = file_path.read_text()
    materials = []

    # Split by H2 headers
    sections = re.split(r'^## ', content, flags=re.MULTILINE)

    for section in sections[1:]:  # Skip the first empty section
        lines = section.strip().split('\n')
        if not lines:
            continue

        material_code = lines[0].strip()

        # Extract description
        description = ""
        for line in lines[1:]:
            if line.startswith('**Description:**'):
                description = line.replace('**Description:**', '').strip()
                break

        if material_code and description:
            materials.append(Material(
                material_code=material_code,
                description=description
            ))

    return materials


def append_prefix_to_file(file_path: Path, proposal: PrefixProposal) -> bool:
    """Append approved prefix proposal to prefixes file.

    Args:
        file_path: Path to prefixes.md
        proposal: Approved prefix proposal

    Returns:
        True if successful
    """
    try:
        # Ensure file exists
        if not file_path.exists():
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text("# Part Prefixes\n\n")

        # Format the entry
        entry = f"## {proposal['prefix']}\n\n"
        entry += f"**Description:** {proposal['description']}\n\n"
        entry += f"**Format:** `{proposal['format_template']}`\n\n"

        # Append to file
        with open(file_path, 'a') as f:
            f.write(entry)

        return True

    except Exception as e:
        print(f"Error appending prefix: {e}")
        return False


def append_material_to_file(file_path: Path, proposal: MaterialProposal) -> bool:
    """Append approved material proposal to materials file.

    Args:
        file_path: Path to materials.md
        proposal: Approved material proposal

    Returns:
        True if successful
    """
    try:
        # Ensure file exists
        if not file_path.exists():
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text("# Materials\n\n")

        # Format the entry
        entry = f"## {proposal['material_code']}\n\n"
        entry += f"**Description:** {proposal['description']}\n\n"

        # Append to file
        with open(file_path, 'a') as f:
            f.write(entry)

        return True

    except Exception as e:
        print(f"Error appending material: {e}")
        return False

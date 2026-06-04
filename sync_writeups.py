#!/usr/bin/env python3
"""
Sync HTB writeups from the external repo into the MkDocs structure.

Usage:
    python sync_writeups.py [--repo-url URL] [--work-dir DIR]

The script clones (or updates) the writeups repo and copies files
into the docs/ folder for MkDocs to serve.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_URL = "https://github.com/egz-dev/HTB.git"
WORK_DIR = Path(".sync_cache")
DOCS_DIR = Path("docs")

# Mapping: source repo folders → docs/ folders
FOLDER_MAP = {
    "machines": "writeups",
    "documentation": "guides",
}


def run(cmd: list[str], cwd: Path | None = None) -> None:
    """Run a command and abort if it fails."""
    print(f"  → {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ✗ Error: {result.stderr.strip()}")
        sys.exit(1)


def get_default_branch(work_dir: Path) -> str:
    """Detect the default branch of the cloned repo."""
    result = subprocess.run(
        ["git", "remote", "show", "origin"],
        cwd=work_dir, capture_output=True, text=True
    )
    for line in result.stdout.splitlines():
        stripped = line.strip()
        if stripped.startswith("HEAD branch:"):
            return stripped.split(":")[1].strip()
    return "main"  # fallback


def clone_or_pull(repo_url: str, work_dir: Path) -> None:
    """Clone the repo if it doesn't exist, or pull if already cloned."""
    if (work_dir / ".git").exists():
        print(f"[*] Updating repo in {work_dir}...")
        run(["git", "fetch", "origin"], cwd=work_dir)
        branch = get_default_branch(work_dir)
        run(["git", "reset", "--hard", f"origin/{branch}"], cwd=work_dir)
    else:
        print(f"[*] Cloning {repo_url} into {work_dir}...")
        work_dir.parent.mkdir(parents=True, exist_ok=True)
        run(["git", "clone", "--depth", "1", repo_url, str(work_dir)])

def parse_frontmatter(text: str) -> tuple[dict[str, str], int] | None:
    """Extract simple YAML frontmatter (key: value) from a .md file.
    Returns (props, end_pos) or None if no frontmatter."""
    match = re.match(r'^---\s*\n(.*?)\n---', text, re.DOTALL)
    if not match:
        return None
    props: dict[str, str] = {}
    for line in match.group(1).splitlines():
        line = line.strip()
        if ':' in line:
            key, _, value = line.partition(':')
            props[key.strip()] = value.strip()
    return props, match.end()


def badge_class(key: str, value: str) -> str:
    """Return the CSS class for a badge based on key and value."""
    if key == "OS":
        v = value.lower()
        if "windows" in v:
            return "windows"
        if "linux" in v:
            return "linux"
    if key == "Level":
        v = value.lower().replace(" ", "-")
        if v in ("very-easy", "easy", "medium", "hard", "insane"):
            return v
    if key == "Skills":
        return "skills"
    return ""


def inject_properties_card(md_path: Path) -> None:
    """Read a .md, extract its frontmatter, and insert an HTML properties badge bar
    right after the first h1 heading."""
    text = md_path.read_text()
    result = parse_frontmatter(text)
    if not result:
        return
    props, end_of_fm = result

    parts: list[str] = []

    # IP as inline code
    if props.get("IP"):
        parts.append(f'<span class="prop-ip">{props["IP"]}</span>')

    # OS badge
    if props.get("OS"):
        cls = badge_class("OS", props["OS"])
        parts.append(f'<span class="prop-badge {cls}">{props["OS"]}</span>')

    # Level badge
    if props.get("Level"):
        cls = badge_class("Level", props["Level"])
        parts.append(f'<span class="prop-badge {cls}">{props["Level"]}</span>')

    # Skills badge (can be comma-separated)
    if props.get("Skills"):
        for skill in props["Skills"].split(","):
            skill = skill.strip()
            if skill:
                parts.append(f'<span class="prop-badge skills">{skill}</span>')

    if not parts:
        return

    badge_bar = f'\n<div class="machine-properties">\n  {" ".join(parts)}\n</div>\n'

    # Find the first h1 heading and insert the badge bar right after it
    h1_match = re.search(r'^# .+$', text, re.MULTILINE)
    if h1_match:
        insert_pos = h1_match.end()
        new_text = text[:insert_pos] + badge_bar + text[insert_pos:]
    else:
        # Fallback: insert after frontmatter
        insert_pos = end_of_fm
        new_text = text[:insert_pos] + badge_bar + text[insert_pos:]

    md_path.write_text(new_text)
    print(f"    ↳ Properties injected: {', '.join(f'{k}={v}' for k, v in props.items())}")


def copy_content(src_dir: Path, dst_dir: Path, label: str) -> list[str]:
    """
    Copy content from src_dir to dst_dir.
    Returns a list of copied relative paths (without extension).
    """
    if not src_dir.exists():
        print(f"  ⚠ Folder '{src_dir}' not found, skipping...")
        return []

    # Clean destination
    if dst_dir.exists():
        shutil.rmtree(dst_dir)
    dst_dir.mkdir(parents=True, exist_ok=True)

    entries: list[str] = []
    for item in sorted(src_dir.iterdir()):
        dest = dst_dir / item.name
        if item.is_dir():
            shutil.copytree(item, dest)
            # Find the main .md inside
            for md_file in sorted(dest.rglob("*.md")):
                rel = md_file.relative_to(DOCS_DIR)
                entries.append(str(rel.with_suffix("")))
                break  # only the first .md per folder
        elif item.suffix == ".md":
            shutil.copy2(item, dest)
            inject_properties_card(dest)
            rel = dest.relative_to(DOCS_DIR)
            entries.append(str(rel.with_suffix("")))

    print(f"  ✓ {label}: {len(entries)} items copied")
    return entries


LEVEL_ORDER = ["Very Easy", "Easy", "Medium", "Hard", "Insane"]


def get_entry_level(entry: str) -> str:
    """Read the frontmatter of a writeup and return its normalized Level. Defaults to 'Other'."""
    md_path = DOCS_DIR / f"{entry}.md"
    if not md_path.exists():
        return "Other"
    result = parse_frontmatter(md_path.read_text())
    if not result:
        return "Other"
    raw = result[0].get("Level", "")
    if not raw:
        return "Other"
    # Normalize: "very-easy" → "Very Easy", "VERY EASY" → "Very Easy"
    normalized = raw.replace("-", " ").title()
    return normalized if normalized in LEVEL_ORDER else "Other"


def generate_nav(writeup_entries: list[str], guia_entries: list[str]) -> str:
    """Generate the 'nav' section of mkdocs.yml grouped by difficulty."""
    lines = [
        "nav:",
        '  - Home: index.md',
    ]

    if writeup_entries:
        lines.append("  - Writeups:")
        lines.append("      - writeups/index.md")

        # Group by difficulty
        groups: dict[str, list[str]] = {level: [] for level in LEVEL_ORDER}
        groups["Other"] = []
        for entry in writeup_entries:
            level = get_entry_level(entry)
            groups.setdefault(level, []).append(entry)

        for level in LEVEL_ORDER:
            if groups.get(level):
                lines.append(f"      - {level}:")
                for entry in groups[level]:
                    name = entry.split("/")[-1].replace("-", " ").replace("_", " ").title()
                    lines.append(f"          - {name}: {entry}.md")
        if groups.get("Other"):
            lines.append("      - Other:")
            for entry in groups["Other"]:
                name = entry.split("/")[-1].replace("-", " ").replace("_", " ").title()
                lines.append(f"          - {name}: {entry}.md")
    else:
        lines.append("  - Writeups: writeups/index.md")

    if guia_entries:
        lines.append("  - Guides:")
        lines.append("      - guides/index.md")
        for entry in guia_entries:
            name = entry.split("/")[-1].replace("-", " ").replace("_", " ").title()
            lines.append(f"      - {name}: {entry}.md")
    else:
        lines.append("  - Guides: guides/index.md")

    return "\n".join(lines) + "\n"


def update_mkdocs_nav(writeup_entries: list[str], guia_entries: list[str]) -> None:
    """Update the nav section in mkdocs.yml with the generated entries."""
    mkdocs_path = Path("mkdocs.yml")
    content = mkdocs_path.read_text()

    # Find and replace the 'nav:' section
    nav_start_marker = "# --nav-auto-start--"
    nav_end_marker = "# --nav-auto-end--"

    if nav_start_marker in content and nav_end_marker in content:
        # Replace between markers
        before = content.split(nav_start_marker)[0]
        after = content.split(nav_end_marker)[1]
        new_nav = generate_nav(writeup_entries, guia_entries)
        new_content = before + nav_start_marker + "\n" + new_nav + nav_end_marker + after
        mkdocs_path.write_text(new_content)
        print("[*] mkdocs.yml nav updated")
    else:
        print("[*] Nav markers # --nav-auto-start--/--nav-auto-end-- not found in mkdocs.yml")
        print("    Keeping existing nav as-is")


def create_index(dst_dir: Path, title: str, entries: list[str]) -> None:
    """Create an index.md in dst_dir with nice cards for each entry."""
    index_path = dst_dir / "index.md"
    index_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [f"# {title}", ""]
    if entries:
        lines.append('<div class="machine-grid">')
        for entry in entries:
            name = entry.split("/")[-1].replace("-", " ").replace("_", " ").title()
            link = entry.split('/', 1)[1] if '/' in entry else entry

            # Extract frontmatter from the .md to show badges in the card
            md_file = DOCS_DIR / f"{entry}.md"
            props: dict[str, str] = {}
            if md_file.exists():
                result = parse_frontmatter(md_file.read_text())
                if result:
                    props, _ = result

            icon = props.get("Icon", "📦")
            # Use the emoji from the title or first emoji found in the name
            if not icon or icon == "📦":
                for ch in name:
                    if ord(ch) > 127:
                        icon = ch
                        break

            # Plain name without emoji for cleaner cards
            plain_name = name
            if icon and icon in name:
                plain_name = name.replace(icon, "").strip()

            badges_html = ""
            if props.get("OS"):
                badges_html += f' <span class="prop-badge {badge_class("OS", props["OS"])}">{props["OS"]}</span>'
            if props.get("Level"):
                badges_html += f' <span class="prop-badge {badge_class("Level", props["Level"])}">{props["Level"]}</span>'

            lines.append(f'<a class="machine-card" href="{link}/">')
            lines.append(f'  <span class="card-title">{icon} {plain_name}</span>')
            if badges_html:
                lines.append(f'  <span class="card-meta">{badges_html}</span>')
            lines.append('</a>')
        lines.append('</div>')
    else:
        lines.append("> ℹ️ No entries yet. When you add guides in the `documentation/` folder of the writeups repo, they will appear here automatically.")

    index_path.write_text("\n".join(lines) + "\n")
    print(f"  ✓ index.md created in {dst_dir}")


def main():
    parser = argparse.ArgumentParser(description="Sync HTB writeups → MkDocs")
    parser.add_argument("--repo-url", default=REPO_URL, help="Writeups repo URL")
    parser.add_argument("--work-dir", default=str(WORK_DIR), help="Working directory for the clone")
    args = parser.parse_args()

    repo_url: str = args.repo_url
    work_dir = Path(args.work_dir)

    print("=" * 50)
    print("  HTB Writeups Sync → MkDocs")
    print("=" * 50)

    # 1. Clone or update
    clone_or_pull(repo_url, work_dir)

    # 2. Copy content
    all_writeup_entries: list[str] = []
    all_guia_entries: list[str] = []

    for src_folder, dst_folder in FOLDER_MAP.items():
        src = work_dir / src_folder
        dst = DOCS_DIR / dst_folder
        entries = copy_content(src, dst, dst_folder)

        if dst_folder == "writeups":
            all_writeup_entries = entries
        elif dst_folder == "guides":
            all_guia_entries = entries

    # 3. Copy assets if they exist
    assets_src = work_dir / "assets"
    assets_dst = DOCS_DIR / "assets"
    if assets_src.exists():
        if assets_dst.exists():
            shutil.rmtree(assets_dst)
        shutil.copytree(assets_src, assets_dst)
        print(f"  ✓ assets copied to {assets_dst}")
    else:
        print("  ⚠ 'assets' folder not found, skipping...")

    # 4. Create indexes
    create_index(DOCS_DIR / "writeups", "HTB Machine Writeups", all_writeup_entries)
    create_index(DOCS_DIR / "guides", "Practical Guides", all_guia_entries)

    # 5. Update nav
    update_mkdocs_nav(all_writeup_entries, all_guia_entries)

    print()
    print("[✓] Sync complete.")
    print(f"    Writeups: {len(all_writeup_entries)}")
    print(f"    Guides:  {len(all_guia_entries)}")


if __name__ == "__main__":
    main()

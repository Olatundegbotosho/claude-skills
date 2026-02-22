#!/usr/bin/env python3
"""
skills_manager.py
-----------------
Claude Code Skills Manager for Tunde Gbotosho

Gives Claude Code the ability to:
  1. Check Tunde's personal skills repo first (Tier 0)
  2. Pull skills from curated public GitHub repositories
  3. Create new skills from scratch when nothing existing fits
  4. Push new/updated skills back to the personal repo
  5. List, update, and remove installed skills
  6. Log growth entries after significant tasks

Usage:
  python skills_manager.py list
  python skills_manager.py pull <github_repo_url> [--skill <skill_name>]
  python skills_manager.py create <skill_name> [--description "..."]
  python skills_manager.py update <skill_name>
  python skills_manager.py remove <skill_name>
  python skills_manager.py push <skill_name>
  python skills_manager.py push --all
  python skills_manager.py log "<task> | <skill used> | <what you learned>"
  python skills_manager.py search <keyword>

Examples:
  python skills_manager.py pull https://github.com/anthropics/skills --skill content-creator
  python skills_manager.py create social-repurposer --description "Repurposes content across platforms"
  python skills_manager.py push social-repurposer
  python skills_manager.py log "built content calendar | content-creator | cadence matters more than volume"
"""

import os
import sys
import json
import shutil
import argparse
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime, timezone

# ── Configuration ─────────────────────────────────────────────────────────────

SKILLS_DIR = Path(os.environ.get("SKILLS_DIR", Path.home() / ".claude" / "skills" / "user"))
REGISTRY_FILE = SKILLS_DIR / ".registry.json"
GROWTH_LOG = SKILLS_DIR / ".growth-log.md"

# Tunde's personal skills repo — Tier 0, always checked first
PERSONAL_REPO = "https://github.com/olatundegbotosho/claude-skills"
PERSONAL_REPO_SSH = "git@github.com:olatundegbotosho/claude-skills.git"

# Skill structure
SKILL_MD = "SKILL.md"

# Curated repo catalog (in priority order)
REPO_CATALOG = {
    "tier0_personal": {
        "url": PERSONAL_REPO,
        "description": "Tunde's personal skills repo — validated, battle-tested skills",
        "priority": 0,
    },
    "tier1_anthropic": {
        "url": "https://github.com/anthropics/skills",
        "description": "Anthropic official skills — docx, pdf, pptx, xlsx, skill-creator, frontend-design, canvas-design, mcp-builder",
        "priority": 1,
    },
    "tier1_voltagent": {
        "url": "https://github.com/VoltAgent/awesome-agent-skills",
        "description": "380+ skills from Google Labs, Stripe, Cloudflare, Hugging Face, Vercel, Sentry",
        "priority": 1,
    },
    "tier2_daymade": {
        "url": "https://github.com/daymade/claude-code-skills",
        "description": "GitHub ops, markdown, diagrams, PPT, teams comms — Claude Code specific",
        "priority": 2,
    },
    "tier2_alireza": {
        "url": "https://github.com/alirezarezvani/claude-skills",
        "description": "53 domain skills: RFP responses, sales engineering, revenue ops, content-creator, brand-voice",
        "priority": 2,
    },
    "tier2_composio": {
        "url": "https://github.com/ComposioHQ/awesome-claude-skills",
        "description": "MCP builder, git workflows, TDD, software architecture, D3 visualization",
        "priority": 2,
    },
    "tier2_travisvn": {
        "url": "https://github.com/travisvn/awesome-claude-skills",
        "description": "Curated discovery list — use when you need to find a skill name",
        "priority": 2,
    },
    "tier3_abubakarsiddik": {
        "url": "https://github.com/abubakarsiddik31/claude-skills-collection",
        "description": "Broad community collection — edge cases and niche formats",
        "priority": 3,
    },
    "tier3_smartnews": {
        "url": "https://github.com/smartnews/claude-skills",
        "description": "Additional creative and enterprise workflow examples",
        "priority": 3,
    },
}

# ── Registry helpers ──────────────────────────────────────────────────────────

def load_registry() -> dict:
    if REGISTRY_FILE.exists():
        with open(REGISTRY_FILE) as f:
            return json.load(f)
    return {}


def save_registry(registry: dict):
    REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(REGISTRY_FILE, "w") as f:
        json.dump(registry, f, indent=2)


# ── Git helpers ───────────────────────────────────────────────────────────────

def git_run(args: list[str], cwd: Path = None, silent: bool = False) -> tuple[int, str, str]:
    result = subprocess.run(
        ["git"] + args,
        capture_output=True, text=True,
        cwd=str(cwd) if cwd else None
    )
    if not silent and result.returncode != 0:
        print(f"  git {' '.join(args)} failed:\n{result.stderr.strip()}")
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def clone_repo(repo_url: str, target_dir: Path) -> bool:
    print(f"  Cloning {repo_url} ...")
    code, _, err = git_run(["clone", "--depth", "1", repo_url, str(target_dir)])
    if code != 0:
        print(f"  ✗ Clone failed: {err}")
        return False
    return True


def find_skills_in_repo(repo_dir: Path) -> list[str]:
    search_roots = [
        repo_dir,
        repo_dir / "skills",
        repo_dir / "user",
        repo_dir / "public",
        repo_dir / "document-skills",
    ]
    found = []
    for root in search_roots:
        if not root.exists():
            continue
        for item in root.iterdir():
            if item.is_dir() and (item / SKILL_MD).exists():
                found.append(item.name)
    return list(set(found))


def locate_skill_dir(repo_dir: Path, skill_name: str) -> Path | None:
    search_roots = [
        repo_dir,
        repo_dir / "skills",
        repo_dir / "user",
        repo_dir / "public",
        repo_dir / "document-skills",
    ]
    for root in search_roots:
        candidate = root / skill_name
        if candidate.is_dir() and (candidate / SKILL_MD).exists():
            return candidate
    return None


# ── Core commands ─────────────────────────────────────────────────────────────

def cmd_list():
    """List all installed skills."""
    registry = load_registry()

    if not registry:
        if SKILLS_DIR.exists():
            dirs = [d.name for d in SKILLS_DIR.iterdir() if d.is_dir() and not d.name.startswith(".")]
            if dirs:
                print(f"Skills found in {SKILLS_DIR} (not in registry):")
                for d in sorted(dirs):
                    print(f"  • {d}")
                return
        print("No skills installed yet.")
        print(f"  Try: python skills_manager.py pull https://github.com/anthropics/skills --skill content-creator")
        return

    print(f"Installed skills ({len(registry)}):\n")
    for name, meta in sorted(registry.items()):
        tier = "🏠 personal" if meta.get("source") == PERSONAL_REPO else \
               "⭐ official" if "anthropics" in meta.get("source", "") else \
               "📦 community" if meta.get("source") == "created-locally" else "🔗 external"
        print(f"  • {name}  [{tier}]")
        print(f"    Source:    {meta.get('source', 'unknown')}")
        print(f"    Installed: {meta.get('installed_at', 'unknown')}")
        print()


def cmd_search(keyword: str):
    """Search installed skills and repo catalog for a keyword."""
    keyword_lower = keyword.lower()

    print(f"Searching for '{keyword}'...\n")

    # Search installed skills
    registry = load_registry()
    matches = [name for name in registry if keyword_lower in name.lower()]
    if matches:
        print(f"✓ Found in installed skills: {', '.join(matches)}")
    else:
        print("✗ Not found in installed skills.")

    # Search repo catalog descriptions
    print("\nRepos most likely to have this skill:")
    for key, meta in sorted(REPO_CATALOG.items(), key=lambda x: x[1]["priority"]):
        if keyword_lower in meta["description"].lower() or keyword_lower in key.lower():
            print(f"  [{meta['priority']}] {meta['url']}")
            print(f"      {meta['description']}")

    print(f"\nTo pull, run:")
    print(f"  python skills_manager.py pull <repo_url> --skill {keyword_lower.replace(' ', '-')}")


def cmd_pull(repo_url: str, skill_name: str | None = None):
    """Pull one or all skills from a public GitHub repo."""
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    registry = load_registry()

    with tempfile.TemporaryDirectory() as tmpdir:
        repo_dir = Path(tmpdir) / "repo"
        if not clone_repo(repo_url, repo_dir):
            sys.exit(1)

        if skill_name:
            skills_to_install = [skill_name]
        else:
            skills_to_install = find_skills_in_repo(repo_dir)
            if not skills_to_install:
                print("  ✗ No skills found in this repository.")
                sys.exit(1)
            print(f"  Found {len(skills_to_install)} skill(s): {', '.join(skills_to_install)}")

        installed = []
        for name in skills_to_install:
            src = locate_skill_dir(repo_dir, name)
            if src is None:
                print(f"  ✗ Skill '{name}' not found in repo. Skipping.")
                continue

            dest = SKILLS_DIR / name
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(src, dest)

            registry[name] = {
                "source": repo_url,
                "installed_at": datetime.now(timezone.utc).isoformat(),
                "path": str(dest),
            }
            installed.append(name)
            print(f"  ✓ Installed: {name}")

    save_registry(registry)
    if installed:
        print(f"\n✅ Done. Push to personal repo with:")
        print(f"   python skills_manager.py push {installed[0]}" if len(installed) == 1 else
              f"   python skills_manager.py push --all")


def cmd_create(skill_name: str, description: str = ""):
    """Scaffold a new skill folder with a template SKILL.md."""
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    skill_dir = SKILLS_DIR / skill_name
    scripts_dir = skill_dir / "scripts"

    if skill_dir.exists():
        print(f"  ✗ Skill '{skill_name}' already exists. Use `update` or remove it first.")
        sys.exit(1)

    skill_dir.mkdir(parents=True)
    scripts_dir.mkdir()

    skill_md = skill_dir / SKILL_MD
    skill_md.write_text(f"""---
name: {skill_name}
description: |
  {description or f"[Describe what the {skill_name} skill does and when Claude Code should use it.]"}
---

# {skill_name.replace("-", " ").title()}

## When to Use
[Describe trigger patterns — what user requests or task types should activate this skill.]

## Dependencies
[List any pip packages, npm modules, or system tools needed.]
```bash
pip install <package> --break-system-packages
```

## Workflow

### Step 1 — [First step]
[Instructions]

```python
# Example
```

### Step 2 — [Second step]
[Instructions]

## Output Format
[Describe what the output looks like and where it goes.]

## Notes
- Created: {datetime.now(timezone.utc).strftime("%Y-%m-%d")}
- Author: Claude Code (Tunde Gbotosho)
- [Add any caveats, edge cases, or tips here]

## Social Media Engine Integration
[If this skill connects to the social media engine, describe how here. Otherwise remove this section.]
""")

    placeholder = scripts_dir / f"{skill_name.replace('-', '_')}.py"
    placeholder.write_text(f"""#!/usr/bin/env python3
\"\"\"
{skill_name} skill — main script
Generated by skills_manager.py
\"\"\"

def main():
    pass

if __name__ == "__main__":
    main()
""")

    registry = load_registry()
    registry[skill_name] = {
        "source": "created-locally",
        "installed_at": datetime.now(timezone.utc).isoformat(),
        "path": str(skill_dir),
    }
    save_registry(registry)

    print(f"✅ Skill scaffolded: {skill_dir}")
    print(f"   Edit: {skill_md}")
    print(f"   Then push: python skills_manager.py push {skill_name}")


def cmd_push(skill_name: str | None = None, push_all: bool = False):
    """
    Push skill(s) to Tunde's personal GitHub repo.
    Initializes the repo if it doesn't exist yet.
    """
    personal_dir = SKILLS_DIR.parent / "personal-repo"
    personal_dir.mkdir(parents=True, exist_ok=True)

    # Init or pull personal repo
    if not (personal_dir / ".git").exists():
        print(f"Initializing personal skills repo at {personal_dir} ...")
        git_run(["init"], cwd=personal_dir)
        git_run(["remote", "add", "origin", PERSONAL_REPO], cwd=personal_dir)

        # Try to pull if remote exists
        code, _, _ = git_run(["pull", "origin", "main", "--allow-unrelated-histories"], cwd=personal_dir, silent=True)
        if code != 0:
            # First push — set up README
            readme = personal_dir / "README.md"
            if not readme.exists():
                readme.write_text("""# Claude Skills — @olatundegbotosho

Personal skills library for Claude Code. Auto-managed by skills_manager.py.

Each folder is a self-contained skill with a SKILL.md and optional scripts/.

## Focus Areas
- Social media engine (content creation, repurposing, scheduling, analytics)
- Motive Power / NPUC consulting workflows
- RFP responses and business development
- Publishing and author platform

Skills sourced from: Anthropic, VoltAgent, daymade, alirezarezvani, ComposioHQ, and custom-built.
""")
            git_run(["add", "README.md"], cwd=personal_dir)
            git_run(["commit", "-m", "init: personal skills repo"], cwd=personal_dir)
    else:
        print("Syncing personal repo ...")
        git_run(["pull", "origin", "main", "--rebase"], cwd=personal_dir, silent=True)

    # Determine which skills to push
    registry = load_registry()
    if push_all:
        skills_to_push = list(registry.keys())
    elif skill_name:
        skills_to_push = [skill_name]
    else:
        print("Specify a skill name or use --all")
        sys.exit(1)

    pushed = []
    for name in skills_to_push:
        src = SKILLS_DIR / name
        if not src.exists():
            print(f"  ✗ Skill '{name}' not found locally. Skipping.")
            continue

        dest = personal_dir / "skills" / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest)
        pushed.append(name)
        print(f"  ✓ Staged: {name}")

    if not pushed:
        print("Nothing to push.")
        return

    # Copy registry too
    shutil.copy2(REGISTRY_FILE, personal_dir / ".registry.json")

    # Commit and push
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    msg = f"update skills: {', '.join(pushed)} [{timestamp}]"
    git_run(["add", "-A"], cwd=personal_dir)
    code, _, _ = git_run(["commit", "-m", msg], cwd=personal_dir)
    if code != 0:
        print("  Nothing new to commit.")
        return

    code, _, err = git_run(["push", "origin", "main"], cwd=personal_dir)
    if code != 0:
        # Try push with upstream set
        git_run(["push", "--set-upstream", "origin", "main"], cwd=personal_dir)

    print(f"\n✅ Pushed {len(pushed)} skill(s) to {PERSONAL_REPO}")


def cmd_update(skill_name: str):
    """Re-pull a skill from its original source."""
    registry = load_registry()
    if skill_name not in registry:
        print(f"  ✗ Skill '{skill_name}' not found. Use `list` to see installed skills.")
        sys.exit(1)

    source = registry[skill_name].get("source")
    if source in ("created-locally", PERSONAL_REPO):
        print(f"  Skill '{skill_name}' is locally managed. Edit it directly at:")
        print(f"  {SKILLS_DIR / skill_name / SKILL_MD}")
        return

    print(f"Updating '{skill_name}' from {source} ...")
    cmd_pull(source, skill_name)


def cmd_remove(skill_name: str):
    """Remove an installed skill."""
    skill_dir = SKILLS_DIR / skill_name
    if not skill_dir.exists():
        print(f"  ✗ Skill '{skill_name}' not found.")
        sys.exit(1)

    shutil.rmtree(skill_dir)
    registry = load_registry()
    registry.pop(skill_name, None)
    save_registry(registry)
    print(f"✅ Removed skill: {skill_name}")


def cmd_log(entry: str):
    """Append a growth log entry."""
    GROWTH_LOG.parent.mkdir(parents=True, exist_ok=True)
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    line = f"{date} | {entry}\n"

    if not GROWTH_LOG.exists():
        GROWTH_LOG.write_text("# Claude Code Growth Log\n\nDate | Task | Skill | Learning\n---|---|---|---\n")

    with open(GROWTH_LOG, "a") as f:
        f.write(line)

    print(f"✅ Logged: {line.strip()}")


def cmd_catalog():
    """Print the full repo catalog."""
    print("Skills Repo Catalog (priority order):\n")
    for key, meta in sorted(REPO_CATALOG.items(), key=lambda x: x[1]["priority"]):
        tier_label = ["🏠 Tier 0 Personal", "⭐ Tier 1 Official", "🥈 Tier 2 Quality", "🥉 Tier 3 Community"][meta["priority"]]
        print(f"  [{tier_label}] {meta['url']}")
        print(f"   {meta['description']}\n")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Claude Code Skills Manager — pull, create, push, and manage skills.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="List all installed skills")

    p_search = subparsers.add_parser("search", help="Search for a skill by keyword")
    p_search.add_argument("keyword")

    p_pull = subparsers.add_parser("pull", help="Pull skill(s) from a GitHub repo")
    p_pull.add_argument("repo_url")
    p_pull.add_argument("--skill", help="Specific skill to pull (default: all)")

    p_create = subparsers.add_parser("create", help="Scaffold a new skill locally")
    p_create.add_argument("skill_name")
    p_create.add_argument("--description", default="")

    p_push = subparsers.add_parser("push", help="Push skill(s) to personal GitHub repo")
    p_push.add_argument("skill_name", nargs="?")
    p_push.add_argument("--all", action="store_true", dest="push_all")

    p_update = subparsers.add_parser("update", help="Re-pull a skill from its source")
    p_update.add_argument("skill_name")

    p_remove = subparsers.add_parser("remove", help="Remove a skill")
    p_remove.add_argument("skill_name")

    p_log = subparsers.add_parser("log", help="Append a growth log entry")
    p_log.add_argument("entry", help="Format: 'task | skill used | what you learned'")

    subparsers.add_parser("catalog", help="Print the full repo catalog")

    args = parser.parse_args()

    if args.command == "list":        cmd_list()
    elif args.command == "search":    cmd_search(args.keyword)
    elif args.command == "pull":      cmd_pull(args.repo_url, args.skill)
    elif args.command == "create":    cmd_create(args.skill_name, args.description)
    elif args.command == "push":      cmd_push(args.skill_name, args.push_all)
    elif args.command == "update":    cmd_update(args.skill_name)
    elif args.command == "remove":    cmd_remove(args.skill_name)
    elif args.command == "log":       cmd_log(args.entry)
    elif args.command == "catalog":   cmd_catalog()


if __name__ == "__main__":
    main()

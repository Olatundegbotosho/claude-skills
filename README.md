# Claude Skills — Tunde Gbotosho

Personal skills repository for Claude Code — autonomous agent configuration, skills manager, and installed skill library.

## Structure
```
├── CLAUDE.md               ← global Claude Code config & autonomy directives
├── skills_manager.py       ← CLI tool to install, pull, create, and push skills
└── skills/
    └── user/               ← installed & created skills live here
        └── .registry.json  ← tracks skill sources and install dates
```

## Quick Start
```bash
python ~/.claude/skills_manager.py list
python ~/.claude/skills_manager.py pull <repo_url> --skill <skill_name>
python ~/.claude/skills_manager.py create <skill_name> --description "..."
```

## Priority Project
**Social Media Engine** — autonomous content generation across LinkedIn, X, Instagram, and newsletter for Motive Power / NPUC, Connecting Bridges Publishing, and AI consulting.

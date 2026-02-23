---
name: research-synthesizer
description: Use when converting raw research (URLs, PDFs, transcripts, notes, competitor posts) into structured content briefs with niche-specific angles. Called before drafting any post, newsletter, or article to ensure content is grounded in evidence, not conjecture.
---

# Research Synthesizer

## Overview

Transforms raw research inputs (URLs, text, notes, transcripts) into a structured content brief — summarized insights, key facts, niche-relevant angles, and a recommended hook type. The brief feeds directly into the post/newsletter generation pipeline.

**Core principle:** Opinion without evidence is noise. Research without synthesis is a pile. This turns piles into posts.

---

## When to Use

- Before drafting any long-form post, article, or newsletter
- When repurposing research from reports, podcasts, or competitor content
- When you have a URL or PDF and need to extract content-relevant insights fast
- When multiple sources need to be synthesized into a single coherent angle
- As the first step in the full pipeline: Research → Synthesize → Hook → Draft → Voice Check

---

## Input Types Supported

| Input Type | How to Pass |
|-----------|-------------|
| URL | `--url https://...` |
| Text/notes | `--text "paste raw notes here"` |
| File (.txt, .md, .pdf path) | `--file path/to/source.md` |
| Multiple sources | `--url ... --url ... --text "..."` (combined) |

---

## Output: Content Brief Structure

```
═══════════════════════════════════════════
RESEARCH BRIEF
═══════════════════════════════════════════
Niche:     ttbp
Platform:  linkedin

SOURCE SUMMARY
───────────────────────────────────────────
[Condensed 3-5 sentence summary of the source material]

KEY FACTS & QUOTABLES (≤5)
  • [Specific stat, claim, or quote worth using]
  • [...]

CONTENT ANGLES (per niche voice)
  1. [Angle 1 — ties source to niche's core audience concern]
  2. [Angle 2 — contrarian or unexpected framing]
  3. [Angle 3 — personal story entry point]

RECOMMENDED HOOK TYPE
  → bold_claim | curiosity_gap | personal_story | ...
  → Reasoning: [1 sentence]

SUGGESTED TAGS / CLUSTERS
  → [topic cluster 1], [topic cluster 2]

VOICE FLAGS
  ⚠️  [Any source language that's too corporate/banned — flag before use]
  ✅  [Any source language that's already niche-aligned — usable directly]

═══════════════════════════════════════════
```

---

## Usage

```bash
# Synthesize a URL
python research_synth.py --niche ttbp --url https://hbr.org/article --platform linkedin

# Synthesize raw notes
python research_synth.py --niche tundexai --text "GPT-4 benchmark results show..."

# Synthesize a local file
python research_synth.py --niche cb --file notes/chinua_achebe_research.md

# Multi-source synthesis
python research_synth.py --niche ttbp --url https://... --text "Additional context..." --platform newsletter

# JSON output (for pipeline integration)
python research_synth.py --niche ttbp --url https://... --json
```

---

## Pipeline Integration

```python
# In repurpose.py or any content generation flow
from research_synth import synthesize

brief = synthesize(
    niche="ttbp",
    sources=[{"type": "url", "content": "https://hbr.org/..."}],
    platform="linkedin"
)

# Feed brief into hook generator
from hook_gen import generate_hooks
hooks = generate_hooks(niche="ttbp", topic=brief.primary_angle, platform="linkedin")

# Feed brief + best hook into post writer
best_hook = hooks.top_hook.text
post = draft_linkedin_post(niche="ttbp", hook=best_hook, brief=brief)
```

---

## Extraction Rules

The synthesizer applies these rules when extracting from source material:

1. **Facts over opinions** — Extract verifiable claims with numbers, names, dates
2. **Niche angle filter** — Skip insights irrelevant to the target niche's audience
3. **Voice pre-check** — Flag any banned phrases found in source text before they contaminate drafts
4. **Quotable detection** — Identify short, punchable statements worth direct attribution
5. **Gap detection** — Note what the source *doesn't* address (often the best angle)

---

## File Structure

```
research-synthesizer/
  SKILL.md
  scripts/
    research_synth.py    ← main synthesizer
```

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Drafting before synthesizing | Brief first, always — it forces angle selection before word count |
| Using the source summary as the post | The brief is scaffolding, not the output |
| Ignoring VOICE FLAGS section | Source language often leaks banned phrases into drafts |
| One source only | Two sources create tension; tension creates better angles |

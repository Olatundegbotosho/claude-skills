---
name: newsletter-writer
description: Use when drafting newsletter issues for any of the 5 niches across Substack, ConvertKit, Beehiiv, or ContentStudio — produces a niche-voiced draft plus platform-ready export (markdown for Substack manual post, JSON API payload for automated platforms).
---

# Newsletter Writer

## Overview

Drafts full newsletter issues from a content brief, research summary, or topic prompt. Enforces niche voice, produces structured content, and exports in the right format for the target platform.

**Core principle:** Every issue has one core insight the reader couldn't have Googled. Everything else serves that insight.

---

## When to Use

- Drafting a weekly or one-off newsletter for any niche
- Converting a content brief (from research-synthesizer) into a full issue
- Repurposing a LinkedIn post or article into a longer newsletter form
- When you need platform-ready output (Substack markdown or API JSON)
- As the third step in the pipeline: Research → Synthesize → **Newsletter Draft** → Voice Check

---

## Supported Platforms

| Platform | Transport | Output Format |
|----------|-----------|---------------|
| `substack` | Manual (paste) | Markdown file |
| `convertkit` | API (POST `/broadcasts`) | JSON payload |
| `beehiiv` | API (POST `/publications/{id}/emails`) | JSON payload |
| `contentstudio` | API (POST `/article`) | JSON payload |

Substack: Claude writes → you paste. ConvertKit/Beehiiv/ContentStudio: JSON payload → automated send.

---

## Newsletter Structure (all niches)

```
═══════════════════════════════════════════
NEWSLETTER DRAFT
═══════════════════════════════════════════
Niche:      [ttbp|cb|tundexai|wellwithtunde|tundestalksmen]
Platform:   [substack|convertkit|beehiiv|contentstudio]
Issue No.:  [#N or draft]
Subject:    [subject line — tested against open rate heuristics]
Preview:    [50–90 char preview text — what subscribers see before opening]

───────────────────────────────────────────
FULL DRAFT
───────────────────────────────────────────
[Opening hook — 1–2 sentences, no preamble]

[Body — 3–5 paragraphs, clear sections, niche voice enforced]

[Closing CTA — specific, one ask only]

───────────────────────────────────────────
SUBJECT LINE VARIANTS (3 options)
  A. [Primary — direct, specific]
  B. [Curiosity gap variant]
  C. [Personal story variant]

VOICE SCORE (pre-check)
  → [Score/100] [PASS|REVISE|HEAVY REVISE]
  → [Any flagged issues]

PLATFORM EXPORT
  → [Markdown file path OR JSON payload]
═══════════════════════════════════════════
```

---

## Niche Newsletter Defaults

| Niche | Length Target | Tone | Signature Format |
|-------|--------------|------|-----------------|
| `ttbp` | 500–900 words | Confident, personal | Insight → Evidence → Implication → CTA |
| `cb` | 400–700 words | Cultural, literary | Book angle → Broader meaning → What to read next |
| `tundexai` | 600–1000 words | Analytical, direct | Claim → Benchmark → Framework → Takeaway |
| `wellwithtunde` | 400–650 words | Warm, sustainable | Observation → Body connection → One practice |
| `tundestalksmen` | 450–750 words | Direct, accountable | Tension → What men don't say → The ask |

---

## Usage

```bash
# From a topic
python newsletter_writer.py --niche ttbp --topic "why middle managers plateau" --platform substack

# From a research brief (JSON from research_synth.py)
python newsletter_writer.py --niche tundexai --brief brief.json --platform beehiiv

# From a text prompt
python newsletter_writer.py --niche cb --text "Chinua Achebe and the decolonizing of African literature" --platform convertkit

# With issue number
python newsletter_writer.py --niche ttbp --topic "..." --platform substack --issue 47

# JSON output (for pipeline)
python newsletter_writer.py --niche ttbp --topic "..." --platform contentstudio --json
```

---

## Output Files

| Mode | Output |
|------|--------|
| Substack | `output/newsletter_{niche}_{date}.md` — paste-ready markdown |
| ConvertKit | `output/newsletter_{niche}_{date}_convertkit.json` |
| Beehiiv | `output/newsletter_{niche}_{date}_beehiiv.json` |
| ContentStudio | `output/newsletter_{niche}_{date}_contentstudio.json` |
| `--json` flag | Prints full `NewsletterDraft` dataclass as JSON to stdout |

---

## Pipeline Integration

```python
from research_synth import synthesize
from newsletter_writer import draft_newsletter

# Step 1: Synthesize research
brief = synthesize(niche="ttbp", sources=[{"type": "url", "content": "https://..."}], platform="newsletter")

# Step 2: Draft newsletter
draft = draft_newsletter(
    niche="ttbp",
    platform="beehiiv",
    topic=brief.primary_angle,
    research_brief=brief
)

# Step 3: Validate voice
if draft.voice_score >= 85:
    print(draft.platform_payload)  # Ready to POST
else:
    print(draft.report)  # See what to fix
```

---

## Subject Line Rules

1. **Specificity beats cleverness** — name the thing, name the number
2. **Under 50 chars** for mobile-first (most opens happen on mobile)
3. **No ALL CAPS**, no excessive punctuation, no "RE:" tricks
4. **Preview text extends the subject** — treat them as one unit
5. **Banned subject openers:** "This week...", "Issue #N:", "Hello,", "Just wanted to..."

---

## File Structure

```
newsletter-writer/
  SKILL.md
  scripts/
    newsletter_writer.py    ← main writer + platform export
```

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Writing for the whole world | Every issue speaks to one type of person — name them in your head |
| Subject line as title | Subject lines are promises, not labels |
| Ignoring preview text | Preview is free real estate — use it to finish the subject's thought |
| Multiple CTAs | One ask. Period. Two asks = zero action. |
| Using research brief as the draft | Brief is scaffolding — the issue needs a human angle the brief doesn't have |

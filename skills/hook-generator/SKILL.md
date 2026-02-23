---
name: hook-generator
description: Use when generating opening hooks for any social media post, newsletter, or LinkedIn article — especially before repurposing content or when a draft has a weak first line. Generates 8 typed hook variants per topic, scored and ranked for the target niche and platform.
---

# Hook Generator

## Overview

Generates 8 opening hook variants for any topic, one per hook archetype. Each hook is scored (0–10) and tagged with its type. The highest-scoring hook that doesn't violate Voice DNA is recommended for use. Called before full post drafting — not after.

**Core principle:** The hook is the post. If the first line doesn't earn the second, nothing else matters.

---

## When to Use

- Before drafting any LinkedIn post, Twitter thread, or newsletter
- When `repurpose.py` generates content and confidence score is below 85
- When reviewing a draft whose first line starts with a banned opener
- When you have a topic/angle but no clear entry point
- When you need to A/B test opening approaches for a single topic

---

## Hook Types (8 Archetypes)

| Type | Pattern | Best For |
|------|---------|----------|
| `curiosity_gap` | State what's missing from common knowledge | LinkedIn, newsletter |
| `bold_claim` | Make a specific, provable claim that challenges consensus | LinkedIn, Twitter |
| `personal_story` | Open mid-scene with a real moment | All platforms |
| `data_shock` | Lead with a surprising number or stat | LinkedIn, newsletter |
| `pattern_interrupt` | Subvert the expected frame | Twitter, Instagram |
| `question` | A sharp question that demands an answer | All platforms |
| `contrarian` | Name the popular belief, then reject it | Twitter, LinkedIn |
| `number_list` | Promise a specific, finite payoff | LinkedIn, newsletter |

---

## Scoring Criteria (per hook, 0–10)

| Criterion | Weight | What It Checks |
|-----------|--------|----------------|
| Specificity | 30% | Named details, real numbers, precise claims > vague generalities |
| Voice alignment | 25% | Matches niche tone — no banned phrases, fits green flag patterns |
| Tension | 25% | Creates a gap the reader needs to close by reading further |
| Platform fit | 20% | Length appropriate, format suits the platform's scroll behavior |

Score ≥ 7 → Recommended
Score 5–6 → Use with revision
Score < 5 → Discard

---

## Usage

```bash
# Generate all 8 hooks for a topic
python hook_gen.py --niche ttbp --topic "why most people plateau at middle management" --platform linkedin

# With additional context/angle
python hook_gen.py --niche tundexai --topic "RAG implementations" --context "most are just expensive search" --platform linkedin

# Output top N hooks only
python hook_gen.py --niche cb --topic "reading diaspora fiction" --top 3

# JSON output (for pipeline integration)
python hook_gen.py --niche ttbp --topic "burnout and ambition" --platform linkedin --json

# Score an existing hook
python hook_gen.py --niche ttbp --score-hook "In today's fast-paced world, burnout is everywhere."
```

---

## Output Format

```
═══════════════════════════════════════════
HOOK GENERATOR REPORT
═══════════════════════════════════════════
Niche:     ttbp
Platform:  linkedin
Topic:     why most people plateau at middle management

8 HOOKS GENERATED
───────────────────────────────────────────
[1] CURIOSITY GAP          Score: 8.5  ★ RECOMMENDED
    "Nobody talks about the moment you realize you've hit your organizational ceiling — not a failure moment, a clarity moment."
    → Specificity: high | Tension: strong | Voice: clean

[2] BOLD CLAIM             Score: 7.8
    "Most middle managers are optimizing for the wrong promotion."
    → Specific claim, invites disagreement, earns the scroll

[3] PERSONAL STORY         Score: 7.2
    "I sat across from a VP role at 34 and realized I didn't actually want it."
    → Scene-first, no setup needed, platform-appropriate

[4] DATA SHOCK             Score: 6.8
    "70% of managers say they feel underprepared for their current role. Nobody told them before they got there."
    → Stat + implication structure

[5] PATTERN INTERRUPT      Score: 6.5
    "You didn't plateau. The system did exactly what it was designed to do."
    → Reframes blame, creates cognitive tension

[6] QUESTION               Score: 6.1
    "What if the ceiling you've hit isn't a glass ceiling — it's a mirror?"
    → Metaphor may be too abstract for LinkedIn; sharpen if used

[7] CONTRARIAN             Score: 5.9
    "The career advice industry tells you to develop executive presence. That's not why people plateau."
    → Good direction but \"career advice industry\" is vague; name a specific source

[8] NUMBER LIST            Score: 5.4
    "3 reasons your manager stopped sponsoring you — and none of them are about your work."
    → Serviceable but follows a common pattern; combine with data for lift

═══════════════════════════════════════════
```

---

## Pipeline Integration

```python
# In repurpose.py or any generation script
from hook_gen import generate_hooks

result = generate_hooks(
    niche="ttbp",
    topic="why most people plateau at middle management",
    platform="linkedin"
)

# Use top-scored hook as post opener
best = result.top_hook
if best.score >= 7.0:
    post_draft = best.text + "\n\n" + body_content
else:
    print(result.report)  # Show all options for manual selection
```

---

## Niche-Specific Hook Guidance

| Niche | Best Hook Types | Avoid |
|-------|----------------|-------|
| `ttbp` | personal_story, bold_claim, curiosity_gap | number_list as sole hook |
| `cb` | curiosity_gap, personal_story, contrarian | data_shock (wrong tone) |
| `tundexai` | bold_claim, data_shock, contrarian | personal_story unless tied to field experience |
| `wellwithtunde` | personal_story, question, pattern_interrupt | bold_claim that could read as prescriptive |
| `tundestalksmen` | personal_story, pattern_interrupt, bold_claim | question that centers feelings alone |

---

## File Structure

```
hook-generator/
  SKILL.md
  scripts/
    hook_gen.py    ← main generator
```

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Using hook as a creative exercise, not a validation gate | Score every hook before using it — even ones that "feel right" |
| Picking the most clever hook instead of the most specific one | Specificity score matters more than elegance |
| Writing the same hook type every time | Rotate types across posts to avoid audience fatigue |
| Ignoring the Voice DNA banned openers list | `hook_gen.py` catches these — trust the score |

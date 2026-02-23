---
name: linkedin-post-writer
description: Use when drafting LinkedIn posts for any of the 5 niches — enforces the algorithm-aware hook/body/CTA structure, niche voice, character limits, and dwell-time signals. Called before any LinkedIn content goes live.
---

# LinkedIn Post Writer

## Overview

Drafts LinkedIn posts optimized for both voice and platform algorithm. Enforces the first-3-lines hook rule, manages character limits, and builds dwell-time signals into the structure.

**Core principle:** The hook earns the "see more" click. The body earns the share. The CTA earns the comment that feeds the algorithm.

---

## When to Use

- Drafting any original LinkedIn post for the 5 niches
- Repurposing a newsletter excerpt, research brief, or article into LinkedIn format
- When `repurpose.py` targets `platform: linkedin`
- Before scheduling any LinkedIn content

---

## LinkedIn Algorithm Rules (baked into all output)

| Signal | What LinkedIn Rewards | How to Trigger It |
|--------|----------------------|-------------------|
| **Dwell time** | Time spent reading (not just scanning) | Specific details, numbered insights, white space between lines |
| **Comments** | Text replies (not emoji reactions) | End with a direct question or provocation |
| **Saves** | Bookmark icon clicks | Practical frameworks, specific lists, reference content |
| **Shares** | Manual reposts | Contrarian takes, surprising data, things worth being seen sharing |
| **Golden hour** | First 60 min engagement | Post between 7–9am or 5–7pm on Tue/Wed/Thu |

---

## Post Structure

```
LINE 1-3: Hook (shows before "see more" — make them click)
[blank line]
BODY: Insight development — white space after every 1-2 lines
[blank line]
CTA: One question or one direct ask
[blank line]
HASHTAGS: 3–5 max, placed at the bottom
```

### Character Rules
- **Total max:** 3000 chars (hard LinkedIn limit)
- **Sweet spot:** 900–1800 chars for engagement
- **Hook (first 3 lines):** Under 200 chars total — or use a single punch line
- **Hashtags:** 3–5, always last, always relevant

---

## Niche LinkedIn Defaults

| Niche | Ideal Length | Best Post Types | Best Hook Style |
|-------|-------------|-----------------|-----------------|
| `ttbp` | 900–1500 chars | Observation, story, contrarian | Personal story, bold claim |
| `cb` | 700–1200 chars | Book take, cultural moment | Curiosity gap, contrarian |
| `tundexai` | 1000–1800 chars | Framework, benchmark, how-to | Data shock, bold claim |
| `wellwithtunde` | 700–1100 chars | Observation, practice, reframe | Pattern interrupt, question |
| `tundestalksmen` | 800–1400 chars | Story, accountability moment | Personal story, bold claim |

---

## Usage

```bash
# From a topic
python linkedin_writer.py --niche ttbp --topic "why middle managers plateau"

# From notes/context
python linkedin_writer.py --niche tundexai --text "Claude 3.5 Sonnet benchmark notes..."

# With specific hook type
python linkedin_writer.py --niche cb --topic "Chinua Achebe and the Western canon" --hook-type contrarian

# From a research brief JSON
python linkedin_writer.py --niche tundexai --brief brief.json

# Generate 3 variants
python linkedin_writer.py --niche ttbp --topic "..." --variants 3

# JSON output (for pipeline)
python linkedin_writer.py --niche ttbp --topic "..." --json
```

---

## Output Format

```
═══════════════════════════════════════════
LINKEDIN POST DRAFT
═══════════════════════════════════════════
Niche:      ttbp
Topic:      why middle managers plateau
Hook Type:  personal_story    [Score: 8.2]

POST (1,143 chars)
───────────────────────────────────────────
I sat across from a VP offer at 34.

And realized I didn't actually want it.

Not because the role was wrong — because I'd been optimizing for the wrong signal. Title, not scope. Visibility, not influence.

Here's what I see in almost every plateau story:

→ The person is talented
→ The work is good
→ The ceiling isn't made of glass

It's made of invisible criteria nobody told them about.

The moment your manager stops sponsoring you isn't always about performance. Often it's about:

1. You're not making them look good anymore
2. You've become "reliable" (read: not promotable)
3. You haven't made yourself uncomfortable recently

The people who break through aren't louder. They're more specific about what they want — and they say it out loud, to the right people, earlier than feels comfortable.

What's one thing you wish someone had told you before you hit your first ceiling?

#Leadership #CareerGrowth #ManagementInsights

───────────────────────────────────────────
VOICE CHECK:  92/100  ✅ PASS
ALGORITHM:    Dwell signals: 3 | CTA type: question | Hashtags: 3
═══════════════════════════════════════════
```

---

## Pipeline Integration

```python
from research_synth import synthesize
from linkedin_writer import draft_linkedin_post

brief = synthesize(niche="ttbp", sources=[{"type": "url", "content": "https://..."}])
post = draft_linkedin_post(
    niche="ttbp",
    topic=brief.primary_angle,
    hook_type=brief.recommended_hook_type,
    research_brief=brief,
)

if post.voice_score >= 85:
    print(post.text)  # Ready to copy-paste
```

---

## File Structure

```
linkedin-post-writer/
  SKILL.md
  scripts/
    linkedin_writer.py    ← main writer
```

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Starting with "I" as the very first word | Start with the situation, then bring yourself in |
| Wall of text, no line breaks | One idea per visual block — white space is free real estate |
| Asking 2+ questions | One question only. Two = zero answers. |
| Generic hashtags (#business, #success) | Specific pillars only: #Leadership, #AIStrategy, #AfricanLiterature |
| Posting and leaving | Engage with every comment in the first 60 min — it reactivates reach |

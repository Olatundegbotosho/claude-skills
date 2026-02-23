---
name: voice-enforcer
description: Use when validating any generated content against Tunde Gbotosho's Voice DNA before publishing, scheduling, or approving. Catches banned phrases, missing green flags, tone drift, and platform format violations across all 5 niches.
---

# Voice Enforcer

## Overview

Validates any piece of content against the Voice DNA for a given niche. Returns a score (0–100), a verdict, and specific actionable feedback. Called after generation — before export, scheduling, or publishing.

**Core principle:** Content that doesn't sound like Tunde doesn't get posted. This runs on everything.

## When to Use

- After `repurpose.py` generates any platform content
- Before any ContentStudio import or API push
- When manually reviewing AI-generated drafts
- As the final check in any content pipeline step
- When confidence score from `repurpose.py` is below 85

## Verdict Thresholds

| Score | Verdict | Action |
|-------|---------|--------|
| 85–100 | **PASS** | Clear for scheduling/publishing |
| 70–84 | **REVISE** | Fix specific issues flagged, re-score |
| 50–69 | **HEAVY REVISE** | Significant rewrite needed |
| 0–49 | **REJECT** | Regenerate from scratch |

## Usage

```bash
# Validate a single file
python voice_validator.py --niche ttbp --file output/linkedin_post.md

# Validate inline text
python voice_validator.py --niche tundexai --text "Your content here..."

# Validate all files in an output directory
python voice_validator.py --niche cb --dir output/cb_ai_books_2026-W08/

# Score only (no detailed feedback)
python voice_validator.py --niche ttbp --file post.md --score-only

# Output JSON (for pipeline integration)
python voice_validator.py --niche ttbp --file post.md --json
```

## Scoring Criteria

| Criterion | Weight | Checks |
|-----------|--------|--------|
| Banned phrase absence | 30% | Zero banned phrases from Voice DNA |
| Green flag presence | 25% | ≥1 signature phrase or opening pattern match |
| Opening hook quality | 20% | First line does not start with banned openers |
| Tone alignment | 15% | Sentence structure, formality level, enthusiasm calibration |
| Platform fit | 10% | Length within spec, format appropriate for platform |

## Output Format

```
═══ VOICE ENFORCER REPORT ═══
Niche:    ttbp
Platform: linkedin
Score:    78/100
Verdict:  REVISE

Issues Found (2):
  ❌ [BANNED] "leverage" found at line 3 — replace with "use", "apply", or "activate"
  ⚠️  [TONE] Opening starts with "In today's..." — known AI opener, rewrite first line

Strengths (3):
  ✅ "Here's the thing..." signature phrase present
  ✅ No filler phrases detected
  ✅ Length within LinkedIn spec (847 chars)

Suggestion: Rewrite line 3 and opening line, then re-validate.
═══════════════════════════════
```

## Pipeline Integration

```python
# In repurpose.py or any generation script
from voice_validator import validate_content

result = validate_content(niche="ttbp", platform="linkedin", text=generated_text)
if result["verdict"] == "PASS":
    export_manager.write_post("linkedin", generated_text, confidence=result["score"])
else:
    print(result["report"])  # Show issues before continuing
```

## File Structure

```
voice-enforcer/
  SKILL.md
  scripts/
    voice_validator.py    ← main validator
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Validating without specifying platform | Always pass --platform; length checks are platform-specific |
| Ignoring REVISE verdicts under time pressure | A 78 with "leverage" in it will feel off to readers — fix it |
| Using score alone without reading issues | Score is a summary; the issues list is the actual fix list |
| Skipping validation on "quick" posts | Quick posts fail the same ways as long ones |

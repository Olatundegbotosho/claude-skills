---
name: seo-optimizer
description: Use when scoring, optimizing, or generating SEO metadata for any content piece — blog posts, newsletter issues, LinkedIn articles, or landing pages. Extracts primary/secondary keywords, generates meta title and description, scores heading hierarchy, readability, and topical authority. Called before publishing any long-form content or when repurposing newsletter content to a blog.
---

# SEO Optimizer

## Overview

Analyzes content for search visibility and topical authority. Produces a scored SEO report and generates ready-to-use meta tags, optimized headings, and a keyword cluster map.

**Core principle:** For a personal brand, topical authority beats keyword stuffing. Own a topic cluster completely — don't chase individual keywords.

---

## When to Use

- Before publishing any long-form blog post or article
- When repurposing a newsletter issue to a web page
- When optimizing a LinkedIn article for LinkedIn search
- After drafting content — run SEO check before final publish
- When building a content calendar and need keyword clustering

---

## SEO Signals Scored

| Signal | Weight | What It Checks |
|--------|--------|----------------|
| **Primary keyword** | 25% | In title, first 100 words, at least 1 heading |
| **Meta quality** | 20% | Title 50–60 chars, description 140–160 chars, keyword present |
| **Heading hierarchy** | 15% | H1 once, H2s present, H3s for subpoints, no skipped levels |
| **Topical coverage** | 20% | Secondary keywords and semantic variants present |
| **Readability** | 10% | Avg sentence length, paragraph breaks, subheading density |
| **Content length** | 10% | Niche-appropriate word count targets met |

Score thresholds: **OPTIMIZED** ≥85 | **GOOD** 70–84 | **NEEDS WORK** 50–69 | **WEAK** <50

---

## Niche SEO Defaults

| Niche | Primary Keyword Type | Min Word Count | Topic Cluster |
|-------|---------------------|----------------|---------------|
| `ttbp` | Career/leadership concepts | 800 | Leadership, management, career growth |
| `cb` | Author names, book titles, literary movements | 600 | African literature, publishing, cultural commentary |
| `tundexai` | AI tool names, benchmarks, framework terms | 900 | AI strategy, enterprise AI, automation |
| `wellwithtunde` | Health/body/habit terms | 600 | Holistic health, sustainable living, body connection |
| `tundestalksmen` | Men's development concepts | 700 | Men's growth, accountability, relationships |

---

## Output Format

```
═══════════════════════════════════════════
SEO REPORT
═══════════════════════════════════════════
Niche:          tundexai
Platform:       blog
Content:        "Why AI Benchmarks Lie" (1,243 words)

SEO SCORE: 81/100  ✅ GOOD
───────────────────────────────────────────
PRIMARY KEYWORD
  → "AI benchmarks"
  → In title: ✅ | In first 100 words: ✅ | In H2: ✅
  → Density: 1.4% (target: 1–2%)

META TAGS (ready to use)
  → Title (57 chars): Why AI Benchmarks Lie — And What To Trust Instead
  → Description (152 chars): Most AI benchmark scores are misleading. Here's how to read
    them correctly and what metrics actually predict real-world performance.

HEADING HIERARCHY
  → H1 (1): ✅ Why AI Benchmarks Lie
  → H2 (3): ✅ The benchmark problem | How companies game scores | What to use instead
  → H3 (2): ✅ Present
  → Issues: None

KEYWORD CLUSTER
  Primary:    AI benchmarks
  Secondary:  LLM evaluation, model performance, benchmark gaming, MMLU, HumanEval
  Missing:    "real-world AI testing" — consider adding to H2 or body

READABILITY
  → Avg sentence: 18 words (✅ under 25)
  → Subheading every: 180 words (✅ target: every 150–200 words)
  → Paragraph avg: 2.8 sentences (✅ under 4)

CONTENT LENGTH: 1,243 words (✅ above 900 min for tundexai)

RECOMMENDATIONS (3)
  1. Add "real-world AI testing" to one H2 or body paragraph
  2. Meta description could open with the primary keyword
  3. Add internal link anchor text suggestion: "AI benchmarks explained"
═══════════════════════════════════════════
```

---

## Usage

```bash
# Score existing content
python seo_optimizer.py --niche tundexai --file post.md

# Score content from text
python seo_optimizer.py --niche ttbp --text "paste content here"

# Generate meta tags only (fast mode)
python seo_optimizer.py --niche cb --text "..." --meta-only

# Full report with keyword cluster map
python seo_optimizer.py --niche tundexai --file post.md --full-report

# JSON output (for pipeline)
python seo_optimizer.py --niche ttbp --file post.md --json
```

---

## Pipeline Integration

```python
from seo_optimizer import analyze_seo, generate_meta

# After drafting content
report = analyze_seo(niche="tundexai", content=draft_text, platform="blog")

if report.score >= 70:
    print(report.meta_title)        # Ready to use
    print(report.meta_description)  # Ready to use
else:
    for rec in report.recommendations:
        print(rec)  # Fix these before publishing
```

---

## File Structure

```
seo-optimizer/
  SKILL.md
  scripts/
    seo_optimizer.py    ← main analyzer + meta generator
```

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Targeting one keyword per piece | Build topic clusters — one primary + 4–6 semantics |
| Ignoring meta description length | 140–160 chars for Google snippet; shorter = truncated |
| H1 in the body, title tag different | H1 and `<title>` should match or be close variants |
| Stuffing keywords for density | 1–2% density max; semantic variants do more work |
| No internal link strategy | Every piece should reference 1–2 others in the cluster |

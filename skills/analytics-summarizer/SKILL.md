---
name: analytics-summarizer
description: Use when generating weekly or monthly performance briefs from social media analytics — ingests ContentStudio exports or platform CSVs, identifies top/bottom performers per niche, surfaces engagement trends, compares against niche benchmarks, and outputs actionable recommendations for next week's content strategy.
---

# Analytics Summarizer

## Overview

Transforms raw social media analytics into a weekly performance brief. Scores posts against niche-specific benchmarks, ranks top/bottom performers, surfaces what content type and topic drove the most engagement, and feeds those signals back into next week's content decisions.

**Core principle:** Analytics should answer one question — *what should I do differently next week?* Everything else is noise.

---

## When to Use

- Every Monday morning — pull last week's data and generate brief before planning content
- After a content batch posts — measure performance at 48h mark
- When deciding whether to repurpose a topic — check if prior posts on it performed
- Before a quarterly strategy review — run with `--period month`
- When a post significantly over- or under-performs — run single-post deep-dive

---

## Data Sources (Priority Order)

| Source | Format | How to Get |
|--------|--------|------------|
| **ContentStudio** | JSON export or API | Dashboard → Analytics → Export |
| **LinkedIn** | CSV | Profile → Analytics → Export CSV |
| **Instagram** | CSV | Meta Business Suite → Insights → Export |
| **X/Twitter** | CSV | analytics.twitter.com → Export |
| **Manual entry** | JSON | Build with `--manual` flag |

---

## Metrics Tracked

| Metric | What It Signals |
|--------|----------------|
| **Engagement Rate** | Likes + Comments + Shares + Saves / Impressions × 100 |
| **Comment Rate** | Comments / Impressions — algorithm feed signal |
| **Save Rate** | Saves / Impressions — high-value indicator (saves = "worth keeping") |
| **Share Rate** | Shares / Impressions — virality / social proof |
| **Click-Through Rate** | Link clicks / Impressions — demand signal for the topic |
| **Reach / Impressions** | How many unique accounts saw the post |
| **Dwell Proxy** | Estimated from comment length + save rate |

---

## Niche Benchmarks (LinkedIn — what "good" looks like)

| Niche | Avg Engagement Target | Comment Rate Target | Save Rate Target |
|-------|----------------------|---------------------|------------------|
| `ttbp` | ≥ 3.0% | ≥ 0.5% | ≥ 0.3% |
| `cb` | ≥ 2.5% | ≥ 0.4% | ≥ 0.4% |
| `tundexai` | ≥ 3.5% | ≥ 0.6% | ≥ 0.5% |
| `wellwithtunde` | ≥ 2.0% | ≥ 0.3% | ≥ 0.5% |
| `tundestalksmen` | ≥ 2.5% | ≥ 0.5% | ≥ 0.4% |

---

## Output Format

```
═══════════════════════════════════════════════════════
WEEKLY ANALYTICS BRIEF
═══════════════════════════════════════════════════════
Period:     2026-02-10 → 2026-02-16
Niches:     tundexai  |  ttbp
Posts:      8 analyzed

OVERALL PERFORMANCE
  Avg Engagement Rate:  3.8%  ✅  (benchmark: 3.0%)
  Best Day:             Wednesday 7am
  Best Format:          Numbered list (4.9% avg)
  Lowest Format:        Question-only (1.2% avg)

───────────────────────────────────────────────────────
NICHE: tundexai  (4 posts)
───────────────────────────────────────────────────────

  TOP PERFORMERS
  #1  "Why Claude 3.5 Sonnet beats GPT-4o on reasoning..."
      Engmt: 5.2%  |  Comments: 23  |  Saves: 41  |  Shares: 18
      ✦ Hook type: data_shock  |  Tags: #AI #AIStrategy

  #2  "The benchmark problem no one talks about..."
      Engmt: 4.1%  |  Comments: 17  |  Saves: 29  |  Shares: 9

  BOTTOM PERFORMERS
  #1  "AI tools I tried this week — [list]"
      Engmt: 1.1%  |  Comments: 2  |  Saves: 5  |  Shares: 1
      ✦ Likely cause: weak hook + no POV

  BENCHMARK STATUS  ✅ ABOVE TARGET
    Avg: 3.8%  |  Target: 3.5%  |  Delta: +0.3%

  PATTERN DETECTED
    Posts with specific numbers → 4.6% avg
    Posts without numbers → 1.9% avg
    → Add at least one concrete data point to every post

───────────────────────────────────────────────────────
COMPETITOR SNAPSHOT (if data provided)
───────────────────────────────────────────────────────
  Competitor A  (AI Strategy):  Avg 4.2%  (+0.4% above you)
    Top topic this week: "Claude API cost breakdowns"
    → Consider: benchmark/cost comparison post next week

───────────────────────────────────────────────────────
RECOMMENDATIONS FOR NEXT WEEK
───────────────────────────────────────────────────────
  1. [tundexai]  Double down on numbered frameworks — 4.6% vs 1.9%
  2. [tundexai]  Post Wed 7am — historically 60% above avg reach
  3. [ttbp]      3 posts below benchmark — test personal-story hook vs bold-claim
  4. [both]      Saves on tundexai outpace ttbp 2:1 → content is reference-worthy
                 → Consider a LinkedIn article to capture SEO + long-form saves

HASHTAG PERFORMANCE
  Best set (tundexai):    #AI #AIStrategy #EnterpriseAI → 5.1% avg
  Worst set (ttbp):       #Business #Success → 1.1% avg (too generic)
═══════════════════════════════════════════════════════
```

---

## Usage

```bash
# Weekly brief from ContentStudio JSON export
python analytics_summarizer.py --file cs_export.json --period week

# From platform CSV (LinkedIn)
python analytics_summarizer.py --file linkedin_export.csv --source linkedin --niche tundexai

# Multi-niche brief from folder of exports
python analytics_summarizer.py --dir ./exports/ --period week

# With competitor data
python analytics_summarizer.py --file cs_export.json --competitors competitors.json

# Single-post deep dive
python analytics_summarizer.py --post-id "abc123" --file cs_export.json

# Monthly review
python analytics_summarizer.py --dir ./exports/ --period month

# JSON output (for pipeline)
python analytics_summarizer.py --file cs_export.json --json

# Feed recommendations back into content calendar
python analytics_summarizer.py --file cs_export.json --json | python content_calendar.py --analytics-feed -
```

---

## Pipeline Integration

```python
from analytics_summarizer import summarize_week, get_top_topics

# Get weekly brief
brief = summarize_week(data_path="exports/", period="week")

# Feed top topics into next week's content plan
top_topics = get_top_topics(brief, niche="tundexai", n=3)
for topic in top_topics:
    print(f"→ Consider follow-up on: {topic.title} ({topic.avg_engagement:.1f}%)")
```

---

## File Structure

```
analytics-summarizer/
  SKILL.md
  scripts/
    analytics_summarizer.py    ← main analyzer
  data/
    benchmarks.json            ← auto-updated from rolling 30-day avg
    performance_history.json   ← running log of all posts analyzed
```

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Comparing engagement rates across platforms | Each platform benchmarked separately — LinkedIn ≠ Instagram |
| Averaging over niches | Each niche has different baseline — never pool them |
| Optimizing for likes only | Saves + comments drive algorithm; likes are vanity |
| Reacting to one bad post | Look at 3-post rolling average before adjusting strategy |
| Ignoring post timing | Best day/time patterns compound over months — track every week |

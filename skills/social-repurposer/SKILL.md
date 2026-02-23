---
name: social-repurposer
description: Use when repurposing content for the Content Empire pipeline (Stage 5), generating platform posts for LinkedIn, Twitter/X, Instagram, Facebook, newsletter, or YouTube from a research brief or topic. Use for any niche (ttbp, cb, tundexai, wellwithtunde, tundestalksmen). Triggers on --niche and --topic flags.
---

# social-repurposer

## Overview
Standalone CLI tool that repurposes one content piece into all platform formats
with Voice DNA injection baked in. Algorithm-first: every output is engineered
for platform-native discovery. Exports dual format: Markdown (human review) +
ContentStudio JSON (machine-ready bulk import) + confidence score per item.

**Pipeline position:** Stage 5 (Social Generation) + Stage 3 (Newsletter)
**VPS-ready:** Runs headless, cron-friendly, logs to file, clean exit codes

---

## CLI Reference

```bash
python scripts/repurpose.py \
  --niche ttbp \               # ttbp | cb | tundexai | wellwithtunde | tundestalksmen
  --topic "AI replacing jobs" \  # Human-readable topic string
  --source research.md \         # Optional: path to research file or article
  --week 2026-W08 \              # Optional: ISO week for calendar alignment
  --formats all \                # all | linkedin | twitter | instagram | facebook | newsletter | youtube
  --out ./output/ \              # Output directory (created if missing)
  --log ./logs/repurpose.log     # Optional: log file path
```

### Flags
| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--niche` | YES | — | One of 5 content niches |
| `--topic` | YES | — | Topic string (used in prompts + filenames) |
| `--source` | NO | None | Path to research file for context injection |
| `--week` | NO | current | ISO week (2026-W08) for calendar alignment |
| `--formats` | NO | all | Comma-separated list or "all" |
| `--out` | NO | ./output | Output directory |
| `--log` | NO | stdout | Log file path |
| `--dry-run` | NO | False | Print prompts, don't call API |
| `--confidence-only` | NO | False | Score existing output files only |

### Exit Codes
| Code | Meaning |
|------|---------|
| 0 | Success — all outputs generated |
| 1 | API error |
| 2 | Missing required flag |
| 3 | Source file not found |
| 4 | Niche not recognized |

---

## Voice DNA Injection
Voice DNA is injected as the **first context block** in every generation prompt.

### Loading Order
1. Load `/prompts/voice/[niche]_voice_dna.md` (niche-specific)
2. Fall back to `/prompts/voice/ttbp_voice_dna.md` (master TTBP DNA)
3. Inject as: `[VOICE DNA]\n{content}\n[/VOICE DNA]`

### Voice Requirements (from TTBP DNA)
- Opens with personal story or provocative observation
- Uses "you" to address reader directly
- Includes at least one "The truth is..." or "Here's the thing..."
- Ends with clear takeaway + invitation to continue
- Occasional "(lol)" when it naturally fits
- Swearing only when it serves emphasis (sparingly)
- NEVER: "unpack", "at the end of the day", "it goes without saying",
  "In today's fast-paced world", "synergy", "leverage" (unless ironic),
  "In this article we will discuss...", "Thank you for reading!"
- Trust reader's intelligence — don't over-explain

---

## Platform Specs (Algorithm-First)

### LinkedIn (long-form)
- Length: 700–1,300 characters
- Hook: First 2 lines before "see more" fold — must create curiosity gap
- Format: No headers. Short paragraphs (1–3 lines). Heavy line breaks.
- Hashtags: 3–5. Mix: niche (#AIConsulting), broad (#Leadership), trending
- Algorithm signals: Native content beats links. Dwell time > CTR. First-hour engagement critical.
- CTA: End with question or poll prompt. Drive comments, not clicks.

### Twitter/X (thread)
- Hook tweet: 240 chars max. Must be hot take or surprising stat. Standalone.
- Thread length: 6–10 tweets
- Each tweet: Standalone value. No "continued in thread..." language.
- Hashtags: 1–2 max per tweet. Don't hashtag-stuff.
- Algorithm signals: Quote tweets and replies > retweets > likes. Thread completion rate.
- Thread format: 1/ hook, 2–8/ value, 9/ synthesis, 10/ CTA

### Instagram (caption)
- Hook: First sentence before "more" — must stop the scroll
- Length: 125–150 chars visible, 2,200 max total
- Format: Short punchy paragraphs. Line breaks. One idea per paragraph.
- Hashtags: 20–30. Mix: broad (100k+), niche (10k–100k), micro (<10k). Separate block.
- Algorithm signals: Save rate > likes. Story → feed link strategy.
- CTA: "Save this for later" or "Drop your answer below"

### Facebook (post)
- Length: 80–200 chars for most reach; 400+ for groups
- Hook: First 2–3 lines. Question-based hooks perform well.
- Hashtags: 1–3 only. Facebook hashtags add noise, not reach.
- Algorithm signals: Meaningful social interactions (comments > reactions). Groups amplify reach.
- CTA: Tag someone, share to a group, or comment with answer.

### Newsletter (Beehiiv)
- Format: Full article, 600–1,200 words
- Structure: Hook → Story → Truth → Insight → CTA
- Opening: Personal anecdote or direct observation. No "In this newsletter..."
- Subheadings: Use sparingly. Keep reading flow intact.
- Links: 2–3 max. Internal (past issues) + one external.
- CTA: One clear action. Recommend an issue, share, or reply.
- Deliverability: Plain text or minimal HTML. Avoid image-heavy templates.
- Discovery: Optimize subject line for open rate. Preview text = second subject line.

### YouTube Script (short-form, <60s)
- Hook (0–3s): Visual action or spoken line that creates immediate curiosity
- Body: One clear insight. One example. One proof point.
- CTA (last 5s): Subscribe, comment, or watch next video
- Pacing: Energetic. Cut filler words in script. Write for ear, not eye.
- Captions: Script should work with and without sound.

### YouTube Script (long-form, 8–15 min)
- Hook (0–30s): Pattern interrupt. Make viewer commit to watching.
- Intro (30–90s): What they'll learn + why they should care
- Body: 3–5 main points. Each: claim → evidence → example → transition
- Outro: Summary → CTA → subscribe + notification bell
- Chapters: 6–8 chapters. Optimize chapter titles for search.
- Description: First 2 lines above fold matter most. Include primary keyword.

---

## Output Formats

### Directory Structure (per run)
```
output/
  {niche}_{topic_slug}_{week}/
    markdown/
      linkedin.md
      twitter_thread.md
      instagram.md
      facebook.md
      newsletter.md
      youtube_short.md
      youtube_long.md
    contentstudio/
      bulk_import.json
    report/
      confidence_scores.json
      summary.md
```

## ContentStudio Export Schema

```json
{
  "workspace": "ttbp",
  "week": "2026-W08",
  "generated_at": "2026-02-18T00:00:00Z",
  "niche": "ttbp",
  "topic": "AI replacing jobs",
  "posts": [
    {
      "post_id": "ttbp_2026W08_linkedin_longform_01",
      "platform": "linkedin",
      "type": "long-form-post",
      "scheduled_time": "2026-02-18T08:00:00-05:00",
      "status": "PENDING_REVIEW",
      "confidence": 87,
      "content": {
        "text": "...",
        "hashtags": ["#AI", "#FutureOfWork", "#CareerStrategy"],
        "media_type": "none"
      }
    },
    {
      "post_id": "ttbp_2026W08_instagram_carousel_01",
      "platform": "instagram",
      "type": "carousel",
      "scheduled_time": "2026-02-18T12:00:00-05:00",
      "status": "PENDING_REVIEW",
      "confidence": 92,
      "content": {
        "slides": [
          {"slide": 1, "headline": "Hook slide text", "body": "..."},
          {"slide": 2, "headline": "Point 1", "body": "..."}
        ],
        "caption": "...",
        "hashtags": ["#AItools", "#CareerGrowth"],
        "placid_template": "carousel_7slide_v1"
      }
    }
  ]
}
```

## Confidence Scoring

Each output receives a 0–100 confidence score. Phase 2 (Week 9+) auto-approves ≥ 90.

| Criterion | Weight | What It Checks |
|-----------|--------|----------------|
| Voice match | 30% | Passes green flags, 0 red flags from Voice DNA |
| Hook strength | 25% | First line stops scroll — stat, bold claim, or tension |
| Platform fit | 20% | Format, length, hashtag count within spec |
| Algorithm signal | 15% | Dwell-optimized, save/share trigger present |
| Niche coherence | 10% | Topic aligns with niche content pillars |

**Score thresholds:**
- 90–100: Auto-approved (Phase 2+)
- 75–89: Publish with light review
- 60–74: Needs revision
- < 60: Regenerate

Scores are written to `output/{niche}_{topic}_{week}/report/confidence_scores.json`.

## Niche Configuration

| Niche | Brand Colors | Primary Audience | Voice Calibration | Top Hashtags |
|-------|-------------|-----------------|-------------------|--------------|
| `ttbp` | Gold + Black | Mid-career professionals, MBA types | Direct, data-informed, personal story open | #AI #FutureOfWork #CareerStrategy #Leadership |
| `cb` | Deep Green + Cream | Book lovers, educators, Nigerian diaspora | Literary, warm, cultural pride, author voice | #Books #Diaspora #Publishing #NigerianAuthors |
| `tundexai` | Electric Blue + White | Tech founders, AI practitioners | Sharp, technical accessible, contrarian takes | #AItools #Startups #BuildInPublic #MachineLearning |
| `wellwithtunde` | Warm Terracotta + Sage | Health-conscious professionals, 30s–50s | Holistic, encouraging, rooted in science | #Wellness #MensHealth #MindBody #HealthyLiving |
| `tundestalksmen` | Navy + Gold | Men in transition, fathers, faith-curious | Grounded, masculine, honest, biblically rooted | #MensLife #Fatherhood #Faith #ManUp |

Voice DNA file path per niche: `/prompts/voice/{niche}_voice_dna.md`

## File Structure

```
~/.claude/skills/user/social-repurposer/
  SKILL.md                     ← this file
  scripts/
    repurpose.py               ← main CLI orchestrator
    voice_loader.py            ← loads Voice DNA from /prompts/voice/
    platform_specs.py          ← per-platform format rules + validation
    export.py                  ← dual Markdown + ContentStudio JSON writer
    niche_config.py            ← niche brand colors, hashtags, voice cal.
  templates/
    invideo_prompt.txt         ← InVideo.ai prompt template
    carousel_structure.json    ← Placid carousel template config
```

## Quick Reference

```bash
# Single niche, all platforms
python scripts/repurpose.py --niche ttbp --topic "AI replacing jobs" --week 2026-W08

# From research brief file
python scripts/repurpose.py --niche cb --source research.md --week 2026-W08

# Specific platforms only
python scripts/repurpose.py --niche tundexai --topic "LLM benchmarks are broken" \
  --formats linkedin,twitter,newsletter --week 2026-W08

# Export ContentStudio JSON only
python scripts/repurpose.py --niche ttbp --topic "AI jobs" --output-format json --week 2026-W08

# Dry run (preview without writing)
python scripts/repurpose.py --niche ttbp --topic "AI jobs" --dry-run

# Check output
ls output/ttbp_ai-replacing-jobs_2026-W08/
cat output/ttbp_ai-replacing-jobs_2026-W08/report/confidence_scores.json
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Forgetting --week flag | Script uses current ISO week by default — always pass explicitly for scheduled output |
| Single voice DNA for all niches | Each niche has its own voice file — pass --niche to load the right one |
| Exporting before review | Check confidence_scores.json; don't bulk-import posts below 75 |
| Platform hashtag overflow | platform_specs.py enforces limits — don't add hashtags manually post-export |
| No source file and no --topic | One of --source or --topic required; both can be combined |

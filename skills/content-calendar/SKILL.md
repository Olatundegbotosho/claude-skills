---
name: content-calendar
description: Use when generating a weekly content calendar for any Content Empire niche (ttbp, cb, tundexai, wellwithtunde, tundestalksmen). Use when scheduling posts across platforms or exporting a ContentStudio JSON or CSV schedule for Buffer/Hootsuite. Triggers on --niche and --week flags.
---

# content-calendar

## Overview
Standalone CLI tool that generates a complete weekly content calendar for any
Content Empire niche. Timing-optimized by platform and audience. Exports
ContentStudio JSON (machine-ready bulk schedule import) + CSV (Buffer/Hootsuite
compatible). Integrates with social-repurposer for end-to-end automation.

**Pipeline position:** Stage 3 (Calendar Planning) + post-Stage 5 (scheduling)
**VPS-ready:** Runs headless, cron-friendly, logs to file, clean exit codes

---

## CLI Reference

```bash
python scripts/calendar_gen.py \
  --niche ttbp \               # ttbp | cb | tundexai | wellwithtunde | tundestalksmen
  --week 2026-W08 \            # ISO week string
  --topics topics.json \       # Optional: JSON file with topic list
  --out ./calendar/ \          # Output directory
  --log ./logs/calendar.log    # Optional: log file path
```

### Flags
| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--niche` | YES | — | One of 5 content niches |
| `--week` | YES | — | ISO week (2026-W08) |
| `--topics` | NO | None | JSON: [{"topic": "...", "priority": 1}] |
| `--out` | NO | ./calendar | Output directory |
| `--log` | NO | stdout | Log file path |
| `--preview` | NO | False | Print schedule table, don't write files |
| `--merge` | NO | None | Path to existing calendar JSON to merge |

### Exit Codes
| Code | Meaning |
|------|---------|
| 0 | Success — calendar files written |
| 1 | API/config error |
| 2 | Missing required flag |
| 3 | Topics file not found |
| 4 | Niche not recognized |

---

## Timing Optimization (Algorithm-First)

### Platform Best Times (by engagement data)
| Platform | Best Days | Best Times (local) | Notes |
|----------|-----------|-------------------|-------|
| LinkedIn | Tue, Wed, Thu | 8am–10am, 5pm–6pm | Avoid weekends |
| Twitter/X | Mon–Fri | 9am–11am, 6pm–8pm | 3–5x/day OK |
| Instagram | Wed, Fri | 11am–1pm, 7pm–9pm | Stories separate cadence |
| Facebook | Wed | 1pm–4pm | Group posts separate |
| Newsletter | Tue or Thu | 8am–10am | Consistency beats optimal day |
| YouTube | Fri, Sat | 2pm–4pm | Upload early, premiere on schedule |

### Weekly Content Mix (per niche, ~36 pieces)
| Format | Per Week | Platforms |
|--------|----------|-----------|
| Short-form scripts (30–60s) | 4 | YT Shorts, IG Reels, TikTok |
| Long-form video script | 1 | YouTube |
| InVideo prompts | 5 | InVideo.ai |
| Carousel posts (7 slides each) | 3 | IG, LinkedIn, FB |
| Quote cards | 3 | IG, X, LinkedIn |
| LinkedIn long-form posts | 2–3 | LinkedIn |
| X threads | 3–4 | Twitter/X |
| Instagram captions | 5–7 | Instagram |
| Facebook posts | 2–3 | Facebook |
| Newsletter | 1 | Beehiiv |

---

## Output Formats

### Directory Structure (per run)
```
calendar/
  {niche}_{week}/
    contentstudio_import.json    ← Bulk import to ContentStudio
    schedule.csv                 ← Buffer/Hootsuite compatible
    overview.md                  ← Human-readable week summary
    topics_used.json             ← Topics assigned to calendar slots
```

### ContentStudio JSON (Schedule Format)
```json
{
  "workspace": "ttbp",
  "week": "2026-W08",
  "schedule": [
    {
      "slot_id": "ttbp_2026W08_mon_linkedin_01",
      "platform": "linkedin",
      "type": "long-form-post",
      "topic": "AI replacing jobs",
      "content_source": "social-repurposer output",
      "scheduled_time": "2026-02-18T08:00:00-05:00",
      "status": "PENDING_CONTENT",
      "labels": ["niche:ttbp", "week:2026-W08", "format:linkedin-post"]
    }
  ]
}
```

### CSV Format
```csv
slot_id,platform,type,topic,scheduled_time,status
ttbp_2026W08_mon_linkedin_01,linkedin,long-form-post,AI replacing jobs,2026-02-18 08:00,PENDING
```

---

## Default Schedule (per niche)

| Day | Platform | Format | Time |
|-----|----------|--------|------|
| Monday | LinkedIn | Long-form post | 8am |
| Monday | X | Thread | 9am |
| Tuesday | Instagram | Carousel | 11am |
| Tuesday | Newsletter | Full issue | 8am |
| Wednesday | LinkedIn | Quote card | 5pm |
| Wednesday | Facebook | Post | 1pm |
| Thursday | X | Thread | 9am |
| Thursday | YouTube | Short-form script | 2pm |
| Friday | Instagram | Caption | 11am |
| Friday | YouTube | Long-form script | 2pm |
| Saturday | Instagram | Reel caption | 10am |

See `config/default_schedule.yaml` for full per-niche timing config.

---

## File Structure

```
content-calendar/
  SKILL.md                         ← this file
  scripts/
    calendar_gen.py                ← main orchestrator (argparse CLI)
    timing_engine.py               ← best-time optimization per platform
    contentstudio_export.py        ← ContentStudio JSON builder
    csv_export.py                  ← CSV schedule builder
  config/
    default_schedule.yaml          ← default weekly schedule per niche
```

---

## Quick Reference

```bash
# Generate full week calendar
python scripts/calendar_gen.py --niche ttbp --week 2026-W08

# With custom topic list
python scripts/calendar_gen.py --niche cb --week 2026-W09 --topics topics.json

# Preview only (no files written)
python scripts/calendar_gen.py --niche tundexai --week 2026-W08 --preview

# Merge with existing calendar
python scripts/calendar_gen.py --niche ttbp --week 2026-W08 --merge ./existing.json
```

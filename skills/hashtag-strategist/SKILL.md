---
name: hashtag-strategist
description: Use when selecting hashtags for any post, LinkedIn article, or newsletter — enforces per-niche hashtag pools, platform limits, rotation logic to prevent repetition fatigue, and reach-tier mixing (broad + niche + micro). Called before any content goes to scheduling.
---

# Hashtag Strategist

## Overview

Selects the optimal hashtag set for a piece of content based on niche, platform, topic, and recent usage history. Prevents overuse of the same tags (shadow-ban risk), mixes reach tiers for algorithm discovery, and rotates sets across a 14-post cycle.

**Core principle:** Hashtags are discovery signals, not decoration. One wrong repeat tag set and the algorithm stops distributing.

---

## When to Use

- Before finalizing any LinkedIn post, article, or newsletter
- When scheduling a batch of posts — run full-week hashtag rotation
- When a post topic is unusual for the niche — need emergency adjacent tags
- When the same tags have been used 3+ posts in a row (rotation alert)

---

## Platform Rules

| Platform | Max Tags | Sweet Spot | Notes |
|----------|----------|------------|-------|
| LinkedIn | 30 | **3–5** | Algorithm rewards 3–5 highly relevant tags; 10+ is penalized |
| Instagram | 30 | **10–15** | Mix broad (1M+), niche (100K–1M), micro (<100K) |
| X/Twitter | 10 | **1–2** | One topical, one broader; more looks spammy |
| Newsletter | N/A | 0 | No hashtags in newsletters (Substack/Beehiiv don't support) |

---

## Reach Tier Mixing (LinkedIn + Instagram)

| Tier | Follow Count | Role | Example |
|------|-------------|------|---------|
| **Broad** | 5M+ followers | Discovery reach | #Leadership #AI #Wellness |
| **Niche** | 100K–1M | Engaged community | #CareerGrowth #EnterpriseAI |
| **Micro** | <100K | Highest engagement rate | #AfricanLiterature #MensMentalHealth |

Ideal LinkedIn set: 1 broad + 2 niche + 1 micro

---

## Rotation Logic

- **Cooldown:** Each tag gets a 3-post cooldown before reuse
- **Set cooldown:** Identical sets are never used back-to-back
- **Cycle:** Rotate through 4–5 distinct set configurations per niche
- **Emergency tags:** Always available for topic-specific coverage

---

## Niche Hashtag Pools

Each niche maintains 3 tiers. The strategist selects from the active rotation pool, respecting cooldowns.

### `ttbp` (Leadership / Career)
- **Broad:** #Leadership, #Management, #Career, #Business, #Strategy
- **Niche:** #CareerGrowth, #ManagementInsights, #ProfessionalDevelopment, #MiddleManagement, #CorporateCulture
- **Micro:** #AfricanLeaders, #NigerianProfessionals, #LeadershipInAfrica, #DiasporaLeadership, #ExecutivePresence

### `cb` (Connecting Bridges / Literature)
- **Broad:** #Books, #Literature, #Reading, #Writing, #Culture
- **Niche:** #AfricanLiterature, #Bookstagram, #LiteraryCriticism, #AfricanAuthors, #BookReview
- **Micro:** #NigerianLiterature, #ChinuaAchebe, #AfricanFiction, #DecolonizingLiterature, #AfricanPublishing

### `tundexai` (AI Strategy)
- **Broad:** #AI, #ArtificialIntelligence, #Technology, #Innovation, #FutureOfWork
- **Niche:** #AIStrategy, #EnterpriseAI, #LLM, #AITools, #GenerativeAI
- **Micro:** #AIImplementation, #AfricanAI, #AIInAfrica, #EnterpriseLLM, #AIProductivity

### `wellwithtunde` (Wellness)
- **Broad:** #Health, #Wellness, #Mindfulness, #Fitness, #Nutrition
- **Niche:** #HolisticHealth, #SustainableWellness, #MentalHealth, #BodyAwareness, #HabitFormation
- **Micro:** #BlackWellness, #AfricanWellness, #SustainableHealth, #ChronicDiseasePrevention, #BodyConnection

### `tundestalksmen` (Men's Growth)
- **Broad:** #Men, #Fatherhood, #Relationships, #MentalHealth, #PersonalDevelopment
- **Niche:** #MensGrowth, #MensMentalHealth, #MasculinityRedefined, #Accountability, #Brotherhood
- **Micro:** #AfricanMen, #NigerianMen, #BlackMen, #MenOfFaith, #MenInTherapy

---

## Output Format

```
═══════════════════════════════════════════
HASHTAG SET
═══════════════════════════════════════════
Niche:      tundexai
Platform:   linkedin
Topic:      AI benchmarks
Rotation:   Set B (last used: Set A, 2 posts ago)

RECOMMENDED SET (4 tags)
  #AI  [broad — 2.1M followers]
  #AIStrategy  [niche — 320K followers]
  #EnterpriseAI  [niche — 180K followers]
  #AIImplementation  [micro — 45K followers]

TIER BREAKDOWN
  Broad: 1  |  Niche: 2  |  Micro: 1  ✅

COOLDOWN STATUS
  #LLM → on cooldown (used 1 post ago, available in 2)
  #GenerativeAI → available

ALTERNATIVES (if you want a different set)
  Set C:  #ArtificialIntelligence  #LLM  #AITools  #EnterpriseLLM
  Set D:  #Technology  #GenerativeAI  #AIStrategy  #AfricanAI
═══════════════════════════════════════════
```

---

## Usage

```bash
# Get hashtag set for a post
python hashtag_strategist.py --niche tundexai --platform linkedin --topic "AI benchmarks"

# Get full week rotation (7 posts)
python hashtag_strategist.py --niche ttbp --platform linkedin --week

# Check cooldown status for a niche
python hashtag_strategist.py --niche cb --status

# Mark tags as used (call after posting)
python hashtag_strategist.py --niche ttbp --mark-used "#Leadership #CareerGrowth #AfricanLeaders"

# Get emergency adjacent tags for unusual topic
python hashtag_strategist.py --niche tundexai --topic "quantum computing" --emergency

# JSON output (for pipeline)
python hashtag_strategist.py --niche ttbp --platform linkedin --topic "promotions" --json
```

---

## File Structure

```
hashtag-strategist/
  SKILL.md
  scripts/
    hashtag_strategist.py    ← strategist + rotation tracker
  data/
    hashtag_usage.json       ← auto-generated usage history (per niche)
```

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Using the same 3 tags every post | Rotate sets — at least 4 distinct configurations |
| All broad tags | Mix tiers — one broad is enough; niche + micro drive engagement |
| 10+ hashtags on LinkedIn | 3–5 max — more is penalized, not rewarded |
| Hashtags mid-post on LinkedIn | Place all tags at the bottom, after the CTA |
| Seasonal/trending tags on evergreen content | Only use trending tags when the content is actually timely |

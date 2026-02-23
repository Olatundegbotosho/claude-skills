"""
hashtag_strategist.py — Hashtag Set Generator with Rotation Logic
Part of the Social Media Engine skill stack.

Usage:
    python hashtag_strategist.py --niche tundexai --platform linkedin --topic "AI benchmarks"
    python hashtag_strategist.py --niche ttbp --platform linkedin --week
    python hashtag_strategist.py --niche cb --status
    python hashtag_strategist.py --niche ttbp --mark-used "#Leadership #CareerGrowth"
    python hashtag_strategist.py --niche tundexai --topic "quantum computing" --emergency
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, date
from pathlib import Path
from typing import Optional


# ─── Constants ───────────────────────────────────────────────────────────────

VALID_NICHES = {"ttbp", "cb", "tundexai", "wellwithtunde", "tundestalksmen"}

PLATFORM_LIMITS = {
    "linkedin": {"max": 30, "sweet_spot": (3, 5), "placement": "bottom"},
    "instagram": {"max": 30, "sweet_spot": (10, 15), "placement": "caption_or_comment"},
    "twitter": {"max": 10, "sweet_spot": (1, 2), "placement": "inline_or_end"},
    "x": {"max": 10, "sweet_spot": (1, 2), "placement": "inline_or_end"},
}

COOLDOWN_POSTS = 3    # Posts before a tag can be reused
DATA_DIR = Path(__file__).parent.parent / "data"
USAGE_FILE = DATA_DIR / "hashtag_usage.json"


# ─── Hashtag Pool Definitions ─────────────────────────────────────────────────
# Each tag has: tier (broad/niche/micro), estimated follower count, topic affinities

HASHTAG_POOLS: dict[str, dict] = {
    "ttbp": {
        "broad": [
            {"tag": "#Leadership", "followers": 47_000_000},
            {"tag": "#Management", "followers": 22_000_000},
            {"tag": "#Career", "followers": 18_000_000},
            {"tag": "#Business", "followers": 95_000_000},
            {"tag": "#Strategy", "followers": 12_000_000},
            {"tag": "#WorkplaceWellness", "followers": 6_000_000},
        ],
        "niche": [
            {"tag": "#CareerGrowth", "followers": 850_000, "topics": ["promotion", "plateau", "growth"]},
            {"tag": "#ManagementInsights", "followers": 420_000, "topics": ["management", "manager", "team"]},
            {"tag": "#ProfessionalDevelopment", "followers": 780_000, "topics": ["skills", "development", "learning"]},
            {"tag": "#MiddleManagement", "followers": 180_000, "topics": ["middle", "plateau", "manager"]},
            {"tag": "#CorporateCulture", "followers": 390_000, "topics": ["culture", "corporate", "organization"]},
            {"tag": "#ExecutivePresence", "followers": 220_000, "topics": ["executive", "presence", "influence"]},
            {"tag": "#WorkplaceIntelligence", "followers": 150_000, "topics": ["workplace", "culture", "smart"]},
        ],
        "micro": [
            {"tag": "#AfricanLeaders", "followers": 45_000, "topics": ["africa", "nigerian", "diaspora"]},
            {"tag": "#NigerianProfessionals", "followers": 38_000, "topics": ["nigerian", "nigeria"]},
            {"tag": "#LeadershipInAfrica", "followers": 22_000, "topics": ["africa", "leadership"]},
            {"tag": "#DiasporaLeadership", "followers": 18_000, "topics": ["diaspora", "african american", "nigerian"]},
            {"tag": "#BlackLeaders", "followers": 62_000, "topics": ["black", "diverse", "inclusion"]},
        ],
        # Pre-defined rotation sets (A, B, C, D)
        "rotation_sets": {
            "A": ["#Leadership", "#CareerGrowth", "#ManagementInsights", "#AfricanLeaders"],
            "B": ["#Management", "#ProfessionalDevelopment", "#CorporateCulture", "#NigerianProfessionals"],
            "C": ["#Leadership", "#ExecutivePresence", "#MiddleManagement", "#DiasporaLeadership"],
            "D": ["#Career", "#CareerGrowth", "#WorkplaceIntelligence", "#BlackLeaders"],
            "E": ["#Strategy", "#ManagementInsights", "#ProfessionalDevelopment", "#LeadershipInAfrica"],
        },
    },

    "cb": {
        "broad": [
            {"tag": "#Books", "followers": 52_000_000},
            {"tag": "#Literature", "followers": 15_000_000},
            {"tag": "#Reading", "followers": 38_000_000},
            {"tag": "#Writing", "followers": 25_000_000},
            {"tag": "#Culture", "followers": 20_000_000},
        ],
        "niche": [
            {"tag": "#AfricanLiterature", "followers": 480_000, "topics": ["african", "literature", "fiction"]},
            {"tag": "#Bookstagram", "followers": 620_000, "topics": ["book", "reading", "review"]},
            {"tag": "#LiteraryCriticism", "followers": 180_000, "topics": ["criticism", "analysis", "literary"]},
            {"tag": "#AfricanAuthors", "followers": 320_000, "topics": ["author", "african", "writer"]},
            {"tag": "#BookReview", "followers": 550_000, "topics": ["review", "book", "read"]},
            {"tag": "#PostcolonialLiterature", "followers": 120_000, "topics": ["postcolonial", "decolonial", "colonial"]},
        ],
        "micro": [
            {"tag": "#NigerianLiterature", "followers": 42_000, "topics": ["nigerian", "nigeria"]},
            {"tag": "#ChinuaAchebe", "followers": 28_000, "topics": ["achebe", "things fall apart", "okonkwo"]},
            {"tag": "#AfricanFiction", "followers": 68_000, "topics": ["fiction", "african", "novel"]},
            {"tag": "#DecolonizingLiterature", "followers": 35_000, "topics": ["decolonize", "colonial", "western"]},
            {"tag": "#AfricanPublishing", "followers": 22_000, "topics": ["publishing", "publish", "book"]},
        ],
        "rotation_sets": {
            "A": ["#Books", "#AfricanLiterature", "#BookReview", "#NigerianLiterature"],
            "B": ["#Literature", "#AfricanAuthors", "#LiteraryCriticism", "#AfricanFiction"],
            "C": ["#Reading", "#AfricanLiterature", "#PostcolonialLiterature", "#DecolonizingLiterature"],
            "D": ["#Writing", "#Bookstagram", "#AfricanAuthors", "#AfricanPublishing"],
            "E": ["#Culture", "#AfricanLiterature", "#LiteraryCriticism", "#ChinuaAchebe"],
        },
    },

    "tundexai": {
        "broad": [
            {"tag": "#AI", "followers": 120_000_000},
            {"tag": "#ArtificialIntelligence", "followers": 85_000_000},
            {"tag": "#Technology", "followers": 95_000_000},
            {"tag": "#Innovation", "followers": 45_000_000},
            {"tag": "#FutureOfWork", "followers": 18_000_000},
        ],
        "niche": [
            {"tag": "#AIStrategy", "followers": 320_000, "topics": ["strategy", "plan", "roadmap", "adoption"]},
            {"tag": "#EnterpriseAI", "followers": 180_000, "topics": ["enterprise", "business", "corporate"]},
            {"tag": "#LLM", "followers": 520_000, "topics": ["llm", "language model", "gpt", "claude"]},
            {"tag": "#AITools", "followers": 380_000, "topics": ["tool", "tools", "software", "platform"]},
            {"tag": "#GenerativeAI", "followers": 620_000, "topics": ["generative", "generate", "image", "text"]},
            {"tag": "#PromptEngineering", "followers": 280_000, "topics": ["prompt", "prompting", "engineering"]},
            {"tag": "#AIAgents", "followers": 240_000, "topics": ["agent", "agents", "agentic", "autonomous"]},
        ],
        "micro": [
            {"tag": "#AIImplementation", "followers": 45_000, "topics": ["implement", "deploy", "rollout"]},
            {"tag": "#AfricanAI", "followers": 28_000, "topics": ["africa", "african"]},
            {"tag": "#AIInAfrica", "followers": 18_000, "topics": ["africa", "african"]},
            {"tag": "#EnterpriseLLM", "followers": 38_000, "topics": ["enterprise", "llm", "business"]},
            {"tag": "#AIProductivity", "followers": 62_000, "topics": ["productivity", "workflow", "efficiency"]},
        ],
        "rotation_sets": {
            "A": ["#AI", "#AIStrategy", "#EnterpriseAI", "#AIImplementation"],
            "B": ["#ArtificialIntelligence", "#LLM", "#AITools", "#EnterpriseLLM"],
            "C": ["#AI", "#GenerativeAI", "#AIStrategy", "#AIProductivity"],
            "D": ["#Technology", "#AIAgents", "#EnterpriseAI", "#AfricanAI"],
            "E": ["#FutureOfWork", "#PromptEngineering", "#GenerativeAI", "#AIInAfrica"],
        },
    },

    "wellwithtunde": {
        "broad": [
            {"tag": "#Health", "followers": 78_000_000},
            {"tag": "#Wellness", "followers": 62_000_000},
            {"tag": "#Mindfulness", "followers": 35_000_000},
            {"tag": "#Fitness", "followers": 55_000_000},
            {"tag": "#Nutrition", "followers": 28_000_000},
        ],
        "niche": [
            {"tag": "#HolisticHealth", "followers": 780_000, "topics": ["holistic", "whole", "integrated"]},
            {"tag": "#SustainableWellness", "followers": 220_000, "topics": ["sustainable", "long-term", "lifestyle"]},
            {"tag": "#MentalHealth", "followers": 12_000_000, "topics": ["mental", "stress", "anxiety", "burnout"]},
            {"tag": "#BodyAwareness", "followers": 180_000, "topics": ["body", "awareness", "connection", "feeling"]},
            {"tag": "#HabitFormation", "followers": 320_000, "topics": ["habit", "routine", "daily", "practice"]},
            {"tag": "#ChronicWellness", "followers": 150_000, "topics": ["chronic", "disease", "prevention", "management"]},
        ],
        "micro": [
            {"tag": "#BlackWellness", "followers": 68_000, "topics": ["black", "african american"]},
            {"tag": "#AfricanWellness", "followers": 35_000, "topics": ["african", "africa"]},
            {"tag": "#SustainableHealth", "followers": 45_000, "topics": ["sustainable", "lifestyle", "long term"]},
            {"tag": "#ChronicDiseasePrevention", "followers": 28_000, "topics": ["chronic", "disease", "prevention"]},
            {"tag": "#BodyConnection", "followers": 22_000, "topics": ["body", "connection", "somatic"]},
        ],
        "rotation_sets": {
            "A": ["#Wellness", "#HolisticHealth", "#HabitFormation", "#BlackWellness"],
            "B": ["#Health", "#MentalHealth", "#SustainableWellness", "#AfricanWellness"],
            "C": ["#Mindfulness", "#BodyAwareness", "#HolisticHealth", "#BodyConnection"],
            "D": ["#Fitness", "#HabitFormation", "#SustainableWellness", "#SustainableHealth"],
            "E": ["#Nutrition", "#ChronicWellness", "#HolisticHealth", "#ChronicDiseasePrevention"],
        },
    },

    "tundestalksmen": {
        "broad": [
            {"tag": "#Men", "followers": 18_000_000},
            {"tag": "#Fatherhood", "followers": 22_000_000},
            {"tag": "#Relationships", "followers": 45_000_000},
            {"tag": "#MentalHealth", "followers": 12_000_000},
            {"tag": "#PersonalDevelopment", "followers": 35_000_000},
        ],
        "niche": [
            {"tag": "#MensGrowth", "followers": 180_000, "topics": ["growth", "development", "change"]},
            {"tag": "#MensMentalHealth", "followers": 420_000, "topics": ["mental", "health", "therapy", "emotions"]},
            {"tag": "#MasculinityRedefined", "followers": 220_000, "topics": ["masculinity", "manhood", "redefine"]},
            {"tag": "#Accountability", "followers": 380_000, "topics": ["accountability", "accountable", "responsibility"]},
            {"tag": "#Brotherhood", "followers": 250_000, "topics": ["brotherhood", "community", "brothers", "men together"]},
            {"tag": "#DadLife", "followers": 620_000, "topics": ["dad", "father", "parenting", "kids"]},
        ],
        "micro": [
            {"tag": "#AfricanMen", "followers": 38_000, "topics": ["african", "africa"]},
            {"tag": "#NigerianMen", "followers": 28_000, "topics": ["nigerian", "nigeria"]},
            {"tag": "#BlackMen", "followers": 85_000, "topics": ["black", "black men", "african american"]},
            {"tag": "#MenOfFaith", "followers": 52_000, "topics": ["faith", "christian", "church", "god"]},
            {"tag": "#MenInTherapy", "followers": 42_000, "topics": ["therapy", "therapist", "mental health", "healing"]},
        ],
        "rotation_sets": {
            "A": ["#Men", "#MensGrowth", "#Accountability", "#AfricanMen"],
            "B": ["#PersonalDevelopment", "#MensMentalHealth", "#Brotherhood", "#BlackMen"],
            "C": ["#Fatherhood", "#DadLife", "#MasculinityRedefined", "#NigerianMen"],
            "D": ["#Relationships", "#Accountability", "#MensGrowth", "#MenInTherapy"],
            "E": ["#MentalHealth", "#MensMentalHealth", "#Brotherhood", "#MenOfFaith"],
        },
    },
}


# ─── Emergency / Adjacent Tags ────────────────────────────────────────────────
# Used when topic falls outside the normal niche cluster

EMERGENCY_ADJACENT_TAGS: dict[str, list[str]] = {
    "ttbp": ["#Entrepreneurship", "#StartUp", "#SideHustle", "#WorkLifeBalance", "#Productivity"],
    "cb": ["#Poetry", "#Storytelling", "#Memoir", "#Creative Writing", "#BlackAuthors"],
    "tundexai": ["#DataScience", "#MachineLearning", "#CloudComputing", "#DigitalTransformation", "#TechLeadership"],
    "wellwithtunde": ["#Yoga", "#Meditation", "#SleepHealth", "#GutHealth", "#WomensHealth"],
    "tundestalksmen": ["#Marriage", "#Divorce", "#SingleDad", "#Manhood", "#MensRights"],
}


# ─── Dataclasses ─────────────────────────────────────────────────────────────

@dataclass
class HashtagInfo:
    tag: str
    tier: str  # broad / niche / micro
    followers: int
    on_cooldown: bool
    last_used_post: Optional[int]  # posts ago, None if never used


@dataclass
class HashtagSet:
    niche: str
    platform: str
    topic: str
    set_label: str  # A, B, C, D, E
    tags: list[str]
    tier_breakdown: dict[str, int]  # {"broad": 1, "niche": 2, "micro": 1}
    alternative_sets: dict[str, list[str]]
    cooldown_notes: list[str]
    generated_at: str
    report: str


# ─── Usage History ────────────────────────────────────────────────────────────

def _load_usage_history() -> dict:
    """Load usage history from JSON file. Returns empty dict if not found."""
    if USAGE_FILE.exists():
        try:
            return json.loads(USAGE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_usage_history(history: dict) -> None:
    """Save usage history to JSON file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    USAGE_FILE.write_text(json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")


def _get_niche_history(history: dict, niche: str) -> dict:
    """Get usage history for a specific niche."""
    return history.get(niche, {
        "post_count": 0,
        "last_set": None,
        "tag_last_used": {},  # tag -> post_count_when_used
    })


def mark_tags_used(niche: str, tags: list[str]) -> None:
    """Mark a list of tags as used (call after posting)."""
    history = _load_usage_history()
    nh = _get_niche_history(history, niche)
    nh["post_count"] += 1
    for tag in tags:
        clean = tag.strip() if tag.startswith("#") else f"#{tag.strip()}"
        nh["tag_last_used"][clean] = nh["post_count"]
    history[niche] = nh
    _save_usage_history(history)


def _is_on_cooldown(tag: str, niche_history: dict) -> tuple[bool, Optional[int]]:
    """Return (is_on_cooldown, posts_ago). posts_ago is None if never used."""
    post_count = niche_history.get("post_count", 0)
    last_used = niche_history.get("tag_last_used", {}).get(tag)
    if last_used is None:
        return False, None
    posts_ago = post_count - last_used
    return posts_ago < COOLDOWN_POSTS, posts_ago


# ─── Topic Relevance Scoring ─────────────────────────────────────────────────

def _topic_score(tag_info: dict, topic: str) -> int:
    """
    Score a tag's relevance to the given topic.
    Returns 0–3: 0=no match, 1=weak, 2=good, 3=strong
    """
    topic_lower = topic.lower()
    affinities = tag_info.get("topics", [])
    matches = sum(1 for a in affinities if a.lower() in topic_lower or topic_lower in a.lower())
    return min(3, matches)


# ─── Set Selection ────────────────────────────────────────────────────────────

def _pick_rotation_set(niche: str, niche_history: dict) -> str:
    """
    Pick the next rotation set (A→E), avoiding the one used last time.
    Returns set label: A, B, C, D, or E.
    """
    last_set = niche_history.get("last_set")
    all_sets = list(HASHTAG_POOLS[niche]["rotation_sets"].keys())

    if last_set is None:
        return all_sets[0]

    try:
        last_index = all_sets.index(last_set)
        next_index = (last_index + 1) % len(all_sets)
        return all_sets[next_index]
    except ValueError:
        return all_sets[0]


def _select_tags_for_topic(
    niche: str, platform: str, topic: str, niche_history: dict
) -> tuple[str, list[str], list[str]]:
    """
    Select the best hashtag set for the given topic, respecting cooldowns.
    Returns (set_label, selected_tags, cooldown_notes).
    """
    pool = HASHTAG_POOLS[niche]
    rotation_sets = pool["rotation_sets"]

    # Get platform sweet spot
    platform_config = PLATFORM_LIMITS.get(platform, PLATFORM_LIMITS["linkedin"])
    min_tags, max_tags = platform_config["sweet_spot"]
    target_count = min(max_tags, 4)  # LinkedIn target: 4 tags

    # Start with the rotation set
    set_label = _pick_rotation_set(niche, niche_history)
    base_tags = rotation_sets[set_label].copy()

    cooldown_notes = []
    final_tags = []
    substitutions_needed = []

    for tag in base_tags:
        on_cd, posts_ago = _is_on_cooldown(tag, niche_history)
        if not on_cd:
            final_tags.append(tag)
        else:
            cooldown_notes.append(
                f"{tag} → on cooldown (used {posts_ago} post{'s' if posts_ago != 1 else ''} ago, "
                f"available in {COOLDOWN_POSTS - posts_ago})"
            )
            substitutions_needed.append(tag)

    # Fill gaps from pool based on topic relevance
    if substitutions_needed:
        all_pool_tags = (
            pool["broad"] + pool["niche"] + pool["micro"]
        )
        scored = []
        for tag_info in all_pool_tags:
            t = tag_info["tag"]
            if t in final_tags or t in base_tags:
                continue
            on_cd, _ = _is_on_cooldown(t, niche_history)
            if on_cd:
                continue
            score = _topic_score(tag_info, topic)
            # Tier preference weight: niche > micro > broad (for substitution)
            tier_weight = {"niche": 3, "micro": 2, "broad": 1}
            tier = _get_tier(niche, t)
            total_score = score * 2 + tier_weight.get(tier, 1)
            scored.append((total_score, t))

        scored.sort(reverse=True)
        for _, t in scored:
            if len(final_tags) >= target_count:
                break
            final_tags.append(t)

    # Trim to target
    final_tags = final_tags[:target_count]

    # If we still don't have enough, fill with any available tag
    if len(final_tags) < min_tags:
        all_pool_tags = pool["broad"] + pool["niche"] + pool["micro"]
        for tag_info in all_pool_tags:
            t = tag_info["tag"]
            if t in final_tags:
                continue
            on_cd, _ = _is_on_cooldown(t, niche_history)
            if not on_cd:
                final_tags.append(t)
            if len(final_tags) >= min_tags:
                break

    return set_label, final_tags, cooldown_notes


def _get_tier(niche: str, tag: str) -> str:
    """Look up what tier a tag belongs to."""
    pool = HASHTAG_POOLS[niche]
    for tier in ("broad", "niche", "micro"):
        for tag_info in pool.get(tier, []):
            if tag_info["tag"] == tag:
                return tier
    return "niche"  # default


def _get_tag_info(niche: str, tag: str) -> Optional[dict]:
    """Get full tag info dict from pool."""
    pool = HASHTAG_POOLS[niche]
    for tier in ("broad", "niche", "micro"):
        for tag_info in pool.get(tier, []):
            if tag_info["tag"] == tag:
                return {**tag_info, "tier": tier}
    return None


def _tier_breakdown(niche: str, tags: list[str]) -> dict[str, int]:
    breakdown = {"broad": 0, "niche": 0, "micro": 0}
    for tag in tags:
        tier = _get_tier(niche, tag)
        breakdown[tier] = breakdown.get(tier, 0) + 1
    return breakdown


def _get_alternative_sets(niche: str, selected_set: str) -> dict[str, list[str]]:
    """Return up to 2 other rotation sets as alternatives."""
    all_sets = HASHTAG_POOLS[niche]["rotation_sets"]
    alts = {}
    for label, tags in all_sets.items():
        if label != selected_set:
            alts[label] = tags
        if len(alts) >= 2:
            break
    return alts


# ─── Report Formatting ────────────────────────────────────────────────────────

def _format_followers(n: int) -> str:
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.0f}K"
    return str(n)


def _format_hashtag_set(
    niche: str,
    platform: str,
    topic: str,
    set_label: str,
    tags: list[str],
    tier_breakdown: dict[str, int],
    alternative_sets: dict[str, list[str]],
    cooldown_notes: list[str],
    niche_history: dict,
) -> str:
    # Get follower counts
    tag_lines = []
    for tag in tags:
        info = _get_tag_info(niche, tag)
        if info:
            tier = info["tier"]
            followers_str = _format_followers(info["followers"])
            tag_lines.append(f"  {tag}  [{tier} — {followers_str} followers]")
        else:
            tag_lines.append(f"  {tag}")

    tags_display = "\n".join(tag_lines)

    # Tier check
    ideal = {"broad": 1, "niche": 2, "micro": 1}
    tier_ok = all(tier_breakdown.get(k, 0) == v for k, v in ideal.items())
    tier_icon = "✅" if tier_ok else "~"
    tier_line = (
        f"  Broad: {tier_breakdown.get('broad', 0)}  |  "
        f"Niche: {tier_breakdown.get('niche', 0)}  |  "
        f"Micro: {tier_breakdown.get('micro', 0)}  {tier_icon}"
    )

    # Last set info
    last_set = niche_history.get("last_set", "None")
    post_count = niche_history.get("post_count", 0)

    # Cooldown notes
    cooldown_block = ""
    if cooldown_notes:
        cooldown_block = "\nCOOLDOWN NOTES\n" + "\n".join(f"  {n}" for n in cooldown_notes) + "\n"

    # Alternatives
    alt_lines = []
    for label, alt_tags in alternative_sets.items():
        alt_lines.append(f"  Set {label}:  {chr(32).join(alt_tags)}")
    alt_block = "\n".join(alt_lines)

    lines = [
        "═══════════════════════════════════════════",
        "HASHTAG SET",
        "═══════════════════════════════════════════",
        f"Niche:      {niche}",
        f"Platform:   {platform}",
        f"Topic:      {topic}",
        f"Rotation:   Set {set_label} (last used: Set {last_set}, post #{post_count})",
        "",
        f"RECOMMENDED SET ({len(tags)} tags)",
        tags_display,
        "",
        "TIER BREAKDOWN",
        tier_line,
        "",
    ]

    if cooldown_block:
        lines.append(cooldown_block)

    if alt_block:
        lines += [
            "ALTERNATIVES",
            alt_block,
        ]

    lines.append("═══════════════════════════════════════════")
    return "\n".join(lines)


# ─── Status Report ────────────────────────────────────────────────────────────

def _format_status(niche: str) -> str:
    history = _load_usage_history()
    nh = _get_niche_history(history, niche)
    post_count = nh.get("post_count", 0)
    tag_usage = nh.get("tag_last_used", {})
    last_set = nh.get("last_set", "None")

    # Categorize tags
    available = []
    on_cooldown_list = []
    never_used = []

    pool = HASHTAG_POOLS[niche]
    all_tags = []
    for tier in ("broad", "niche", "micro"):
        for t in pool[tier]:
            all_tags.append((t["tag"], tier))

    for tag, tier in all_tags:
        if tag in tag_usage:
            posts_ago = post_count - tag_usage[tag]
            if posts_ago < COOLDOWN_POSTS:
                on_cooldown_list.append(f"  {tag} ({tier}) — used {posts_ago}p ago, available in {COOLDOWN_POSTS - posts_ago}")
            else:
                available.append(f"  {tag} ({tier}) — last used {posts_ago}p ago")
        else:
            never_used.append(f"  {tag} ({tier})")

    lines = [
        f"═══ HASHTAG STATUS: {niche.upper()} ═══",
        f"Post count: {post_count}  |  Last rotation set: {last_set}",
        "",
        f"AVAILABLE ({len(available) + len(never_used)} tags)",
        *available[:8],
        "",
        f"NEVER USED ({len(never_used)} tags)",
        *never_used[:6],
        "",
        f"ON COOLDOWN ({len(on_cooldown_list)} tags)",
        *on_cooldown_list,
        "═══════════════════════════════════════════",
    ]
    return "\n".join(lines)


# ─── Week Generation ─────────────────────────────────────────────────────────

def generate_week_rotation(niche: str, platform: str) -> list[HashtagSet]:
    """Generate 7 distinct hashtag sets for a week of posting."""
    sets = []
    history = _load_usage_history()
    nh = _get_niche_history(history, niche)
    rotation_sets = HASHTAG_POOLS[niche]["rotation_sets"]
    set_labels = list(rotation_sets.keys())

    temp_history = dict(nh)  # simulate without writing

    for i in range(7):
        # Cycle through sets
        set_label = set_labels[i % len(set_labels)]
        tags = rotation_sets[set_label]
        tier_bkdn = _tier_breakdown(niche, tags)
        alt_sets = _get_alternative_sets(niche, set_label)

        report = _format_hashtag_set(
            niche, platform, f"Day {i+1} post", set_label,
            tags, tier_bkdn, alt_sets, [], temp_history,
        )

        sets.append(HashtagSet(
            niche=niche,
            platform=platform,
            topic=f"Day {i+1}",
            set_label=set_label,
            tags=tags,
            tier_breakdown=tier_bkdn,
            alternative_sets=alt_sets,
            cooldown_notes=[],
            generated_at=datetime.now().isoformat(),
            report=report,
        ))

    return sets


# ─── Main Entry Point ─────────────────────────────────────────────────────────

def get_hashtag_set(
    niche: str,
    platform: str = "linkedin",
    topic: str = "",
    emergency: bool = False,
) -> HashtagSet:
    """
    Get the recommended hashtag set for a post.

    Args:
        niche: One of ttbp / cb / tundexai / wellwithtunde / tundestalksmen
        platform: linkedin / instagram / twitter / x
        topic: Content topic (used for relevance scoring)
        emergency: If True, include emergency adjacent tags for unusual topics

    Returns:
        HashtagSet with recommended tags and rotation metadata
    """
    if niche not in VALID_NICHES:
        raise ValueError(f"Unknown niche '{niche}'. Valid: {VALID_NICHES}")

    history = _load_usage_history()
    nh = _get_niche_history(history, niche)

    set_label, tags, cooldown_notes = _select_tags_for_topic(
        niche, platform, topic, nh
    )

    if emergency:
        adj_tags = EMERGENCY_ADJACENT_TAGS.get(niche, [])
        for t in adj_tags[:2]:
            if t not in tags:
                tags.append(t)
        platform_config = PLATFORM_LIMITS.get(platform, PLATFORM_LIMITS["linkedin"])
        tags = tags[:platform_config["sweet_spot"][1]]

    tier_bkdn = _tier_breakdown(niche, tags)
    alt_sets = _get_alternative_sets(niche, set_label)

    report = _format_hashtag_set(
        niche, platform, topic, set_label,
        tags, tier_bkdn, alt_sets, cooldown_notes, nh,
    )

    return HashtagSet(
        niche=niche,
        platform=platform,
        topic=topic,
        set_label=set_label,
        tags=tags,
        tier_breakdown=tier_bkdn,
        alternative_sets=alt_sets,
        cooldown_notes=cooldown_notes,
        generated_at=datetime.now().isoformat(),
        report=report,
    )


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Hashtag Strategist — select optimized hashtag sets with rotation"
    )
    parser.add_argument(
        "--niche", required=True,
        choices=list(VALID_NICHES),
        help="Content niche"
    )
    parser.add_argument(
        "--platform",
        default="linkedin",
        choices=["linkedin", "instagram", "twitter", "x"],
        help="Target platform (default: linkedin)"
    )
    parser.add_argument("--topic", default="", help="Post topic for relevance scoring")
    parser.add_argument(
        "--week",
        action="store_true",
        help="Generate full 7-day rotation"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show cooldown status for the niche"
    )
    parser.add_argument(
        "--mark-used",
        metavar="TAGS",
        help="Mark tags as used after posting (e.g. '#Leadership #AI')"
    )
    parser.add_argument(
        "--emergency",
        action="store_true",
        help="Include emergency adjacent tags for unusual topics"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output full set as JSON"
    )
    args = parser.parse_args()

    # Mark used mode
    if args.mark_used:
        tags = re.findall(r'#\w+', args.mark_used)
        if not tags:
            print("Error: no valid hashtags found in --mark-used string", file=sys.stderr)
            sys.exit(1)
        mark_tags_used(args.niche, tags)
        print(f"Marked {len(tags)} tags as used for niche '{args.niche}':")
        for t in tags:
            print(f"  {t}")
        sys.exit(0)

    # Status mode
    if args.status:
        print(_format_status(args.niche))
        sys.exit(0)

    # Week mode
    if args.week:
        week_sets = generate_week_rotation(args.niche, args.platform)
        if args.json:
            print(json.dumps([asdict(s) for s in week_sets], indent=2, ensure_ascii=False))
        else:
            for i, s in enumerate(week_sets, 1):
                print(f"\n{'─'*45}")
                print(f"DAY {i}")
                print("  " + "  ".join(s.tags))
        sys.exit(0)

    # Standard single-post mode
    result = get_hashtag_set(
        niche=args.niche,
        platform=args.platform,
        topic=args.topic,
        emergency=args.emergency,
    )

    if args.json:
        print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
    else:
        print(result.report)

    sys.exit(0)


if __name__ == "__main__":
    main()

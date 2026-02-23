"""
Analytics Summarizer — Social Media Performance Brief Generator
Niche: ttbp | cb | tundexai | wellwithtunde | tundestalksmen
Author: Social Media Engine (Tunde Gbotosho)

Ingests ContentStudio exports, LinkedIn/Instagram/Twitter CSVs, or manual JSON.
Produces weekly/monthly performance briefs with niche benchmarks, pattern detection,
competitor comparison, and actionable recommendations.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from statistics import mean, median
from typing import Optional

# ─────────────────────────────────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).parent.parent / "data"
BENCHMARKS_FILE = DATA_DIR / "benchmarks.json"
HISTORY_FILE = DATA_DIR / "performance_history.json"

# ─────────────────────────────────────────────────────────────────────────────
# Niche benchmarks (LinkedIn-first; scaled for other platforms)
# ─────────────────────────────────────────────────────────────────────────────

NICHE_BENCHMARKS: dict[str, dict] = {
    "ttbp": {
        "name": "The Tunde Gbotosho Post (Leadership/Career)",
        "engagement_target": 3.0,
        "comment_rate_target": 0.5,
        "save_rate_target": 0.3,
        "share_rate_target": 0.2,
        "platform_scale": {"linkedin": 1.0, "instagram": 1.4, "twitter": 0.6},
        "pillars": ["leadership", "career", "management", "promotion", "africa"],
    },
    "cb": {
        "name": "Connecting Bridges (Literature/Culture)",
        "engagement_target": 2.5,
        "comment_rate_target": 0.4,
        "save_rate_target": 0.4,
        "share_rate_target": 0.3,
        "platform_scale": {"linkedin": 1.0, "instagram": 1.6, "twitter": 0.7},
        "pillars": ["books", "literature", "africa", "culture", "publishing", "chinua", "achebe"],
    },
    "tundexai": {
        "name": "TundeX AI (AI Strategy)",
        "engagement_target": 3.5,
        "comment_rate_target": 0.6,
        "save_rate_target": 0.5,
        "share_rate_target": 0.3,
        "platform_scale": {"linkedin": 1.0, "instagram": 1.2, "twitter": 0.8},
        "pillars": ["ai", "claude", "chatgpt", "llm", "automation", "benchmark", "enterprise"],
    },
    "wellwithtunde": {
        "name": "Well With Tunde (Wellness)",
        "engagement_target": 2.0,
        "comment_rate_target": 0.3,
        "save_rate_target": 0.5,
        "share_rate_target": 0.4,
        "platform_scale": {"linkedin": 1.0, "instagram": 1.8, "twitter": 0.5},
        "pillars": ["wellness", "health", "mindfulness", "habit", "body", "nutrition", "chronic"],
    },
    "tundestalksmen": {
        "name": "Tunde Talks Men (Men's Growth)",
        "engagement_target": 2.5,
        "comment_rate_target": 0.5,
        "save_rate_target": 0.4,
        "share_rate_target": 0.3,
        "platform_scale": {"linkedin": 1.0, "instagram": 1.5, "twitter": 0.7},
        "pillars": ["men", "father", "relationship", "accountability", "brotherhood", "faith"],
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# Content format patterns
# ─────────────────────────────────────────────────────────────────────────────

FORMAT_PATTERNS: dict[str, list[str]] = {
    "numbered_list":   [r"^\d+\.", r"→ \d+", r"#\d+"],
    "bullet_list":     [r"^[-•→]", r"^•"],
    "personal_story":  [r"\bI\b.{0,40}\byears?\b", r"\bI\b.{0,30}\bremember\b", r"\bmy\s+\w+\b.{0,20}\btold\b"],
    "bold_claim":      [r"[A-Z]{3,}", r"^\s*Stop\b", r"^\s*This is wrong", r"Nobody tells you"],
    "data_shock":      [r"\d+%", r"\$[\d,]+", r"\d+x\b", r"\d+K\b", r"\d+M\b"],
    "question_only":   [r"^\s*\w.{0,80}\?$"],
    "framework":       [r"\bframework\b", r"\bstep \d\b", r"\bphase \d\b", r"\bstage \d\b"],
    "contrarian":      [r"\bwrong\b", r"\blie\b", r"\bmyth\b", r"\bunpopular\b", r"\bno one says\b"],
}

# ─────────────────────────────────────────────────────────────────────────────
# Data classes
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class PostMetrics:
    post_id: str
    niche: str                       # detected or provided
    platform: str                    # linkedin | instagram | twitter
    published_at: str                # ISO date string
    content_preview: str             # first 120 chars
    format_type: str = "unknown"     # detected content format
    hook_words: str = ""             # first line extracted
    # Engagement
    impressions: int = 0
    reach: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    saves: int = 0
    clicks: int = 0
    # Computed
    engagement_rate: float = 0.0
    comment_rate: float = 0.0
    save_rate: float = 0.0
    share_rate: float = 0.0
    click_rate: float = 0.0
    benchmark_delta: float = 0.0    # vs niche target
    composite_score: float = 0.0    # 0-100
    hashtags: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class TopicInsight:
    title: str
    avg_engagement: float
    post_count: int
    format_type: str
    best_post_id: str


@dataclass
class NichePerformance:
    niche: str
    platform: str
    period_start: str
    period_end: str
    post_count: int
    avg_engagement_rate: float
    median_engagement_rate: float
    benchmark_target: float
    benchmark_status: str       # ABOVE | MEETING | BELOW
    top_performers: list[PostMetrics]
    bottom_performers: list[PostMetrics]
    format_breakdown: dict[str, float]   # format → avg engagement
    best_format: str
    worst_format: str
    timing_insights: dict[str, float]    # day/hour → avg engagement
    best_day: str
    best_hour: str
    patterns: list[str]
    hashtag_performance: dict[str, float]  # tag_set_label → avg engagement
    recommendations: list[str]
    trend: str                  # UP | STABLE | DOWN vs prior period
    trend_delta: float          # percentage point change


@dataclass
class CompetitorInsight:
    name: str
    platform: str
    avg_engagement_rate: float
    delta_vs_ours: float        # positive = they're ahead
    top_topic: str
    top_topic_engagement: float
    suggested_response: str


@dataclass
class WeeklyBrief:
    period: str
    period_start: str
    period_end: str
    niches_analyzed: list[str]
    platforms_analyzed: list[str]
    total_posts: int
    overall_avg_engagement: float
    niche_performances: list[NichePerformance]
    competitor_insights: list[CompetitorInsight]
    overall_recommendations: list[str]
    top_topics: list[TopicInsight]
    generated_at: str
    report: str


# ─────────────────────────────────────────────────────────────────────────────
# Parsers — normalize different source formats into PostMetrics
# ─────────────────────────────────────────────────────────────────────────────

def _safe_int(val) -> int:
    try:
        return int(str(val).replace(",", "").strip())
    except (ValueError, TypeError):
        return 0


def _safe_float(val) -> float:
    try:
        cleaned = str(val).replace("%", "").replace(",", "").strip()
        return float(cleaned)
    except (ValueError, TypeError):
        return 0.0


def _detect_niche(content: str) -> str:
    """Detect which niche a post belongs to based on content keywords."""
    text = content.lower()
    scores: dict[str, int] = {}
    for niche, config in NICHE_BENCHMARKS.items():
        score = sum(1 for pillar in config["pillars"] if pillar in text)
        if score > 0:
            scores[niche] = score
    if scores:
        return max(scores, key=lambda k: scores[k])
    return "ttbp"  # default


def _detect_format(content: str) -> str:
    """Detect the content format from the post text."""
    for fmt, patterns in FORMAT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
                return fmt
    return "narrative"


def _extract_hook(content: str) -> str:
    """Extract the first line / hook of the post."""
    lines = [ln.strip() for ln in content.split("\n") if ln.strip()]
    return lines[0][:120] if lines else content[:120]


def _compute_rates(post: PostMetrics) -> PostMetrics:
    """Fill in computed engagement rates."""
    base = post.impressions if post.impressions > 0 else max(post.reach, 1)
    total_eng = post.likes + post.comments + post.shares + post.saves
    post.engagement_rate = round((total_eng / base) * 100, 2)
    post.comment_rate = round((post.comments / base) * 100, 2)
    post.save_rate = round((post.saves / base) * 100, 2)
    post.share_rate = round((post.shares / base) * 100, 2)
    post.click_rate = round((post.clicks / base) * 100, 2)
    return post


def _score_post(post: PostMetrics) -> PostMetrics:
    """Compute composite score (0-100) vs benchmark."""
    bench = NICHE_BENCHMARKS.get(post.niche, NICHE_BENCHMARKS["ttbp"])
    target = bench["engagement_target"]
    scale = bench["platform_scale"].get(post.platform, 1.0)
    scaled_target = target * scale

    # Engagement rate component (50%)
    eng_score = min(50, (post.engagement_rate / scaled_target) * 50) if scaled_target > 0 else 0

    # Comment + save weight (30%)
    comment_score = min(15, (post.comment_rate / bench["comment_rate_target"]) * 15) if bench["comment_rate_target"] > 0 else 0
    save_score = min(15, (post.save_rate / bench["save_rate_target"]) * 15) if bench["save_rate_target"] > 0 else 0

    # Share + click (20%)
    share_score = min(10, (post.share_rate / bench["share_rate_target"]) * 10) if bench["share_rate_target"] > 0 else 0
    click_score = min(10, post.click_rate * 5)  # bonus for CTR

    post.composite_score = round(eng_score + comment_score + save_score + share_score + click_score, 1)
    post.benchmark_delta = round(post.engagement_rate - scaled_target, 2)
    return post


def _parse_contentstudio_json(raw: dict | list) -> list[PostMetrics]:
    """Parse ContentStudio analytics export (JSON)."""
    posts = []
    items = raw if isinstance(raw, list) else raw.get("data", raw.get("posts", []))
    for item in items:
        content = item.get("message", item.get("content", item.get("caption", "")))
        niche = item.get("niche") or _detect_niche(content)
        platform = item.get("platform", item.get("social_account_type", "linkedin")).lower()
        p = PostMetrics(
            post_id=str(item.get("id", item.get("post_id", ""))),
            niche=niche,
            platform=platform,
            published_at=str(item.get("published_at", item.get("created_at", ""))),
            content_preview=content[:120],
            format_type=_detect_format(content),
            hook_words=_extract_hook(content),
            impressions=_safe_int(item.get("impressions", item.get("reach", 0))),
            reach=_safe_int(item.get("reach", 0)),
            likes=_safe_int(item.get("likes", item.get("reactions", 0))),
            comments=_safe_int(item.get("comments", 0)),
            shares=_safe_int(item.get("shares", item.get("reposts", 0))),
            saves=_safe_int(item.get("saves", item.get("bookmarks", 0))),
            clicks=_safe_int(item.get("link_clicks", item.get("clicks", 0))),
            hashtags=item.get("hashtags", []),
        )
        posts.append(_score_post(_compute_rates(p)))
    return posts


def _parse_linkedin_csv(rows: list[dict]) -> list[PostMetrics]:
    """Parse LinkedIn native analytics CSV export."""
    posts = []
    for row in rows:
        content = row.get("Post Content", row.get("content", ""))
        niche = _detect_niche(content)
        p = PostMetrics(
            post_id=row.get("Post ID", row.get("id", "")),
            niche=niche,
            platform="linkedin",
            published_at=row.get("Date", row.get("Published Date", "")),
            content_preview=content[:120],
            format_type=_detect_format(content),
            hook_words=_extract_hook(content),
            impressions=_safe_int(row.get("Impressions", 0)),
            reach=_safe_int(row.get("Unique Views", row.get("Reach", 0))),
            likes=_safe_int(row.get("Likes", row.get("Reactions", 0))),
            comments=_safe_int(row.get("Comments", 0)),
            shares=_safe_int(row.get("Shares", row.get("Reposts", 0))),
            saves=0,  # LinkedIn CSV doesn't include saves
            clicks=_safe_int(row.get("Clicks", row.get("Link Clicks", 0))),
        )
        posts.append(_score_post(_compute_rates(p)))
    return posts


def _parse_instagram_csv(rows: list[dict]) -> list[PostMetrics]:
    """Parse Instagram / Meta Business Suite CSV export."""
    posts = []
    for row in rows:
        content = row.get("Description", row.get("Caption", row.get("Text", "")))
        niche = _detect_niche(content)
        p = PostMetrics(
            post_id=row.get("Post ID", row.get("Media ID", "")),
            niche=niche,
            platform="instagram",
            published_at=row.get("Date Published", row.get("Publish Time", "")),
            content_preview=content[:120],
            format_type=_detect_format(content),
            hook_words=_extract_hook(content),
            impressions=_safe_int(row.get("Impressions", 0)),
            reach=_safe_int(row.get("Reach", row.get("Accounts Reached", 0))),
            likes=_safe_int(row.get("Likes", 0)),
            comments=_safe_int(row.get("Comments", 0)),
            shares=_safe_int(row.get("Shares", 0)),
            saves=_safe_int(row.get("Saves", row.get("Bookmarks", 0))),
            clicks=_safe_int(row.get("Profile Visits", row.get("Link Clicks", 0))),
        )
        posts.append(_score_post(_compute_rates(p)))
    return posts


def _parse_twitter_csv(rows: list[dict]) -> list[PostMetrics]:
    """Parse Twitter/X analytics CSV export."""
    posts = []
    for row in rows:
        content = row.get("Tweet text", row.get("text", ""))
        niche = _detect_niche(content)
        p = PostMetrics(
            post_id=row.get("Tweet id", row.get("id", "")),
            niche=niche,
            platform="twitter",
            published_at=row.get("time", row.get("created_at", "")),
            content_preview=content[:120],
            format_type=_detect_format(content),
            hook_words=_extract_hook(content),
            impressions=_safe_int(row.get("impressions", 0)),
            reach=_safe_int(row.get("impressions", 0)),
            likes=_safe_int(row.get("likes", row.get("favorites", 0))),
            comments=_safe_int(row.get("replies", 0)),
            shares=_safe_int(row.get("retweets", 0)),
            saves=_safe_int(row.get("bookmarks", 0)),
            clicks=_safe_int(row.get("url clicks", row.get("link_clicks", 0))),
        )
        posts.append(_score_post(_compute_rates(p)))
    return posts


def _load_csv(path: Path) -> list[dict]:
    with open(path, "r", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def load_posts_from_file(path: Path, source: str = "auto") -> list[PostMetrics]:
    """Load and parse posts from a file. Auto-detects format if source='auto'."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    ext = path.suffix.lower()
    if ext == ".json":
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return _parse_contentstudio_json(raw)

    if ext == ".csv":
        rows = _load_csv(path)
        if not rows:
            return []
        headers = set(rows[0].keys())
        # Detect platform from CSV headers
        if source != "auto":
            src = source.lower()
        elif "Tweet text" in headers or "Tweet id" in headers:
            src = "twitter"
        elif "Description" in headers or "Media ID" in headers or "Accounts Reached" in headers:
            src = "instagram"
        else:
            src = "linkedin"

        parsers = {"linkedin": _parse_linkedin_csv, "instagram": _parse_instagram_csv, "twitter": _parse_twitter_csv}
        return parsers.get(src, _parse_linkedin_csv)(rows)

    raise ValueError(f"Unsupported file format: {ext}. Use .json or .csv")


def load_posts_from_dir(dir_path: Path) -> list[PostMetrics]:
    """Load all analytics files from a directory."""
    all_posts: list[PostMetrics] = []
    for f in Path(dir_path).iterdir():
        if f.suffix.lower() in (".json", ".csv"):
            try:
                all_posts.extend(load_posts_from_file(f))
            except Exception:
                pass
    return all_posts


# ─────────────────────────────────────────────────────────────────────────────
# Analysis
# ─────────────────────────────────────────────────────────────────────────────

def _filter_by_period(posts: list[PostMetrics], period: str) -> list[PostMetrics]:
    """Filter posts to the specified period (week | month | all)."""
    if period == "all":
        return posts
    now = datetime.now()
    cutoff = now - (timedelta(days=7) if period == "week" else timedelta(days=30))
    result = []
    for p in posts:
        try:
            dt = datetime.fromisoformat(p.published_at.split("T")[0])
            if dt >= cutoff:
                result.append(p)
        except (ValueError, AttributeError):
            result.append(p)  # keep if date unparseable
    return result or posts  # fallback to all if filtering yields nothing


def _analyze_formats(posts: list[PostMetrics]) -> tuple[dict[str, float], str, str]:
    """Returns {format: avg_engagement}, best_format, worst_format."""
    fmt_eng: dict[str, list[float]] = {}
    for p in posts:
        fmt_eng.setdefault(p.format_type, []).append(p.engagement_rate)
    breakdown = {fmt: round(mean(rates), 2) for fmt, rates in fmt_eng.items() if rates}
    if not breakdown:
        return {}, "unknown", "unknown"
    best = max(breakdown, key=lambda k: breakdown[k])
    worst = min(breakdown, key=lambda k: breakdown[k])
    return breakdown, best, worst


def _analyze_timing(posts: list[PostMetrics]) -> tuple[dict[str, float], str, str]:
    """Returns {day: avg_eng}, best_day, best_hour."""
    day_eng: dict[str, list[float]] = {}
    hour_eng: dict[str, list[float]] = {}
    days_map = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"}

    for p in posts:
        try:
            dt = datetime.fromisoformat(p.published_at.replace("Z", "+00:00").split("+")[0])
            day = days_map[dt.weekday()]
            hour = f"{dt.hour:02d}:00"
            day_eng.setdefault(day, []).append(p.engagement_rate)
            hour_eng.setdefault(hour, []).append(p.engagement_rate)
        except (ValueError, AttributeError):
            pass

    day_avgs = {d: round(mean(v), 2) for d, v in day_eng.items() if v}
    hour_avgs = {h: round(mean(v), 2) for h, v in hour_eng.items() if v}

    best_day = max(day_avgs, key=lambda k: day_avgs[k]) if day_avgs else "N/A"
    best_hour = max(hour_avgs, key=lambda k: hour_avgs[k]) if hour_avgs else "N/A"
    timing = {**day_avgs, **hour_avgs}
    return timing, best_day, best_hour


def _analyze_hashtag_performance(posts: list[PostMetrics]) -> dict[str, float]:
    """Map hashtag sets to average engagement rates."""
    set_eng: dict[str, list[float]] = {}
    for p in posts:
        if p.hashtags:
            key = " ".join(sorted(p.hashtags[:4]))
            set_eng.setdefault(key, []).append(p.engagement_rate)
    return {k: round(mean(v), 2) for k, v in set_eng.items() if v}


def _detect_patterns(posts: list[PostMetrics]) -> list[str]:
    """Detect high-signal patterns in the data."""
    patterns = []
    if not posts:
        return patterns

    # Format gap
    fmt_eng: dict[str, list[float]] = {}
    for p in posts:
        fmt_eng.setdefault(p.format_type, []).append(p.engagement_rate)
    for fmt, rates in fmt_eng.items():
        avg = mean(rates)
        others = [r for k, v in fmt_eng.items() for r in v if k != fmt]
        if others:
            others_avg = mean(others)
            if avg > others_avg * 1.5:
                patterns.append(f"Posts with '{fmt}' format: {avg:.1f}% avg vs {others_avg:.1f}% for others (+{avg - others_avg:.1f}pp)")
            elif avg < others_avg * 0.7:
                patterns.append(f"Posts with '{fmt}' format underperform: {avg:.1f}% vs {others_avg:.1f}% avg")

    # High-save posts
    high_save = [p for p in posts if p.save_rate > 0.5]
    if len(high_save) >= 2:
        formats = [p.format_type for p in high_save]
        dominant = max(set(formats), key=formats.count)
        patterns.append(f"High-save posts (>{0.5:.0%} save rate) are mostly '{dominant}' format — reference-quality content")

    # Comment engagement
    high_comment = [p for p in posts if p.comment_rate > 0.5]
    if high_comment:
        formats = [p.format_type for p in high_comment]
        dominant = max(set(formats), key=formats.count)
        patterns.append(f"Posts driving comments tend to be '{dominant}' format — algorithm reward signal active")

    # Low performers
    low = [p for p in posts if p.benchmark_delta < -1.5]
    if len(low) >= 2:
        formats = [p.format_type for p in low]
        dominant = max(set(formats), key=formats.count)
        patterns.append(f"Low performers cluster around '{dominant}' format — review hook quality for these")

    return patterns[:5]  # cap at 5 patterns


def _build_niche_recommendations(
    perf: NichePerformance,
    all_posts: list[PostMetrics],
) -> list[str]:
    """Generate actionable recommendations for a niche."""
    recs = []
    bench = NICHE_BENCHMARKS.get(perf.niche, {})

    if perf.benchmark_status == "BELOW":
        delta = abs(perf.avg_engagement_rate - perf.benchmark_target)
        recs.append(
            f"[{perf.niche}] Avg {perf.avg_engagement_rate:.1f}% is {delta:.1f}pp below {perf.benchmark_target:.1f}% target — "
            f"test '{perf.best_format}' format (your top performer this period)"
        )

    if perf.best_format != "unknown" and perf.worst_format != "unknown":
        best_rate = perf.format_breakdown.get(perf.best_format, 0)
        worst_rate = perf.format_breakdown.get(perf.worst_format, 0)
        if best_rate > worst_rate * 1.5:
            recs.append(
                f"[{perf.niche}] '{perf.best_format}' format: {best_rate:.1f}% vs '{perf.worst_format}': {worst_rate:.1f}% — "
                f"shift mix toward {perf.best_format}"
            )

    if perf.best_day != "N/A":
        recs.append(f"[{perf.niche}] Post on {perf.best_day} at {perf.best_hour} — historically highest reach/engagement")

    top = perf.top_performers[0] if perf.top_performers else None
    if top:
        recs.append(
            f"[{perf.niche}] Top post ({top.engagement_rate:.1f}%) used '{top.format_type}' hook — "
            f"consider a follow-up or repurpose for deeper engagement"
        )

    # Save rate signal
    avg_save = mean([p.save_rate for p in all_posts if p.niche == perf.niche]) if all_posts else 0
    target_save = bench.get("save_rate_target", 0.3)
    if avg_save > target_save * 1.5:
        recs.append(
            f"[{perf.niche}] Save rate {avg_save:.1f}% is well above target — "
            f"content is reference-worthy; consider LinkedIn Article to capture long-tail SEO"
        )

    return recs[:4]  # max 4 per niche


def _analyze_niche(
    posts: list[PostMetrics],
    niche: str,
    platform: str,
) -> Optional[NichePerformance]:
    """Build a NichePerformance summary for one niche + platform combination."""
    filtered = [p for p in posts if p.niche == niche and p.platform == platform]
    if not filtered:
        return None

    bench = NICHE_BENCHMARKS.get(niche, NICHE_BENCHMARKS["ttbp"])
    scale = bench["platform_scale"].get(platform, 1.0)
    target = bench["engagement_target"] * scale

    sorted_posts = sorted(filtered, key=lambda p: p.composite_score, reverse=True)
    avg_eng = round(mean([p.engagement_rate for p in filtered]), 2)
    med_eng = round(median([p.engagement_rate for p in filtered]), 2)

    if avg_eng >= target:
        status = "ABOVE"
    elif avg_eng >= target * 0.85:
        status = "MEETING"
    else:
        status = "BELOW"

    fmt_breakdown, best_fmt, worst_fmt = _analyze_formats(filtered)
    timing, best_day, best_hour = _analyze_timing(filtered)
    hashtag_perf = _analyze_hashtag_performance(filtered)
    patterns = _detect_patterns(filtered)

    published_dates = []
    for p in filtered:
        try:
            published_dates.append(datetime.fromisoformat(p.published_at.split("T")[0]))
        except (ValueError, AttributeError):
            pass
    period_start = min(published_dates).strftime("%Y-%m-%d") if published_dates else "N/A"
    period_end = max(published_dates).strftime("%Y-%m-%d") if published_dates else "N/A"

    perf = NichePerformance(
        niche=niche,
        platform=platform,
        period_start=period_start,
        period_end=period_end,
        post_count=len(filtered),
        avg_engagement_rate=avg_eng,
        median_engagement_rate=med_eng,
        benchmark_target=round(target, 2),
        benchmark_status=status,
        top_performers=sorted_posts[:3],
        bottom_performers=sorted_posts[-3:][::-1],
        format_breakdown=fmt_breakdown,
        best_format=best_fmt,
        worst_format=worst_fmt,
        timing_insights=timing,
        best_day=best_day,
        best_hour=best_hour,
        patterns=patterns,
        hashtag_performance=hashtag_perf,
        recommendations=[],
        trend="STABLE",
        trend_delta=0.0,
    )
    perf.recommendations = _build_niche_recommendations(perf, filtered)
    return perf


def _compare_competitors(
    our_posts: list[PostMetrics],
    competitor_data: list[dict],
) -> list[CompetitorInsight]:
    """Compare our performance to competitor data."""
    our_avg = mean([p.engagement_rate for p in our_posts]) if our_posts else 0
    insights = []
    for comp in competitor_data:
        their_avg = _safe_float(comp.get("avg_engagement_rate", 0))
        delta = round(their_avg - our_avg, 2)
        top_topic = comp.get("top_topic", "")
        top_topic_eng = _safe_float(comp.get("top_topic_engagement", 0))

        if delta > 0.5:
            suggestion = f"They outperform on '{top_topic}' — consider a response or adjacent take"
        elif delta < -0.5:
            suggestion = f"We outperform them ({abs(delta):.1f}pp ahead) — maintain content quality"
        else:
            suggestion = f"Comparable performance — differentiate by doubling down on unique angles"

        insights.append(CompetitorInsight(
            name=comp.get("name", "Competitor"),
            platform=comp.get("platform", "linkedin"),
            avg_engagement_rate=their_avg,
            delta_vs_ours=delta,
            top_topic=top_topic,
            top_topic_engagement=top_topic_eng,
            suggested_response=suggestion,
        ))
    return insights


def _extract_top_topics(performances: list[NichePerformance]) -> list[TopicInsight]:
    """Extract top topics from top-performing posts."""
    seen = set()
    topics = []
    for perf in performances:
        for post in perf.top_performers[:2]:
            key = post.content_preview[:60].lower()
            if key not in seen:
                seen.add(key)
                topics.append(TopicInsight(
                    title=post.content_preview[:80],
                    avg_engagement=post.engagement_rate,
                    post_count=1,
                    format_type=post.format_type,
                    best_post_id=post.post_id,
                ))
    return sorted(topics, key=lambda t: t.avg_engagement, reverse=True)[:6]


# ─────────────────────────────────────────────────────────────────────────────
# Formatting
# ─────────────────────────────────────────────────────────────────────────────

_W = 60  # report width

def _bar(value: float, target: float, width: int = 20) -> str:
    filled = int(min(width, (value / max(target, 0.01)) * width))
    return "[" + "=" * filled + "-" * (width - filled) + "]"


def _status_icon(status: str) -> str:
    return {"ABOVE": "✅", "MEETING": "✓ ", "BELOW": "⚠️"}.get(status, "  ")


def _format_post_summary(post: PostMetrics, rank: int, prefix: str = "") -> str:
    hook = post.hook_words[:70] + ("..." if len(post.hook_words) > 70 else "")
    return (
        f"  {prefix}#{rank}  \"{hook}\"\n"
        f"       Engmt: {post.engagement_rate:.1f}%  |  Comments: {post.comments}"
        f"  |  Saves: {post.saves}  |  Shares: {post.shares}\n"
        f"       Format: {post.format_type}  |  Score: {post.composite_score:.0f}/100"
    )


def _format_weekly_brief(brief: WeeklyBrief) -> str:
    sep = "═" * _W
    sub = "─" * _W
    lines = [
        sep,
        "WEEKLY ANALYTICS BRIEF",
        sep,
        f"Period:   {brief.period_start}  →  {brief.period_end}",
        f"Niches:   {' | '.join(brief.niches_analyzed)}",
        f"Posts:    {brief.total_posts} analyzed",
        f"Generated: {brief.generated_at}",
        "",
        "OVERALL PERFORMANCE",
        f"  Avg Engagement Rate:  {brief.overall_avg_engagement:.1f}%",
    ]

    # Timing across all niches
    all_days = {}
    for perf in brief.niche_performances:
        for day, val in perf.timing_insights.items():
            if not day[0].isdigit():  # days only, not hours
                all_days.setdefault(day, []).append(val)
    if all_days:
        best_overall_day = max(all_days, key=lambda d: mean(all_days[d]))
        lines.append(f"  Best Day (overall):   {best_overall_day}")

    # Best format across all niches
    all_fmts: dict[str, list[float]] = {}
    for perf in brief.niche_performances:
        for fmt, rate in perf.format_breakdown.items():
            all_fmts.setdefault(fmt, []).append(rate)
    if all_fmts:
        best_fmt = max(all_fmts, key=lambda k: mean(all_fmts[k]))
        worst_fmt = min(all_fmts, key=lambda k: mean(all_fmts[k]))
        lines.append(f"  Best Format:          {best_fmt} ({mean(all_fmts[best_fmt]):.1f}% avg)")
        lines.append(f"  Lowest Format:        {worst_fmt} ({mean(all_fmts[worst_fmt]):.1f}% avg)")

    # Per-niche sections
    for perf in brief.niche_performances:
        bench = NICHE_BENCHMARKS.get(perf.niche, {})
        lines += [
            "",
            sub,
            f"NICHE: {perf.niche}  ({perf.post_count} posts)  [{perf.platform.upper()}]",
            sub,
            "",
            "  TOP PERFORMERS",
        ]
        for i, post in enumerate(perf.top_performers, 1):
            lines.append(_format_post_summary(post, i))
            lines.append("")

        lines.append("  BOTTOM PERFORMERS")
        for i, post in enumerate(perf.bottom_performers, 1):
            lines.append(_format_post_summary(post, i, prefix="⚠ "))
            lines.append("")

        icon = _status_icon(perf.benchmark_status)
        lines += [
            f"  BENCHMARK STATUS  {icon} {perf.benchmark_status}",
            f"    Avg: {perf.avg_engagement_rate:.1f}%  |  Target: {perf.benchmark_target:.1f}%  |  "
            f"Delta: {perf.avg_engagement_rate - perf.benchmark_target:+.1f}pp",
            "",
        ]

        if perf.patterns:
            lines.append("  PATTERNS DETECTED")
            for p in perf.patterns:
                lines.append(f"    → {p}")
            lines.append("")

        if perf.hashtag_performance:
            lines.append("  HASHTAG PERFORMANCE")
            for tag_set, rate in sorted(perf.hashtag_performance.items(), key=lambda x: x[1], reverse=True)[:3]:
                lines.append(f"    {tag_set[:50]}  →  {rate:.1f}%")
            lines.append("")

    # Competitor section
    if brief.competitor_insights:
        lines += [sub, "COMPETITOR SNAPSHOT", sub, ""]
        for comp in brief.competitor_insights:
            sign = "+" if comp.delta_vs_ours > 0 else ""
            lines += [
                f"  {comp.name}  ({comp.platform.upper()}):  Avg {comp.avg_engagement_rate:.1f}%  "
                f"({sign}{comp.delta_vs_ours:.1f}pp vs us)",
                f"    Top topic: \"{comp.top_topic}\"  ({comp.top_topic_engagement:.1f}%)",
                f"    → {comp.suggested_response}",
                "",
            ]

    # Overall recommendations
    lines += [sub, "RECOMMENDATIONS FOR NEXT WEEK", sub, ""]
    all_recs = brief.overall_recommendations
    for i, rec in enumerate(all_recs, 1):
        lines.append(f"  {i}. {rec}")
    lines.append("")

    # Top topics
    if brief.top_topics:
        lines += ["TOP PERFORMING TOPICS (repurpose candidates)", ""]
        for t in brief.top_topics[:4]:
            lines.append(f"  {t.avg_engagement:.1f}%  |  {t.format_type}  |  \"{t.title[:60]}\"")
        lines.append("")

    lines.append(sep)
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# History + persistence
# ─────────────────────────────────────────────────────────────────────────────

def _save_to_history(posts: list[PostMetrics]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    history: list[dict] = []
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except (json.JSONDecodeError, IOError):
            history = []
    existing_ids = {p["post_id"] for p in history}
    new_posts = [asdict(p) for p in posts if p.post_id not in existing_ids]
    history.extend(new_posts)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def _load_history() -> list[PostMetrics]:
    if not HISTORY_FILE.exists():
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return [PostMetrics(**p) for p in raw]
    except (json.JSONDecodeError, TypeError, IOError):
        return []


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def summarize_week(
    data_path: str | Path = None,
    period: str = "week",
    competitors_path: str | Path = None,
    niche_filter: str = None,
    platform_filter: str = None,
) -> WeeklyBrief:
    """
    Main entry point. Load analytics data, analyze, and return a WeeklyBrief.

    Args:
        data_path: Path to file or directory of exports.
        period: 'week' | 'month' | 'all'
        competitors_path: Optional path to competitor JSON data.
        niche_filter: Limit to one niche.
        platform_filter: Limit to one platform.
    """
    # Load posts
    if data_path:
        p = Path(data_path)
        posts = load_posts_from_dir(p) if p.is_dir() else load_posts_from_file(p)
    else:
        posts = _load_history()

    posts = _filter_by_period(posts, period)

    if niche_filter:
        posts = [p for p in posts if p.niche == niche_filter]
    if platform_filter:
        posts = [p for p in posts if p.platform == platform_filter]

    if not posts:
        raise ValueError("No posts found for the specified period and filters.")

    # Save new data to history
    _save_to_history(posts)

    # Analyze per niche × platform
    niches = list(dict.fromkeys(p.niche for p in posts))
    platforms = list(dict.fromkeys(p.platform for p in posts))
    performances: list[NichePerformance] = []
    for niche in niches:
        for plat in platforms:
            perf = _analyze_niche(posts, niche, plat)
            if perf:
                performances.append(perf)

    # Competitors
    competitor_insights: list[CompetitorInsight] = []
    if competitors_path:
        try:
            with open(competitors_path, "r", encoding="utf-8") as f:
                comp_data = json.load(f)
            competitor_insights = _compare_competitors(posts, comp_data if isinstance(comp_data, list) else comp_data.get("competitors", []))
        except (IOError, json.JSONDecodeError):
            pass

    # Overall recommendations (aggregate + de-dup)
    all_recs = []
    seen_recs = set()
    for perf in performances:
        for rec in perf.recommendations:
            if rec not in seen_recs:
                seen_recs.add(rec)
                all_recs.append(rec)
    for comp in competitor_insights:
        suggestion = f"[competitor] {comp.suggested_response}"
        if suggestion not in seen_recs:
            all_recs.append(suggestion)

    # Dates
    published_dates = []
    for p in posts:
        try:
            published_dates.append(datetime.fromisoformat(p.published_at.split("T")[0]))
        except (ValueError, AttributeError):
            pass
    period_start = min(published_dates).strftime("%Y-%m-%d") if published_dates else "N/A"
    period_end = max(published_dates).strftime("%Y-%m-%d") if published_dates else "N/A"
    overall_avg = round(mean([p.engagement_rate for p in posts]), 2)

    brief = WeeklyBrief(
        period=period,
        period_start=period_start,
        period_end=period_end,
        niches_analyzed=niches,
        platforms_analyzed=platforms,
        total_posts=len(posts),
        overall_avg_engagement=overall_avg,
        niche_performances=performances,
        competitor_insights=competitor_insights,
        overall_recommendations=all_recs[:8],
        top_topics=_extract_top_topics(performances),
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        report="",
    )
    brief.report = _format_weekly_brief(brief)
    return brief


def get_top_topics(brief: WeeklyBrief, niche: str = None, n: int = 3) -> list[TopicInsight]:
    """Return top N topics from a brief, optionally filtered by niche."""
    topics = brief.top_topics
    if niche:
        perfs = [p for p in brief.niche_performances if p.niche == niche]
        if perfs:
            niche_post_ids = {post.post_id for perf in perfs for post in perf.top_performers}
            topics = [t for t in topics if t.best_post_id in niche_post_ids]
    return topics[:n]


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="analytics_summarizer",
        description="Social Media Analytics Summarizer — generates weekly performance briefs",
    )
    p.add_argument("--file", help="Path to analytics export file (.json or .csv)")
    p.add_argument("--dir", help="Path to directory of analytics files")
    p.add_argument("--source", default="auto", choices=["auto", "contentstudio", "linkedin", "instagram", "twitter"],
                   help="Data source (auto-detected if not specified)")
    p.add_argument("--period", default="week", choices=["week", "month", "all"],
                   help="Analysis period (default: week)")
    p.add_argument("--niche", help="Limit to one niche: ttbp | cb | tundexai | wellwithtunde | tundestalksmen")
    p.add_argument("--platform", help="Limit to one platform: linkedin | instagram | twitter")
    p.add_argument("--competitors", help="Path to competitor data JSON")
    p.add_argument("--post-id", help="Single post deep-dive")
    p.add_argument("--top-topics", action="store_true", help="Output top topics only (for pipeline)")
    p.add_argument("--json", action="store_true", help="Output raw JSON (for pipeline)")
    return p


def _deep_dive(post_id: str, data_path: str) -> str:
    """Single post detailed breakdown."""
    path = Path(data_path)
    posts = load_posts_from_dir(path) if path.is_dir() else load_posts_from_file(path)
    match = [p for p in posts if p.post_id == post_id]
    if not match:
        return f"Post ID '{post_id}' not found in data."
    p = match[0]
    return (
        f"═══ POST DEEP DIVE ═══\n"
        f"ID:           {p.post_id}\n"
        f"Niche:        {p.niche}  |  Platform: {p.platform}\n"
        f"Published:    {p.published_at}\n"
        f"Format:       {p.format_type}\n"
        f"Hook:         \"{p.hook_words[:100]}\"\n\n"
        f"ENGAGEMENT\n"
        f"  Impressions:   {p.impressions:,}\n"
        f"  Reach:         {p.reach:,}\n"
        f"  Likes:         {p.likes}\n"
        f"  Comments:      {p.comments}  ({p.comment_rate:.2f}%)\n"
        f"  Saves:         {p.saves}  ({p.save_rate:.2f}%)\n"
        f"  Shares:        {p.shares}  ({p.share_rate:.2f}%)\n"
        f"  Link Clicks:   {p.clicks}  ({p.click_rate:.2f}%)\n"
        f"  Overall:       {p.engagement_rate:.2f}%\n\n"
        f"SCORE:  {p.composite_score:.0f}/100  |  Benchmark delta: {p.benchmark_delta:+.2f}pp\n"
        f"Hashtags: {' '.join(p.hashtags) or 'N/A'}\n"
    )


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    # Single post deep dive
    if args.post_id:
        source_path = args.file or args.dir or "."
        print(_deep_dive(args.post_id, source_path))
        sys.exit(0)

    data_path = args.file or args.dir
    try:
        brief = summarize_week(
            data_path=data_path,
            period=args.period,
            competitors_path=args.competitors,
            niche_filter=args.niche,
            platform_filter=args.platform,
        )
    except (ValueError, FileNotFoundError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        # Serialize without the formatted report for clean pipeline output
        output = asdict(brief)
        output.pop("report", None)
        # Convert PostMetrics objects to dicts inside niche_performances
        print(json.dumps(output, indent=2, default=str))
        sys.exit(0)

    if args.top_topics:
        topics = get_top_topics(brief, niche=args.niche)
        for t in topics:
            print(f"{t.avg_engagement:.1f}%  |  {t.format_type}  |  \"{t.title}\"")
        sys.exit(0)

    print(brief.report)

    # Exit codes: 0=all niches above/meeting benchmark, 1=some below
    below = [p for p in brief.niche_performances if p.benchmark_status == "BELOW"]
    sys.exit(1 if below else 0)


if __name__ == "__main__":
    main()

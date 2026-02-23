"""
timing_engine.py — Best-time optimization engine for Content Empire scheduling.

Returns optimal posting times per platform per day, adjusted for niche audience
and day-of-week. All times are Eastern Time (ET) since Tunde's core audience
is US-based.

Usage:
    from timing_engine import get_best_times, get_week_schedule
    times = get_best_times("linkedin", "tuesday")
    schedule = get_week_schedule("ttbp", "2026-W08")
"""

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")

# ── Optimal posting windows per platform ──────────────────────────────────────
# Based on: platform algorithm research, B2C/B2B audience patterns, niche analysis
# Format: {day: [(hour, minute), ...]}  — listed best-to-good order

PLATFORM_TIMING: dict[str, dict[str, list[tuple[int, int]]]] = {
    "linkedin": {
        "monday":    [(8, 0), (12, 0)],
        "tuesday":   [(8, 0), (10, 0), (12, 0)],
        "wednesday": [(9, 0), (12, 0)],
        "thursday":  [(8, 0), (10, 0)],
        "friday":    [(9, 0)],
        "saturday":  [],   # LinkedIn dead on weekends
        "sunday":    [],
    },
    "twitter": {
        "monday":    [(8, 0), (12, 0), (17, 0)],
        "tuesday":   [(9, 0), (12, 0), (18, 0)],
        "wednesday": [(8, 0), (17, 0)],
        "thursday":  [(8, 0), (18, 0)],
        "friday":    [(9, 0), (12, 0)],
        "saturday":  [(10, 0)],
        "sunday":    [(11, 0)],
    },
    "instagram": {
        "monday":    [(11, 0), (14, 0)],
        "tuesday":   [(8, 0), (14, 0)],
        "wednesday": [(11, 0)],
        "thursday":  [(8, 0), (17, 0)],
        "friday":    [(11, 0), (14, 0)],
        "saturday":  [(9, 0), (11, 0)],
        "sunday":    [(10, 0)],
    },
    "facebook": {
        "monday":    [(13, 0)],
        "tuesday":   [(13, 0), (15, 0)],
        "wednesday": [(13, 0)],
        "thursday":  [(9, 0), (13, 0)],
        "friday":    [(11, 0)],
        "saturday":  [(12, 0)],
        "sunday":    [(11, 0)],
    },
    "newsletter": {
        "tuesday":   [(7, 0)],
        "thursday":  [(8, 0)],
        # Newsletters only go out on best days — skip others
    },
    "youtube_short": {
        "monday":    [(15, 0)],
        "wednesday": [(15, 0)],
        "friday":    [(15, 0)],
        "saturday":  [(10, 0)],
        "sunday":    [(14, 0)],
    },
    "youtube_long": {
        "tuesday":   [(15, 0)],
        "thursday":  [(15, 0)],
        "saturday":  [(12, 0)],
    },
}

# ── Niche audience adjustments ────────────────────────────────────────────────
# Shift in hours relative to base platform time for niche-specific audience

NICHE_TIME_ADJUSTMENTS: dict[str, int] = {
    "ttbp":            0,   # Professional US audience — standard times work
    "cb":              1,   # Book readers skew later morning / evenings
    "tundexai":       -1,   # Tech founders often check early AM
    "wellwithtunde":   0,   # Standard
    "tundestalksmen":  1,   # Men check social during lunch / evenings
}


def get_best_time(platform: str, day: str, niche: str = "ttbp") -> tuple[int, int] | None:
    """
    Return (hour, minute) for the best posting time on a given platform + day.
    Returns None if platform doesn't post on that day.
    """
    day = day.lower()
    times = PLATFORM_TIMING.get(platform, {}).get(day, [])
    if not times:
        return None

    h, m = times[0]  # Best time is first in list
    adj = NICHE_TIME_ADJUSTMENTS.get(niche, 0)
    h = max(6, min(22, h + adj))  # Clamp to 6am–10pm
    return (h, m)


def get_all_times(platform: str, day: str, niche: str = "ttbp") -> list[tuple[int, int]]:
    """Return all valid posting times for platform + day (adjusted for niche)."""
    day = day.lower()
    times = PLATFORM_TIMING.get(platform, {}).get(day, [])
    adj = NICHE_TIME_ADJUSTMENTS.get(niche, 0)
    return [(max(6, min(22, h + adj)), m) for h, m in times]


def iso_week_to_monday(iso_week: str) -> datetime:
    """
    Convert ISO week string (e.g. '2026-W08') to the Monday datetime for that week.
    Returns naive datetime — caller adds timezone.
    """
    year, week_num = iso_week.split("-W")
    # ISO week Monday = Jan 4 + (week-1)*7 days back to Monday
    jan_4 = datetime(int(year), 1, 4)
    start_of_week = jan_4 + timedelta(weeks=int(week_num) - 1)
    # Roll back to Monday
    monday = start_of_week - timedelta(days=start_of_week.weekday())
    return monday


def get_week_schedule(
    niche: str,
    iso_week: str,
    platforms: list[str] | None = None,
) -> list[dict]:
    """
    Build a full week's optimized posting schedule for all platforms.
    Returns list of slot dicts with ISO datetime strings (ET).

    Each slot: {
        "slot_id": str,
        "platform": str,
        "day": str,
        "scheduled_time": str (ISO 8601 with ET offset),
        "status": "PENDING_CONTENT",
        "content_type": str,
    }
    """
    from platform_specs import VALID_PLATFORMS
    platforms = platforms or VALID_PLATFORMS

    monday = iso_week_to_monday(iso_week)
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    slots = []

    for day_idx, day_name in enumerate(days):
        day_date = monday + timedelta(days=day_idx)

        for platform in platforms:
            times = get_all_times(platform, day_name, niche)
            for slot_idx, (hour, minute) in enumerate(times):
                dt = datetime(
                    day_date.year, day_date.month, day_date.day,
                    hour, minute, 0,
                    tzinfo=ET
                )
                # ContentStudio expects ISO 8601 with offset
                iso_time = dt.isoformat()

                week_compact = iso_week.replace("-", "").replace("W", "W")
                slot_id = f"{niche}_{week_compact}_{day_name[:3]}_{platform}_{slot_idx+1:02d}"

                from platform_specs import get_spec
                spec = get_spec(platform)

                slots.append({
                    "slot_id": slot_id,
                    "platform": platform,
                    "contentstudio_platform": spec.contentstudio_platform,
                    "day": day_name,
                    "date": day_date.strftime("%Y-%m-%d"),
                    "scheduled_time": iso_time,
                    "status": "PENDING_CONTENT",
                    "content_type": spec.post_types[0],
                    "niche": niche,
                    "week": iso_week,
                })

    return slots


def get_best_days(platform: str) -> list[str]:
    """Return days (in order) where this platform has optimal posting times."""
    timing = PLATFORM_TIMING.get(platform, {})
    return [day for day, times in timing.items() if times]

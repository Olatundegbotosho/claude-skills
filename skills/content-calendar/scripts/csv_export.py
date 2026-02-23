"""
csv_export.py — CSV schedule writer for Content Empire content calendar.

Produces a human-readable, Buffer/Hootsuite-compatible CSV of the week's
posting schedule. Can also be opened in Google Sheets / Excel for manual review.

CSV columns:
    slot_id, niche, week, platform, day, date, scheduled_time_et, content_type,
    status, content_preview, hashtags, notes

Usage:
    from csv_export import write_csv_schedule, slots_to_csv_rows
    write_csv_schedule(slots, out_dir="./output", niche="ttbp", week="2026-W08")
"""

import csv
import io
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")

# CSV column headers — in display order
CSV_HEADERS = [
    "slot_id",
    "niche",
    "week",
    "platform",
    "day",
    "date",
    "scheduled_time_et",
    "content_type",
    "status",
    "content_preview",
    "hashtags",
    "media_url",
    "notes",
]

# Platform display names for human-readable CSV
PLATFORM_DISPLAY = {
    "linkedin":      "LinkedIn",
    "twitter":       "Twitter / X",
    "instagram":     "Instagram",
    "facebook":      "Facebook",
    "newsletter":    "Newsletter (Beehiiv)",
    "youtube_short": "YouTube Short",
    "youtube_long":  "YouTube Long",
}


def slot_to_csv_row(
    slot: dict,
    content_preview: str = "",
    hashtags: str = "",
    media_url: str = "",
    notes: str = "",
) -> dict:
    """
    Convert a slot dict (from timing_engine) to a flat CSV row dict.

    Args:
        slot: Slot dict from timing_engine.get_week_schedule()
        content_preview: First 100 chars of content (if available)
        hashtags: Space-separated hashtag string
        media_url: URL to media asset (if scheduled)
        notes: Any manual notes for this slot

    Returns:
        Dict matching CSV_HEADERS
    """
    # Parse scheduled_time and format for human-readable ET
    raw_time = slot.get("scheduled_time", "")
    try:
        dt = datetime.fromisoformat(raw_time)
        et_str = dt.astimezone(ET).strftime("%Y-%m-%d %I:%M %p ET")
    except (ValueError, TypeError):
        et_str = raw_time

    platform = slot.get("platform", "")
    preview = content_preview[:100] + "..." if len(content_preview) > 100 else content_preview

    return {
        "slot_id": slot.get("slot_id", ""),
        "niche": slot.get("niche", ""),
        "week": slot.get("week", ""),
        "platform": PLATFORM_DISPLAY.get(platform, platform),
        "day": slot.get("day", "").capitalize(),
        "date": slot.get("date", ""),
        "scheduled_time_et": et_str,
        "content_type": slot.get("content_type", ""),
        "status": slot.get("status", "PENDING_CONTENT"),
        "content_preview": preview,
        "hashtags": hashtags,
        "media_url": media_url,
        "notes": notes,
    }


def slots_to_csv_rows(
    slots: list[dict],
    content_map: dict[str, str] | None = None,
    hashtag_map: dict[str, str] | None = None,
) -> list[dict]:
    """
    Convert a list of slots to CSV rows.

    Args:
        slots: List of slot dicts from timing_engine
        content_map: Optional {slot_id: content_text}
        hashtag_map: Optional {slot_id: hashtag_string}

    Returns:
        List of CSV row dicts
    """
    content_map = content_map or {}
    hashtag_map = hashtag_map or {}

    rows = []
    for slot in slots:
        sid = slot.get("slot_id", "")
        row = slot_to_csv_row(
            slot,
            content_preview=content_map.get(sid, ""),
            hashtags=hashtag_map.get(sid, ""),
        )
        rows.append(row)
    return rows


def write_csv_schedule(
    slots: list[dict],
    out_dir: str | Path,
    niche: str,
    week: str,
    content_map: dict[str, str] | None = None,
    hashtag_map: dict[str, str] | None = None,
    filename: str | None = None,
) -> Path:
    """
    Write full week schedule to CSV file.

    Args:
        slots: List of slot dicts from timing_engine.get_week_schedule()
        out_dir: Directory to write to
        niche: Niche slug (for filename)
        week: ISO week string (for filename)
        content_map: Optional {slot_id: content_text}
        hashtag_map: Optional {slot_id: hashtag_string}
        filename: Override output filename

    Returns:
        Path to written CSV file
    """
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    if not filename:
        week_compact = week.replace("-", "")
        filename = f"schedule_{niche}_{week_compact}.csv"

    file_path = out_path / filename
    rows = slots_to_csv_rows(slots, content_map=content_map, hashtag_map=hashtag_map)

    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writeheader()
        writer.writerows(rows)

    return file_path


def csv_to_string(
    slots: list[dict],
    content_map: dict[str, str] | None = None,
) -> str:
    """Return CSV as a string (for preview or API posting)."""
    rows = slots_to_csv_rows(slots, content_map=content_map)
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=CSV_HEADERS)
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def filter_slots_by_platform(slots: list[dict], platform: str) -> list[dict]:
    """Return only slots for a given platform."""
    return [s for s in slots if s.get("platform") == platform]


def filter_slots_by_day(slots: list[dict], day: str) -> list[dict]:
    """Return only slots for a given day of week."""
    return [s for s in slots if s.get("day", "").lower() == day.lower()]


def summary_stats(slots: list[dict]) -> dict:
    """Return a summary of slot counts by platform."""
    from collections import Counter
    platform_counts = Counter(s.get("platform") for s in slots)
    return {
        "total_slots": len(slots),
        "by_platform": dict(platform_counts),
        "days_covered": len({s.get("day") for s in slots}),
    }

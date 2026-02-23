"""
contentstudio_export.py — ContentStudio Agency Unlimited bulk import JSON builder.

Takes a list of schedule slots (from timing_engine) and builds a ContentStudio-
compatible bulk import payload. ContentStudio's bulk import accepts a JSON array
of post objects per workspace.

Reference: ContentStudio Agency Unlimited (25 accounts, 5 workspaces, full API)

Usage:
    from contentstudio_export import build_bulk_import, write_bulk_import
    payload = build_bulk_import(slots, niche="ttbp", week="2026-W08")
    write_bulk_import(payload, out_dir="./output/cs")
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ── ContentStudio workspace mapping ──────────────────────────────────────────
# These map niche slugs to ContentStudio workspace IDs.
# Replace with actual workspace IDs from your ContentStudio account.

CS_WORKSPACE_MAP: dict[str, str] = {
    "ttbp":            "ws_ttbp_001",       # Replace with actual CS workspace ID
    "cb":              "ws_cb_001",
    "tundexai":        "ws_tundexai_001",
    "wellwithtunde":   "ws_wellwithtunde_001",
    "tundestalksmen":  "ws_tundestalksmen_001",
}

# ContentStudio platform identifiers
CS_PLATFORM_IDS: dict[str, str] = {
    "linkedin":      "linkedin",
    "twitter":       "twitter",
    "instagram":     "instagram",
    "facebook":      "facebook",
    "newsletter":    "email",
    "youtube_short": "youtube",
    "youtube_long":  "youtube",
}

# ContentStudio post type mapping
CS_POST_TYPES: dict[str, str] = {
    "long-form-post": "text",
    "short-post":     "text",
    "carousel":       "carousel",
    "thread":         "text",
    "feed-post":      "text",
    "link-post":      "link",
    "newsletter":     "email",
    "youtube-short":  "video",
    "youtube-video":  "video",
    "reel":           "video",
    "document":       "document",
}


def build_post_object(slot: dict, content: str | None = None, media_urls: list[str] | None = None) -> dict:
    """
    Build a single ContentStudio post object from a schedule slot.

    Args:
        slot: Slot dict from timing_engine.get_week_schedule()
        content: Post content text (None = PENDING_CONTENT placeholder)
        media_urls: Optional list of media URLs for image/video posts
    """
    platform = slot["platform"]
    cs_platform = CS_PLATFORM_IDS.get(platform, platform)
    cs_post_type = CS_POST_TYPES.get(slot.get("content_type", "text"), "text")

    post = {
        "id": slot["slot_id"],
        "workspace_id": CS_WORKSPACE_MAP.get(slot["niche"], "ws_default"),
        "platform": cs_platform,
        "post_type": cs_post_type,
        "scheduled_time": slot["scheduled_time"],
        "status": slot["status"],
        "content": {
            "text": content or f"[PENDING — {slot['niche']} {platform} {slot['week']}]",
            "hashtags": [],
            "media": [{"url": u, "type": "image"} for u in (media_urls or [])],
        },
        "metadata": {
            "niche": slot["niche"],
            "week": slot["week"],
            "day": slot["day"],
            "slot_id": slot["slot_id"],
            "generated_by": "content-calendar",
        },
    }

    # Platform-specific additions
    if platform == "newsletter":
        post["email"] = {
            "subject": f"[PENDING SUBJECT — {slot['week']}]",
            "preview_text": "[PENDING PREVIEW TEXT]",
            "from_name": "Tunde Gbotosho",
        }

    if platform in ("youtube_short", "youtube_long"):
        post["video"] = {
            "title": f"[PENDING TITLE — {slot['week']}]",
            "description": "[PENDING DESCRIPTION]",
            "tags": [],
        }

    return post


def build_bulk_import(
    slots: list[dict],
    niche: str,
    week: str,
    content_map: dict[str, str] | None = None,
) -> dict:
    """
    Build a full ContentStudio bulk import payload.

    Args:
        slots: List of slot dicts from timing_engine.get_week_schedule()
        niche: Niche slug
        week: ISO week string (e.g. '2026-W08')
        content_map: Optional {slot_id: content_text} to pre-fill content

    Returns:
        Dict matching ContentStudio bulk import schema
    """
    content_map = content_map or {}
    posts = []

    for slot in slots:
        content = content_map.get(slot["slot_id"])
        post = build_post_object(slot, content=content)
        posts.append(post)

    return {
        "schema_version": "1.0",
        "workspace_id": CS_WORKSPACE_MAP.get(niche, "ws_default"),
        "niche": niche,
        "week": week,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "post_count": len(posts),
        "posts": posts,
        "_import_instructions": (
            "Import via ContentStudio > Bulk Scheduling > Upload JSON. "
            "Review PENDING_CONTENT slots before activating schedule."
        ),
    }


def write_bulk_import(payload: dict, out_dir: str | Path, filename: str | None = None) -> Path:
    """
    Write the bulk import JSON to disk.

    Args:
        payload: Dict from build_bulk_import()
        out_dir: Directory to write to (created if needed)
        filename: Override filename (default: bulk_import_{niche}_{week}.json)

    Returns:
        Path to written file
    """
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    if not filename:
        niche = payload.get("niche", "unknown")
        week = payload.get("week", "W00").replace("-", "")
        filename = f"bulk_import_{niche}_{week}.json"

    file_path = out_path / filename
    file_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    return file_path


def split_by_platform(payload: dict) -> dict[str, dict]:
    """
    Split a bulk import payload into per-platform sub-payloads.
    Useful for platforms that need separate ContentStudio imports.

    Returns: {platform_slug: {payload_dict}}
    """
    by_platform: dict[str, list] = {}
    for post in payload.get("posts", []):
        p = post["platform"]
        by_platform.setdefault(p, []).append(post)

    result = {}
    for platform, posts in by_platform.items():
        sub_payload = dict(payload)  # shallow copy
        sub_payload["posts"] = posts
        sub_payload["post_count"] = len(posts)
        result[platform] = sub_payload

    return result

"""
calendar_gen.py — Main CLI orchestrator for the Content Empire content calendar.

Generates a weekly content calendar for any niche, exports to ContentStudio JSON
and/or CSV, and prints a human-readable summary.

Usage:
    python calendar_gen.py --niche ttbp --week 2026-W08
    python calendar_gen.py --niche all --week 2026-W08 --out ./calendars
    python calendar_gen.py --niche tundexai --week 2026-W08 --platforms linkedin,twitter
    python calendar_gen.py --niche ttbp --week 2026-W08 --format csv
    python calendar_gen.py --niche ttbp --week 2026-W08 --dry-run

Exit codes:
    0  Success
    1  Invalid arguments
    2  Config error
    3  Export error
"""

import argparse
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add scripts dir to path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "social-repurposer" / "scripts"))

from timing_engine import get_week_schedule, get_iso_week, VALID_PLATFORMS
from contentstudio_export import build_bulk_import, write_bulk_import
from csv_export import write_csv_schedule, summary_stats

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

VALID_NICHES = ["ttbp", "cb", "tundexai", "wellwithtunde", "tundestalksmen"]
DEFAULT_SCHEDULE_PATH = Path(__file__).parent.parent / "config" / "default_schedule.yaml"


# ── Logging ────────────────────────────────────────────────────────────────────

def setup_logging(log_path: str | None = None, verbose: bool = False) -> logging.Logger:
    level = logging.DEBUG if verbose else logging.INFO
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_path:
        Path(log_path).parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_path, encoding="utf-8"))
    logging.basicConfig(
        level=level,
        format="[%(asctime)s] %(levelname)s %(message)s",
        handlers=handlers
    )
    return logging.getLogger("calendar_gen")


# ── Argument parsing ────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="calendar_gen.py",
        description="Content Empire Content Calendar Generator",
    )
    parser.add_argument(
        "--niche", required=True,
        choices=VALID_NICHES + ["all"],
        help="Niche slug or 'all' to generate for every niche"
    )
    parser.add_argument(
        "--week", default=None,
        help="ISO week string e.g. 2026-W08 (defaults to current week)"
    )
    parser.add_argument(
        "--platforms", default="all",
        help=f"Comma-separated platform list or 'all'. Options: {', '.join(VALID_PLATFORMS)}"
    )
    parser.add_argument(
        "--out", default="./calendars",
        help="Output directory root (default: ./calendars)"
    )
    parser.add_argument(
        "--format", choices=["both", "json", "csv"], default="both",
        help="Output format: both (default), json only, csv only"
    )
    parser.add_argument(
        "--log", default=None,
        help="Path to log file"
    )
    parser.add_argument(
        "--priority-filter", choices=["high", "medium", "low", "all"], default="all",
        help="Only include slots at this priority level or above"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print what would be generated without writing files"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Enable verbose logging"
    )
    return parser.parse_args()


# ── Schedule config loading ────────────────────────────────────────────────────

def load_schedule_config(niche: str) -> dict | None:
    """Load the default_schedule.yaml config for a niche, if available."""
    if not YAML_AVAILABLE:
        return None
    if not DEFAULT_SCHEDULE_PATH.exists():
        return None
    with open(DEFAULT_SCHEDULE_PATH, encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config.get("niches", {}).get(niche)


def filter_slots_by_priority(slots: list[dict], niche: str, priority_filter: str) -> list[dict]:
    """
    Filter schedule slots based on priority level from default_schedule.yaml.
    Falls back to returning all slots if config unavailable.
    """
    if priority_filter == "all":
        return slots

    niche_config = load_schedule_config(niche)
    if not niche_config:
        return slots  # Can't filter — no config

    priority_order = {"high": 3, "medium": 2, "low": 1}
    min_priority = priority_order.get(priority_filter, 1)

    # Build lookup: (platform, day) → priority
    priority_map: dict[tuple, str] = {}
    for entry in niche_config.get("schedule", []):
        key = (entry["platform"], entry["day"])
        priority_map[key] = entry.get("priority", "medium")

    filtered = []
    for slot in slots:
        key = (slot["platform"], slot["day"])
        slot_priority = priority_map.get(key, "medium")
        if priority_order.get(slot_priority, 2) >= min_priority:
            filtered.append(slot)

    return filtered


# ── Platform resolver ──────────────────────────────────────────────────────────

def resolve_platforms(platforms_arg: str) -> list[str]:
    if platforms_arg.lower() == "all":
        return VALID_PLATFORMS
    platforms = [p.strip() for p in platforms_arg.split(",")]
    invalid = [p for p in platforms if p not in VALID_PLATFORMS]
    if invalid:
        print(f"ERROR: Unknown platforms: {', '.join(invalid)}", file=sys.stderr)
        sys.exit(1)
    return platforms


# ── Single-niche calendar generation ──────────────────────────────────────────

def generate_calendar(
    niche: str,
    week: str,
    platforms: list[str],
    out_dir: str | Path,
    output_format: str,
    priority_filter: str,
    dry_run: bool,
    logger: logging.Logger,
) -> dict:
    """
    Generate and export the content calendar for one niche + week.
    Returns dict of output paths.
    """
    logger.info(f"Generating calendar: niche={niche}, week={week}")

    # Build slots from timing engine
    slots = get_week_schedule(niche, week, platforms=platforms)
    slots = filter_slots_by_priority(slots, niche, priority_filter)

    logger.info(f"[{niche}] {len(slots)} slots generated across {len(platforms)} platforms")

    if dry_run:
        stats = summary_stats(slots)
        print(f"\n🔍 DRY RUN — {niche} / {week}")
        print(f"  Total slots: {stats['total_slots']}")
        print(f"  By platform: {stats['by_platform']}")
        print(f"  Days covered: {stats['days_covered']}")
        print(f"  Would write to: {Path(out_dir) / niche}\n")
        return {}

    # Create niche-specific output subdirectory
    niche_out = Path(out_dir) / niche / week.replace("-", "")
    niche_out.mkdir(parents=True, exist_ok=True)

    output_paths = {}

    # Write ContentStudio JSON
    if output_format in ("both", "json"):
        payload = build_bulk_import(slots, niche=niche, week=week)
        json_path = write_bulk_import(payload, out_dir=niche_out)
        output_paths["json"] = json_path
        logger.info(f"[{niche}] ContentStudio JSON → {json_path}")

    # Write CSV schedule
    if output_format in ("both", "csv"):
        csv_path = write_csv_schedule(
            slots,
            out_dir=niche_out,
            niche=niche,
            week=week,
        )
        output_paths["csv"] = csv_path
        logger.info(f"[{niche}] CSV schedule → {csv_path}")

    return output_paths


# ── Main ────────────────────────────────────────────────────────────────────────

def main() -> int:
    args = parse_args()
    logger = setup_logging(args.log, args.verbose)

    week = args.week or get_iso_week()
    platforms = resolve_platforms(args.platforms)
    niches = VALID_NICHES if args.niche == "all" else [args.niche]

    logger.info(f"Content Calendar: week={week}, niches={niches}, platforms={len(platforms)}")

    all_paths = {}
    errors = []

    for niche in niches:
        try:
            paths = generate_calendar(
                niche=niche,
                week=week,
                platforms=platforms,
                out_dir=args.out,
                output_format=args.format,
                priority_filter=args.priority_filter,
                dry_run=args.dry_run,
                logger=logger,
            )
            all_paths[niche] = paths
        except Exception as e:
            logger.error(f"[{niche}] FAILED: {e}")
            errors.append(niche)

    if not args.dry_run:
        print(f"\n✅ Calendar generation complete")
        print(f"   Week: {week}")
        print(f"   Niches: {', '.join(niches)}")
        for niche, paths in all_paths.items():
            for fmt, path in paths.items():
                print(f"   [{niche}] {fmt.upper()}: {path}")

    if errors:
        logger.warning(f"Errors on niches: {', '.join(errors)}")
        return 3

    return 0


if __name__ == "__main__":
    sys.exit(main())

"""
repurpose.py — Main CLI orchestrator for the Content Empire social repurposer.

Repurposes one piece of content (topic + optional research file) into platform-
native posts for LinkedIn, Twitter/X, Instagram, Facebook, Newsletter, and YouTube.

Usage:
    python repurpose.py --niche ttbp --topic "AI replacing jobs" --week 2026-W08
    python repurpose.py --niche cb --source research.md --week 2026-W08
    python repurpose.py --niche tundexai --topic "LLM benchmarks" --formats linkedin,twitter
    python repurpose.py --niche ttbp --topic "AI jobs" --dry-run

Exit codes:
    0  Success — all outputs written
    1  Invalid arguments
    2  Niche config error
    3  Generation error (partial outputs may exist)
    4  Export error
"""

import argparse
import json
import logging
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add scripts dir to path so we can import sibling modules
sys.path.insert(0, str(Path(__file__).parent))

from niche_config import get_niche_config, list_niches, VALID_NICHES
from platform_specs import VALID_PLATFORMS, get_spec, get_generation_prompt, validate_output
from voice_loader import build_voice_context
from export import ExportManager

# ── Logging ──────────────────────────────────────────────────────────────────

def setup_logging(log_path: str | None, verbose: bool = False) -> logging.Logger:
    level = logging.DEBUG if verbose else logging.INFO
    fmt = "[%(asctime)s] %(levelname)s %(message)s"
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_path:
        Path(log_path).parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_path, encoding="utf-8"))
    logging.basicConfig(level=level, format=fmt, handlers=handlers)
    return logging.getLogger("repurpose")


# ── Argument parsing ──────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="repurpose.py",
        description="Content Empire Social Repurposer — one topic → all platforms",
    )
    # Required-ish
    parser.add_argument("--niche", required=True, choices=VALID_NICHES,
                        help="Content niche slug (ttbp, cb, tundexai, wellwithtunde, tundestalksmen)")
    parser.add_argument("--topic", default=None,
                        help="Topic or title string for this repurpose run")
    parser.add_argument("--source", default=None,
                        help="Path to research brief markdown file")

    # Optional
    parser.add_argument("--week", default=None,
                        help="ISO week string e.g. 2026-W08 (defaults to current week)")
    parser.add_argument("--formats", default="all",
                        help=f"Comma-separated platforms or 'all'. Options: {', '.join(VALID_PLATFORMS)}")
    parser.add_argument("--out", default="./output",
                        help="Output directory root (default: ./output)")
    parser.add_argument("--log", default=None,
                        help="Path to log file")
    parser.add_argument("--output-format", choices=["both", "markdown", "json"], default="both",
                        help="Output format: both (default), markdown only, json only")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview what would be generated without writing files")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Enable verbose logging")

    args = parser.parse_args()

    # Validate: must have --topic OR --source
    if not args.topic and not args.source:
        parser.error("At least one of --topic or --source is required")

    return args


# ── Source loading ────────────────────────────────────────────────────────────

def load_source(source_path: str | None, topic: str | None) -> tuple[str, str]:
    """
    Load research content and derive topic if not provided.
    Returns (topic_str, source_content_str).
    """
    source_content = ""

    if source_path:
        path = Path(source_path)
        if not path.exists():
            print(f"ERROR: Source file not found: {source_path}", file=sys.stderr)
            sys.exit(1)
        source_content = path.read_text(encoding="utf-8").strip()

    if not topic:
        # Try to extract topic from first H1 in source
        match = re.search(r"^#\s+(.+)$", source_content, re.MULTILINE)
        topic = match.group(1).strip() if match else "Content Empire Post"

    return topic, source_content


# ── ISO week helper ────────────────────────────────────────────────────────────

def get_iso_week() -> str:
    now = datetime.now(timezone.utc)
    year, week, _ = now.isocalendar()
    return f"{year}-W{week:02d}"


# ── Format resolver ────────────────────────────────────────────────────────────

def resolve_formats(formats_arg: str) -> list[str]:
    if formats_arg.lower() == "all":
        return VALID_PLATFORMS
    platforms = [p.strip() for p in formats_arg.split(",")]
    invalid = [p for p in platforms if p not in VALID_PLATFORMS]
    if invalid:
        print(f"ERROR: Unknown platforms: {', '.join(invalid)}. Valid: {', '.join(VALID_PLATFORMS)}", file=sys.stderr)
        sys.exit(1)
    return platforms


# ── Content generation ────────────────────────────────────────────────────────

def generate_post(
    niche: str,
    platform: str,
    topic: str,
    source_content: str,
    voice_context: str,
    logger: logging.Logger,
    dry_run: bool = False,
) -> tuple[str, int]:
    """
    Generate platform-specific content.
    In dry-run mode, returns a placeholder.
    Returns (content_str, confidence_score).

    NOTE: In production, this calls an LLM API (Anthropic Claude).
    For offline/cron use, this can call a local generation script or API.
    The generation prompt is fully assembled here and logged for debugging.
    """
    spec = get_spec(platform)
    platform_prompt = get_generation_prompt(platform, niche, topic)

    full_prompt = (
        f"{voice_context}\n\n"
        f"{platform_prompt}\n\n"
        f"Source Research:\n{source_content or topic}\n\n"
        f"Generate the post now:"
    )

    logger.debug(f"[{platform}] Prompt length: {len(full_prompt)} chars")

    if dry_run:
        preview = (
            f"[DRY RUN — {spec.display_name}]\n"
            f"Topic: {topic}\n"
            f"Niche: {niche}\n"
            f"Prompt length: {len(full_prompt)} chars\n"
            f"Structure: {', '.join(spec.structure[:3])}..."
        )
        logger.info(f"[{platform}] DRY RUN — would generate {spec.char_limit} {spec.char_unit}")
        return preview, 0

    # ── Production: Replace this with your LLM call ──────────────────────────
    # Example Anthropic SDK call (uncomment and configure):
    #
    # import anthropic
    # client = anthropic.Anthropic()
    # message = client.messages.create(
    #     model="claude-opus-4-5",
    #     max_tokens=2048,
    #     messages=[{"role": "user", "content": full_prompt}]
    # )
    # content = message.content[0].text
    # confidence = score_content(content, platform, niche)
    # return content, confidence
    # ─────────────────────────────────────────────────────────────────────────

    # Placeholder for now — replace with LLM call above
    logger.warning(f"[{platform}] LLM generation not yet wired. Returning placeholder.")
    placeholder = (
        f"[PLACEHOLDER — configure LLM call in generate_post()]\n"
        f"Platform: {platform}\nTopic: {topic}\nNiche: {niche}"
    )
    return placeholder, 50


def score_content(content: str, platform: str, niche: str) -> int:
    """
    Heuristic confidence scorer (0-100).
    Replace with LLM-based scoring in Phase 2.
    """
    score = 50  # baseline

    # Hook strength: does it open with a strong first line?
    first_line = content.split("\n")[0] if content else ""
    if any(c.isdigit() for c in first_line[:20]):
        score += 10  # Has a stat up front
    if "?" in first_line or ":" in first_line:
        score += 5   # Tension or colon hook

    # Platform length compliance
    spec = get_spec(platform)
    if spec.char_unit == "chars" and len(content) <= spec.char_limit:
        score += 10
    if spec.char_unit == "words" and len(content.split()) <= spec.char_limit:
        score += 10

    # Hashtag presence
    hashtag_count = content.count("#")
    min_tags, max_tags = spec.hashtag_count
    if max_tags > 0 and min_tags <= hashtag_count <= max_tags:
        score += 10

    # Red flag detection (banned phrases from Voice DNA)
    banned = ["unpack", "at the end of the day", "it goes without saying",
              "In today's fast-paced world", "synergy", "leverage"]
    for phrase in banned:
        if phrase.lower() in content.lower():
            score -= 15

    return max(0, min(100, score))


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    args = parse_args()
    logger = setup_logging(args.log, args.verbose)

    # Resolve week
    week = args.week or get_iso_week()
    logger.info(f"Repurpose run: niche={args.niche}, week={week}")

    # Load source content
    topic, source_content = load_source(args.source, args.topic)
    logger.info(f"Topic: {topic}")

    # Resolve platforms
    platforms = resolve_formats(args.formats)
    logger.info(f"Platforms: {', '.join(platforms)}")

    # Dry-run mode
    if args.dry_run:
        print(f"\n🔍 DRY RUN — Content Empire Social Repurposer")
        print(f"  Niche:    {args.niche}")
        print(f"  Topic:    {topic}")
        print(f"  Week:     {week}")
        print(f"  Formats:  {', '.join(platforms)}")
        print(f"  Output:   {args.out}")
        print(f"\n  Would generate {len(platforms)} platform posts.")
        print(f"  Run without --dry-run to execute.\n")
        return 0

    # Build voice context (loaded once, reused across all platforms)
    try:
        voice_context = build_voice_context(args.niche)
        logger.info(f"Voice DNA loaded for niche: {args.niche}")
    except Exception as e:
        logger.error(f"Failed to load Voice DNA: {e}")
        return 2

    # Set up export manager
    em = ExportManager(
        out_dir=args.out,
        niche=args.niche,
        topic=topic,
        week=week,
    )

    # Generate and export per platform
    errors = []
    for platform in platforms:
        logger.info(f"Generating: {platform}...")
        try:
            content, confidence = generate_post(
                niche=args.niche,
                platform=platform,
                topic=topic,
                source_content=source_content,
                voice_context=voice_context,
                logger=logger,
                dry_run=args.dry_run,
            )

            # Re-score with our heuristic if LLM didn't score
            if confidence == 50:
                confidence = score_content(content, platform, args.niche)

            # Validate
            validation = validate_output(platform, content)
            if validation["issues"]:
                for issue in validation["issues"]:
                    logger.warning(f"[{platform}] Validation issue: {issue}")
                confidence = max(0, confidence - 10)

            # Write output (skip markdown/json based on output-format flag)
            if args.output_format in ("both", "markdown", "json"):
                em.write_post(platform, content, confidence=confidence)
                logger.info(f"[{platform}] ✅ Written — confidence: {confidence}/100")

        except Exception as e:
            logger.error(f"[{platform}] FAILED: {e}")
            errors.append(platform)

    # Finalize export
    try:
        paths = em.finalize()
        logger.info(f"Export complete → {paths['run_dir']}")
    except Exception as e:
        logger.error(f"Export finalization failed: {e}")
        return 4

    if errors:
        logger.warning(f"Completed with errors on: {', '.join(errors)}")
        return 3

    return 0


if __name__ == "__main__":
    sys.exit(main())

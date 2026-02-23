"""
platform_specs.py — Per-platform format rules, character limits, and validation.

Each platform spec defines what a valid output looks like and how to format it
for ContentStudio bulk import. All specs are algorithm-first: optimized for
native discovery signals, not just character compliance.

Usage:
    from platform_specs import get_spec, VALID_PLATFORMS, validate_output
    spec = get_spec("linkedin")
"""

from dataclasses import dataclass, field

VALID_PLATFORMS = [
    "linkedin", "twitter", "instagram", "facebook", "newsletter", "youtube_short", "youtube_long"
]

ALL_FORMATS = VALID_PLATFORMS  # alias for CLI --formats all


@dataclass
class PlatformSpec:
    name: str
    display_name: str
    contentstudio_platform: str          # ContentStudio API platform identifier
    char_limit: int                       # Hard character/word limit
    char_unit: str                        # "chars" or "words"
    hook_rule: str                        # First line / opening rule
    structure: list[str]                  # Expected content blocks in order
    hashtag_count: tuple[int, int]        # (min, max)
    algorithm_signals: list[str]          # What signals to optimize for
    post_types: list[str]                 # Content types for this platform
    media_types: list[str]                # Supported media
    output_file: str                      # Default output filename stub
    extra: dict = field(default_factory=dict)  # Platform-specific extras


PLATFORM_SPECS: dict[str, PlatformSpec] = {

    "linkedin": PlatformSpec(
        name="linkedin",
        display_name="LinkedIn",
        contentstudio_platform="linkedin",
        char_limit=3000,
        char_unit="chars",
        hook_rule="First 2 lines must stand alone without 'See more'. Bold claim, stat, or story tension.",
        structure=[
            "Hook (lines 1-2, < 200 chars)",
            "Bridge: why this matters to the reader",
            "Body: 3-5 insight blocks (short paragraphs, 2-3 lines each)",
            "Evidence or personal story",
            "Call to action or closing question",
            "Hashtags (line break before, 3-5 tags)",
        ],
        hashtag_count=(3, 5),
        algorithm_signals=["dwell_time", "comments", "saves", "first_hour_engagement"],
        post_types=["long-form-post", "short-post", "carousel", "document", "video"],
        media_types=["none", "image", "video", "document", "carousel"],
        output_file="linkedin.md",
        extra={
            "optimal_length": "1200-2000 chars",
            "best_times_et": ["Tue 8am", "Wed 9am", "Thu 8am"],
            "avoid_times": ["Fri afternoon", "weekends"],
            "emoji_rule": "Sparingly — 1-2 max, only to break sections not decorate",
        }
    ),

    "twitter": PlatformSpec(
        name="twitter",
        display_name="Twitter / X",
        contentstudio_platform="twitter",
        char_limit=280,
        char_unit="chars",
        hook_rule="Lead with the hot take or the most surprising stat. First tweet must stand alone.",
        structure=[
            "Tweet 1: Hook / hot take (standalone, < 240 chars with media space)",
            "Tweet 2: Context or tension (1-2 sentences)",
            "Tweets 3-7: Build the argument (1 point per tweet)",
            "Tweet 8: Payoff or call to action",
            "Tweet 9 (optional): Signature + link",
        ],
        hashtag_count=(1, 2),
        algorithm_signals=["retweets", "bookmarks", "replies", "first_30min_engagement"],
        post_types=["thread", "single-tweet", "quote-tweet"],
        media_types=["none", "image", "video", "gif"],
        output_file="twitter_thread.md",
        extra={
            "thread_length": "5-9 tweets optimal",
            "best_times_et": ["Mon-Fri 8-10am", "12pm", "6-9pm"],
            "numbering": "Number each tweet: '1/ ', '2/ ' etc.",
            "each_tweet_standalone": True,
        }
    ),

    "instagram": PlatformSpec(
        name="instagram",
        display_name="Instagram",
        contentstudio_platform="instagram",
        char_limit=2200,
        char_unit="chars",
        hook_rule="First line of caption must hook before 'more'. Visual-first: hook assumes image is seen.",
        structure=[
            "Hook line 1 (< 125 chars — shows before 'more')",
            "Line break",
            "Body: story or insight (3-4 short paragraphs)",
            "Call to action (save, share, comment prompt)",
            "Line break",
            "Hashtag block (20-30 tags, can go in first comment)",
        ],
        hashtag_count=(20, 30),
        algorithm_signals=["save_rate", "shares", "comments", "watch_time_for_reels"],
        post_types=["feed-post", "carousel", "reel", "story"],
        media_types=["image", "carousel", "video", "reel"],
        output_file="instagram.md",
        extra={
            "carousel_slides": "7 slides optimal (hook, 5 value, CTA)",
            "best_times_et": ["Mon/Wed/Fri 12pm", "Tue/Thu 8am"],
            "hashtag_placement": "First comment preferred for clean look",
            "reel_hook_seconds": 3,
        }
    ),

    "facebook": PlatformSpec(
        name="facebook",
        display_name="Facebook",
        contentstudio_platform="facebook",
        char_limit=500,
        char_unit="chars",
        hook_rule="First sentence drives curiosity or relatability. Community tone, not broadcast.",
        structure=[
            "Hook (curiosity or relatable question, 1-2 sentences)",
            "Body: short, punchy paragraphs (3-5 lines total)",
            "Engagement prompt (question to drive comments)",
            "2-4 hashtags max",
        ],
        hashtag_count=(2, 4),
        algorithm_signals=["comments", "shares", "reactions", "link_clicks"],
        post_types=["feed-post", "link-post", "video", "event"],
        media_types=["image", "video", "link", "none"],
        output_file="facebook.md",
        extra={
            "best_times_et": ["Wed 1pm", "Thu 9am", "Fri 11am"],
            "group_posting": "Cross-post to relevant Facebook Groups for 3-5x reach",
            "link_note": "Native video outperforms link posts; avoid link-in-caption",
        }
    ),

    "newsletter": PlatformSpec(
        name="newsletter",
        display_name="Newsletter (Beehiiv)",
        contentstudio_platform="email",
        char_limit=1200,
        char_unit="words",
        hook_rule="Subject line + preview text must work together as one unit. Open loop in subject.",
        structure=[
            "Subject line (40-60 chars, open loop or number)",
            "Preview text (90-130 chars, continues the hook)",
            "Opening story (150-250 words, personal or surprising)",
            "Bridge: why this matters now",
            "Core content: 3-4 insight sections with subheadings",
            "Practical takeaway or action step",
            "Signature sign-off (warm, personal)",
            "P.S. (optional — best for CTAs)",
        ],
        hashtag_count=(0, 0),  # No hashtags in email
        algorithm_signals=["open_rate", "click_rate", "forward_rate", "reply_rate"],
        post_types=["newsletter", "digest", "feature-story"],
        media_types=["image", "none"],
        output_file="newsletter.md",
        extra={
            "word_range": "600-1200 words",
            "best_send_days_et": ["Tuesday 7am", "Thursday 8am"],
            "platform": "Beehiiv",
            "subject_line_rule": "Never start with 'I'. Use tension, number, or direct address.",
            "preview_text_rule": "Don't repeat subject line. Continue the hook.",
        }
    ),

    "youtube_short": PlatformSpec(
        name="youtube_short",
        display_name="YouTube Short",
        contentstudio_platform="youtube",
        char_limit=60,
        char_unit="seconds",
        hook_rule="Hook in first 3 seconds — bold claim or question. Energy is high from frame 1.",
        structure=[
            "Hook (0-3 sec): bold claim or pattern interrupt",
            "Point (4-45 sec): one clear insight or story beat",
            "Payoff (46-55 sec): punchline or key takeaway",
            "CTA (55-60 sec): subscribe, comment, or follow prompt",
        ],
        hashtag_count=(3, 5),
        algorithm_signals=["watch_time_pct", "swipe_away_rate", "comments", "shares"],
        post_types=["youtube-short"],
        media_types=["vertical-video"],
        output_file="youtube_short_script.md",
        extra={
            "format": "Vertical 9:16",
            "script_delivery": "Conversational, punchy, no jargon",
            "invideo_prompt": True,  # Trigger InVideo.ai prompt generation
        }
    ),

    "youtube_long": PlatformSpec(
        name="youtube_long",
        display_name="YouTube Long-Form",
        contentstudio_platform="youtube",
        char_limit=12,
        char_unit="minutes",
        hook_rule="Open loop in first 30 seconds. State the payoff, don't deliver it yet.",
        structure=[
            "Hook (0-30 sec): bold claim + tease of payoff",
            "Credibility bridge (30-60 sec): why Tunde is the right voice",
            "Chapter 1: Problem or context (2-3 min)",
            "Chapter 2: Insight or framework (3-4 min)",
            "Chapter 3: Application or story (3-4 min)",
            "Recap + CTA (1-2 min): subscribe, newsletter, next video",
        ],
        hashtag_count=(5, 8),
        algorithm_signals=["avg_view_duration", "click_through_rate", "comments", "end_screen_clicks"],
        post_types=["youtube-video"],
        media_types=["horizontal-video"],
        output_file="youtube_long_script.md",
        extra={
            "thumbnail_brief": True,  # Generate thumbnail copy alongside script
            "chapter_markers": True,  # Include timestamp chapter markers
            "optimal_length": "8-12 minutes",
            "invideo_prompt": False,
        }
    ),
}


def get_spec(platform: str) -> PlatformSpec:
    """Return the PlatformSpec for the given platform slug."""
    if platform not in PLATFORM_SPECS:
        raise ValueError(
            f"Unknown platform '{platform}'. Valid: {', '.join(VALID_PLATFORMS)}"
        )
    return PLATFORM_SPECS[platform]


def validate_output(platform: str, content: str) -> dict:
    """
    Basic validation of generated content against platform spec.
    Returns {"valid": bool, "issues": list[str], "warnings": list[str]}.
    """
    spec = get_spec(platform)
    issues = []
    warnings = []

    # Length check
    if spec.char_unit == "chars":
        length = len(content)
        if length > spec.char_limit:
            issues.append(f"Content {length} chars exceeds {spec.char_limit} char limit")
        elif length > spec.char_limit * 0.95:
            warnings.append(f"Content approaching limit: {length}/{spec.char_limit} chars")

    elif spec.char_unit == "words":
        word_count = len(content.split())
        word_limit = spec.char_limit
        if word_count > word_limit:
            issues.append(f"Content {word_count} words exceeds {word_limit} word limit")

    # Hashtag count check (simple)
    hashtag_count = content.count("#")
    min_tags, max_tags = spec.hashtag_count
    if max_tags > 0 and hashtag_count > max_tags:
        issues.append(f"Too many hashtags: {hashtag_count} (max {max_tags})")
    if min_tags > 0 and hashtag_count < min_tags:
        warnings.append(f"Low hashtag count: {hashtag_count} (min {min_tags})")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "platform": platform,
    }


def get_generation_prompt(platform: str, niche: str, topic: str) -> str:
    """
    Build the platform-specific generation instruction block.
    Prepended after Voice DNA in generation calls.
    """
    spec = get_spec(platform)
    from niche_config import get_hashtags
    tags = get_hashtags(niche, platform, max_count=spec.hashtag_count[1])
    tag_str = " ".join(tags)

    structure_str = "\n".join(f"  {i+1}. {s}" for i, s in enumerate(spec.structure))

    return f"""=== PLATFORM: {spec.display_name.upper()} ===
Limit: {spec.char_limit} {spec.char_unit}
Hook Rule: {spec.hook_rule}

Required Structure:
{structure_str}

Hashtags to use ({spec.hashtag_count[0]}-{spec.hashtag_count[1]}): {tag_str}
Algorithm Signals to optimize for: {', '.join(spec.algorithm_signals)}
Topic: {topic}

Generate one high-quality {spec.display_name} post. Follow structure exactly.
=== END PLATFORM SPEC ===
"""

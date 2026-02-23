"""
voice_loader.py — Loads Voice DNA context blocks for any Content Empire niche.

Voice DNA files live at: ~/prompts/voice/{niche}_voice_dna.md
If the file is missing, returns a minimal fallback so generation can still run.

Usage:
    from voice_loader import load_voice_dna, build_voice_context
    voice_ctx = build_voice_context("ttbp")
"""

from pathlib import Path
from niche_config import get_niche_config

# Fallback Voice DNA used when niche-specific file is missing
FALLBACK_VOICE_DNA = """
## Voice DNA (Fallback — Tunde Gbotosho Core Voice)

IDENTITY: Tunde Gbotosho — Nigerian-American, UVA Stats + HBS CORe, author, entrepreneur, AI consultant.

TONE: Confident, warm, intellectually curious. Bridges tech/AI + utilities + culture + faith + entrepreneurship.

OPENING PATTERN: Always starts with a personal story, observation, or sharp data point. Never with the topic itself.

SIGNATURE PHRASES (use naturally, not mechanically):
- "Here's the thing..."
- "The truth is..."
- "Nobody talks about this, but..."

BANNED WORDS/PHRASES:
- "unpack" / "at the end of the day" / "it goes without saying"
- "In today's fast-paced world" / "synergy" / "leverage" (unless ironic)
- Corporate bullet-point lists masquerading as insight

STRUCTURAL RULES:
- Hook in first 2 lines — stops the scroll
- Personal story or data point before any argument
- End with a question OR a call to action, never both

PLATFORM VOICE CALIBRATION:
- LinkedIn: Professional authority, personal vulnerability, data-backed
- Twitter/X: Hot take first, defend later, each tweet standalone
- Instagram: Visual-first thinking, hook in caption line 1, save-worthy
- Newsletter: Full voice, story opens, 600–1200 words, educational
- YouTube: Conversational opener, energy in first 30 seconds
"""


def load_voice_dna(niche: str) -> str:
    """
    Load Voice DNA markdown for a niche.
    Returns file contents if found, fallback voice if not.
    """
    cfg = get_niche_config(niche)
    voice_path: Path = cfg["voice_dna_file"]

    if voice_path.exists():
        content = voice_path.read_text(encoding="utf-8").strip()
        return content

    # Try common alternate locations
    alt_paths = [
        Path.home() / ".claude" / "prompts" / "voice" / f"{niche}_voice_dna.md",
        Path.home() / ".claude" / "voice" / f"{niche}_voice_dna.md",
        Path.cwd() / "prompts" / f"{niche}_voice_dna.md",
    ]
    for alt in alt_paths:
        if alt.exists():
            return alt.read_text(encoding="utf-8").strip()

    # Return fallback so generation doesn't block
    print(f"[voice_loader] WARNING: No Voice DNA file found for '{niche}'. Using fallback.")
    print(f"  Expected: {voice_path}")
    print(f"  Create it there to get niche-specific voice calibration.")
    return FALLBACK_VOICE_DNA.strip()


def build_voice_context(niche: str, platform: str | None = None) -> str:
    """
    Build the full voice context block to prepend to any generation prompt.
    Optionally narrows calibration to a specific platform.
    """
    voice_dna = load_voice_dna(niche)
    cfg = get_niche_config(niche)

    platform_note = ""
    if platform:
        platform_note = f"\n\n### Active Platform: {platform.upper()}\nApply {platform} voice calibration from the Voice DNA above."

    return f"""=== VOICE DNA — {cfg['display_name'].upper()} ===
Primary Audience: {cfg['primary_audience']}
Voice Calibration: {cfg['voice_calibration']}

{voice_dna}{platform_note}

=== END VOICE DNA ===
"""


def voice_dna_exists(niche: str) -> bool:
    """Return True if a Voice DNA file exists for the niche."""
    cfg = get_niche_config(niche)
    return cfg["voice_dna_file"].exists()

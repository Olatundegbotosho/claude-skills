#!/usr/bin/env python3
"""
research_synth.py — Research Synthesizer for the Content Empire
Converts raw research inputs into structured content briefs.

Usage:
  python research_synth.py --niche ttbp --url https://hbr.org/...
  python research_synth.py --niche tundexai --text "GPT-4 benchmark results show..."
  python research_synth.py --niche cb --file notes/research.md
  python research_synth.py --niche ttbp --url https://... --text "extra context" --json
"""

import argparse
import json
import re
import sys
import urllib.request
import urllib.error
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

# ── Constants ─────────────────────────────────────────────────────────────────

VALID_NICHES = ["ttbp", "cb", "tundexai", "wellwithtunde", "tundestalksmen"]

# Niche-specific angle lenses — what does each audience care about most?
NICHE_ANGLE_LENSES: dict[str, dict] = {
    "ttbp": {
        "audience_concerns": [
            "career strategy and transitions",
            "AI and the future of work",
            "leadership and management realities",
            "entrepreneurship and building",
            "data literacy and evidence-based decisions",
            "faith, discipline, and identity",
        ],
        "angle_frames": [
            "What does this mean for mid-career professionals?",
            "What's the counterintuitive insight here?",
            "Where does the conventional advice fall short?",
            "What personal story does this enable?",
        ],
        "voice_keywords": [
            "here's the thing", "the truth is", "what nobody tells you",
            "think about that", "i've seen this",
        ],
        "banned_terms": [
            "unpack", "at the end of the day", "synergy", "game-changer",
            "thought leader", "circle back", "delve into", "leverage",
            "in today's fast-paced world",
        ],
    },
    "cb": {
        "audience_concerns": [
            "African and diaspora literature",
            "the publishing industry's gaps",
            "reading as cultural practice",
            "authors and their craft",
            "the politics of storytelling",
        ],
        "angle_frames": [
            "What is this book/story actually doing?",
            "What does this mean for African/diaspora readers specifically?",
            "What conversation does this open that wasn't open before?",
            "Who is missing from this story and why?",
        ],
        "voice_keywords": [
            "the story behind the story", "what this is really doing",
            "read this slowly", "the diaspora needs",
        ],
        "banned_terms": [
            "diverse voices", "own voices", "must-read", "representation matters",
            "powerful story", "delve into", "thought-provoking",
        ],
    },
    "tundexai": {
        "audience_concerns": [
            "enterprise AI adoption and failure modes",
            "model evaluation and benchmarks",
            "AI frameworks and mental models",
            "utilities and infrastructure AI",
            "what actually works vs. hype",
        ],
        "angle_frames": [
            "What do the benchmarks not tell you?",
            "What framework explains this better than the current framing?",
            "Where is the industry optimizing the wrong layer?",
            "What would a practitioner do differently?",
        ],
        "voice_keywords": [
            "here's what the benchmarks", "the pattern i keep seeing",
            "that's a tools problem", "framework first", "i tested this",
            "most people are optimizing", "let me be specific",
        ],
        "banned_terms": [
            "ai is going to change everything", "the future is now",
            "unlock the power of ai", "revolutionary", "groundbreaking",
            "harness", "democratize", "keep up with ai", "the ai revolution",
            "delve into", "hallucination",
        ],
    },
    "wellwithtunde": {
        "audience_concerns": [
            "sustainable performance for ambitious people",
            "burnout and recovery",
            "sleep, movement, and recovery fundamentals",
            "mental and emotional health for high achievers",
            "faith and rest as integrated practice",
            "ancestral and Nigerian wellness wisdom",
        ],
        "angle_frames": [
            "What is this person's body actually telling them?",
            "What does sustainable look like here vs. aspirational?",
            "What permission does this research give?",
            "How does this connect to whole-person health?",
        ],
        "voice_keywords": [
            "your body keeps the score", "this is sustainable",
            "you don't earn rest", "what are you actually hungry for",
            "start smaller", "the whole person shows up",
        ],
        "banned_terms": [
            "self-care", "hustle culture", "glow up", "manifest",
            "wellness journey", "toxic positivity", "biohacking",
            "optimizing your body",
        ],
    },
    "tundestalksmen": {
        "audience_concerns": [
            "fatherhood in reality vs. performance",
            "career and identity transitions for men",
            "Nigerian/African cultural expectations of manhood",
            "faith and masculine identity",
            "marriage, partnership, and family",
        ],
        "angle_frames": [
            "What does this mean for the man who's actually doing the work?",
            "What pressure does this research name that men don't talk about?",
            "What does this look like through a fatherhood lens?",
            "What does this say about the model men are passing down?",
        ],
        "voice_keywords": [
            "that's the work", "nobody's coming to save you",
            "strong men build", "what are you modeling",
            "the version of you your children", "men don't talk about this",
        ],
        "banned_terms": [
            "toxic masculinity", "man up", "alpha male", "sigma",
            "boys will be boys", "real men", "bro",
        ],
    },
}

PLATFORM_BRIEF_LENGTH = {
    "linkedin":      "medium (300-800 word post)",
    "twitter":       "short (280 chars or thread)",
    "instagram":     "short caption (50-150 chars opener)",
    "facebook":      "medium (200-500 words)",
    "newsletter":    "long (800-3000 words)",
    "youtube_short": "script bullet points only",
    "youtube_long":  "full outline with sections",
}

HOOK_TYPES = [
    "curiosity_gap", "bold_claim", "personal_story", "data_shock",
    "pattern_interrupt", "question", "contrarian", "number_list"
]

# ── Data classes ───────────────────────────────────────────────────────────────

@dataclass
class SourceInput:
    source_type: str   # "url" | "text" | "file"
    content: str       # raw text content (URLs fetched before passing here)
    source_ref: str = ""  # original URL or filename for attribution


@dataclass
class ContentAngle:
    angle: str
    frame: str
    hook_type_suggestion: str


@dataclass
class VoiceFlag:
    flag_type: str     # "warning" | "green"
    term: str
    context: str


@dataclass
class ContentBrief:
    niche: str
    platform: str
    source_summary: str
    key_facts: list[str] = field(default_factory=list)
    content_angles: list[ContentAngle] = field(default_factory=list)
    primary_angle: str = ""
    recommended_hook_type: str = ""
    hook_reasoning: str = ""
    suggested_tags: list[str] = field(default_factory=list)
    voice_flags: list[VoiceFlag] = field(default_factory=list)
    source_refs: list[str] = field(default_factory=list)
    report: str = ""


# ── Text extraction helpers ───────────────────────────────────────────────────

def fetch_url_text(url: str) -> str:
    """Fetch plain text from a URL. Returns stripped text or error message."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        # Basic HTML tag stripping
        text = re.sub(r'<script[^>]*>.*?</script>', ' ', raw, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', ' ', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'&[a-z]+;', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:12000]  # Cap at ~12k chars to prevent context explosion
    except Exception as e:
        return f"[URL fetch error: {e}]"


def read_file_text(filepath: Path) -> str:
    """Read a text/markdown file. PDF support is basic."""
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    if filepath.suffix.lower() == ".pdf":
        # Basic PDF text extraction without external deps
        try:
            raw = filepath.read_bytes()
            # Extract text between BT...ET markers (basic PDF text)
            matches = re.findall(rb'\(([^)]{3,200})\)', raw)
            text = " ".join(m.decode("latin-1", errors="replace") for m in matches)
            return re.sub(r'\s+', ' ', text).strip()[:12000]
        except Exception:
            return f"[PDF parse error — install pdfminer for better extraction: {filepath.name}]"
    return filepath.read_text(encoding="utf-8", errors="replace")[:12000]


# ── Core synthesis logic ──────────────────────────────────────────────────────

def _extract_key_facts(text: str, max_facts: int = 5) -> list[str]:
    """Extract sentences containing numbers, percentages, or strong claims."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    scored = []
    for sent in sentences:
        sent = sent.strip()
        if len(sent) < 20 or len(sent) > 300:
            continue
        score = 0
        if re.search(r'\b\d+[\.\d]*%', sent):
            score += 3  # percentage
        if re.search(r'\$[\d,]+|\d+ (million|billion|trillion)', sent, re.I):
            score += 2  # financial figure
        if re.search(r'\b(found|shows?|reveals?|reports?|according to|study|research|data)\b', sent, re.I):
            score += 2  # attributed claim
        if re.search(r'\b\d{4}\b', sent):
            score += 1  # year anchor
        if re.search(r'"[^"]{10,}"', sent):
            score += 2  # contains a quotable
        if score > 0:
            scored.append((score, sent))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [s for _, s in scored[:max_facts]] if scored else [
        text[:200].strip() + "..." if len(text) > 200 else text.strip()
    ]


def _generate_angles(niche: str, key_facts: list[str], combined_text: str) -> list[ContentAngle]:
    """Generate 3 niche-relevant content angles from extracted material."""
    config = NICHE_ANGLE_LENSES[niche]
    angles = []
    frames = config["angle_frames"]
    concerns = config["audience_concerns"]

    # Angle 1: Most data-driven fact → bold claim or data shock
    if key_facts:
        fact_snippet = key_facts[0][:120].rstrip(".")
        angle1_text = f"{fact_snippet} — and its implications for {concerns[0]}"
        angles.append(ContentAngle(
            angle=angle1_text,
            frame=frames[0],
            hook_type_suggestion="data_shock" if re.search(r'\d+', fact_snippet) else "bold_claim"
        ))

    # Angle 2: Contrarian/gap angle — what does this source NOT address?
    # Look for tension keywords in the text
    gap_topics = []
    for concern in concerns[1:3]:
        if concern.split()[0].lower() not in combined_text.lower():
            gap_topics.append(concern)
    gap = gap_topics[0] if gap_topics else concerns[1]
    angles.append(ContentAngle(
        angle=f"What this research misses about {gap} — and why that gap matters",
        frame=frames[1] if len(frames) > 1 else frames[0],
        hook_type_suggestion="contrarian"
    ))

    # Angle 3: Personal story entry point
    # Build using the key insight + niche audience framing
    personal_frame = frames[2] if len(frames) > 2 else frames[0]
    concern = concerns[2] if len(concerns) > 2 else concerns[0]
    angles.append(ContentAngle(
        angle=f"A personal experience lens on {concern}: what this data confirms",
        frame=personal_frame,
        hook_type_suggestion="personal_story"
    ))

    return angles


def _detect_voice_flags(niche: str, text: str) -> list[VoiceFlag]:
    """Scan source text for banned terms and green-flag phrases."""
    config = NICHE_ANGLE_LENSES[niche]
    flags = []
    text_lower = text.lower()

    for term in config["banned_terms"]:
        if term.lower() in text_lower:
            # Find context snippet
            idx = text_lower.find(term.lower())
            ctx_start = max(0, idx - 40)
            ctx_end = min(len(text), idx + len(term) + 40)
            context = "..." + text[ctx_start:ctx_end].strip() + "..."
            flags.append(VoiceFlag(
                flag_type="warning",
                term=term,
                context=context
            ))

    for keyword in config["voice_keywords"]:
        if keyword.lower() in text_lower:
            idx = text_lower.find(keyword.lower())
            ctx_start = max(0, idx - 20)
            ctx_end = min(len(text), idx + len(keyword) + 60)
            context = "..." + text[ctx_start:ctx_end].strip() + "..."
            flags.append(VoiceFlag(
                flag_type="green",
                term=keyword,
                context=context
            ))

    return flags


def _generate_tags(niche: str, combined_text: str, angles: list[ContentAngle]) -> list[str]:
    """Suggest content cluster tags based on niche concerns + text keywords."""
    config = NICHE_ANGLE_LENSES[niche]
    tags = []
    text_lower = combined_text.lower()

    # Match niche concerns to content
    for concern in config["audience_concerns"]:
        words = concern.split()[:2]  # Take first 2 words of concern
        if any(w.lower() in text_lower for w in words):
            tags.append(concern)
        if len(tags) >= 4:
            break

    # Add angle-based tags
    for angle in angles[:2]:
        angle_words = angle.angle.split()[:3]
        tag = " ".join(angle_words)
        if tag not in tags:
            tags.append(tag)

    return tags[:5]


def _build_summary(text: str, max_sentences: int = 4) -> str:
    """Build a 3-5 sentence summary of the source material."""
    sentences = re.split(r'(?<=[.!?])\s+', text.replace('\n', ' '))
    sentences = [s.strip() for s in sentences if len(s.strip()) > 40]

    # Prefer opening sentences (they usually contain the main claim)
    # plus any sentence with strong claim markers
    selected = sentences[:2]  # Always take first 2

    for sent in sentences[2:]:
        if re.search(r'\b(key|main|important|central|critical|finding|conclusion|result)\b', sent, re.I):
            selected.append(sent)
        if len(selected) >= max_sentences:
            break

    if len(selected) < 2 and sentences:
        selected = sentences[:max_sentences]

    summary = " ".join(selected[:max_sentences])
    if len(summary) > 800:
        summary = summary[:800].rsplit(' ', 1)[0] + "..."
    return summary


# ── Main synthesis function ───────────────────────────────────────────────────

def synthesize(
    niche: str,
    sources: list[dict],  # [{"type": "url"|"text"|"file", "content": "..."}]
    platform: str = "linkedin"
) -> ContentBrief:
    """
    Main synthesis function. Returns a ContentBrief.

    sources: list of dicts with keys:
        - type: "url" | "text" | "file"
        - content: URL string, raw text, or file path string
    """
    if niche not in VALID_NICHES:
        raise ValueError(f"Unknown niche: {niche}. Valid: {VALID_NICHES}")

    # ── 1. Collect and normalize all source text ─────────────────────────────
    processed_sources: list[SourceInput] = []
    source_refs = []

    for src in sources:
        src_type = src.get("type", "text")
        content = src.get("content", "").strip()

        if src_type == "url":
            raw_text = fetch_url_text(content)
            processed_sources.append(SourceInput("url", raw_text, content))
            source_refs.append(content)
        elif src_type == "file":
            fp = Path(content)
            raw_text = read_file_text(fp)
            processed_sources.append(SourceInput("file", raw_text, fp.name))
            source_refs.append(fp.name)
        else:  # text
            processed_sources.append(SourceInput("text", content, "inline"))
            source_refs.append("inline text")

    combined_text = "\n\n".join(src.content for src in processed_sources)

    if not combined_text.strip():
        raise ValueError("No content extracted from provided sources.")

    # ── 2. Extract components ─────────────────────────────────────────────────
    summary = _build_summary(combined_text)
    key_facts = _extract_key_facts(combined_text)
    angles = _generate_angles(niche, key_facts, combined_text)
    voice_flags = _detect_voice_flags(niche, combined_text)
    tags = _generate_tags(niche, combined_text, angles)

    # ── 3. Determine recommended hook type ───────────────────────────────────
    # Use the first angle's suggestion, but validate against niche preferences
    best_type = angles[0].hook_type_suggestion if angles else "curiosity_gap"
    niche_preferred = {
        "ttbp": ["curiosity_gap", "bold_claim", "personal_story"],
        "cb": ["curiosity_gap", "personal_story", "contrarian"],
        "tundexai": ["bold_claim", "data_shock", "contrarian"],
        "wellwithtunde": ["personal_story", "question", "pattern_interrupt"],
        "tundestalksmen": ["personal_story", "pattern_interrupt", "bold_claim"],
    }
    preferred = niche_preferred.get(niche, HOOK_TYPES)
    if best_type not in preferred:
        best_type = preferred[0]

    hook_reasoning = (
        f"Source contains {'strong data points' if key_facts and re.search(r'\\d', key_facts[0]) else 'a strong claim'} "
        f"that maps well to {best_type.replace('_', ' ')} for the {niche} audience."
    )

    primary_angle = angles[0].angle if angles else summary[:120]

    # ── 4. Build and return brief ─────────────────────────────────────────────
    brief = ContentBrief(
        niche=niche,
        platform=platform,
        source_summary=summary,
        key_facts=key_facts,
        content_angles=angles,
        primary_angle=primary_angle,
        recommended_hook_type=best_type,
        hook_reasoning=hook_reasoning,
        suggested_tags=tags,
        voice_flags=voice_flags,
        source_refs=source_refs,
    )
    brief.report = _build_report(brief)
    return brief


# ── Report builder ────────────────────────────────────────────────────────────

def _build_report(b: ContentBrief) -> str:
    sep = "═" * 45
    lines = [
        sep,
        "RESEARCH BRIEF",
        sep,
        f"Niche:     {b.niche}",
        f"Platform:  {b.platform}",
        f"Sources:   {', '.join(b.source_refs)}",
        "",
        "SOURCE SUMMARY",
        "─" * 45,
        b.source_summary,
        "",
    ]

    if b.key_facts:
        lines.append(f"KEY FACTS & QUOTABLES ({len(b.key_facts)}):")
        for fact in b.key_facts:
            lines.append(f"  • {fact[:200]}")
        lines.append("")

    if b.content_angles:
        lines.append(f"CONTENT ANGLES ({len(b.content_angles)}):")
        for i, angle in enumerate(b.content_angles, 1):
            lines.append(f"  {i}. {angle.angle}")
            lines.append(f"     Frame: {angle.frame}")
            lines.append(f"     Hook suggestion: {angle.hook_type_suggestion}")
        lines.append("")

    lines.append("RECOMMENDED HOOK TYPE")
    lines.append(f"  → {b.recommended_hook_type}")
    lines.append(f"  → Reasoning: {b.hook_reasoning}")
    lines.append("")

    if b.suggested_tags:
        lines.append(f"SUGGESTED TAGS / CLUSTERS")
        lines.append(f"  → {', '.join(b.suggested_tags)}")
        lines.append("")

    warnings = [f for f in b.voice_flags if f.flag_type == "warning"]
    greens = [f for f in b.voice_flags if f.flag_type == "green"]

    if warnings or greens:
        lines.append("VOICE FLAGS")
        for flag in warnings:
            lines.append(f"  ⚠️  \"{flag.term}\" — banned in {b.niche}")
            lines.append(f"      Context: {flag.context[:100]}")
        for flag in greens:
            lines.append(f"  ✅  \"{flag.term}\" — niche-aligned phrase detected")
        lines.append("")

    lines.append(sep)
    return "\n".join(lines)


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Synthesize research into content briefs for Tunde's Content Empire",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python research_synth.py --niche ttbp --url https://hbr.org/...
  python research_synth.py --niche tundexai --text "GPT-4 benchmark..." --platform linkedin
  python research_synth.py --niche cb --file notes/research.md
  python research_synth.py --niche ttbp --url https://... --url https://... --platform newsletter
  python research_synth.py --niche ttbp --url https://... --json
        """
    )
    parser.add_argument("--niche", required=True, choices=VALID_NICHES)
    parser.add_argument("--url", action="append", dest="urls", default=[],
                        help="URL to fetch and synthesize (can repeat)")
    parser.add_argument("--text", action="append", dest="texts", default=[],
                        help="Raw text or notes (can repeat)")
    parser.add_argument("--file", action="append", dest="files", default=[],
                        help="Path to .txt/.md/.pdf file (can repeat)")
    parser.add_argument("--platform", default="linkedin",
                        choices=["linkedin", "twitter", "instagram", "facebook",
                                 "newsletter", "youtube_short", "youtube_long"])
    parser.add_argument("--json", action="store_true", help="Output JSON")

    args = parser.parse_args()

    if not args.urls and not args.texts and not args.files:
        parser.error("Provide at least one of: --url, --text, --file")

    # Build sources list
    sources = []
    for url in args.urls:
        sources.append({"type": "url", "content": url})
    for text in args.texts:
        sources.append({"type": "text", "content": text})
    for filepath in args.files:
        sources.append({"type": "file", "content": filepath})

    brief = synthesize(niche=args.niche, sources=sources, platform=args.platform)

    if args.json:
        print(json.dumps(asdict(brief), indent=2, default=str))
    else:
        print(brief.report)

    sys.exit(0)


if __name__ == "__main__":
    main()

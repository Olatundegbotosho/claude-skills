#!/usr/bin/env python3
"""
voice_validator.py — Voice DNA content validator for the Content Empire
Validates any text against niche-specific Voice DNA rules.

Usage:
  python voice_validator.py --niche ttbp --file post.md
  python voice_validator.py --niche tundexai --text "Your content here..."
  python voice_validator.py --niche cb --dir output/cb_2026-W08/
  python voice_validator.py --niche ttbp --file post.md --json
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

# ── Constants ────────────────────────────────────────────────────────────────

VOICE_DNA_BASE = Path.home() / "prompts" / "voice"
SKILL_BASE = Path(__file__).parent.parent

VALID_NICHES = ["ttbp", "cb", "tundexai", "wellwithtunde", "tundestalksmen"]

PLATFORM_LENGTH_SPECS = {
    "linkedin":      (100, 3000),
    "twitter":       (10,  280),
    "instagram":     (50,  2200),
    "facebook":      (50,  500),
    "newsletter":    (300, 7000),
    "youtube_short": (30,  600),
    "youtube_long":  (200, 5000),
}

# ── Per-niche Voice DNA rules ─────────────────────────────────────────────────

VOICE_RULES: dict[str, dict] = {
    "ttbp": {
        "banned_phrases": [
            "unpack", "at the end of the day", "synergy", "game-changer",
            "thought leader", "circle back", "delve into",
            "it's important to note that", "in today's fast-paced world",
            "leverage" , "journey",
        ],
        "banned_openers": [
            "hi everyone", "happy monday", "happy tuesday", "happy wednesday",
            "happy thursday", "happy friday", "good morning", "greetings",
            "in today's", "as we navigate", "in this post i will",
        ],
        "green_flags": [
            "here's the thing", "the truth is", "what nobody tells you",
            "think about that", "i've seen this", "that's not a small thing",
            "this is the part where",
        ],
        "tone_markers": {
            "too_casual": ["lol", "omg", "tbh", "ngl", "imo", "fwiw"],
            "too_corporate": ["synergize", "best-in-class", "robust solution",
                              "value-add", "stakeholder", "actionable insights"],
        },
    },
    "cb": {
        "banned_phrases": [
            "diverse voices", "own voices", "must-read",
            "representation matters", "powerful story", "delve into",
            "thought-provoking",
        ],
        "banned_openers": [
            "hi everyone", "happy monday", "in this post",
            "today we're going to", "let me share",
        ],
        "green_flags": [
            "the story behind the story", "what this book is really doing",
            "there's a reason this one", "the diaspora needs", "read this slowly",
            "things fall apart", "chinua achebe", "chimamanda",
        ],
        "tone_markers": {
            "too_casual": ["lol", "omg", "vibe", "fire", "lit"],
            "too_corporate": ["content strategy", "target audience", "engagement metrics"],
        },
    },
    "tundexai": {
        "banned_phrases": [
            "ai is going to change everything", "the future is now",
            "unlock the power of ai", "revolutionary", "groundbreaking",
            "harness", "democratize", "keep up with ai",
            "the ai revolution", "delve into", "hallucination",
        ],
        "banned_openers": [
            "ai is changing", "in today's rapidly evolving", "as ai continues",
            "the world of ai", "with the rise of ai",
        ],
        "green_flags": [
            "here's what the benchmarks", "the pattern i keep seeing",
            "that's a tools problem", "framework first", "i tested this",
            "most people are optimizing", "let me be specific",
        ],
        "tone_markers": {
            "too_casual": ["wow", "amazing", "mind-blowing", "insane", "crazy good"],
            "too_hype": ["revolutionary", "unprecedented", "game-changing",
                         "never before seen", "will change everything"],
        },
    },
    "wellwithtunde": {
        "banned_phrases": [
            "self-care", "hustle culture", "glow up", "manifest",
            "wellness journey", "toxic positivity", "biohacking",
            "optimizing your body",
        ],
        "banned_openers": [
            "hi everyone", "good morning beautiful", "rise and shine",
            "today's tip", "in today's post",
        ],
        "green_flags": [
            "your body keeps the score", "this is sustainable", "you don't earn rest",
            "what are you actually hungry for", "start smaller",
            "the whole person shows up",
        ],
        "tone_markers": {
            "too_clinical": ["protocol", "optimization", "biometric", "quantified self"],
            "too_spiritual_only": ["manifest", "the universe will", "just believe"],
        },
    },
    "tundestalksmen": {
        "banned_phrases": [
            "toxic masculinity", "man up", "alpha male", "sigma",
            "boys will be boys", "real men", "bro",
        ],
        "banned_openers": [
            "hey guys", "what's up men", "gentlemen,",
            "as men we need to", "this is for the fellas",
        ],
        "green_flags": [
            "that's the work", "nobody's coming to save you",
            "strong men build", "what are you modeling",
            "the version of you your children", "men don't talk about this",
        ],
        "tone_markers": {
            "too_redpill": ["alpha", "sigma", "chad", "hypergamy", "the wall"],
            "too_soft": ["just be yourself", "it's okay to cry", "feelings are valid"],
        },
    },
}

# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class ValidationIssue:
    severity: str       # "error" | "warning" | "info"
    category: str       # "banned" | "opener" | "tone" | "length" | "green_flag"
    message: str
    line_hint: str = ""

@dataclass
class ValidationResult:
    niche: str
    platform: str
    score: int
    verdict: str
    issues: list[ValidationIssue] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    char_count: int = 0
    word_count: int = 0
    report: str = ""

# ── Core validation logic ─────────────────────────────────────────────────────

def validate_content(niche: str, text: str, platform: str = "linkedin") -> ValidationResult:
    """Main validation function. Returns a ValidationResult."""
    if niche not in VALID_NICHES:
        raise ValueError(f"Unknown niche: {niche}. Valid: {VALID_NICHES}")

    rules = VOICE_RULES[niche]
    issues: list[ValidationIssue] = []
    strengths: list[str] = []
    text_lower = text.lower()
    lines = text.strip().split("\n")
    first_line = lines[0].strip().lower() if lines else ""

    # ── 1. Banned phrase check (30% weight) ──────────────────────────────────
    banned_score = 30
    banned_hit_count = 0
    for phrase in rules["banned_phrases"]:
        if phrase.lower() in text_lower:
            banned_hit_count += 1
            # Find approximate line
            for i, line in enumerate(lines, 1):
                if phrase.lower() in line.lower():
                    issues.append(ValidationIssue(
                        severity="error",
                        category="banned",
                        message=f'"{phrase}" — banned phrase, see Voice DNA for replacements',
                        line_hint=f"line {i}: ...{line.strip()[:60]}..."
                    ))
                    break

    if banned_hit_count == 0:
        strengths.append("No banned phrases detected")
        banned_actual = 30
    else:
        banned_actual = max(0, 30 - (banned_hit_count * 10))

    # ── 2. Green flag presence (25% weight) ──────────────────────────────────
    green_found = []
    for flag in rules["green_flags"]:
        if flag.lower() in text_lower:
            green_found.append(f'"{flag}"')

    if green_found:
        strengths.append(f"Green flag phrase present: {', '.join(green_found[:2])}")
        green_actual = 25
    else:
        issues.append(ValidationIssue(
            severity="warning",
            category="green_flag",
            message="No signature phrases found — consider adding one for voice authenticity",
            line_hint="Check Voice DNA green flags section"
        ))
        green_actual = 10  # Partial credit — absence is warning not failure

    # ── 3. Opening hook quality (20% weight) ─────────────────────────────────
    opener_ok = True
    for bad_opener in rules.get("banned_openers", []):
        if first_line.startswith(bad_opener.lower()):
            opener_ok = False
            issues.append(ValidationIssue(
                severity="error",
                category="opener",
                message=f'Opening starts with "{bad_opener}" — rewrite first line',
                line_hint=f"First line: {lines[0][:80]}"
            ))
            break

    if opener_ok and len(first_line) > 10:
        strengths.append("Opening does not use a banned opener")
        opener_actual = 20
    elif opener_ok:
        issues.append(ValidationIssue(
            severity="warning",
            category="opener",
            message="Opening line is very short — ensure it's a strong hook",
            line_hint=f"First line: {lines[0][:80]}"
        ))
        opener_actual = 15
    else:
        opener_actual = 5

    # ── 4. Tone alignment (15% weight) ───────────────────────────────────────
    tone_issues = 0
    tone_markers = rules.get("tone_markers", {})
    for tone_type, markers in tone_markers.items():
        for marker in markers:
            if marker.lower() in text_lower:
                tone_issues += 1
                issues.append(ValidationIssue(
                    severity="warning",
                    category="tone",
                    message=f'Tone marker "{marker}" ({tone_type}) — may clash with niche voice',
                    line_hint=""
                ))

    if tone_issues == 0:
        strengths.append("Tone markers look clean")
        tone_actual = 15
    else:
        tone_actual = max(5, 15 - (tone_issues * 5))

    # ── 5. Platform fit (10% weight) ─────────────────────────────────────────
    char_count = len(text)
    word_count = len(text.split())

    if platform in PLATFORM_LENGTH_SPECS:
        min_len, max_len = PLATFORM_LENGTH_SPECS[platform]
        if char_count < min_len:
            issues.append(ValidationIssue(
                severity="warning",
                category="length",
                message=f"Content too short for {platform} ({char_count} chars, min {min_len})",
                line_hint=""
            ))
            platform_actual = 5
        elif char_count > max_len:
            issues.append(ValidationIssue(
                severity="error",
                category="length",
                message=f"Content too long for {platform} ({char_count} chars, max {max_len})",
                line_hint=""
            ))
            platform_actual = 5
        else:
            strengths.append(f"Length within {platform} spec ({char_count} chars)")
            platform_actual = 10
    else:
        platform_actual = 8  # Unknown platform — partial credit

    # ── Compute final score ───────────────────────────────────────────────────
    score = banned_actual + green_actual + opener_actual + tone_actual + platform_actual

    if score >= 85:
        verdict = "PASS"
    elif score >= 70:
        verdict = "REVISE"
    elif score >= 50:
        verdict = "HEAVY REVISE"
    else:
        verdict = "REJECT"

    result = ValidationResult(
        niche=niche, platform=platform, score=score, verdict=verdict,
        issues=issues, strengths=strengths, char_count=char_count, word_count=word_count
    )
    result.report = _build_report(result)
    return result


def _build_report(r: ValidationResult) -> str:
    sep = "═" * 40
    lines = [
        sep,
        "VOICE ENFORCER REPORT",
        sep,
        f"Niche:      {r.niche}",
        f"Platform:   {r.platform}",
        f"Score:      {r.score}/100",
        f"Verdict:    {r.verdict}",
        f"Length:     {r.char_count} chars / {r.word_count} words",
        "",
    ]

    if r.issues:
        lines.append(f"Issues Found ({len(r.issues)}):")
        for issue in r.issues:
            icon = "❌" if issue.severity == "error" else "⚠️ "
            lines.append(f"  {icon} [{issue.category.upper()}] {issue.message}")
            if issue.line_hint:
                lines.append(f"     → {issue.line_hint}")
        lines.append("")

    if r.strengths:
        lines.append(f"Strengths ({len(r.strengths)}):")
        for s in r.strengths:
            lines.append(f"  ✅ {s}")
        lines.append("")

    if r.verdict == "PASS":
        lines.append("✅ Clear for scheduling/publishing.")
    elif r.verdict == "REVISE":
        lines.append("⚠️  Fix flagged issues, then re-validate before scheduling.")
    elif r.verdict == "HEAVY REVISE":
        lines.append("🔴 Significant rewrite needed. Address all errors first.")
    else:
        lines.append("🔴 REJECT — Regenerate from scratch.")

    lines.append(sep)
    return "\n".join(lines)


def validate_file(niche: str, filepath: Path, platform: str = "linkedin") -> ValidationResult:
    """Validate a file."""
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    text = filepath.read_text(encoding="utf-8")
    return validate_content(niche, text, platform)


def validate_directory(niche: str, dirpath: Path, platform: str = "linkedin") -> list[ValidationResult]:
    """Validate all .md and .txt files in a directory."""
    results = []
    for ext in ["*.md", "*.txt"]:
        for f in dirpath.glob(ext):
            try:
                r = validate_file(niche, f, platform)
                results.append(r)
            except Exception as e:
                print(f"  ⚠️  Skipped {f.name}: {e}")
    return results


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Validate content against Tunde's Voice DNA",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python voice_validator.py --niche ttbp --file post.md
  python voice_validator.py --niche tundexai --text "AI is going to change everything..."
  python voice_validator.py --niche cb --dir ./output/cb_books/
  python voice_validator.py --niche ttbp --file post.md --platform twitter
  python voice_validator.py --niche ttbp --file post.md --json
  python voice_validator.py --niche ttbp --file post.md --score-only
        """
    )
    parser.add_argument("--niche", required=True, choices=VALID_NICHES)
    parser.add_argument("--file", type=Path, help="Path to content file")
    parser.add_argument("--text", type=str, help="Inline content string")
    parser.add_argument("--dir", type=Path, help="Directory of files to validate")
    parser.add_argument("--platform", default="linkedin",
                        choices=list(PLATFORM_LENGTH_SPECS.keys()),
                        help="Target platform (default: linkedin)")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--score-only", action="store_true", help="Print score only")

    args = parser.parse_args()

    if args.dir:
        results = validate_directory(args.niche, args.dir, args.platform)
        if args.json:
            print(json.dumps([asdict(r) for r in results], indent=2, default=str))
        else:
            for r in results:
                print(r.report)
            # Summary
            print(f"\n📊 Batch Summary: {len(results)} files")
            for v in ["PASS", "REVISE", "HEAVY REVISE", "REJECT"]:
                count = sum(1 for r in results if r.verdict == v)
                if count:
                    print(f"   {v}: {count}")
        sys.exit(0 if all(r.verdict == "PASS" for r in results) else 1)

    elif args.file:
        result = validate_file(args.niche, args.file, args.platform)
    elif args.text:
        result = validate_content(args.niche, args.text, args.platform)
    else:
        parser.error("Provide --file, --text, or --dir")
        return

    if args.json:
        print(json.dumps(asdict(result), indent=2, default=str))
    elif args.score_only:
        print(f"{result.score}")
    else:
        print(result.report)

    # Exit codes: 0=PASS, 1=REVISE, 2=HEAVY REVISE/REJECT
    if result.verdict == "PASS":
        sys.exit(0)
    elif result.verdict == "REVISE":
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == "__main__":
    main()

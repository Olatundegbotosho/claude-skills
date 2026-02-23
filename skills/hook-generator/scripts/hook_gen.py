#!/usr/bin/env python3
"""
hook_gen.py — Hook Generator for the Content Empire
Generates 8 typed hook variants per topic, scored and ranked.

Usage:
  python hook_gen.py --niche ttbp --topic "why most people plateau at middle management"
  python hook_gen.py --niche tundexai --topic "RAG" --context "most are just expensive search"
  python hook_gen.py --niche ttbp --topic "burnout" --platform linkedin --top 3
  python hook_gen.py --niche ttbp --score-hook "In today's world..."
  python hook_gen.py --niche ttbp --topic "..." --json
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

# ── Constants ─────────────────────────────────────────────────────────────────

VALID_NICHES = ["ttbp", "cb", "tundexai", "wellwithtunde", "tundestalksmen"]

HOOK_TYPES = [
    "curiosity_gap",
    "bold_claim",
    "personal_story",
    "data_shock",
    "pattern_interrupt",
    "question",
    "contrarian",
    "number_list",
]

# Per-platform max hook length (chars) and style notes
PLATFORM_HOOK_SPECS = {
    "linkedin":      {"max_chars": 220, "style": "professional tension, earn the scroll"},
    "twitter":       {"max_chars": 140, "style": "sharp, punchy, single idea"},
    "instagram":     {"max_chars": 125, "style": "visual opener, personal or emotional"},
    "facebook":      {"max_chars": 200, "style": "community resonance, relatable moment"},
    "newsletter":    {"max_chars": 300, "style": "letter-opening energy, promise of depth"},
    "youtube_short": {"max_chars": 100, "style": "instant visual hook, 3-second hook"},
    "youtube_long":  {"max_chars": 200, "style": "problem-first, stakes clear immediately"},
}

# ── Per-niche hook configuration ──────────────────────────────────────────────

NICHE_HOOK_CONFIG: dict[str, dict] = {
    "ttbp": {
        "best_types": ["curiosity_gap", "bold_claim", "personal_story"],
        "tone": "confident, warm, intellectually honest",
        "persona": "Tunde Gbotosho — MBA, tech/AI exec, entrepreneur, author",
        "banned_openers": [
            "in today's fast-paced", "in today's world", "as we navigate",
            "hi everyone", "happy monday", "good morning", "greetings",
            "in this post i will", "let me share with you",
        ],
        "green_flag_starters": [
            "here's the thing", "the truth is", "what nobody tells you",
            "i've watched", "i've sat in rooms where", "let me be honest about",
            "think about that", "this is the part where",
        ],
        "avoid_patterns": [
            r"game.changer", r"leverage", r"synergy", r"delve into",
            r"thought leader", r"in today's fast",
        ],
    },
    "cb": {
        "best_types": ["curiosity_gap", "personal_story", "contrarian"],
        "tone": "literary, warm, diaspora-aware, intellectually serious",
        "persona": "Connecting Bridges Publishing — curator of African/diaspora literature",
        "banned_openers": [
            "hi everyone", "happy monday", "in this post",
            "today we're going to", "let me share",
        ],
        "green_flag_starters": [
            "the story behind the story", "what this book is really doing",
            "there's a reason this one", "read this slowly",
            "most people finish this book without noticing",
        ],
        "avoid_patterns": [
            r"must.read", r"powerful story", r"diverse voices",
            r"own voices", r"representation matters",
        ],
    },
    "tundexai": {
        "best_types": ["bold_claim", "data_shock", "contrarian"],
        "tone": "practitioner-sharp, skeptically optimistic, technically precise",
        "persona": "Tunde Gbotosho — AI consultant, enterprise operator, UVA Stats + HBS CORe",
        "banned_openers": [
            "ai is changing", "in today's rapidly evolving", "as ai continues",
            "the world of ai", "with the rise of ai",
        ],
        "green_flag_starters": [
            "here's what the benchmarks aren't telling you",
            "the pattern i keep seeing",
            "i tested this", "most people are optimizing the wrong",
            "let me be specific", "framework first",
        ],
        "avoid_patterns": [
            r"revolutionary", r"groundbreaking", r"unlock the power",
            r"ai is going to change everything", r"the ai revolution",
            r"harness", r"democratize",
        ],
    },
    "wellwithtunde": {
        "best_types": ["personal_story", "question", "pattern_interrupt"],
        "tone": "grounding, honest, practically warm, faith-integrated",
        "persona": "WellWithTunde — whole-person wellness for ambitious professionals",
        "banned_openers": [
            "hi everyone", "good morning beautiful", "rise and shine",
            "today's tip", "in today's post",
        ],
        "green_flag_starters": [
            "you've been running on", "that thing you keep pushing through",
            "your body kept score even when you didn't",
            "here's what sustainable actually looks like",
            "what are you actually hungry for",
        ],
        "avoid_patterns": [
            r"self.care", r"glow up", r"manifest", r"wellness journey",
            r"biohacking", r"optimizing your body", r"toxic positivity",
        ],
    },
    "tundestalksmen": {
        "best_types": ["personal_story", "pattern_interrupt", "bold_claim"],
        "tone": "grounded, masculine without posturing, father-first, brotherhood energy",
        "persona": "TundesTalksMen — Nigerian/African men navigating identity, fatherhood, faith",
        "banned_openers": [
            "hey guys", "what's up men", "gentlemen,",
            "as men we need to", "this is for the fellas",
        ],
        "green_flag_starters": [
            "my son asked me", "i didn't have an answer for that",
            "the version of you your children are watching",
            "nobody's coming to save you", "that's the work",
            "in nigerian culture, men don't",
        ],
        "avoid_patterns": [
            r"alpha male", r"sigma", r"toxic masculinity",
            r"man up", r"real men", r"\bbro\b",
        ],
    },
}

# ── Hook templates (structural patterns per type) ─────────────────────────────
# These are structural scaffolds — the generator fills them with topic-specific content

HOOK_TEMPLATES: dict[str, list[str]] = {
    "curiosity_gap": [
        "Nobody talks about {specific_angle} — not the failure moment, the {reframe} moment.",
        "There's a part of {topic} that almost no one prepares you for.",
        "What {topic} actually requires is something the {authority} never tells you.",
    ],
    "bold_claim": [
        "Most {audience} are optimizing {topic} at the wrong layer.",
        "{topic} isn't a {common_belief} problem. It's a {reframe} problem.",
        "The conventional advice on {topic} is wrong — not useless, wrong.",
    ],
    "personal_story": [
        "I {past_action} at {specific_time} and realized {insight}.",
        "There was a moment — {scene_detail} — where {topic} became completely clear to me.",
        "My {relationship} asked me why {observation}. I had no good answer.",
    ],
    "data_shock": [
        "{stat}% of {audience} {finding}. Nobody told them before they started.",
        "The number that stopped me on {topic}: {stat}.",
        "Here's what the data on {topic} actually shows — and why it should bother you.",
    ],
    "pattern_interrupt": [
        "You didn't {problem}. The {system} did exactly what it was designed to do.",
        "This isn't a {common_frame} story. It's a {reframe} story.",
        "The {topic} conversation is being had in the wrong room.",
    ],
    "question": [
        "What if {topic} isn't the problem you think it is?",
        "When did {common_behavior} start feeling like the only option?",
        "What are you actually {verb} when you {topic_action}?",
    ],
    "contrarian": [
        "The {industry} tells you to {common_advice}. That's not why {problem_outcome}.",
        "Everyone's talking about {topic_trend}. Nobody's asking if it works.",
        "{popular_belief} sounds right. It isn't — and here's the data.",
    ],
    "number_list": [
        "{N} things about {topic} that {common_source} won't tell you.",
        "{N} reasons {audience} hit {problem} — and {N_minus_1} of them have nothing to do with {scapegoat}.",
        "I've seen {N} patterns in {topic}. One of them explains almost everything.",
    ],
}

# ── Scoring logic ─────────────────────────────────────────────────────────────

def score_hook(hook_text: str, hook_type: str, niche: str, platform: str) -> float:
    """Score a hook 0.0–10.0 based on specificity, voice, tension, platform fit."""
    config = NICHE_HOOK_CONFIG.get(niche, {})
    text_lower = hook_text.lower()
    score = 0.0

    # ── Specificity (3.0 pts) ─────────────────────────────────────────────────
    spec_score = 1.5  # baseline
    # Numbers boost specificity
    if re.search(r'\b\d+[\.\d]*%|\b\d+\s*(years?|months?|quarters?|weeks?)\b|\b\d{2,}\b', hook_text):
        spec_score += 0.8
    # Named entities / proper nouns boost specificity
    if re.search(r'\b[A-Z][a-z]+ [A-Z][a-z]+|\bGPT-\d|\bLinkedIn\b|\bHBS\b|\bNigerian\b', hook_text):
        spec_score += 0.5
    # Vague quantifiers reduce specificity
    if re.search(r'\b(many|some|often|sometimes|various|a lot of|things like)\b', text_lower):
        spec_score -= 0.5
    score += min(3.0, max(0.0, spec_score))

    # ── Voice alignment (2.5 pts) ─────────────────────────────────────────────
    voice_score = 1.8  # baseline

    # Banned opener check
    for opener in config.get("banned_openers", []):
        if text_lower.startswith(opener.lower()):
            voice_score -= 1.5
            break

    # Banned pattern check
    for pattern in config.get("avoid_patterns", []):
        if re.search(pattern, text_lower, re.IGNORECASE):
            voice_score -= 0.7
            break

    # Green flag starters boost
    for starter in config.get("green_flag_starters", []):
        if text_lower.startswith(starter.lower()):
            voice_score += 0.8
            break

    score += min(2.5, max(0.0, voice_score))

    # ── Tension (2.5 pts) ─────────────────────────────────────────────────────
    tension_score = 1.2  # baseline

    # Contradiction / contrast creates tension
    if re.search(r'\b(but|not|never|wrong|fail|missed|nobody|no one|instead|actually)\b', text_lower):
        tension_score += 0.6
    # Unexplained reference creates curiosity
    if re.search(r'\b(this|that|here\'s|it)\b.*\b(why|how|what)\b', text_lower):
        tension_score += 0.4
    # Direct address creates immediacy
    if re.search(r'\b(you|your|you\'ve|you\'re)\b', text_lower):
        tension_score += 0.3

    score += min(2.5, max(0.0, tension_score))

    # ── Platform fit (2.0 pts) ────────────────────────────────────────────────
    platform_score = 1.0  # baseline
    if platform in PLATFORM_HOOK_SPECS:
        max_chars = PLATFORM_HOOK_SPECS[platform]["max_chars"]
        char_len = len(hook_text)
        if char_len <= max_chars:
            platform_score += 0.8
        elif char_len <= max_chars * 1.2:
            platform_score += 0.3
        else:
            platform_score -= 0.5

    # Type-platform affinity bonus
    type_platform_matrix = {
        "curiosity_gap":   ["linkedin", "newsletter"],
        "bold_claim":      ["linkedin", "twitter"],
        "personal_story":  ["linkedin", "instagram", "facebook", "newsletter"],
        "data_shock":      ["linkedin", "newsletter", "twitter"],
        "pattern_interrupt": ["twitter", "instagram"],
        "question":        ["instagram", "facebook", "twitter"],
        "contrarian":      ["twitter", "linkedin"],
        "number_list":     ["linkedin", "newsletter"],
    }
    if platform in type_platform_matrix.get(hook_type, []):
        platform_score += 0.2

    score += min(2.0, max(0.0, platform_score))

    return round(min(10.0, max(0.0, score)), 1)


def get_score_label(score: float) -> str:
    if score >= 7.0:
        return "RECOMMENDED"
    elif score >= 5.0:
        return "USE WITH REVISION"
    else:
        return "DISCARD"


# ── Hook generation ───────────────────────────────────────────────────────────

def _build_hook_text(hook_type: str, niche: str, topic: str, context: str = "") -> str:
    """
    Build a hook from the template scaffold + topic + niche config.
    Returns a complete, usable hook string.
    """
    config = NICHE_HOOK_CONFIG[niche]
    topic_clean = topic.strip().rstrip(".")

    # Pick the best green-flag starter for niche (first item in list)
    green_starter = config["green_flag_starters"][0] if config["green_flag_starters"] else ""

    hooks = {
        "curiosity_gap": (
            f"Nobody prepares you for the moment when {topic_clean} stops being a strategy "
            f"and becomes a mirror."
            if not context else
            f"Most people get {topic_clean} wrong — not because of effort, but because "
            f"{context}."
        ),
        "bold_claim": (
            f"The common advice on {topic_clean} is optimizing the wrong layer."
            if not context else
            f"{topic_clean.capitalize()} isn't a tools problem. {context.capitalize()}."
        ),
        "personal_story": (
            f"I sat with {topic_clean} for three years before I understood what it was "
            f"actually asking of me."
            if not context else
            f"I built the whole thing — {context}. That's when {topic_clean} finally made sense."
        ),
        "data_shock": (
            f"The stat on {topic_clean} that nobody leads with: "
            f"most people are solving the wrong version of the problem."
            if not context else
            f"Here's the number that changed how I think about {topic_clean}: "
            f"{context}."
        ),
        "pattern_interrupt": (
            f"The {topic_clean} conversation is happening in the wrong room."
            if not context else
            f"You didn't fail at {topic_clean}. {context.capitalize()}."
        ),
        "question": (
            f"What are you actually building when you invest everything into {topic_clean}?"
            if not context else
            f"If {context}, what does that say about how we've framed {topic_clean}?"
        ),
        "contrarian": (
            f"Everyone's focused on {topic_clean}. Nobody's asking whether the framing is right."
            if not context else
            f"The conventional wisdom on {topic_clean} sounds correct. "
            f"{context.capitalize()} — and that changes everything."
        ),
        "number_list": (
            f"3 things about {topic_clean} that most frameworks completely miss."
            if not context else
            f"3 patterns I keep seeing in {topic_clean} — and {context}."
        ),
    }

    return hooks.get(hook_type, f"On {topic_clean}: {context or 'something worth examining.'}")


# ── Data classes ───────────────────────────────────────────────────────────────

@dataclass
class HookResult:
    hook_type: str
    text: str
    score: float
    label: str
    notes: str
    rank: int = 0


@dataclass
class HookReport:
    niche: str
    platform: str
    topic: str
    context: str
    hooks: list[HookResult] = field(default_factory=list)
    report: str = ""

    @property
    def top_hook(self) -> HookResult | None:
        return self.hooks[0] if self.hooks else None


# ── Core generation function ──────────────────────────────────────────────────

def generate_hooks(
    niche: str,
    topic: str,
    platform: str = "linkedin",
    context: str = "",
    top_n: int = 0
) -> HookReport:
    """Main generation function. Returns a HookReport with all 8 hooks scored and ranked."""
    if niche not in VALID_NICHES:
        raise ValueError(f"Unknown niche: {niche}. Valid: {VALID_NICHES}")

    hooks = []
    for hook_type in HOOK_TYPES:
        text = _build_hook_text(hook_type, niche, topic, context)
        score = score_hook(text, hook_type, niche, platform)
        label = get_score_label(score)

        # Build notes
        notes_parts = []
        config = NICHE_HOOK_CONFIG[niche]
        text_lower = text.lower()

        for ban in config.get("banned_openers", []):
            if text_lower.startswith(ban.lower()):
                notes_parts.append(f"⚠️ Starts with banned opener: \"{ban}\"")
        for pat in config.get("avoid_patterns", []):
            if re.search(pat, text_lower, re.IGNORECASE):
                notes_parts.append(f"⚠️ Contains avoid-pattern: {pat}")
        if not notes_parts:
            if hook_type in NICHE_HOOK_CONFIG[niche]["best_types"]:
                notes_parts.append(f"✅ Preferred type for {niche}")
            if len(text) <= PLATFORM_HOOK_SPECS.get(platform, {}).get("max_chars", 999):
                notes_parts.append(f"✅ Length fits {platform}")
            else:
                notes_parts.append(f"⚠️ Slightly long for {platform}")

        hooks.append(HookResult(
            hook_type=hook_type,
            text=text,
            score=score,
            label=label,
            notes=" | ".join(notes_parts) if notes_parts else "No issues",
        ))

    # Sort by score descending, assign ranks
    hooks.sort(key=lambda h: h.score, reverse=True)
    for i, h in enumerate(hooks, 1):
        h.rank = i

    # Limit if top_n requested
    displayed = hooks[:top_n] if top_n > 0 else hooks

    report_obj = HookReport(
        niche=niche,
        platform=platform,
        topic=topic,
        context=context,
        hooks=hooks,
    )
    report_obj.report = _build_report(report_obj, displayed)
    return report_obj


def score_existing_hook(hook_text: str, niche: str, platform: str = "linkedin") -> HookResult:
    """Score an existing hook string without generating new ones."""
    # Detect hook type by pattern
    text_lower = hook_text.lower()
    detected_type = "curiosity_gap"  # default
    if re.search(r'\b\d+[\s]*(%|reasons?|ways?|things?|patterns?)\b', text_lower):
        detected_type = "number_list"
    elif text_lower.startswith(("i ", "my ", "last ", "three years")):
        detected_type = "personal_story"
    elif re.search(r'\b\d+[\.\d]*%\b', text_lower):
        detected_type = "data_shock"
    elif "?" in hook_text:
        detected_type = "question"
    elif re.search(r'\b(everyone|conventional|common|popular)\b', text_lower):
        detected_type = "contrarian"

    score = score_hook(hook_text, detected_type, niche, platform)
    return HookResult(
        hook_type=f"detected: {detected_type}",
        text=hook_text,
        score=score,
        label=get_score_label(score),
        notes=f"Auto-detected as {detected_type}",
        rank=1
    )


# ── Report builder ────────────────────────────────────────────────────────────

def _build_report(r: HookReport, displayed: list[HookResult]) -> str:
    sep = "═" * 45
    lines = [
        sep,
        "HOOK GENERATOR REPORT",
        sep,
        f"Niche:     {r.niche}",
        f"Platform:  {r.platform}",
        f"Topic:     {r.topic}",
    ]
    if r.context:
        lines.append(f"Context:   {r.context}")
    lines += ["", f"{len(displayed)} HOOK(S) — Sorted by Score", "─" * 45]

    for h in displayed:
        star = "★ " if h.rank == 1 else "  "
        type_display = h.hook_type.upper().replace("_", " ")
        lines.append(f"\n[{h.rank}] {type_display:<20} Score: {h.score:<4}  {star}{h.label}")
        lines.append(f'    "{h.text}"')
        lines.append(f"    → {h.notes}")

    lines.append("")
    lines.append(sep)
    if r.top_hook:
        lines.append(f"TOP PICK: [{r.top_hook.hook_type.upper().replace('_', ' ')}]")
        lines.append(f'"{r.top_hook.text}"')
    lines.append(sep)
    return "\n".join(lines)


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate and score opening hooks for Tunde's Content Empire",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python hook_gen.py --niche ttbp --topic "why people plateau at middle management"
  python hook_gen.py --niche tundexai --topic "RAG" --context "most are expensive search"
  python hook_gen.py --niche cb --topic "reading diaspora fiction" --top 3
  python hook_gen.py --niche ttbp --score-hook "In today's fast-paced world..."
  python hook_gen.py --niche ttbp --topic "burnout" --platform newsletter --json
        """
    )
    parser.add_argument("--niche", required=True, choices=VALID_NICHES)
    parser.add_argument("--topic", type=str, help="Core topic or angle for hook generation")
    parser.add_argument("--context", type=str, default="",
                        help="Optional angle or insight to weave into hooks")
    parser.add_argument("--platform", default="linkedin",
                        choices=list(PLATFORM_HOOK_SPECS.keys()))
    parser.add_argument("--top", type=int, default=0,
                        help="Show only top N hooks (default: all 8)")
    parser.add_argument("--score-hook", type=str, dest="score_hook",
                        help="Score an existing hook instead of generating new ones")
    parser.add_argument("--json", action="store_true", help="Output JSON")

    args = parser.parse_args()

    if args.score_hook:
        result = score_existing_hook(args.score_hook, args.niche, args.platform)
        if args.json:
            print(json.dumps(asdict(result), indent=2))
        else:
            print(f"\nHook Score: {result.score}/10  →  {result.label}")
            print(f"Detected type: {result.hook_type}")
            print(f"Notes: {result.notes}")
        sys.exit(0 if result.score >= 7.0 else 1)

    if not args.topic:
        parser.error("--topic is required unless using --score-hook")

    report = generate_hooks(
        niche=args.niche,
        topic=args.topic,
        platform=args.platform,
        context=args.context,
        top_n=args.top,
    )

    if args.json:
        print(json.dumps(asdict(report), indent=2, default=str))
    else:
        print(report.report)

    # Exit code: 0 if top hook is RECOMMENDED, 1 otherwise
    sys.exit(0 if report.top_hook and report.top_hook.score >= 7.0 else 1)


if __name__ == "__main__":
    main()

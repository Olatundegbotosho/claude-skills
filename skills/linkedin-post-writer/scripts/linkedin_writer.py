#!/usr/bin/env python3
"""
linkedin_writer.py — Algorithm-aware LinkedIn post drafter for the Content Empire
Produces niche-voiced posts with dwell-time signals, hook scoring, and voice pre-check.

Usage:
  python linkedin_writer.py --niche ttbp --topic "why middle managers plateau"
  python linkedin_writer.py --niche tundexai --brief brief.json
  python linkedin_writer.py --niche cb --topic "Achebe and the Western canon" --hook-type contrarian
  python linkedin_writer.py --niche ttbp --topic "..." --variants 3
  python linkedin_writer.py --niche ttbp --topic "..." --json
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path

# ── Constants ────────────────────────────────────────────────────────────────

VALID_NICHES = ["ttbp", "cb", "tundexai", "wellwithtunde", "tundestalksmen"]

HOOK_TYPES = [
    "personal_story", "bold_claim", "curiosity_gap",
    "data_shock", "pattern_interrupt", "question", "contrarian", "number_list",
]

LINKEDIN_CHAR_LIMIT = 3000
LINKEDIN_SWEET_SPOT = (900, 1800)
LINKEDIN_HOOK_LIMIT = 200   # chars before "see more"
MAX_HASHTAGS = 5

# ── Per-niche LinkedIn config ─────────────────────────────────────────────────

NICHE_LINKEDIN_CONFIG: dict[str, dict] = {
    "ttbp": {
        "preferred_hooks": ["personal_story", "bold_claim", "curiosity_gap"],
        "length_target": (900, 1500),
        "tone": "Confident, warm. Specific moments > vague generalities. First-person OK after line 1.",
        "hashtag_pool": [
            "#Leadership", "#CareerGrowth", "#ManagementInsights",
            "#Ambition", "#ExecutiveCoaching", "#ProfessionalDevelopment",
            "#WorkplaceWisdom", "#CareerAdvice",
        ],
        "banned_phrases": [
            "unpack", "synergy", "game-changer", "thought leader",
            "circle back", "leverage", "journey", "in today's fast-paced world",
        ],
        "banned_openers": [
            "hi everyone", "happy monday", "happy friday", "good morning",
            "in today's", "as we navigate", "in this post i will",
        ],
        "green_flags": [
            "here's the thing", "the truth is", "what nobody tells you",
            "i've seen this", "think about that", "that's not a small thing",
        ],
        "cta_templates": [
            "What's one thing you wish someone had told you before you hit your first ceiling?",
            "Have you seen this pattern? What changed it for you?",
            "Where are you in this right now — hit reply or drop it in the comments.",
        ],
        "list_marker": "→",
    },
    "cb": {
        "preferred_hooks": ["curiosity_gap", "contrarian", "personal_story"],
        "length_target": (700, 1200),
        "tone": "Literary, culturally grounded. Treats reader as intelligent. No condescension.",
        "hashtag_pool": [
            "#AfricanLiterature", "#DiasporaFiction", "#BookRecommendations",
            "#ChinuaAchebe", "#AfricanAuthors", "#LiteraryFiction",
            "#BookCommunity", "#ReadingList",
        ],
        "banned_phrases": [
            "diverse voices", "own voices", "must-read", "representation matters",
            "powerful story", "thought-provoking", "delve into",
        ],
        "banned_openers": [
            "hi everyone", "happy monday", "in this post",
            "today we're going to", "let me share",
        ],
        "green_flags": [
            "the story behind the story", "what this book is really doing",
            "there's a reason this one", "the diaspora needs", "read this slowly",
        ],
        "cta_templates": [
            "What book has unsettled something you thought was settled? I'm genuinely asking.",
            "Which African author do you think is most underread in the West right now?",
            "What are you reading this month? Drop it below.",
        ],
        "list_marker": "—",
    },
    "tundexai": {
        "preferred_hooks": ["bold_claim", "data_shock", "contrarian"],
        "length_target": (1000, 1800),
        "tone": "Analytical, technically specific. Name models, name tools, cite benchmarks.",
        "hashtag_pool": [
            "#AIStrategy", "#MachineLearning", "#GenAI", "#LLM",
            "#AIProductivity", "#TechLeadership", "#AIImplementation",
            "#ArtificialIntelligence", "#AITools",
        ],
        "banned_phrases": [
            "ai is going to change everything", "unlock the power of ai",
            "revolutionary", "groundbreaking", "harness", "democratize",
            "the ai revolution", "delve into",
        ],
        "banned_openers": [
            "ai is changing", "in today's rapidly evolving", "as ai continues",
            "the world of ai", "with the rise of ai",
        ],
        "green_flags": [
            "here's what the benchmarks aren't telling you",
            "the pattern i keep seeing", "framework first", "i tested this",
            "most people are optimizing for the wrong thing", "let me be specific",
        ],
        "cta_templates": [
            "What's the AI implementation problem you're actually stuck on? Drop it below.",
            "Are you seeing this pattern too — or is this specific to certain contexts?",
            "What would you test here? I'm curious what angles I'm missing.",
        ],
        "list_marker": "→",
    },
    "wellwithtunde": {
        "preferred_hooks": ["pattern_interrupt", "question", "personal_story"],
        "length_target": (700, 1100),
        "tone": "Warm, sustainable, not prescriptive. The reader knows their body.",
        "hashtag_pool": [
            "#WellBeing", "#SustainableHealth", "#MindBodyConnection",
            "#HealthHabits", "#WholePerson", "#HolisticHealth",
            "#MentalHealth", "#Wellness",
        ],
        "banned_phrases": [
            "self-care", "hustle culture", "glow up", "manifest",
            "wellness journey", "toxic positivity", "biohacking", "optimizing your body",
        ],
        "banned_openers": [
            "hi everyone", "good morning beautiful", "rise and shine",
            "today's tip", "in today's post",
        ],
        "green_flags": [
            "your body keeps the score", "this is sustainable",
            "you don't earn rest", "what are you actually hungry for",
            "start smaller", "the whole person shows up",
        ],
        "cta_templates": [
            "What does your body do when you actually slow down? I'm curious.",
            "One thing you can try this week — just once. What would it be?",
            "What would 'sustainable' actually look like for you right now?",
        ],
        "list_marker": "—",
    },
    "tundestalksmen": {
        "preferred_hooks": ["personal_story", "pattern_interrupt", "bold_claim"],
        "length_target": (800, 1400),
        "tone": "Direct, accountable, warm underneath. No softening. No judgment.",
        "hashtag_pool": [
            "#MensMentalHealth", "#Fatherhood", "#MasculinityRedefined",
            "#MenAndMentalHealth", "#DadLife", "#Manhood",
            "#InnerWork", "#MenWhoLead",
        ],
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
            "what are you modeling", "strong men build",
            "the version of you your children", "men don't talk about this",
        ],
        "cta_templates": [
            "What's the thing you're sitting with right now that nobody's asked about?",
            "What are you modeling for the people watching you most closely?",
            "Drop a word below — just one — that describes where you are right now.",
        ],
        "list_marker": "→",
    },
}

# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class DwellSignal:
    signal_type: str    # "list", "line_break", "specific_detail", "open_loop"
    description: str


@dataclass
class AlgorithmReport:
    dwell_signals: list[DwellSignal]
    cta_type: str           # "question" | "directive" | "provocation"
    hashtag_count: int
    char_count: int
    in_sweet_spot: bool
    golden_hour_note: str = "Best windows: Tue–Thu, 7–9am or 5–7pm"


@dataclass
class LinkedInPost:
    niche: str
    topic: str
    hook_type: str
    text: str
    char_count: int
    hook_text: str
    hashtags: list[str]
    voice_score: int
    voice_verdict: str
    voice_issues: list[str]
    algorithm: AlgorithmReport
    report: str = ""
    generated_at: str = ""

    def __post_init__(self):
        if not self.generated_at:
            self.generated_at = datetime.now().strftime("%Y-%m-%d")


# ── Voice pre-check ───────────────────────────────────────────────────────────

def _voice_check(niche: str, text: str) -> tuple[int, str, list[str]]:
    """Quick voice gate. Returns (score, verdict, issues)."""
    config = NICHE_LINKEDIN_CONFIG[niche]
    text_lower = text.lower()
    lines = text.strip().split("\n")
    first_line = lines[0].strip().lower() if lines else ""

    issues = []

    # Banned phrases (max -10 each)
    banned_hits = 0
    for phrase in config["banned_phrases"]:
        if phrase.lower() in text_lower:
            issues.append(f'Banned phrase: "{phrase}"')
            banned_hits += 1

    # Banned openers
    opener_ok = True
    for opener in config["banned_openers"]:
        if first_line.startswith(opener.lower()):
            issues.append(f"Banned opener: \"{lines[0][:60]}\"")
            opener_ok = False
            break

    # Green flag bonus
    green_found = any(gf.lower() in text_lower for gf in config["green_flags"])

    # Score
    score = 50
    score -= banned_hits * 10
    score += 20 if opener_ok else 0
    score += 15 if green_found else 0
    score += 10 if LINKEDIN_CHAR_LIMIT >= len(text) >= LINKEDIN_SWEET_SPOT[0] else 0
    score = max(0, min(100, score))

    if score >= 85:
        verdict = "PASS"
    elif score >= 70:
        verdict = "REVISE"
    elif score >= 50:
        verdict = "HEAVY REVISE"
    else:
        verdict = "REJECT"

    return score, verdict, issues


# ── Algorithm signals ─────────────────────────────────────────────────────────

def _analyze_algorithm(text: str, niche: str) -> AlgorithmReport:
    """Scan for dwell-time signals and CTA type."""
    config = NICHE_LINKEDIN_CONFIG[niche]
    marker = config["list_marker"]

    signals = []

    # List detected
    list_count = text.count(marker)
    if list_count >= 2:
        signals.append(DwellSignal("list", f"{list_count} list items with {marker}"))

    # Line breaks (short paragraphs = scannable)
    blank_lines = text.count("\n\n")
    if blank_lines >= 3:
        signals.append(DwellSignal("line_break", f"{blank_lines} visual breaks — high scannability"))

    # Numbers/specifics
    number_matches = re.findall(r'\b\d+[\w%]?\b', text)
    if len(number_matches) >= 2:
        signals.append(DwellSignal("specific_detail", f"{len(number_matches)} specific numbers"))

    # Open loop (question at end = comment bait)
    last_paragraph = text.strip().split("\n\n")[-1].strip()
    cta_type = "question" if last_paragraph.endswith("?") else "directive"
    if cta_type == "question":
        signals.append(DwellSignal("open_loop", "Ends with question — triggers comment responses"))

    char_count = len(text)
    hashtag_count = len(re.findall(r'#\w+', text))
    in_sweet_spot = LINKEDIN_SWEET_SPOT[0] <= char_count <= LINKEDIN_SWEET_SPOT[1]

    return AlgorithmReport(
        dwell_signals=signals,
        cta_type=cta_type,
        hashtag_count=hashtag_count,
        char_count=char_count,
        in_sweet_spot=in_sweet_spot,
    )


# ── Hashtag selection ─────────────────────────────────────────────────────────

def _pick_hashtags(niche: str, topic: str, count: int = 3) -> list[str]:
    """Pick the most relevant hashtags from the niche pool."""
    pool = NICHE_LINKEDIN_CONFIG[niche]["hashtag_pool"]
    # Simple relevance: return first N (pool is ordered by priority)
    return pool[:min(count, MAX_HASHTAGS)]


# ── Hook drafters ─────────────────────────────────────────────────────────────

def _draft_hook_line(niche: str, topic: str, hook_type: str, key_facts: list[str] | None = None) -> str:
    """Draft the opening hook (3 lines max, under LINKEDIN_HOOK_LIMIT chars)."""
    facts = key_facts or []
    first_fact = facts[0] if facts else ""

    if hook_type == "personal_story":
        return f"I sat with this one longer than I expected.\n\nAbout {topic.lower().rstrip('.')}."

    elif hook_type == "bold_claim":
        return f"Most people are solving the wrong problem here.\n\nThe actual issue with {topic.lower().rstrip('.')} is simpler — and more specific."

    elif hook_type == "curiosity_gap":
        return f"Nobody talks about the real reason {topic.lower().rstrip('.')} happens.\n\nNot the version that sounds good in an interview. The actual one."

    elif hook_type == "data_shock":
        if first_fact:
            return f"{first_fact[:120]}\n\nAnd almost nobody changes their approach because of it."
        return f"The data on {topic.lower().rstrip('.')} is clearer than most people admit.\n\nThe gap is between knowing and doing."

    elif hook_type == "pattern_interrupt":
        return f"You didn't fail at {topic.lower().rstrip('.')}.\n\nThe framework you were given was wrong."

    elif hook_type == "question":
        return f"What if everything you've been taught about {topic.lower().rstrip('.')} was optimizing for the wrong outcome?\n\nSit with that for a second."

    elif hook_type == "contrarian":
        return f"The conventional wisdom about {topic.lower().rstrip('.')} is backwards.\n\nHere's what actually works — and why nobody says it out loud."

    elif hook_type == "number_list":
        return f"3 things about {topic.lower().rstrip('.')} that nobody told you before it mattered.\n\n(None of them are what you think.)"

    return f"Here's the thing nobody said out loud about {topic.lower().rstrip('.')}."


# ── Body drafters ─────────────────────────────────────────────────────────────

def _draft_body(niche: str, topic: str, hook_type: str, brief_summary: str = "", key_facts: list[str] | None = None) -> str:
    """Draft the post body with white space and list markers."""
    config = NICHE_LINKEDIN_CONFIG[niche]
    marker = config["list_marker"]
    facts = key_facts or []

    if niche == "ttbp":
        fact_block = "\n".join(f"{marker} {f[:100]}" for f in facts[:3]) if facts else (
            f"{marker} You're talented — the work is good\n"
            f"{marker} The ceiling isn't made of glass\n"
            f"{marker} It's made of invisible criteria nobody explained"
        )
        return (
            f"Here's what I see in almost every plateau story:\n\n"
            f"{fact_block}\n\n"
            f"The moment your manager stops sponsoring you isn't always about performance.\n\n"
            f"Often it's about:\n\n"
            f"{marker} You've become 'reliable' — which reads as 'not promotable'\n"
            f"{marker} You stopped making them look good in new ways\n"
            f"{marker} You haven't made yourself uncomfortable recently\n\n"
            f"The people who break through aren't louder.\n\n"
            f"They're more specific about what they want — and they say it out loud, to the right people, earlier than feels comfortable."
        )

    elif niche == "cb":
        return (
            f"The best writing doesn't give you answers.\n\n"
            f"It gives you a better set of questions.\n\n"
            f"When I look at {topic.lower().rstrip('.')} — what I keep coming back to is the gap between what gets celebrated and what actually endures.\n\n"
            f"The work that stays with you:\n\n"
            f"{marker} Doesn't explain itself\n"
            f"{marker} Trusts you to hold the tension\n"
            f"{marker} Refuses to resolve what shouldn't be resolved\n\n"
            f"That's not a style choice. It's a philosophy of what literature is for."
        )

    elif niche == "tundexai":
        fact_block = "\n".join(f"{marker} {f[:100]}" for f in facts[:3]) if facts else (
            f"{marker} Most implementations are built around the tool, not the outcome\n"
            f"{marker} The benchmarks look good in labs — not in production\n"
            f"{marker} The failure mode is usually invisible until it's expensive"
        )
        return (
            f"Here's the pattern I keep seeing:\n\n"
            f"{fact_block}\n\n"
            f"Framework first. Tools second.\n\n"
            f"Before you pick a model or a stack, answer three questions:\n\n"
            f"{marker} What's the failure mode if this goes wrong?\n"
            f"{marker} What does 'good enough' actually look like here?\n"
            f"{marker} What human in the loop catches what the AI misses?\n\n"
            f"The builders who get this right aren't smarter.\n\n"
            f"They're more specific about constraints before they're specific about tools."
        )

    elif niche == "wellwithtunde":
        return (
            f"Your body keeps the score.\n\n"
            f"But it also keeps the calendar — it knows what day of the week it is.\n\n"
            f"The things we label as 'health problems' are often:\n\n"
            f"{marker} Information, not failure\n"
            f"{marker} Signals, not noise\n"
            f"{marker} Patterns asking to be noticed\n\n"
            f"The sustainable version of {topic.lower().rstrip('.')} isn't harder.\n\n"
            f"It's more honest about what you're actually working with.\n\n"
            f"Start smaller than you think you need to. Much smaller."
        )

    elif niche == "tundestalksmen":
        return (
            f"The part nobody talks about:\n\n"
            f"The version of {topic.lower().rstrip('.')} that men actually experience isn't the one that gets discussed publicly.\n\n"
            f"It's quieter. More specific. And it compounds when it doesn't get named.\n\n"
            f"What men actually need:\n\n"
            f"{marker} Space to name what's actually happening\n"
            f"{marker} Accountability that doesn't feel like judgment\n"
            f"{marker} A clear picture of what 'strong' actually looks like\n\n"
            f"That's the work. Not performing strength — developing it.\n\n"
            f"Nobody's coming to save you from the work. But you're not alone in it."
        )

    return (
        f"The thing that most people miss about {topic.lower().rstrip('.')}:\n\n"
        f"It's not a strategy problem. It's a specificity problem.\n\n"
        f"Get specific about what you actually want — and say it out loud to the right people."
    )


# ── Full post assembler ───────────────────────────────────────────────────────

def _assemble_post(hook: str, body: str, cta: str, hashtags: list[str]) -> str:
    """Assemble all sections into a final LinkedIn post."""
    hashtag_line = " ".join(hashtags)
    parts = [hook.strip(), body.strip(), cta.strip(), hashtag_line]
    return "\n\n".join(p for p in parts if p.strip())


# ── Report builder ────────────────────────────────────────────────────────────

def _build_report(post: "LinkedInPost") -> str:
    sep = "=" * 45
    lines = [
        sep,
        "LINKEDIN POST DRAFT",
        sep,
        f"Niche:      {post.niche}",
        f"Topic:      {post.topic[:50]}",
        f"Hook Type:  {post.hook_type}",
        f"Generated:  {post.generated_at}",
        "",
        f"POST ({post.char_count} chars)",
        "─" * 45,
        post.text,
        "─" * 45,
        "",
        "VOICE CHECK",
        f"  Score:   {post.voice_score}/100   {post.voice_verdict}",
    ]
    if post.voice_issues:
        for issue in post.voice_issues:
            lines.append(f"  ⚠️  {issue}")

    lines += [
        "",
        "ALGORITHM SIGNALS",
        f"  Chars:       {post.algorithm.char_count} {'✅ sweet spot' if post.algorithm.in_sweet_spot else '⚠️  outside sweet spot'}",
        f"  CTA type:    {post.algorithm.cta_type}",
        f"  Hashtags:    {post.algorithm.hashtag_count}",
        f"  Dwell signals: {len(post.algorithm.dwell_signals)}",
    ]
    for signal in post.algorithm.dwell_signals:
        lines.append(f"    → {signal.signal_type}: {signal.description}")

    lines += [
        "",
        f"  {post.algorithm.golden_hour_note}",
        sep,
    ]
    return "\n".join(lines)


# ── Main draft function ───────────────────────────────────────────────────────

def draft_linkedin_post(
    niche: str,
    topic: str = "",
    text: str = "",
    hook_type: str = "",
    research_brief=None,
) -> "LinkedInPost":
    """
    Draft a LinkedIn post. Returns LinkedInPost.

    Args:
        niche:           One of VALID_NICHES
        topic:           Topic string
        text:            Raw notes/context text
        hook_type:       One of HOOK_TYPES (auto-selected if empty)
        research_brief:  ContentBrief dataclass from research_synth.synthesize()
    """
    if niche not in VALID_NICHES:
        raise ValueError(f"Unknown niche: {niche}. Valid: {VALID_NICHES}")

    # Resolve topic and context
    brief_summary = ""
    key_facts: list[str] = []

    if research_brief is not None:
        topic = topic or getattr(research_brief, "primary_angle", topic)
        brief_summary = getattr(research_brief, "source_summary", "")
        key_facts = getattr(research_brief, "key_facts", [])
    elif text:
        brief_summary = text[:300]
        topic = topic or text.split(".")[0][:80]

    topic = topic or "what nobody tells you"

    # Auto-select hook type
    config = NICHE_LINKEDIN_CONFIG[niche]
    if not hook_type or hook_type not in HOOK_TYPES:
        hook_type = config["preferred_hooks"][0]

    # Draft sections
    hook_text = _draft_hook_line(niche, topic, hook_type, key_facts)
    body_text = _draft_body(niche, topic, hook_type, brief_summary, key_facts)
    cta_text = config["cta_templates"][0]
    hashtags = _pick_hashtags(niche, topic, count=3)

    # Assemble
    full_text = _assemble_post(hook_text, body_text, cta_text, hashtags)
    char_count = len(full_text)

    # Truncate if over limit
    if char_count > LINKEDIN_CHAR_LIMIT:
        full_text = full_text[:LINKEDIN_CHAR_LIMIT - 3] + "..."
        char_count = len(full_text)

    # Voice check
    voice_score, voice_verdict, voice_issues = _voice_check(niche, full_text)

    # Algorithm analysis
    algorithm = _analyze_algorithm(full_text, niche)

    post = LinkedInPost(
        niche=niche,
        topic=topic,
        hook_type=hook_type,
        text=full_text,
        char_count=char_count,
        hook_text=hook_text,
        hashtags=hashtags,
        voice_score=voice_score,
        voice_verdict=voice_verdict,
        voice_issues=voice_issues,
        algorithm=algorithm,
    )
    post.report = _build_report(post)
    return post


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Draft algorithm-aware LinkedIn posts with niche voice enforcement",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python linkedin_writer.py --niche ttbp --topic "why middle managers plateau"
  python linkedin_writer.py --niche tundexai --text "Claude 3.5 Sonnet benchmark notes..."
  python linkedin_writer.py --niche cb --topic "Achebe and the Western canon" --hook-type contrarian
  python linkedin_writer.py --niche ttbp --topic "..." --variants 3
  python linkedin_writer.py --niche ttbp --topic "..." --json
        """
    )
    parser.add_argument("--niche", required=True, choices=VALID_NICHES)
    parser.add_argument("--topic", type=str, default="")
    parser.add_argument("--text", type=str, default="", help="Raw notes or context text")
    parser.add_argument("--brief", type=Path, help="Path to research brief JSON")
    parser.add_argument("--hook-type", type=str, choices=HOOK_TYPES, default="",
                        help="Force a specific hook type (default: auto-selected per niche)")
    parser.add_argument("--variants", type=int, default=1, choices=[1, 2, 3],
                        help="Number of hook variants to generate")
    parser.add_argument("--json", action="store_true", help="Output JSON to stdout")
    parser.add_argument("--post-only", action="store_true", help="Print post text only")

    args = parser.parse_args()

    # Load brief if provided
    research_brief = None
    if args.brief:
        if not args.brief.exists():
            print(f"Error: Brief not found: {args.brief}", file=sys.stderr)
            sys.exit(1)
        brief_data = json.loads(args.brief.read_text(encoding="utf-8"))

        class SimpleBrief:
            pass
        research_brief = SimpleBrief()
        for k, v in brief_data.items():
            setattr(research_brief, k, v)

    # Generate variants
    config = NICHE_LINKEDIN_CONFIG[args.niche]
    hook_types_to_try = (
        [args.hook_type] if args.hook_type
        else config["preferred_hooks"][:args.variants]
    )

    posts = []
    for ht in hook_types_to_try[:args.variants]:
        post = draft_linkedin_post(
            niche=args.niche,
            topic=args.topic,
            text=args.text,
            hook_type=ht,
            research_brief=research_brief,
        )
        posts.append(post)

    # Output
    if args.json:
        output = [asdict(p) for p in posts]
        print(json.dumps(output if len(output) > 1 else output[0], indent=2, default=str))
    elif args.post_only:
        for p in posts:
            print(p.text)
            if len(posts) > 1:
                print("\n" + "─" * 45 + "\n")
    else:
        for i, p in enumerate(posts, 1):
            if len(posts) > 1:
                print(f"\n── VARIANT {i} ({p.hook_type}) ──")
            print(p.report)

    # Exit based on best voice score
    best_score = max(p.voice_score for p in posts)
    best = next(p for p in posts if p.voice_score == best_score)
    if best.voice_verdict == "PASS":
        sys.exit(0)
    elif best.voice_verdict == "REVISE":
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == "__main__":
    main()

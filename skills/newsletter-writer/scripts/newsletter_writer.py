#!/usr/bin/env python3
"""
newsletter_writer.py — Multi-platform newsletter drafter for the Content Empire
Produces voice-enforced newsletter drafts and platform-ready exports.

Usage:
  python newsletter_writer.py --niche ttbp --topic "why middle managers plateau" --platform substack
  python newsletter_writer.py --niche tundexai --brief brief.json --platform beehiiv
  python newsletter_writer.py --niche cb --text "Chinua Achebe and decolonization" --platform convertkit
  python newsletter_writer.py --niche ttbp --topic "..." --platform contentstudio --json
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
VALID_PLATFORMS = ["substack", "convertkit", "beehiiv", "contentstudio"]

# Word count targets per niche (min, max)
NICHE_LENGTH_TARGETS = {
    "ttbp":           (500, 900),
    "cb":             (400, 700),
    "tundexai":       (600, 1000),
    "wellwithtunde":  (400, 650),
    "tundestalksmen": (450, 750),
}

# ── Per-niche newsletter config ───────────────────────────────────────────────

NICHE_NEWSLETTER_CONFIG: dict[str, dict] = {
    "ttbp": {
        "name": "The Tunde Gbotosho Post",
        "tagline": "Insights on leadership, career, and what nobody tells you at work",
        "structure": "insight_evidence_implication",
        "tone": "Confident, warm, intellectually direct. No hedging. Personal specifics over vague generalities.",
        "audience": "Mid-to-senior professionals navigating ambition, transition, and leadership",
        "signature_phrases": [
            "Here's the thing nobody said out loud:",
            "The truth is,",
            "What I've seen consistently is",
            "Think about that for a second.",
            "That's not a small thing.",
        ],
        "banned_openers": [
            "Hi everyone", "Happy Monday", "This week I wanted to",
            "In today's newsletter", "Welcome back",
        ],
        "cta_templates": [
            "If this resonated — forward it to one person who needs to read it.",
            "Reply and tell me where you've seen this play out.",
            "One question worth sitting with this week:",
        ],
        "banned_phrases": [
            "unpack", "synergy", "game-changer", "thought leader", "circle back",
            "delve into", "leverage", "journey", "in today's fast-paced world",
        ],
        "subject_line_patterns": [
            "The real reason [specific thing] happens",
            "[Number] things your [role] won't tell you about [topic]",
            "What happens when [tension]",
            "I watched [person] [action]. Here's what I noticed.",
        ],
    },
    "cb": {
        "name": "Connecting Bridges",
        "tagline": "African and diaspora literature, culture, and the stories behind the stories",
        "structure": "book_angle_broader_meaning_read_next",
        "tone": "Literary, cultural, personally grounded. Treats readers as intelligent. Avoids condescension.",
        "audience": "Readers of African and diaspora fiction, cultural commentators, lovers of literary craft",
        "signature_phrases": [
            "The story behind the story is",
            "What this book is really doing is",
            "There's a reason this one stays with you.",
            "Read this slowly.",
            "The diaspora needs",
        ],
        "banned_openers": [
            "Hi everyone", "Happy Monday", "In this issue", "Today we explore",
            "Let me share", "I'm excited to",
        ],
        "cta_templates": [
            "What are you reading this month? Hit reply.",
            "If this sparked something — share it with someone who reads.",
            "One book to add to the list:",
        ],
        "banned_phrases": [
            "diverse voices", "own voices", "must-read", "representation matters",
            "powerful story", "thought-provoking", "delve into",
        ],
        "subject_line_patterns": [
            "What [Author] knew that we forgot",
            "The book that [specific impact]",
            "[Title] and the question it refuses to answer",
            "Why [cultural moment] matters for [audience]",
        ],
    },
    "tundexai": {
        "name": "TundeXAI",
        "tagline": "AI insights for builders and operators — without the hype",
        "structure": "claim_benchmark_framework_takeaway",
        "tone": "Analytical, technically grounded, builder-friendly. Name models, name tools, cite specifics.",
        "audience": "Tech founders, AI practitioners, enterprise operators, builders evaluating AI tools",
        "signature_phrases": [
            "Here's what the benchmarks aren't telling you:",
            "The pattern I keep seeing is",
            "Framework first, tools second.",
            "I tested this. Here's what happened.",
            "Most people are optimizing for the wrong thing.",
            "Let me be specific.",
        ],
        "banned_openers": [
            "AI is changing", "In today's rapidly evolving", "As AI continues",
            "The world of AI", "With the rise of AI",
        ],
        "cta_templates": [
            "What are you building with this? Reply.",
            "One framework worth testing this week:",
            "If you're evaluating [tool], here's the question to ask first:",
        ],
        "banned_phrases": [
            "ai is going to change everything", "unlock the power of ai",
            "revolutionary", "groundbreaking", "harness", "democratize",
            "the ai revolution", "delve into", "hallucination",
        ],
        "subject_line_patterns": [
            "[Model/Tool]: what the benchmarks don't show",
            "Why most [AI use case] implementations fail",
            "[Number] patterns from [N] weeks of testing [tool]",
            "The [specific problem] nobody's solved cleanly yet",
        ],
    },
    "wellwithtunde": {
        "name": "Well With Tunde",
        "tagline": "Sustainable health for people who don't have time for wellness culture",
        "structure": "observation_body_connection_one_practice",
        "tone": "Warm, practical, human. Not prescriptive. The reader knows their body — your job is to make space.",
        "audience": "Health-conscious professionals, people tired of wellness fads, whole-person health seekers",
        "signature_phrases": [
            "Your body keeps the score.",
            "This is sustainable.",
            "You don't earn rest. You require it.",
            "What are you actually hungry for?",
            "Start smaller than you think.",
            "The whole person shows up.",
        ],
        "banned_openers": [
            "Hi everyone", "Good morning", "Rise and shine",
            "Today's tip", "In today's post", "This week's wellness",
        ],
        "cta_templates": [
            "One thing to try this week — just once:",
            "Notice what your body does with that. Reply if something shifts.",
            "Share this with someone who needs permission to rest.",
        ],
        "banned_phrases": [
            "self-care", "hustle culture", "glow up", "manifest",
            "wellness journey", "toxic positivity", "biohacking", "optimizing your body",
        ],
        "subject_line_patterns": [
            "What [body signal] is actually telling you",
            "The [wellness practice] nobody talks about clearly",
            "Why [common health advice] doesn't work the way you think",
            "One thing I noticed about [sustainable practice]",
        ],
    },
    "tundestalksmen": {
        "name": "Tunde's Talks Men",
        "tagline": "Real conversations about what it means to be a man worth becoming",
        "structure": "tension_what_men_dont_say_the_ask",
        "tone": "Direct, accountable, warm underneath. No softening. No judgment. Just the thing men need to hear.",
        "audience": "Men in transition, fathers, men doing the inner work, men tired of surface-level conversations",
        "signature_phrases": [
            "That's the work.",
            "Nobody's coming to save you.",
            "What are you modeling for them?",
            "Strong men build.",
            "Men don't talk about this — so let's talk about it.",
            "The version of you your children will remember.",
        ],
        "banned_openers": [
            "Hey guys", "What's up men", "Gentlemen,",
            "As men we need to", "This is for the fellas",
        ],
        "cta_templates": [
            "One question for this week. Sit with it.",
            "Pass this to a man who's doing the work.",
            "Reply. Tell me what came up.",
        ],
        "banned_phrases": [
            "toxic masculinity", "man up", "alpha male", "sigma",
            "boys will be boys", "real men", "bro",
        ],
        "subject_line_patterns": [
            "What [fatherhood/manhood moment] taught me about [core thing]",
            "The conversation men aren't having about [topic]",
            "What happens when a man [vulnerable action] — actually",
            "[Number] things nobody told you about [transition/stage]",
        ],
    },
}

# ── Platform API payload shapes ───────────────────────────────────────────────

PLATFORM_SPECS = {
    "substack": {
        "transport": "manual",
        "format": "markdown",
        "max_subject_chars": 80,
        "note": "Export as .md file — paste into Substack editor manually",
    },
    "convertkit": {
        "transport": "api",
        "endpoint": "https://api.convertkit.com/v3/broadcasts",
        "method": "POST",
        "auth": "api_key query param",
        "payload_fields": ["subject", "content", "description", "public", "send_at"],
        "content_type": "html",
        "max_subject_chars": 128,
    },
    "beehiiv": {
        "transport": "api",
        "endpoint": "https://api.beehiiv.com/v2/publications/{publication_id}/emails",
        "method": "POST",
        "auth": "Bearer token header",
        "payload_fields": ["subject", "preview_text", "content_json", "status", "send_at"],
        "content_type": "html",
        "max_subject_chars": 120,
    },
    "contentstudio": {
        "transport": "api",
        "endpoint": "https://api.contentstudio.io/api/v2/article",
        "method": "POST",
        "auth": "Bearer token header",
        "payload_fields": ["title", "body", "summary", "tags", "status"],
        "content_type": "html",
        "max_subject_chars": 100,
    },
}

# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class SubjectLine:
    text: str
    variant: str    # "primary" | "curiosity_gap" | "personal_story"
    char_count: int = 0

    def __post_init__(self):
        self.char_count = len(self.text)


@dataclass
class NewsletterSection:
    name: str       # "hook" | "body_1" | "body_2" | "body_3" | "cta"
    content: str
    word_count: int = 0

    def __post_init__(self):
        self.word_count = len(self.content.split())


@dataclass
class VoicePreCheck:
    score: int
    verdict: str    # "PASS" | "REVISE" | "HEAVY REVISE" | "REJECT"
    banned_hits: list[str] = field(default_factory=list)
    opener_ok: bool = True
    issues: list[str] = field(default_factory=list)


@dataclass
class NewsletterDraft:
    niche: str
    platform: str
    subject_lines: list[SubjectLine]
    preview_text: str
    sections: list[NewsletterSection]
    full_text: str
    word_count: int
    voice_check: VoicePreCheck
    platform_payload: dict
    output_path: str = ""
    issue_number: int = 0
    generated_at: str = ""
    report: str = ""

    def __post_init__(self):
        if not self.generated_at:
            self.generated_at = datetime.now().strftime("%Y-%m-%d")

    @property
    def primary_subject(self) -> str:
        primaries = [s for s in self.subject_lines if s.variant == "primary"]
        return primaries[0].text if primaries else (self.subject_lines[0].text if self.subject_lines else "")

    @property
    def voice_score(self) -> int:
        return self.voice_check.score


# ── Voice pre-check ───────────────────────────────────────────────────────────

def _pre_check_voice(niche: str, text: str) -> VoicePreCheck:
    """
    Lightweight voice check before full validation.
    Checks banned phrases and opener — quick gate before output.
    """
    config = NICHE_NEWSLETTER_CONFIG[niche]
    text_lower = text.lower()
    lines = text.strip().split("\n")
    first_line = lines[0].strip().lower() if lines else ""

    banned_hits = []
    for phrase in config["banned_phrases"]:
        if phrase.lower() in text_lower:
            banned_hits.append(phrase)

    opener_ok = True
    for bad in config["banned_openers"]:
        if first_line.startswith(bad.lower()):
            opener_ok = False
            break

    issues = []
    if banned_hits:
        issues.extend([f'Banned phrase: "{p}"' for p in banned_hits])
    if not opener_ok:
        issues.append(f"Banned opener detected in first line: {lines[0][:60]}")

    # Rough score: 50 base + bonuses/penalties
    score = 50
    score -= len(banned_hits) * 10
    if opener_ok:
        score += 20
    # Green flag bonus
    for gf in config["signature_phrases"]:
        if gf.lower() in text_lower:
            score += 6
            break
    score = max(0, min(100, score))

    if score >= 85:
        verdict = "PASS"
    elif score >= 70:
        verdict = "REVISE"
    elif score >= 50:
        verdict = "HEAVY REVISE"
    else:
        verdict = "REJECT"

    return VoicePreCheck(
        score=score,
        verdict=verdict,
        banned_hits=banned_hits,
        opener_ok=opener_ok,
        issues=issues,
    )


# ── Subject line generation ───────────────────────────────────────────────────

def _generate_subject_lines(niche: str, topic: str, brief_summary: str = "") -> list[SubjectLine]:
    """Generate 3 subject line variants from topic + optional brief."""
    config = NICHE_NEWSLETTER_CONFIG[niche]
    patterns = config["subject_line_patterns"]
    context = brief_summary or topic

    # Extract core noun from topic (first meaningful noun phrase)
    topic_clean = topic.strip().rstrip("?.")
    topic_words = topic_clean.split()
    core_noun = " ".join(topic_words[-3:]) if len(topic_words) > 3 else topic_clean

    subjects = [
        # Primary: direct, specific — uses first pattern
        SubjectLine(
            text=f"{topic_clean[:75]}",
            variant="primary",
        ),
        # Curiosity gap: uses second pattern shape
        SubjectLine(
            text=f"The truth about {core_noun[:60]}",
            variant="curiosity_gap",
        ),
        # Personal story: first person entry
        SubjectLine(
            text=f"What I've learned about {core_noun[:55]}",
            variant="personal_story",
        ),
    ]

    # Enforce max length per platform (default 80)
    for s in subjects:
        s.text = s.text[:80]
        s.char_count = len(s.text)

    return subjects


# ── Preview text generation ───────────────────────────────────────────────────

def _generate_preview(niche: str, topic: str, hook_text: str = "") -> str:
    """Generate 50–90 char preview text that extends the subject line's thought."""
    base = hook_text or topic
    # Take first sentence of hook if available
    sentences = re.split(r'(?<=[.!?])\s+', base.strip())
    first = sentences[0][:90] if sentences else base[:90]

    # Ensure it doesn't repeat subject line exactly — add ellipsis if truncated
    if len(first) == 90:
        first = first.rstrip() + "..."

    return first


# ── Section drafts (structured by niche pattern) ─────────────────────────────

def _draft_hook(niche: str, topic: str, brief_summary: str = "") -> str:
    """
    Draft the opening hook section.
    1–2 sentences. No preamble. No pleasantries.
    """
    config = NICHE_NEWSLETTER_CONFIG[niche]
    starter = config["signature_phrases"][0] if config["signature_phrases"] else ""

    if niche == "ttbp":
        return (
            f"{starter}\n\n"
            f"There's a moment in every {_extract_subject(topic)} conversation "
            f"where the real issue finally surfaces — and it's almost never "
            f"what was on the agenda."
        )
    elif niche == "cb":
        return (
            f"The best books don't just tell a story.\n\n"
            f"They unsettle something you thought was settled. "
            f"That's what we're looking at today — {topic.lower().rstrip('.')}."
        )
    elif niche == "tundexai":
        return (
            f"Let me be specific.\n\n"
            f"Most conversations about {topic.lower().rstrip('.')} miss "
            f"the thing that actually determines whether the implementation works or not."
        )
    elif niche == "wellwithtunde":
        return (
            f"Your body has been trying to tell you something.\n\n"
            f"About {topic.lower().rstrip('.')} — and why "
            f"the standard advice keeps missing the mark."
        )
    elif niche == "tundestalksmen":
        return (
            f"Nobody talks about this part.\n\n"
            f"The part where {topic.lower().rstrip('.')} — and what it "
            f"actually takes to move through it."
        )
    return f"Here's what most people miss about {topic.lower()}."


def _draft_body(niche: str, topic: str, brief_summary: str = "", key_facts: list[str] | None = None) -> list[NewsletterSection]:
    """Draft 3 body sections based on niche structure."""
    facts = key_facts or []
    fact_block = ("\n\n".join(f"— {f}" for f in facts[:3])) if facts else ""

    structure = NICHE_NEWSLETTER_CONFIG[niche]["structure"]
    sections = []

    if structure == "insight_evidence_implication":
        sections = [
            NewsletterSection("body_1", (
                f"**The insight**\n\n"
                f"When you look closely at {topic.lower().rstrip('.')}, "
                f"what you find isn't what the conventional wisdom suggests. "
                f"The real pattern is more specific — and more actionable.\n\n"
                + (fact_block if fact_block else
                   f"The data here is consistent: what looks like a leadership or strategy problem "
                   f"is almost always an information problem in disguise.")
            )),
            NewsletterSection("body_2", (
                f"**What the evidence shows**\n\n"
                f"I've watched this play out across different contexts — different industries, "
                f"different org sizes, different career stages. The pattern holds. "
                f"Here's why it matters: the people who figure this out early "
                f"stop optimizing for the wrong signals."
            )),
            NewsletterSection("body_3", (
                f"**The implication**\n\n"
                f"This changes what you should be paying attention to. "
                f"Not more effort in the same direction — a different direction entirely. "
                f"That's not a small thing. It's the whole game."
            )),
        ]

    elif structure == "book_angle_broader_meaning_read_next":
        sections = [
            NewsletterSection("body_1", (
                f"**The story behind the story**\n\n"
                f"What this piece of writing is really doing is asking you to hold "
                f"two things at once: the personal and the political, the intimate and the historical. "
                f"That tension is the point.\n\n"
                + (fact_block if fact_block else
                   f"The writer doesn't resolve it. That's the craft.")
            )),
            NewsletterSection("body_2", (
                f"**What it means more broadly**\n\n"
                f"Every diaspora story is also a negotiation — between the place you came from "
                f"and the place you're becoming. The question this raises for African literature "
                f"isn't just aesthetic. It's about whose story gets to be universal."
            )),
            NewsletterSection("body_3", (
                f"**What to read next**\n\n"
                f"If this resonated — here are two titles in conversation with this one. "
                f"Different angles. Same essential question about {topic.lower().rstrip('.')}."
            )),
        ]

    elif structure == "claim_benchmark_framework_takeaway":
        sections = [
            NewsletterSection("body_1", (
                f"**The claim, stated plainly**\n\n"
                f"Here's what I keep seeing: most {topic.lower().rstrip('.')} implementations "
                f"are built around the tool, not the outcome. That's backwards. "
                f"It guarantees underperformance.\n\n"
                + (fact_block if fact_block else
                   f"The benchmarks confirm this — but benchmarks only tell you what happened in the lab.")
            )),
            NewsletterSection("body_2", (
                f"**The framework that works**\n\n"
                f"Framework first, tools second. Before you pick a model or a stack, "
                f"answer three questions: What's the failure mode if this goes wrong? "
                f"What does 'good enough' actually look like here? "
                f"What human in the loop catches what the AI misses?"
            )),
            NewsletterSection("body_3", (
                f"**Takeaway**\n\n"
                f"The builders who get this right aren't smarter — they're more specific. "
                f"They name the constraint before they name the tool. "
                f"That specificity is the competitive advantage."
            )),
        ]

    elif structure == "observation_body_connection_one_practice":
        sections = [
            NewsletterSection("body_1", (
                f"**What I've noticed**\n\n"
                f"There's a pattern with {topic.lower().rstrip('.')} that nobody "
                f"talks about in the way it actually shows up. "
                f"Not in a clinical way. In a Tuesday-at-3pm way.\n\n"
                + (fact_block if fact_block else
                   f"Your body keeps the score. But it also keeps the calendar — "
                   f"it knows what day of the week it is, and it responds accordingly.")
            )),
            NewsletterSection("body_2", (
                f"**The body connection**\n\n"
                f"This isn't about willpower. The people who've made this sustainable "
                f"didn't try harder — they changed the conditions. "
                f"They made the default easier than the exception. "
                f"That's the whole strategy."
            )),
            NewsletterSection("body_3", (
                f"**One practice**\n\n"
                f"Start smaller than you think you need to. Much smaller. "
                f"The goal isn't the habit — it's the relationship with the habit. "
                f"That takes time. Give it time."
            )),
        ]

    elif structure == "tension_what_men_dont_say_the_ask":
        sections = [
            NewsletterSection("body_1", (
                f"**The tension**\n\n"
                f"Here's the part of {topic.lower().rstrip('.')} that "
                f"most men sit with alone. The part that doesn't come up "
                f"in the group chat. The part that gets filed under "
                f"'fine' when somebody asks how you're doing.\n\n"
                + (fact_block if fact_block else
                   f"It's not fine. And somewhere underneath it all, you know that.")
            )),
            NewsletterSection("body_2", (
                f"**What men don't say**\n\n"
                f"The version of this that men actually experience is "
                f"different from what gets discussed publicly. It's quieter. "
                f"It's more specific. And it carries weight that compounds "
                f"when it doesn't get named."
            )),
            NewsletterSection("body_3", (
                f"**The ask**\n\n"
                f"That's the work. Not performing strength — developing it. "
                f"The version of you your children will remember isn't the one "
                f"who had it all figured out. It's the one who stayed at the table "
                f"when the work got hard."
            )),
        ]

    else:
        # Generic fallback
        sections = [
            NewsletterSection("body_1", f"**On {topic}**\n\nHere's what most people miss about this."),
            NewsletterSection("body_2", f"The evidence points in one direction."),
            NewsletterSection("body_3", f"The implication is worth sitting with."),
        ]

    return sections


def _draft_cta(niche: str) -> NewsletterSection:
    """Generate closing CTA section for the niche."""
    config = NICHE_NEWSLETTER_CONFIG[niche]
    cta = config["cta_templates"][0]
    return NewsletterSection("cta", f"\n---\n\n{cta}")


# ── Full draft assembler ──────────────────────────────────────────────────────

def _assemble_full_text(hook: str, body_sections: list[NewsletterSection], cta: NewsletterSection) -> str:
    """Assemble all sections into one readable draft."""
    parts = [hook.strip()]
    for section in body_sections:
        parts.append(section.content.strip())
    parts.append(cta.content.strip())
    return "\n\n".join(parts)


# ── Platform payload builders ─────────────────────────────────────────────────

def _build_substack_markdown(
    niche: str,
    subject: str,
    preview: str,
    full_text: str,
    issue_number: int,
) -> tuple[dict, str]:
    """Build Substack paste-ready markdown and return (payload_meta, markdown_text)."""
    config = NICHE_NEWSLETTER_CONFIG[niche]
    date_str = datetime.now().strftime("%Y-%m-%d")
    issue_label = f"Issue #{issue_number}" if issue_number else "Draft"

    md = f"""# {subject}

> {preview}

---

{full_text}

---

*{config['name']} — {issue_label} — {date_str}*
*{config['tagline']}*
"""
    payload = {
        "platform": "substack",
        "transport": "manual",
        "subject": subject,
        "preview_text": preview,
        "body_markdown": md,
        "instructions": "Paste body_markdown into Substack editor. Set subject and preview text separately.",
    }
    return payload, md


def _build_convertkit_payload(
    niche: str,
    subject: str,
    preview: str,
    full_text: str,
) -> dict:
    """Build ConvertKit broadcast API payload."""
    html_body = _markdown_to_html(full_text)
    return {
        "platform": "convertkit",
        "transport": "api",
        "endpoint": "https://api.convertkit.com/v3/broadcasts",
        "method": "POST",
        "auth_note": "Add api_key as query param: ?api_key=YOUR_KEY",
        "payload": {
            "subject": subject,
            "description": preview,
            "content": html_body,
            "public": True,
        },
        "send_at_note": "Add send_at: ISO8601 timestamp to schedule. Omit to save as draft.",
    }


def _build_beehiiv_payload(
    niche: str,
    subject: str,
    preview: str,
    full_text: str,
) -> dict:
    """Build Beehiiv email API payload."""
    html_body = _markdown_to_html(full_text)
    return {
        "platform": "beehiiv",
        "transport": "api",
        "endpoint": "https://api.beehiiv.com/v2/publications/{PUBLICATION_ID}/emails",
        "method": "POST",
        "auth_note": "Header: Authorization: Bearer YOUR_BEEHIIV_API_KEY",
        "payload": {
            "subject": subject,
            "preview_text": preview,
            "content_json": {
                "type": "doc",
                "content": html_body,
            },
            "status": "draft",
        },
        "send_at_note": "Set status to 'confirmed' and add send_at to schedule.",
    }


def _build_contentstudio_payload(
    niche: str,
    subject: str,
    preview: str,
    full_text: str,
) -> dict:
    """Build ContentStudio article API payload."""
    config = NICHE_NEWSLETTER_CONFIG[niche]
    html_body = _markdown_to_html(full_text)
    return {
        "platform": "contentstudio",
        "transport": "api",
        "endpoint": "https://api.contentstudio.io/api/v2/article",
        "method": "POST",
        "auth_note": "Header: Authorization: Bearer YOUR_CONTENTSTUDIO_TOKEN",
        "payload": {
            "title": subject,
            "summary": preview,
            "body": html_body,
            "tags": [niche, "newsletter"],
            "status": "draft",
        },
        "note": "Replace status with 'published' to publish immediately.",
    }


def _markdown_to_html(md_text: str) -> str:
    """
    Minimal markdown → HTML conversion for API payloads.
    Handles: **bold**, *italic*, ## headers, --- dividers, paragraphs.
    """
    lines = md_text.strip().split("\n")
    html_parts = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith("## "):
            html_parts.append(f"<h2>{line[3:]}</h2>")
        elif line.startswith("# "):
            html_parts.append(f"<h1>{line[2:]}</h1>")
        elif line == "---":
            html_parts.append("<hr>")
        else:
            # Inline formatting
            line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
            line = re.sub(r'\*(.+?)\*', r'<em>\1</em>', line)
            line = re.sub(r'`(.+?)`', r'<code>\1</code>', line)
            html_parts.append(f"<p>{line}</p>")
        i += 1

    return "\n".join(html_parts)


# ── Helper ────────────────────────────────────────────────────────────────────

def _extract_subject(topic: str) -> str:
    """Extract a short subject noun from a topic string."""
    stop_words = {"why", "how", "what", "when", "the", "a", "an", "of", "and", "or", "in"}
    words = [w for w in topic.lower().split() if w not in stop_words]
    return " ".join(words[:3]) if words else topic


# ── Report builder ────────────────────────────────────────────────────────────

def _build_report(draft: "NewsletterDraft") -> str:
    sep = "=" * 45
    lines = [
        sep,
        "NEWSLETTER DRAFT",
        sep,
        f"Niche:      {draft.niche}",
        f"Platform:   {draft.platform}",
        f"Date:       {draft.generated_at}",
        f"Words:      {draft.word_count}",
        "",
        "SUBJECT LINE VARIANTS",
        "─" * 45,
    ]
    for i, s in enumerate(draft.subject_lines, 1):
        tag = "  [PRIMARY]" if s.variant == "primary" else ""
        lines.append(f"  {i}. [{s.variant.upper()}]{tag} ({s.char_count} chars)")
        lines.append(f"     \"{s.text}\"")

    lines += [
        "",
        f"PREVIEW TEXT ({len(draft.preview_text)} chars)",
        f"  \"{draft.preview_text}\"",
        "",
        "VOICE PRE-CHECK",
        "─" * 45,
        f"  Score:   {draft.voice_check.score}/100",
        f"  Verdict: {draft.voice_check.verdict}",
    ]
    if draft.voice_check.issues:
        lines.append(f"  Issues:  {len(draft.voice_check.issues)}")
        for issue in draft.voice_check.issues:
            lines.append(f"    ⚠️  {issue}")

    lines += [
        "",
        "DRAFT SECTIONS",
        "─" * 45,
    ]
    for section in draft.sections:
        lines.append(f"  [{section.name.upper()}] {section.word_count} words")

    lines += [
        "",
        "PLATFORM EXPORT",
        "─" * 45,
        f"  Platform:  {draft.platform}",
        f"  Transport: {PLATFORM_SPECS[draft.platform]['transport']}",
    ]
    if draft.output_path:
        lines.append(f"  Output:    {draft.output_path}")
    if draft.voice_check.verdict == "PASS":
        lines.append("  Status:    ✅ Voice check passed — ready to export")
    else:
        lines.append(f"  Status:    ⚠️  {draft.voice_check.verdict} — fix voice issues before sending")

    lines.append(sep)
    return "\n".join(lines)


# ── Main draft function ───────────────────────────────────────────────────────

def draft_newsletter(
    niche: str,
    platform: str,
    topic: str = "",
    text: str = "",
    research_brief=None,
    issue_number: int = 0,
) -> "NewsletterDraft":
    """
    Main entry point. Returns a complete NewsletterDraft.

    Args:
        niche:           One of VALID_NICHES
        platform:        One of VALID_PLATFORMS
        topic:           Topic string (used if no brief/text)
        text:            Raw text/notes to base the draft on
        research_brief:  ContentBrief dataclass from research_synth.synthesize()
        issue_number:    Optional issue number for labeling
    """
    if niche not in VALID_NICHES:
        raise ValueError(f"Unknown niche: {niche}. Valid: {VALID_NICHES}")
    if platform not in VALID_PLATFORMS:
        raise ValueError(f"Unknown platform: {platform}. Valid: {VALID_PLATFORMS}")

    # Resolve topic and brief summary
    brief_summary = ""
    key_facts: list[str] = []

    if research_brief is not None:
        topic = topic or getattr(research_brief, "primary_angle", topic)
        brief_summary = getattr(research_brief, "source_summary", "")
        key_facts = getattr(research_brief, "key_facts", [])
    elif text:
        # Use provided text as context
        brief_summary = text[:500]
        topic = topic or text.split(".")[0][:80]

    topic = topic or "what nobody tells you"

    # Draft sections
    hook_text = _draft_hook(niche, topic, brief_summary)
    hook_section = NewsletterSection("hook", hook_text)
    body_sections = _draft_body(niche, topic, brief_summary, key_facts)
    cta_section = _draft_cta(niche)
    all_sections = [hook_section] + body_sections + [cta_section]

    # Assemble full text
    full_text = _assemble_full_text(hook_text, body_sections, cta_section)
    word_count = len(full_text.split())

    # Subject lines + preview
    subject_lines = _generate_subject_lines(niche, topic, brief_summary)
    preview_text = _generate_preview(niche, topic, hook_text)

    # Voice pre-check
    voice_check = _pre_check_voice(niche, full_text)

    # Platform payload
    primary_subject = subject_lines[0].text if subject_lines else topic
    if platform == "substack":
        platform_payload, _ = _build_substack_markdown(
            niche, primary_subject, preview_text, full_text, issue_number
        )
    elif platform == "convertkit":
        platform_payload = _build_convertkit_payload(niche, primary_subject, preview_text, full_text)
    elif platform == "beehiiv":
        platform_payload = _build_beehiiv_payload(niche, primary_subject, preview_text, full_text)
    elif platform == "contentstudio":
        platform_payload = _build_contentstudio_payload(niche, primary_subject, preview_text, full_text)
    else:
        platform_payload = {}

    draft = NewsletterDraft(
        niche=niche,
        platform=platform,
        subject_lines=subject_lines,
        preview_text=preview_text,
        sections=all_sections,
        full_text=full_text,
        word_count=word_count,
        voice_check=voice_check,
        platform_payload=platform_payload,
        issue_number=issue_number,
    )
    draft.report = _build_report(draft)
    return draft


# ── File output ───────────────────────────────────────────────────────────────

def save_draft(draft: "NewsletterDraft", output_dir: Path = Path("output")) -> str:
    """Save draft to appropriate file. Returns path string."""
    output_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    base = f"newsletter_{draft.niche}_{date_str}"

    if draft.platform == "substack":
        # Save the markdown body
        md_text = draft.platform_payload.get("body_markdown", draft.full_text)
        path = output_dir / f"{base}.md"
        path.write_text(md_text, encoding="utf-8")
    else:
        # Save JSON payload
        path = output_dir / f"{base}_{draft.platform}.json"
        path.write_text(
            json.dumps(draft.platform_payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    return str(path)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Draft newsletter issues with niche voice + platform exports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python newsletter_writer.py --niche ttbp --topic "why most people plateau at middle management" --platform substack
  python newsletter_writer.py --niche tundexai --text "GPT-4o vs Claude 3.5 Sonnet benchmarks show..." --platform beehiiv
  python newsletter_writer.py --niche cb --topic "Chinua Achebe and the African canon" --platform convertkit --issue 12
  python newsletter_writer.py --niche ttbp --topic "..." --platform contentstudio --json
        """
    )
    parser.add_argument("--niche", required=True, choices=VALID_NICHES)
    parser.add_argument("--platform", required=True, choices=VALID_PLATFORMS)
    parser.add_argument("--topic", type=str, default="", help="Topic or angle for the issue")
    parser.add_argument("--text", type=str, default="", help="Raw notes or context text")
    parser.add_argument("--brief", type=Path, help="Path to research brief JSON (from research_synth.py --json)")
    parser.add_argument("--issue", type=int, default=0, help="Issue number (optional)")
    parser.add_argument("--json", action="store_true", help="Output full JSON to stdout")
    parser.add_argument("--no-save", action="store_true", help="Skip saving output file")
    parser.add_argument("--draft-only", action="store_true", help="Print draft text only (no report)")

    args = parser.parse_args()

    # Load brief if provided
    research_brief = None
    if args.brief:
        if not args.brief.exists():
            print(f"Error: Brief file not found: {args.brief}", file=sys.stderr)
            sys.exit(1)
        brief_data = json.loads(args.brief.read_text(encoding="utf-8"))

        # Create a simple object from the JSON
        class SimpleBrief:
            pass
        research_brief = SimpleBrief()
        for k, v in brief_data.items():
            setattr(research_brief, k, v)

    draft = draft_newsletter(
        niche=args.niche,
        platform=args.platform,
        topic=args.topic,
        text=args.text,
        research_brief=research_brief,
        issue_number=args.issue,
    )

    # Save file
    if not args.no_save:
        output_path = save_draft(draft)
        draft.output_path = output_path

    # Output
    if args.json:
        # Serialize dataclass to dict for JSON (custom handler for nested dataclasses)
        def _to_dict(obj):
            if hasattr(obj, "__dataclass_fields__"):
                return {k: _to_dict(v) for k, v in asdict(obj).items()}
            return obj
        print(json.dumps(asdict(draft), indent=2, default=str))
    elif args.draft_only:
        print(draft.full_text)
    else:
        print(draft.report)
        print()
        print("═" * 45)
        print("FULL DRAFT")
        print("═" * 45)
        print(draft.full_text)
        if not args.no_save:
            print(f"\n📁 Saved to: {draft.output_path}")

    # Exit codes
    if draft.voice_check.verdict == "PASS":
        sys.exit(0)
    elif draft.voice_check.verdict == "REVISE":
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == "__main__":
    main()

"""
seo_optimizer.py — SEO Analyzer and Meta Generator
Part of the Social Media Engine skill stack.

Usage:
    python seo_optimizer.py --niche tundexai --file post.md
    python seo_optimizer.py --niche ttbp --text "content here"
    python seo_optimizer.py --niche cb --file post.md --meta-only
    python seo_optimizer.py --niche tundexai --file post.md --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional


# ─── Constants ───────────────────────────────────────────────────────────────

VALID_NICHES = {"ttbp", "cb", "tundexai", "wellwithtunde", "tundestalksmen"}

META_TITLE_MIN = 50
META_TITLE_MAX = 60
META_DESC_MIN = 140
META_DESC_MAX = 160
KEYWORD_DENSITY_MIN = 0.005   # 0.5%
KEYWORD_DENSITY_MAX = 0.020   # 2.0%
MAX_AVG_SENTENCE_WORDS = 25
SUBHEADING_INTERVAL_MAX = 250  # words between subheadings


# ─── Niche SEO Configuration ─────────────────────────────────────────────────

NICHE_SEO_CONFIG: dict[str, dict] = {
    "ttbp": {
        "name": "The Tunde Gbotosho Post",
        "min_word_count": 800,
        "primary_keyword_type": "career_leadership_concepts",
        "topic_cluster": [
            "leadership", "management", "career growth", "middle management",
            "promotion", "corporate", "executive", "strategy", "influence",
            "organizational dynamics", "workplace", "professional development",
        ],
        "semantic_variants": {
            "leadership": ["leading", "lead", "leader", "leaders"],
            "management": ["manager", "managers", "managing", "managed"],
            "career growth": ["career advancement", "career development", "career path"],
            "promotion": ["promoted", "promotable", "advancing"],
        },
        "platform_min": {"blog": 800, "linkedin_article": 700, "newsletter": 500},
        "meta_tone": "direct_personal",
        "stop_words_for_keywords": [
            "the", "a", "an", "is", "it", "in", "on", "at", "to", "for",
            "of", "and", "or", "but", "with", "this", "that", "they",
        ],
    },
    "cb": {
        "name": "Connecting Bridges",
        "min_word_count": 600,
        "primary_keyword_type": "author_book_literary_movement",
        "topic_cluster": [
            "African literature", "Chinua Achebe", "Wole Soyinka", "Ngugi wa Thiong'o",
            "African fiction", "postcolonial", "decolonizing", "African authors",
            "Nigerian literature", "publishing", "cultural commentary", "book review",
            "literary criticism", "African diaspora", "African identity",
        ],
        "semantic_variants": {
            "African literature": ["African fiction", "African writing", "African novels"],
            "postcolonial": ["post-colonial", "decolonial", "decolonizing"],
            "publishing": ["published", "publisher", "book", "books"],
        },
        "platform_min": {"blog": 600, "linkedin_article": 500, "newsletter": 400},
        "meta_tone": "cultural_literary",
        "stop_words_for_keywords": [
            "the", "a", "an", "is", "it", "in", "on", "at", "to", "for",
            "of", "and", "or", "but", "with", "this", "that", "they",
        ],
    },
    "tundexai": {
        "name": "TundeXAI",
        "min_word_count": 900,
        "primary_keyword_type": "ai_tool_benchmark_framework",
        "topic_cluster": [
            "AI strategy", "artificial intelligence", "LLM", "large language models",
            "ChatGPT", "Claude", "enterprise AI", "AI automation", "AI tools",
            "machine learning", "AI benchmarks", "prompt engineering", "AI agents",
            "AI implementation", "AI ROI", "generative AI", "foundation models",
        ],
        "semantic_variants": {
            "AI strategy": ["AI roadmap", "AI planning", "AI adoption"],
            "LLM": ["large language model", "language model", "GPT", "foundation model"],
            "enterprise AI": ["business AI", "corporate AI", "AI for business"],
            "automation": ["automated", "automate", "automating"],
        },
        "platform_min": {"blog": 900, "linkedin_article": 800, "newsletter": 600},
        "meta_tone": "analytical_direct",
        "stop_words_for_keywords": [
            "the", "a", "an", "is", "it", "in", "on", "at", "to", "for",
            "of", "and", "or", "but", "with", "this", "that", "they",
        ],
    },
    "wellwithtunde": {
        "name": "Well With Tunde",
        "min_word_count": 600,
        "primary_keyword_type": "health_body_habit",
        "topic_cluster": [
            "holistic health", "sustainable wellness", "body awareness", "habit formation",
            "nutrition", "movement", "sleep", "stress", "chronic disease prevention",
            "mindfulness", "body connection", "wellness practice", "lifestyle",
            "mental health", "physical health", "burnout", "energy",
        ],
        "semantic_variants": {
            "holistic health": ["whole-body health", "integrated wellness", "holistic wellness"],
            "habit formation": ["building habits", "habit change", "daily habits", "routines"],
            "mindfulness": ["mindful", "awareness", "presence", "conscious"],
        },
        "platform_min": {"blog": 600, "linkedin_article": 500, "newsletter": 400},
        "meta_tone": "warm_approachable",
        "stop_words_for_keywords": [
            "the", "a", "an", "is", "it", "in", "on", "at", "to", "for",
            "of", "and", "or", "but", "with", "this", "that", "they",
        ],
    },
    "tundestalksmen": {
        "name": "Tunde Talks Men",
        "min_word_count": 700,
        "primary_keyword_type": "mens_development_accountability",
        "topic_cluster": [
            "men's growth", "men's mental health", "accountability", "masculinity",
            "fatherhood", "relationships", "men's community", "purpose",
            "men's vulnerability", "integrity", "brotherhood", "men's leadership",
            "identity", "strength", "emotional intelligence for men",
        ],
        "semantic_variants": {
            "accountability": ["accountable", "responsibility", "owning it"],
            "masculinity": ["masculine", "manhood", "being a man"],
            "fatherhood": ["father", "dad", "parenting", "raising kids"],
        },
        "platform_min": {"blog": 700, "linkedin_article": 600, "newsletter": 450},
        "meta_tone": "direct_accountable",
        "stop_words_for_keywords": [
            "the", "a", "an", "is", "it", "in", "on", "at", "to", "for",
            "of", "and", "or", "but", "with", "this", "that", "they",
        ],
    },
}


# ─── Dataclasses ─────────────────────────────────────────────────────────────

@dataclass
class HeadingAnalysis:
    h1_count: int
    h2_count: int
    h3_count: int
    h1_texts: list[str]
    h2_texts: list[str]
    h3_texts: list[str]
    hierarchy_issues: list[str]
    primary_keyword_in_heading: bool
    score: int  # 0–100


@dataclass
class MetaTags:
    title: str
    title_char_count: int
    title_ok: bool
    description: str
    description_char_count: int
    description_ok: bool
    primary_keyword_in_title: bool
    primary_keyword_in_description: bool
    score: int  # 0–100


@dataclass
class KeywordReport:
    primary_keyword: str
    primary_in_first_100_words: bool
    primary_density: float
    density_ok: bool
    secondary_keywords: list[str]
    secondary_found: list[str]
    secondary_missing: list[str]
    semantic_variants_found: list[str]
    score: int  # 0–100


@dataclass
class ReadabilityReport:
    word_count: int
    sentence_count: int
    avg_sentence_words: float
    paragraph_count: int
    avg_paragraph_sentences: float
    subheading_density: float  # words per subheading
    long_sentence_count: int  # sentences > 30 words
    score: int  # 0–100
    issues: list[str]


@dataclass
class SEOReport:
    niche: str
    platform: str
    content_preview: str  # first 80 chars of title or content
    word_count: int
    word_count_ok: bool
    primary_keyword: str
    meta: MetaTags
    headings: HeadingAnalysis
    keywords: KeywordReport
    readability: ReadabilityReport
    recommendations: list[str]
    score: int  # 0–100 composite
    verdict: str  # OPTIMIZED / GOOD / NEEDS WORK / WEAK
    generated_at: str
    report: str  # formatted text report


# ─── Keyword Extraction ───────────────────────────────────────────────────────

def _extract_primary_keyword(content: str, niche: str, title: str = "") -> str:
    """
    Extract the most likely primary keyword from content.
    Priority: title noun phrases > first paragraph noun phrases > topic cluster matches.
    """
    config = NICHE_SEO_CONFIG[niche]
    stop_words = set(config["stop_words_for_keywords"])
    cluster = config["topic_cluster"]

    # Check if any cluster term appears in the title or first 200 chars
    search_text = (title + " " + content[:200]).lower()
    for term in cluster:
        if term.lower() in search_text:
            return term

    # Fall back to most frequent non-stop 2-gram in first 300 words
    words = re.findall(r'\b[a-zA-Z]{3,}\b', content[:1500].lower())
    filtered = [w for w in words if w not in stop_words]

    bigram_freq: dict[str, int] = {}
    for i in range(len(filtered) - 1):
        bg = f"{filtered[i]} {filtered[i+1]}"
        bigram_freq[bg] = bigram_freq.get(bg, 0) + 1

    if bigram_freq:
        return max(bigram_freq, key=lambda k: bigram_freq[k])

    # Fall back to most frequent single word
    word_freq: dict[str, int] = {}
    for w in filtered:
        word_freq[w] = word_freq.get(w, 0) + 1
    if word_freq:
        return max(word_freq, key=lambda k: word_freq[k])

    return cluster[0]  # default to first cluster term


def _extract_secondary_keywords(content: str, niche: str, primary: str) -> list[str]:
    """Return cluster keywords found in content, excluding primary."""
    config = NICHE_SEO_CONFIG[niche]
    content_lower = content.lower()
    found = []
    for term in config["topic_cluster"]:
        if term.lower() == primary.lower():
            continue
        if term.lower() in content_lower:
            found.append(term)
    return found


def _find_missing_secondary(config: dict, primary: str, found: list[str]) -> list[str]:
    """Return cluster terms not found in content (up to 5 suggestions)."""
    found_lower = {t.lower() for t in found}
    missing = []
    for term in config["topic_cluster"]:
        if term.lower() == primary.lower():
            continue
        if term.lower() not in found_lower:
            missing.append(term)
        if len(missing) >= 5:
            break
    return missing


def _find_semantic_variants(content: str, niche: str, primary: str) -> list[str]:
    """Check if semantic variants of primary keyword appear in content."""
    config = NICHE_SEO_CONFIG[niche]
    variants_map = config.get("semantic_variants", {})
    found = []
    content_lower = content.lower()
    # Check variants for primary keyword
    for base_term, variants in variants_map.items():
        if base_term.lower() in primary.lower() or primary.lower() in base_term.lower():
            for v in variants:
                if v.lower() in content_lower:
                    found.append(v)
    return found


def _keyword_density(content: str, keyword: str) -> float:
    """Calculate keyword density as a ratio."""
    words = re.findall(r'\b\w+\b', content.lower())
    if not words:
        return 0.0
    keyword_words = keyword.lower().split()
    count = 0
    for i in range(len(words) - len(keyword_words) + 1):
        if words[i:i + len(keyword_words)] == keyword_words:
            count += 1
    return count / len(words)


# ─── Heading Analysis ─────────────────────────────────────────────────────────

def _analyze_headings(content: str, primary_keyword: str) -> HeadingAnalysis:
    """Parse markdown headings and score their SEO quality."""
    h1_matches = re.findall(r'^#\s+(.+)', content, re.MULTILINE)
    h2_matches = re.findall(r'^##\s+(.+)', content, re.MULTILINE)
    h3_matches = re.findall(r'^###\s+(.+)', content, re.MULTILINE)

    # Also check HTML-style headings
    h1_html = re.findall(r'<h1[^>]*>(.+?)</h1>', content, re.IGNORECASE)
    h2_html = re.findall(r'<h2[^>]*>(.+?)</h2>', content, re.IGNORECASE)
    h3_html = re.findall(r'<h3[^>]*>(.+?)</h3>', content, re.IGNORECASE)

    h1_texts = h1_matches + h1_html
    h2_texts = h2_matches + h2_html
    h3_texts = h3_matches + h3_html

    issues = []
    score = 100

    # H1 checks
    if len(h1_texts) == 0:
        issues.append("No H1 found — add one as the article title")
        score -= 25
    elif len(h1_texts) > 1:
        issues.append(f"Multiple H1s ({len(h1_texts)}) — keep only one")
        score -= 15

    # H2 checks
    if len(h2_texts) == 0:
        issues.append("No H2 headings — add section headings for structure")
        score -= 20

    # H3 present if content is long
    words = re.findall(r'\b\w+\b', content)
    if len(words) > 900 and len(h3_texts) == 0:
        issues.append("Long content without H3s — consider adding subsection headings")
        score -= 10

    # Primary keyword in a heading
    all_headings_text = " ".join(h1_texts + h2_texts + h3_texts).lower()
    kw_lower = primary_keyword.lower()
    kw_words = kw_lower.split()
    kw_in_headings = all(w in all_headings_text for w in kw_words)

    if not kw_in_headings:
        issues.append(f'Primary keyword "{primary_keyword}" not found in any heading')
        score -= 15

    score = max(0, score)

    return HeadingAnalysis(
        h1_count=len(h1_texts),
        h2_count=len(h2_texts),
        h3_count=len(h3_texts),
        h1_texts=h1_texts,
        h2_texts=h2_texts,
        h3_texts=h3_texts,
        hierarchy_issues=issues,
        primary_keyword_in_heading=kw_in_headings,
        score=score,
    )


# ─── Meta Tag Generation ─────────────────────────────────────────────────────

def _generate_meta_title(niche: str, primary_keyword: str, content: str, h1_texts: list[str]) -> str:
    """
    Generate an SEO-optimized meta title.
    Priority: clean the H1 if it exists, else craft from primary keyword + hook phrase.
    """
    config = NICHE_SEO_CONFIG[niche]
    meta_tone = config["meta_tone"]

    # Use H1 as base if it exists and contains primary keyword
    if h1_texts:
        candidate = h1_texts[0].strip()
        if primary_keyword.lower() in candidate.lower():
            # Trim to fit 60 chars
            if len(candidate) <= META_TITLE_MAX:
                return candidate
            # Truncate at word boundary
            words = candidate.split()
            trimmed = ""
            for w in words:
                if len(trimmed) + len(w) + 1 <= META_TITLE_MAX - 3:
                    trimmed += (" " + w if trimmed else w)
                else:
                    break
            return trimmed + "..."

    # Craft meta title from primary keyword based on niche tone
    kw_cap = primary_keyword.title()
    tone_templates = {
        "direct_personal": [
            f"The Real Truth About {kw_cap}",
            f"{kw_cap}: What Nobody Tells You",
            f"Why Most People Get {kw_cap} Wrong",
        ],
        "cultural_literary": [
            f"{kw_cap}: A New Way to Read It",
            f"Understanding {kw_cap} Beyond the Syllabus",
            f"{kw_cap} and What It Means Now",
        ],
        "analytical_direct": [
            f"{kw_cap}: The Honest Breakdown",
            f"What the Data Says About {kw_cap}",
            f"{kw_cap} Explained for Practitioners",
        ],
        "warm_approachable": [
            f"A Gentler Approach to {kw_cap}",
            f"{kw_cap}: Start Here, Not There",
            f"How to Actually Sustain {kw_cap}",
        ],
        "direct_accountable": [
            f"{kw_cap}: The Conversation Men Avoid",
            f"What {kw_cap} Actually Requires",
            f"The {kw_cap} Problem Nobody Names",
        ],
    }

    templates = tone_templates.get(meta_tone, tone_templates["analytical_direct"])
    for candidate in templates:
        if META_TITLE_MIN <= len(candidate) <= META_TITLE_MAX:
            return candidate

    # Fallback: primary keyword padded with power word
    return f"{kw_cap} — The Complete Guide"[:META_TITLE_MAX]


def _generate_meta_description(
    niche: str, primary_keyword: str, content: str
) -> str:
    """
    Generate a 140–160 char meta description.
    Pulls from the first substantive paragraph that contains the primary keyword.
    """
    # Clean content of headings and markdown
    clean = re.sub(r'^#{1,6}\s+.+', '', content, flags=re.MULTILINE)
    clean = re.sub(r'\*{1,2}(.+?)\*{1,2}', r'\1', clean)
    clean = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', clean)
    clean = re.sub(r'\n{2,}', '\n', clean).strip()

    paragraphs = [p.strip() for p in clean.split('\n') if len(p.strip()) > 60]
    kw_lower = primary_keyword.lower()

    # Find a paragraph containing the keyword
    target_para = None
    for p in paragraphs:
        if kw_lower in p.lower():
            target_para = p
            break

    if not target_para and paragraphs:
        target_para = paragraphs[0]

    if not target_para:
        config = NICHE_SEO_CONFIG[niche]
        return f"Insights on {primary_keyword} from {config['name']}. Practical, evidence-backed, and designed to change how you think."

    # Trim to 155 chars at sentence boundary
    sentences = re.split(r'(?<=[.!?])\s+', target_para)
    desc = ""
    for sentence in sentences:
        if len(desc) + len(sentence) + 1 <= 155:
            desc += (" " + sentence if desc else sentence)
        else:
            break

    if not desc:
        desc = target_para[:152] + "..."

    # Ensure it ends cleanly
    if desc and desc[-1] not in ".!?":
        desc = desc.rstrip(",;:- ") + "."

    return desc


def _build_meta_tags(niche: str, primary_keyword: str, content: str, h1_texts: list[str]) -> MetaTags:
    title = _generate_meta_title(niche, primary_keyword, content, h1_texts)
    description = _generate_meta_description(niche, primary_keyword, content)

    title_ok = META_TITLE_MIN <= len(title) <= META_TITLE_MAX
    desc_ok = META_DESC_MIN <= len(description) <= META_DESC_MAX
    kw_lower = primary_keyword.lower()

    meta_score = 100
    if not title_ok:
        meta_score -= 20
    if not desc_ok:
        meta_score -= 20
    if kw_lower not in title.lower():
        meta_score -= 30
    if kw_lower not in description.lower():
        meta_score -= 15
    meta_score = max(0, meta_score)

    return MetaTags(
        title=title,
        title_char_count=len(title),
        title_ok=title_ok,
        description=description,
        description_char_count=len(description),
        description_ok=desc_ok,
        primary_keyword_in_title=kw_lower in title.lower(),
        primary_keyword_in_description=kw_lower in description.lower(),
        score=meta_score,
    )


# ─── Keyword Report ───────────────────────────────────────────────────────────

def _build_keyword_report(content: str, niche: str, primary_keyword: str) -> KeywordReport:
    config = NICHE_SEO_CONFIG[niche]
    content_lower = content.lower()

    # Primary keyword in first 100 words
    first_100 = " ".join(content.split()[:100]).lower()
    primary_in_first_100 = primary_keyword.lower() in first_100

    # Density
    density = _keyword_density(content, primary_keyword)
    density_ok = KEYWORD_DENSITY_MIN <= density <= KEYWORD_DENSITY_MAX

    # Secondary keywords
    secondary_found = _extract_secondary_keywords(content, niche, primary_keyword)
    secondary_missing = _find_missing_secondary(config, primary_keyword, secondary_found)
    semantic_variants = _find_semantic_variants(content, niche, primary_keyword)

    # Score
    score = 100
    if not primary_in_first_100:
        score -= 20
    if not density_ok:
        if density < KEYWORD_DENSITY_MIN:
            score -= 15
        else:
            score -= 20  # over-stuffed
    if len(secondary_found) < 2:
        score -= 20
    elif len(secondary_found) < 4:
        score -= 10
    score = max(0, score)

    # All secondary from cluster (for report)
    all_secondary = config["topic_cluster"][:8]

    return KeywordReport(
        primary_keyword=primary_keyword,
        primary_in_first_100_words=primary_in_first_100,
        primary_density=round(density, 4),
        density_ok=density_ok,
        secondary_keywords=all_secondary,
        secondary_found=secondary_found,
        secondary_missing=secondary_missing[:4],
        semantic_variants_found=semantic_variants,
        score=score,
    )


# ─── Readability ──────────────────────────────────────────────────────────────

def _analyze_readability(content: str) -> ReadabilityReport:
    # Clean markdown
    clean = re.sub(r'^#{1,6}\s+.+', '', content, flags=re.MULTILINE)
    clean = re.sub(r'\*{1,2}(.+?)\*{1,2}', r'\1', clean)
    clean = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', clean)

    words = re.findall(r'\b\w+\b', clean)
    word_count = len(words)

    # Sentences (rough split)
    sentences = re.split(r'(?<=[.!?])\s+', clean.strip())
    sentences = [s for s in sentences if len(s.strip()) > 10]
    sentence_count = max(len(sentences), 1)
    avg_sentence_words = word_count / sentence_count

    # Long sentences
    long_sentence_count = sum(
        1 for s in sentences if len(re.findall(r'\b\w+\b', s)) > 30
    )

    # Paragraphs
    paragraphs = [p.strip() for p in re.split(r'\n{2,}', clean) if p.strip()]
    paragraph_count = max(len(paragraphs), 1)
    para_sentences = [len(re.split(r'(?<=[.!?])\s+', p)) for p in paragraphs]
    avg_para_sentences = sum(para_sentences) / len(para_sentences) if para_sentences else 0

    # Subheading density: words per subheading
    heading_count = len(re.findall(r'^#{1,3}\s', content, re.MULTILINE))
    heading_count += len(re.findall(r'<h[123]', content, re.IGNORECASE))
    subheading_density = word_count / max(heading_count, 1)

    issues = []
    score = 100

    if avg_sentence_words > MAX_AVG_SENTENCE_WORDS:
        issues.append(f"Avg sentence length {avg_sentence_words:.0f} words (target: under {MAX_AVG_SENTENCE_WORDS})")
        score -= 15

    if long_sentence_count > 3:
        issues.append(f"{long_sentence_count} sentences over 30 words — simplify these")
        score -= 10

    if subheading_density > SUBHEADING_INTERVAL_MAX:
        issues.append(f"Subheadings spaced {subheading_density:.0f} words apart (target: under {SUBHEADING_INTERVAL_MAX})")
        score -= 15

    if avg_para_sentences > 4:
        issues.append(f"Avg paragraph is {avg_para_sentences:.1f} sentences — break up long blocks")
        score -= 10

    score = max(0, score)

    return ReadabilityReport(
        word_count=word_count,
        sentence_count=sentence_count,
        avg_sentence_words=round(avg_sentence_words, 1),
        paragraph_count=paragraph_count,
        avg_paragraph_sentences=round(avg_para_sentences, 1),
        subheading_density=round(subheading_density, 0),
        long_sentence_count=long_sentence_count,
        score=score,
        issues=issues,
    )


# ─── Composite Score + Recommendations ───────────────────────────────────────

def _composite_score(
    meta: MetaTags,
    headings: HeadingAnalysis,
    keywords: KeywordReport,
    readability: ReadabilityReport,
    word_count: int,
    min_word_count: int,
) -> tuple[int, str]:
    """Weight the component scores into a composite SEO score."""
    # Weights
    kw_weight = 0.25
    meta_weight = 0.20
    headings_weight = 0.15
    topical_weight = 0.20
    readability_weight = 0.10
    length_weight = 0.10

    # Topical coverage score based on secondary keywords found
    secondary_count = len(keywords.secondary_found)
    topical_score = min(100, (secondary_count / 6) * 100)

    # Length score
    if word_count >= min_word_count:
        length_score = 100
    elif word_count >= min_word_count * 0.8:
        length_score = 75
    elif word_count >= min_word_count * 0.6:
        length_score = 50
    else:
        length_score = 25

    composite = (
        keywords.score * kw_weight
        + meta.score * meta_weight
        + headings.score * headings_weight
        + topical_score * topical_weight
        + readability.score * readability_weight
        + length_score * length_weight
    )

    score = round(composite)

    if score >= 85:
        verdict = "OPTIMIZED"
    elif score >= 70:
        verdict = "GOOD"
    elif score >= 50:
        verdict = "NEEDS WORK"
    else:
        verdict = "WEAK"

    return score, verdict


def _build_recommendations(
    meta: MetaTags,
    headings: HeadingAnalysis,
    keywords: KeywordReport,
    readability: ReadabilityReport,
    word_count: int,
    min_word_count: int,
) -> list[str]:
    recs = []

    # Meta
    if not meta.primary_keyword_in_title:
        recs.append(f'Add "{keywords.primary_keyword}" to the meta title')
    if not meta.title_ok:
        if meta.title_char_count < META_TITLE_MIN:
            recs.append(f"Meta title is {meta.title_char_count} chars — expand to 50–60 chars")
        else:
            recs.append(f"Meta title is {meta.title_char_count} chars — trim to 60 chars max")
    if not meta.description_ok:
        if meta.description_char_count < META_DESC_MIN:
            recs.append(f"Meta description is {meta.description_char_count} chars — expand to 140–160 chars")
        else:
            recs.append(f"Meta description is {meta.description_char_count} chars — trim to 160 chars max")

    # Headings
    for issue in headings.hierarchy_issues[:2]:
        recs.append(issue)

    # Keywords
    if not keywords.primary_in_first_100_words:
        recs.append(f'Use "{keywords.primary_keyword}" in the first 100 words')
    if not keywords.density_ok:
        if keywords.primary_density < KEYWORD_DENSITY_MIN:
            recs.append(f'Primary keyword density {keywords.primary_density*100:.1f}% — increase to 0.5–2%')
        else:
            recs.append(f'Primary keyword density {keywords.primary_density*100:.1f}% — reduce (over-optimized)')
    if keywords.secondary_missing:
        top = keywords.secondary_missing[:2]
        recs.append(f'Consider adding: {", ".join(top)} (missing from topic cluster)')

    # Readability
    for issue in readability.issues[:2]:
        recs.append(issue)

    # Length
    if word_count < min_word_count:
        recs.append(f"Content is {word_count} words — target minimum is {min_word_count} words for this niche")

    return recs[:7]  # Cap at 7 recommendations


# ─── Report Formatting ────────────────────────────────────────────────────────

def _format_report(
    niche: str,
    platform: str,
    content_preview: str,
    word_count: int,
    word_count_ok: bool,
    meta: MetaTags,
    headings: HeadingAnalysis,
    keywords: KeywordReport,
    readability: ReadabilityReport,
    recommendations: list[str],
    score: int,
    verdict: str,
) -> str:
    config = NICHE_SEO_CONFIG[niche]
    verdict_icon = {"OPTIMIZED": "✅", "GOOD": "✅", "NEEDS WORK": "⚠️", "WEAK": "❌"}.get(verdict, "")
    title_ok_icon = "✅" if meta.title_ok else "❌"
    desc_ok_icon = "✅" if meta.description_ok else "❌"
    kw_in_title_icon = "✅" if meta.primary_keyword_in_title else "❌"
    kw_in_desc_icon = "✅" if meta.primary_keyword_in_description else "❌"
    first100_icon = "✅" if keywords.primary_in_first_100_words else "❌"
    density_icon = "✅" if keywords.density_ok else "❌"
    h1_icon = "✅" if headings.h1_count == 1 else "❌"
    h2_icon = "✅" if headings.h2_count > 0 else "❌"
    h3_icon = "✅" if headings.h3_count > 0 else "~"
    kw_heading_icon = "✅" if headings.primary_keyword_in_heading else "❌"
    length_icon = "✅" if word_count_ok else "❌"
    secondary_found_str = (
        ", ".join(keywords.secondary_found[:5]) if keywords.secondary_found else "None found"
    )
    missing_str = (
        ", ".join(keywords.secondary_missing[:3]) if keywords.secondary_missing else "None"
    )

    recs_text = ""
    for i, rec in enumerate(recommendations, 1):
        recs_text += f"  {i}. {rec}\n"

    heading_issues_text = ""
    for issue in headings.hierarchy_issues:
        heading_issues_text += f"\n  ⚠️  {issue}"
    if not heading_issues_text:
        heading_issues_text = "\n  None"

    h1_display = headings.h1_texts[0][:60] if headings.h1_texts else "Not found"
    h2_display = " | ".join(t[:30] for t in headings.h2_texts[:3]) if headings.h2_texts else "None"
    h3_display = f"{headings.h3_count} found" if headings.h3_count else "None"

    lines = [
        "═══════════════════════════════════════════",
        "SEO REPORT",
        "═══════════════════════════════════════════",
        f"Niche:          {niche}  ({config['name']})",
        f"Platform:       {platform}",
        f"Content:        \"{content_preview}\" ({word_count:,} words)",
        "",
        f"SEO SCORE: {score}/100  {verdict_icon} {verdict}",
        "───────────────────────────────────────────",
        "PRIMARY KEYWORD",
        f"  → \"{keywords.primary_keyword}\"",
        f"  → In first 100 words: {first100_icon}  |  Density: {keywords.primary_density*100:.1f}% {density_icon}",
        "",
        "META TAGS (ready to use)",
        f"  → Title ({meta.title_char_count} chars) {title_ok_icon}: {meta.title}",
        f"    Keyword in title: {kw_in_title_icon}",
        f"  → Description ({meta.description_char_count} chars) {desc_ok_icon}:",
        f"    {meta.description[:80]}",
        f"    {meta.description[80:160] if len(meta.description) > 80 else ''}",
        f"    Keyword in description: {kw_in_desc_icon}",
        "",
        "HEADING HIERARCHY",
        f"  → H1 ({headings.h1_count}) {h1_icon}: {h1_display}",
        f"  → H2 ({headings.h2_count}) {h2_icon}: {h2_display}",
        f"  → H3 ({headings.h3_count}) {h3_icon}: {h3_display}",
        f"  → Primary keyword in headings: {kw_heading_icon}",
        f"  → Issues: {heading_issues_text}",
        "",
        "KEYWORD CLUSTER",
        f"  Primary:    {keywords.primary_keyword}",
        f"  Secondary:  {secondary_found_str}",
        f"  Missing:    {missing_str}",
        f"  Semantic variants found: {', '.join(keywords.semantic_variants_found) if keywords.semantic_variants_found else 'None'}",
        "",
        "READABILITY",
        f"  → Avg sentence: {readability.avg_sentence_words:.0f} words {'✅' if readability.avg_sentence_words <= MAX_AVG_SENTENCE_WORDS else '❌'}",
        f"  → Subheading every: {readability.subheading_density:.0f} words {'✅' if readability.subheading_density <= SUBHEADING_INTERVAL_MAX else '❌'}",
        f"  → Avg paragraph: {readability.avg_paragraph_sentences:.1f} sentences {'✅' if readability.avg_paragraph_sentences <= 4 else '❌'}",
        f"  → Long sentences (>30 words): {readability.long_sentence_count}",
        "",
        f"CONTENT LENGTH: {word_count:,} words {length_icon}",
        "",
    ]

    if recommendations:
        lines += [
            f"RECOMMENDATIONS ({len(recommendations)})",
            recs_text.rstrip(),
        ]

    lines += ["═══════════════════════════════════════════"]
    return "\n".join(lines)


# ─── Main Entry Point ─────────────────────────────────────────────────────────

def analyze_seo(
    niche: str,
    content: str,
    platform: str = "blog",
    title: str = "",
) -> SEOReport:
    """
    Full SEO analysis of content for a given niche and platform.

    Args:
        niche: One of ttbp / cb / tundexai / wellwithtunde / tundestalksmen
        content: The full content text (markdown or plain)
        platform: blog | linkedin_article | newsletter
        title: Optional explicit title (otherwise extracted from H1 or content)

    Returns:
        SEOReport dataclass with all scores and generated meta tags
    """
    if niche not in VALID_NICHES:
        raise ValueError(f"Unknown niche '{niche}'. Valid: {VALID_NICHES}")

    config = NICHE_SEO_CONFIG[niche]
    min_word_count = config["platform_min"].get(platform, config["min_word_count"])

    # Word count
    words = re.findall(r'\b\w+\b', content)
    word_count = len(words)
    word_count_ok = word_count >= min_word_count

    # Content preview
    if title:
        content_preview = title[:80]
    else:
        # Try to extract from H1
        h1_match = re.search(r'^#\s+(.+)', content, re.MULTILINE)
        content_preview = (h1_match.group(1) if h1_match else content[:80]).strip()

    # Primary keyword
    primary_keyword = _extract_primary_keyword(content, niche, title or content_preview)

    # Build component reports
    headings = _analyze_headings(content, primary_keyword)
    meta = _build_meta_tags(niche, primary_keyword, content, headings.h1_texts)
    keywords = _build_keyword_report(content, niche, primary_keyword)
    readability = _analyze_readability(content)

    # Composite score
    score, verdict = _composite_score(
        meta, headings, keywords, readability, word_count, min_word_count
    )

    recommendations = _build_recommendations(
        meta, headings, keywords, readability, word_count, min_word_count
    )

    report_text = _format_report(
        niche=niche,
        platform=platform,
        content_preview=content_preview[:60],
        word_count=word_count,
        word_count_ok=word_count_ok,
        meta=meta,
        headings=headings,
        keywords=keywords,
        readability=readability,
        recommendations=recommendations,
        score=score,
        verdict=verdict,
    )

    return SEOReport(
        niche=niche,
        platform=platform,
        content_preview=content_preview[:60],
        word_count=word_count,
        word_count_ok=word_count_ok,
        primary_keyword=primary_keyword,
        meta=meta,
        headings=headings,
        keywords=keywords,
        readability=readability,
        recommendations=recommendations,
        score=score,
        verdict=verdict,
        generated_at=datetime.now().isoformat(),
        report=report_text,
    )


def generate_meta(niche: str, content: str, title: str = "") -> dict:
    """Fast mode: return only meta title + description without full analysis."""
    if niche not in VALID_NICHES:
        raise ValueError(f"Unknown niche '{niche}'. Valid: {VALID_NICHES}")

    primary_keyword = _extract_primary_keyword(content, niche, title)
    headings = _analyze_headings(content, primary_keyword)
    meta = _build_meta_tags(niche, primary_keyword, content, headings.h1_texts)

    return {
        "primary_keyword": primary_keyword,
        "meta_title": meta.title,
        "meta_title_chars": meta.title_char_count,
        "meta_description": meta.description,
        "meta_description_chars": meta.description_char_count,
    }


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="SEO Optimizer — analyze and optimize content for search"
    )
    parser.add_argument(
        "--niche", required=True,
        choices=list(VALID_NICHES),
        help="Content niche"
    )
    parser.add_argument("--file", help="Path to content file (.md or .txt)")
    parser.add_argument("--text", help="Raw content text")
    parser.add_argument(
        "--platform",
        default="blog",
        choices=["blog", "linkedin_article", "newsletter"],
        help="Target platform (default: blog)"
    )
    parser.add_argument("--title", default="", help="Explicit title override")
    parser.add_argument(
        "--meta-only",
        action="store_true",
        help="Fast mode: output meta tags only"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output full SEO report as JSON"
    )
    args = parser.parse_args()

    # Load content
    if args.file:
        content = Path(args.file).read_text(encoding="utf-8")
    elif args.text:
        content = args.text
    else:
        print("Error: provide --file or --text", file=sys.stderr)
        sys.exit(1)

    if not content.strip():
        print("Error: content is empty", file=sys.stderr)
        sys.exit(1)

    # Meta-only fast mode
    if args.meta_only:
        result = generate_meta(args.niche, content, args.title)
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"Primary keyword:   {result['primary_keyword']}")
            print(f"Meta title ({result['meta_title_chars']} chars): {result['meta_title']}")
            print(f"Meta desc ({result['meta_description_chars']} chars):  {result['meta_description']}")
        sys.exit(0)

    # Full analysis
    report = analyze_seo(
        niche=args.niche,
        content=content,
        platform=args.platform,
        title=args.title,
    )

    if args.json:
        print(json.dumps(asdict(report), indent=2, ensure_ascii=False))
        sys.exit(0)

    print(report.report)

    # Exit code based on verdict
    exit_codes = {"OPTIMIZED": 0, "GOOD": 0, "NEEDS WORK": 1, "WEAK": 2}
    sys.exit(exit_codes.get(report.verdict, 1))


if __name__ == "__main__":
    main()

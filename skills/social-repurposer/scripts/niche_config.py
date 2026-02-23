"""
niche_config.py — Per-niche brand configuration for the Content Empire.
Returns brand colors, primary audience, voice calibration notes, hashtag pools,
and Voice DNA file paths for each niche.

Usage:
    from niche_config import get_niche_config, VALID_NICHES
    cfg = get_niche_config("ttbp")
"""

from pathlib import Path

VALID_NICHES = ["ttbp", "cb", "tundexai", "wellwithtunde", "tundestalksmen"]

# Base path where Voice DNA prompt files live
VOICE_DNA_BASE = Path.home() / "prompts" / "voice"

NICHE_CONFIG = {
    "ttbp": {
        "display_name": "That's The Business Podcast / Tunde Gbotosho",
        "brand_colors": {"primary": "#C9A84C", "secondary": "#1A1A1A"},  # Gold + Black
        "primary_audience": "Mid-career professionals, MBA types, executives in transition",
        "voice_calibration": (
            "Direct, data-informed, opens with personal story. "
            "Bridges stats and lived experience. Never corporate-speak."
        ),
        "content_pillars": ["AI & Future of Work", "Career Strategy", "Leadership", "Entrepreneurship"],
        "hashtags": {
            "linkedin": ["#AI", "#FutureOfWork", "#CareerStrategy", "#Leadership", "#Entrepreneurship",
                         "#ProfessionalDevelopment", "#CareerGrowth", "#ThatsTheBusiness"],
            "instagram": ["#AI", "#CareerAdvice", "#FutureOfWork", "#MBAlife", "#BlackExcellence",
                          "#CareerGoals", "#Leadership", "#ThatsTheBusiness", "#NigerianAmerican",
                          "#ProfessionalGrowth", "#TechCareer", "#CareerCoach", "#Hustle", "#Success"],
            "twitter": ["#AI", "#FutureOfWork", "#CareerStrategy"],
            "facebook": ["#AI", "#CareerGrowth", "#FutureOfWork"],
        },
        "contentstudio_workspace": "ttbp",
        "voice_dna_file": VOICE_DNA_BASE / "ttbp_voice_dna.md",
        "newsletter_name": "That's The Business",
        "posting_handle": "@tundegbotosho",
    },
    "cb": {
        "display_name": "Connecting Bridges Publishing",
        "brand_colors": {"primary": "#2D5016", "secondary": "#F5F0E8"},  # Deep Green + Cream
        "primary_audience": "Book lovers, educators, Nigerian diaspora, cultural creatives",
        "voice_calibration": (
            "Literary, warm, rooted in cultural pride. Author voice: educational satire, "
            "accessible depth. Celebrates Nigerian-American identity."
        ),
        "content_pillars": ["African Literature", "Diaspora Identity", "Publishing Industry", "Cultural Commentary"],
        "hashtags": {
            "linkedin": ["#Books", "#Publishing", "#AfricanLiterature", "#Diaspora", "#NigerianAuthors",
                         "#ConnectingBridges"],
            "instagram": ["#Books", "#BookLovers", "#AfricanLit", "#Diaspora", "#NigerianAuthors",
                          "#BookCommunity", "#Reading", "#BlackAuthors", "#ConnectingBridges",
                          "#BookstagramAfrica", "#NigerianWriter", "#CulturalCommentary"],
            "twitter": ["#Books", "#Diaspora", "#NigerianAuthors"],
            "facebook": ["#Books", "#AfricanLiterature", "#Publishing"],
        },
        "contentstudio_workspace": "cb",
        "voice_dna_file": VOICE_DNA_BASE / "cb_voice_dna.md",
        "newsletter_name": "Bridges & Books",
        "posting_handle": "@connectingbridgespub",
    },
    "tundexai": {
        "display_name": "TundeXAI — AI Consulting",
        "brand_colors": {"primary": "#0066FF", "secondary": "#FFFFFF"},  # Electric Blue + White
        "primary_audience": "Tech founders, AI practitioners, product builders, startup ecosystem",
        "voice_calibration": (
            "Sharp, technically accessible, often contrarian. "
            "Makes complex AI simple without dumbing it down. Hot takes backed by data."
        ),
        "content_pillars": ["AI Tools & Frameworks", "Startup Strategy", "Build in Public", "AI Policy"],
        "hashtags": {
            "linkedin": ["#AI", "#MachineLearning", "#AItools", "#Startups", "#BuildInPublic",
                         "#AIstrategy", "#TechLeadership", "#TundeXAI"],
            "instagram": ["#AI", "#MachineLearning", "#Startups", "#BuildInPublic", "#TechFounders",
                          "#AItools", "#DeepLearning", "#LLM", "#TundeXAI", "#TechAfrica",
                          "#AIcommunity", "#OpenAI", "#Anthropic"],
            "twitter": ["#AI", "#BuildInPublic", "#AItools"],
            "facebook": ["#AI", "#Startups", "#TechCommunity"],
        },
        "contentstudio_workspace": "tundexai",
        "voice_dna_file": VOICE_DNA_BASE / "tundexai_voice_dna.md",
        "newsletter_name": "TundeXAI Weekly",
        "posting_handle": "@tundexai",
    },
    "wellwithtunde": {
        "display_name": "Well With Tunde — Holistic Wellness",
        "brand_colors": {"primary": "#C4714B", "secondary": "#7A9E7E"},  # Warm Terracotta + Sage
        "primary_audience": "Health-conscious professionals 30s–50s, men and women in burnout recovery",
        "voice_calibration": (
            "Holistic, encouraging, science-rooted but never clinical. "
            "Normalizes men's wellness conversations. Warm and practical."
        ),
        "content_pillars": ["Men's Health", "Mind-Body Connection", "Nutrition", "Sleep & Recovery"],
        "hashtags": {
            "linkedin": ["#Wellness", "#MensHealth", "#WorkLifeBalance", "#MindBody", "#WellWithTunde"],
            "instagram": ["#Wellness", "#MensHealth", "#HolisticHealth", "#MindBody", "#HealthyLiving",
                          "#WellnessJourney", "#SelfCare", "#MentalHealth", "#WellWithTunde",
                          "#HealthyMindset", "#FunctionalMedicine", "#NaturalHealth"],
            "twitter": ["#Wellness", "#MensHealth", "#MindBody"],
            "facebook": ["#Wellness", "#HealthyLiving", "#MensHealth"],
        },
        "contentstudio_workspace": "wellwithtunde",
        "voice_dna_file": VOICE_DNA_BASE / "wellwithtunde_voice_dna.md",
        "newsletter_name": "Well With Tunde",
        "posting_handle": "@wellwithtunde",
    },
    "tundestalksmen": {
        "display_name": "Tunde Talks Men — Men in Transition",
        "brand_colors": {"primary": "#1B2A4A", "secondary": "#C9A84C"},  # Navy + Gold
        "primary_audience": "Men in transition, fathers, faith-curious men 30s–50s",
        "voice_calibration": (
            "Grounded, honest, masculine without bravado. "
            "Biblically rooted but not preachy. Calls men to accountability and growth."
        ),
        "content_pillars": ["Fatherhood", "Faith & Purpose", "Masculinity Redefined", "Men's Rites of Passage"],
        "hashtags": {
            "linkedin": ["#Fatherhood", "#MensLife", "#Leadership", "#Faith", "#TundeTalksMen"],
            "instagram": ["#Fatherhood", "#MensLife", "#Faith", "#ManUp", "#BlackFathers",
                          "#ChristianMen", "#MensMinistry", "#TundeTalksMen", "#Purpose",
                          "#NigerianDad", "#RealMen", "#MentalHealthMen"],
            "twitter": ["#Fatherhood", "#Faith", "#MensLife"],
            "facebook": ["#Fatherhood", "#Faith", "#MensLife"],
        },
        "contentstudio_workspace": "tundestalksmen",
        "voice_dna_file": VOICE_DNA_BASE / "tundestalksmen_voice_dna.md",
        "newsletter_name": "Tunde Talks Men",
        "posting_handle": "@tundestalksmen",
    },
}


def get_niche_config(niche: str) -> dict:
    """Return full configuration dict for the given niche slug."""
    if niche not in NICHE_CONFIG:
        raise ValueError(
            f"Unknown niche '{niche}'. Valid options: {', '.join(VALID_NICHES)}"
        )
    return NICHE_CONFIG[niche]


def get_hashtags(niche: str, platform: str, max_count: int | None = None) -> list[str]:
    """Return platform hashtags for a niche, optionally capped."""
    cfg = get_niche_config(niche)
    tags = cfg["hashtags"].get(platform, cfg["hashtags"].get("instagram", []))
    if max_count:
        tags = tags[:max_count]
    return tags


def list_niches() -> list[str]:
    """Return all valid niche slugs."""
    return VALID_NICHES

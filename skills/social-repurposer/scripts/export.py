"""
export.py — Dual-format output writer for the Content Empire social repurposer.

Writes generated content to:
  1. Markdown files (human review, one file per platform)
  2. ContentStudio bulk import JSON (machine-ready, one file per batch)
  3. Confidence scores JSON (report)

Usage:
    from export import ExportManager
    em = ExportManager(out_dir="./output", niche="ttbp", topic="AI jobs", week="2026-W08")
    em.write_post("linkedin", content_text, confidence=87)
    em.finalize()  # writes bulk_import.json + confidence_scores.json
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from niche_config import get_niche_config
from platform_specs import get_spec


def slugify(text: str) -> str:
    """Convert text to a safe directory slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text[:50]  # cap length


class ExportManager:
    """
    Manages all file output for a single repurpose run.
    One instance per (niche, topic, week) combination.
    """

    def __init__(self, out_dir: str | Path, niche: str, topic: str, week: str):
        self.niche = niche
        self.topic = topic
        self.week = week
        self.cfg = get_niche_config(niche)

        # Build output directory: output/ttbp_ai-jobs_2026-W08/
        topic_slug = slugify(topic)
        run_slug = f"{niche}_{topic_slug}_{week}"
        self.run_dir = Path(out_dir) / run_slug
        self.md_dir = self.run_dir / "markdown"
        self.cs_dir = self.run_dir / "contentstudio"
        self.report_dir = self.run_dir / "report"

        # Create all dirs
        for d in [self.md_dir, self.cs_dir, self.report_dir]:
            d.mkdir(parents=True, exist_ok=True)

        # Accumulate posts for bulk JSON
        self._posts: list[dict] = []
        self._confidence_scores: dict[str, dict] = {}
        self._generated_at = datetime.now(timezone.utc).isoformat()

    def write_post(
        self,
        platform: str,
        content: str,
        confidence: int = 75,
        post_type: Optional[str] = None,
        media_type: Optional[str] = None,
        scheduled_time: Optional[str] = None,
    ) -> Path:
        """
        Write a single platform post to Markdown and add to ContentStudio queue.
        Returns path to the written markdown file.
        """
        spec = get_spec(platform)
        post_type = post_type or spec.post_types[0]
        media_type = media_type or spec.media_types[0]

        # 1. Write Markdown
        md_path = self.md_dir / spec.output_file
        self._write_markdown(md_path, platform, content, confidence)

        # 2. Build ContentStudio post object
        post_id = f"{self.niche}_{self.week.replace('-', '')}_{platform}_{post_type}_01"
        post_obj = {
            "post_id": post_id,
            "platform": spec.contentstudio_platform,
            "type": post_type,
            "scheduled_time": scheduled_time or self._default_schedule_time(platform),
            "status": "PENDING_REVIEW",
            "confidence": confidence,
            "workspace": self.cfg["contentstudio_workspace"],
            "content": {
                "text": content,
                "hashtags": self._extract_hashtags(content),
                "media_type": media_type,
            },
        }
        self._posts.append(post_obj)

        # 3. Record confidence score
        self._confidence_scores[platform] = {
            "score": confidence,
            "status": self._score_status(confidence),
            "post_id": post_id,
        }

        return md_path

    def write_newsletter(self, subject: str, preview_text: str, body: str, confidence: int = 80) -> Path:
        """Specialized writer for newsletter format."""
        full_content = f"Subject: {subject}\nPreview: {preview_text}\n\n---\n\n{body}"
        return self.write_post("newsletter", full_content, confidence, post_type="newsletter", media_type="none")

    def write_thread(self, tweets: list[str], confidence: int = 80) -> Path:
        """Write a Twitter thread — list of tweet strings."""
        numbered = [f"{i+1}/ {t}" for i, t in enumerate(tweets)]
        thread_text = "\n\n".join(numbered)
        return self.write_post("twitter", thread_text, confidence, post_type="thread")

    def finalize(self) -> dict[str, Path]:
        """
        Write the ContentStudio bulk import JSON and confidence scores report.
        Returns dict of output paths.
        """
        # ContentStudio bulk import
        bulk_payload = {
            "workspace": self.cfg["contentstudio_workspace"],
            "week": self.week,
            "generated_at": self._generated_at,
            "niche": self.niche,
            "topic": self.topic,
            "post_count": len(self._posts),
            "posts": self._posts,
        }
        bulk_path = self.cs_dir / "bulk_import.json"
        bulk_path.write_text(
            json.dumps(bulk_payload, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

        # Confidence scores report
        avg_confidence = (
            sum(v["score"] for v in self._confidence_scores.values()) / len(self._confidence_scores)
            if self._confidence_scores else 0
        )
        report = {
            "run_id": f"{self.niche}_{self.week}",
            "topic": self.topic,
            "niche": self.niche,
            "generated_at": self._generated_at,
            "average_confidence": round(avg_confidence, 1),
            "by_platform": self._confidence_scores,
            "auto_approve_eligible": [
                p for p, v in self._confidence_scores.items() if v["score"] >= 90
            ],
        }
        report_path = self.report_dir / "confidence_scores.json"
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

        # Summary markdown
        summary_path = self.report_dir / "summary.md"
        self._write_summary(summary_path, avg_confidence)

        print(f"\n✅ Export complete: {self.run_dir}")
        print(f"   Posts generated: {len(self._posts)}")
        print(f"   Avg confidence: {avg_confidence:.1f}")
        print(f"   ContentStudio JSON: {bulk_path}")
        print(f"   Review report: {report_path}")

        return {
            "run_dir": self.run_dir,
            "bulk_import": bulk_path,
            "confidence_scores": report_path,
            "summary": summary_path,
        }

    # ── Private helpers ──────────────────────────────────────────────────────

    def _write_markdown(self, path: Path, platform: str, content: str, confidence: int) -> None:
        spec = get_spec(platform)
        status = self._score_status(confidence)
        header = (
            f"# {spec.display_name} — {self.topic}\n"
            f"**Niche:** {self.niche} | **Week:** {self.week} | "
            f"**Confidence:** {confidence}/100 ({status})\n\n"
            f"---\n\n"
        )
        path.write_text(header + content, encoding="utf-8")

    def _extract_hashtags(self, content: str) -> list[str]:
        """Pull hashtags from content string."""
        return re.findall(r"#\w+", content)

    def _default_schedule_time(self, platform: str) -> str:
        """Return a default ISO schedule time for the platform (placeholder)."""
        # This would be replaced by the timing engine in production
        defaults = {
            "linkedin": "T08:00:00-05:00",
            "twitter": "T08:00:00-05:00",
            "instagram": "T12:00:00-05:00",
            "facebook": "T13:00:00-05:00",
            "newsletter": "T07:00:00-05:00",
            "youtube_short": "T15:00:00-05:00",
            "youtube_long": "T15:00:00-05:00",
        }
        # Use Monday of the ISO week as base date (placeholder logic)
        return f"2026-02-16{defaults.get(platform, 'T09:00:00-05:00')}"

    def _score_status(self, score: int) -> str:
        if score >= 90:
            return "AUTO_APPROVE"
        elif score >= 75:
            return "PUBLISH_WITH_REVIEW"
        elif score >= 60:
            return "NEEDS_REVISION"
        return "REGENERATE"

    def _write_summary(self, path: Path, avg_confidence: float) -> None:
        lines = [
            f"# Repurpose Run Summary\n",
            f"**Niche:** {self.niche}  ",
            f"**Topic:** {self.topic}  ",
            f"**Week:** {self.week}  ",
            f"**Generated:** {self._generated_at}  \n",
            f"**Average Confidence:** {avg_confidence:.1f}/100\n",
            f"## Posts by Platform\n",
        ]
        for platform, data in self._confidence_scores.items():
            lines.append(
                f"- **{platform}**: {data['score']}/100 — {data['status']}"
            )
        path.write_text("\n".join(lines), encoding="utf-8")

from __future__ import annotations

import json
import google.generativeai as genai

from app.models import PipelineState
from app.settings import settings
from app.skills.base import Skill


class TimelineBuilderSkill(Skill):
    name = "timeline_builder"

    def run(self, state: PipelineState) -> PipelineState:
        if not settings.google_api_key:
            state.timeline = []
            return state

        note_text = (state.note_text or "").strip()
        if not note_text:
            state.timeline = []
            return state

        prompt = self._build_prompt(note_text)

        try:
            genai.configure(api_key=settings.google_api_key)
            model = genai.GenerativeModel(
                settings.google_model,
                generation_config={"temperature": 0.0, "response_mime_type": "application/json"},
            )
            response = model.generate_content(prompt)

            usage = getattr(response, "usage_metadata", None)
            if usage is not None:
                state.token_usage["prompt"] += int(getattr(usage, "prompt_token_count", 0) or 0)
                state.token_usage["output"] += int(getattr(usage, "candidates_token_count", 0) or 0)
                state.token_usage["total"] += int(getattr(usage, "total_token_count", 0) or 0)

            payload = json.loads((response.text or "{}").strip())
            raw_timeline = payload.get("timeline", []) if isinstance(payload, dict) else []
            state.timeline = self._sanitize_timeline(raw_timeline)
            return state
        except Exception as exc:
            state.errors.append(f"TimelineBuilderSkill error: {exc}")
            state.timeline = []
            return state

    def _build_prompt(self, note_text: str) -> str:
        return f"""
You are a clinical timeline extractor for ADRD chart review.

Task:
- Read the clinical note.
- Extract key disease-course milestones in chronological order.
- Focus on onset/progression, diagnosis milestones, treatment changes, and acute triggers relevant to cognition.

Output format (strict JSON only):
{{
  "timeline": [
    {{"date_label": "...", "text": "..."}}
  ]
}}

Rules:
1) Max 6 timeline items.
2) Keep text concise (<= 16 words).
3) Use explicit date/year if present; otherwise use relative labels like "~2 years ago" or "This admission".
4) If no timeline evidence exists, return an empty array.
5) Do not invent dates or events.

Clinical Note:
{note_text}
""".strip()

    @staticmethod
    def _sanitize_timeline(raw_timeline: object) -> list[dict]:
        if not isinstance(raw_timeline, list):
            return []

        cleaned: list[dict] = []
        seen: set[tuple[str, str]] = set()
        for item in raw_timeline:
            if not isinstance(item, dict):
                continue

            date_label = str(item.get("date_label", "")).strip()
            text = str(item.get("text", "")).strip()
            if not date_label or not text:
                continue

            key = (date_label.lower(), text.lower())
            if key in seen:
                continue
            seen.add(key)

            cleaned.append({"date_label": date_label[:32], "text": text[:160]})
            if len(cleaned) >= 6:
                break

        return cleaned

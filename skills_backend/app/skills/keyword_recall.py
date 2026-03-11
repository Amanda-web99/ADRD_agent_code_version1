from __future__ import annotations

import json
from pathlib import Path
import google.generativeai as genai

from app.models import CandidateSpan, PipelineState
from app.settings import settings
from app.skills.base import Skill


class KeywordRecallSkill(Skill):
    name = "keyword_recall"

    VOCAB_FILE = Path(__file__).resolve().parents[3] / "Chart review vocabulary V2(summary vocabulary).csv"
    ALLOWED_LABELS = (
        "memory",
        "cognitive_test",
        "imaging_ad",
        "vascular",
        "ftd",
        "lbd",
        "medication",
        "lab",
        "function",
        "delirium",
    )
    ALLOWED_LABEL_SET = set(ALLOWED_LABELS)
    _VOCAB_CACHE: str | None = None

    DEFAULT_STRENGTH = 1
    STRENGTH_BY_LABEL = {
        "imaging_ad": 3,
        "vascular": 3,
        "cognitive_test": 2,
        "memory": 2,
        "medication": 2,
        "lab": 2,
        "ftd": 2,
        "lbd": 2,
        "function": 1,
        "delirium": 1,
    }

    def run(self, state: PipelineState) -> PipelineState:
        seen: set[tuple[int, int, str]] = set()
        candidates = self._extract_by_llm(state, seen)
        candidates = self._dedupe_nested_candidates(candidates)

        candidates.sort(key=lambda candidate: (-candidate.strength_score, candidate.start))
        for index, candidate in enumerate(candidates, start=1):
            candidate.id = f"C{index:04d}"
        state.candidates = candidates
        return state

    def _extract_by_llm(
        self,
        state: PipelineState,
        seen: set[tuple[int, int, str]],
    ) -> list[CandidateSpan]:
        if not settings.google_api_key:
            return []

        note_text = state.note_text or ""
        if not note_text.strip():
            return []

        prompt = self._build_llm_prompt(note_text)

        try:
            genai.configure(api_key=settings.google_api_key)
            model = genai.GenerativeModel(
                settings.google_model,
                generation_config={"temperature": 0.0, "response_mime_type": "application/json"},
            )
            response = model.generate_content(prompt)
            payload = json.loads((response.text or "{}").strip())
        except Exception as exc:
            state.errors.append(f"KeywordRecallSkill LLM extraction error: {exc}")
            return []

        llm_items = payload.get("evidence", []) if isinstance(payload, dict) else []
        if not isinstance(llm_items, list):
            return []

        llm_candidates: list[CandidateSpan] = []
        for item in llm_items:
            if not isinstance(item, dict):
                continue

            label = str(item.get("label", "")).strip()
            quote = str(item.get("quote", "")).strip()
            if label not in self.ALLOWED_LABEL_SET or not quote:
                continue
            if self._is_noise_match(label, quote):
                continue

            span = self._find_quote_span(note_text, quote)
            if span is None:
                continue

            start, end = span
            span_key = (start, end, label)
            if span_key in seen:
                continue
            seen.add(span_key)

            section = self._locate_section(state.sections, start)
            llm_candidates.append(
                CandidateSpan(
                    id="",
                    title=label.replace("_", " ").title(),
                    label=label,
                    quote=note_text[start:end],
                    start=start,
                    end=end,
                    section_id=section["id"],
                    section_title=section["title"],
                    strength_score=self.STRENGTH_BY_LABEL.get(label, self.DEFAULT_STRENGTH),
                    source="llm",
                )
            )

        return llm_candidates

    @classmethod
    def _load_vocab_text(cls) -> str:
        if cls._VOCAB_CACHE is not None:
            return cls._VOCAB_CACHE

        try:
            cls._VOCAB_CACHE = cls.VOCAB_FILE.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            cls._VOCAB_CACHE = ""
        return cls._VOCAB_CACHE

    def _build_llm_prompt(self, note_text: str) -> str:
        vocab_text = self._load_vocab_text()
        return f"""
You are a clinical ADRD evidence extractor.
Task: read the clinical note and extract ONLY explicit text spans that support ADRD diagnosis/subtype decisions.

Use this clinician vocabulary as guidance (not a hard exact-match list):
{vocab_text}

Rules:
1) Return strict JSON object with key "evidence".
2) Each item must be: {{"label":"...","quote":"..."}}.
3) label must be one of: {", ".join(self.ALLOWED_LABELS)}.
4) quote must be an exact substring copied from the note.
5) Prefer short evidence phrases/sentences, avoid duplicates, max 30 items.
6) Do not invent quotes or normalize wording.

Clinical Note:
{note_text}
""".strip()

    @staticmethod
    def _find_quote_span(text: str, quote: str) -> tuple[int, int] | None:
        stripped_quote = quote.strip()
        if not stripped_quote:
            return None

        direct_start = text.find(stripped_quote)
        if direct_start >= 0:
            return direct_start, direct_start + len(stripped_quote)

        lower_text = text.lower()
        lower_quote = stripped_quote.lower()
        case_insensitive_start = lower_text.find(lower_quote)
        if case_insensitive_start >= 0:
            return case_insensitive_start, case_insensitive_start + len(stripped_quote)

        return None

    @staticmethod
    def _dedupe_nested_candidates(candidates: list[CandidateSpan]) -> list[CandidateSpan]:
        by_label: dict[str, list[CandidateSpan]] = {}
        for candidate in candidates:
            by_label.setdefault(candidate.label, []).append(candidate)

        kept: list[CandidateSpan] = []
        for label_group in by_label.values():
            sorted_group = sorted(
                label_group,
                key=lambda candidate: (candidate.start, -(candidate.end - candidate.start)),
            )
            label_kept: list[CandidateSpan] = []
            for candidate in sorted_group:
                nested_in_previous = any(
                    previous.start <= candidate.start and candidate.end <= previous.end
                    for previous in label_kept
                )
                if not nested_in_previous:
                    label_kept.append(candidate)
            kept.extend(label_kept)

        return kept

    @staticmethod
    def _is_noise_match(label: str, quote: str) -> bool:
        normalized = " ".join((quote or "").strip().lower().split())
        if label == "function" and normalized in {"fall", "falls"}:
            return True
        return False

    @staticmethod
    def _locate_section(sections: list[dict], position: int) -> dict:
        for section in sections:
            if section["start"] <= position < section["end"]:
                return section
        if sections:
            return sections[-1]
        return {"id": "sec_0", "title": "Full Note", "start": 0, "end": position + 1}

from __future__ import annotations

import re
from app.models import PipelineState
from app.settings import settings
from app.skills.base import Skill


class EvidenceLinkerSkill(Skill):
    name = "evidence_linker"
    MAX_HIGHLIGHTS = 400
    MAX_PER_LABEL = {
        "function": 2,
        "delirium": 2,
    }

    FIXED_SECTIONS = ["history", "lab", "medication", "radiology", "cognitive"]

    LABEL_TO_SECTION = {
        "memory": "history",
        "vascular": "history",
        "ftd": "history",
        "lbd": "history",
        "function": "history",
        "delirium": "history",
        "lab": "lab",
        "medication": "medication",
        "imaging_ad": "radiology",
        "cognitive_test": "cognitive",
    }

    def run(self, state: PipelineState) -> PipelineState:
        selected_ids = set(state.llm_decision.get("selected_evidence_ids", []))

        if selected_ids:
            selected = [candidate for candidate in state.candidates if candidate.id in selected_ids]
        else:
            selected = state.candidates[: settings.max_evidence_items]

        selected = sorted(selected, key=lambda item: item.start)
        selected = selected[: settings.max_evidence_items]

        evidence = []
        meds = set()
        cognitive_tests = set()
        function_signals = set()
        delirium_triggers = set()

        for item in selected:
            strength = "STRONG" if item.strength_score >= 3 else "MODERATE" if item.strength_score == 2 else "WEAK"
            section_name = self._map_to_fixed_section(item.label)

            ev = {
                "id": item.id,
                "title": item.title,
                "strength": strength,
                "quote": item.quote,
                "source": "llm",
                "highlight": {
                    "start": item.start,
                    "end": item.end,
                    "label": item.label,
                    "section": section_name,
                    "section_id": item.section_id,
                },
            }
            evidence.append(ev)

            if item.label == "medication":
                meds.add(item.quote.lower())
            if item.label == "cognitive_test":
                cognitive_tests.add(self._canonical_test_name(item.quote))
            if item.label == "function":
                function_signals.add(item.quote)
            if item.label == "delirium":
                delirium_triggers.add(item.quote)

        # Fallback enrichment from all candidates so medication/cognitive don't disappear
        all_meds = {
            c.quote.lower()
            for c in state.candidates
            if c.label == "medication" and isinstance(c.quote, str) and c.quote.strip()
        }
        all_tests = {
            self._canonical_test_name(c.quote)
            for c in state.candidates
            if c.label == "cognitive_test" and isinstance(c.quote, str) and c.quote.strip()
        }

        meds = meds.union(all_meds)
        cognitive_tests = cognitive_tests.union(all_tests)

        state.evidence = evidence
        state.highlights = self._build_all_highlights(state)
        state.adrd_meds = sorted(meds)
        state.cognitive_tests = sorted(cognitive_tests)
        state.function_signals = sorted(function_signals)
        state.delirium_triggers = sorted(delirium_triggers)

        state.sections = self._build_fixed_sections(state)
        return state

    def _map_to_fixed_section(self, label: str) -> str:
        return self.LABEL_TO_SECTION.get(label, "history")

    def _build_fixed_sections(self, state: PipelineState) -> list[dict]:
        text_len = len(state.note_text or "")
        by_section = {key: [] for key in self.FIXED_SECTIONS}

        for candidate in state.candidates:
            sec = self._map_to_fixed_section(candidate.label)
            by_section[sec].append(candidate)

        blocks: list[dict] = []
        for sec in self.FIXED_SECTIONS:
            items = by_section[sec]
            if items:
                start = min(item.start for item in items)
                end = max(item.end for item in items)
            else:
                start, end = 0, min(text_len, 1)

            blocks.append(
                {
                    "id": f"sec_{sec}",
                    "title": sec.capitalize() if sec != "medication" else "Medication",
                    "start": start,
                    "end": end,
                }
            )
        return blocks

    def _build_all_highlights(self, state: PipelineState) -> list[dict]:
        seen: set[tuple[int, int, str]] = set()
        highlights: list[dict] = []
        label_counts: dict[str, int] = {}

        for candidate in sorted(state.candidates, key=lambda item: (item.start, item.end)):
            if candidate.start < 0 or candidate.end <= candidate.start:
                continue

            cap = self.MAX_PER_LABEL.get(candidate.label)
            if cap is not None and label_counts.get(candidate.label, 0) >= cap:
                continue

            section_name = self._map_to_fixed_section(candidate.label)
            key = (candidate.start, candidate.end, section_name)
            if key in seen:
                continue
            seen.add(key)

            highlights.append(
                {
                    "start": candidate.start,
                    "end": candidate.end,
                    "label": candidate.label,
                    "section": section_name,
                    "section_id": candidate.section_id,
                }
            )
            label_counts[candidate.label] = label_counts.get(candidate.label, 0) + 1

            if len(highlights) >= self.MAX_HIGHLIGHTS:
                break

        return highlights

    @staticmethod
    def _canonical_test_name(quote: str) -> str:
        if re.search(r"MMSE", quote, flags=re.IGNORECASE):
            return "MMSE"
        if re.search(r"MoCA", quote, flags=re.IGNORECASE):
            return "MoCA"
        return quote

from __future__ import annotations

import re
from app.models import PipelineState
from app.skills.base import Skill


class SectionParserSkill(Skill):
    name = "section_parser"

    HEADING_PATTERN = re.compile(r"^\s*([A-Za-z][A-Za-z /_-]{1,40}):\s*$", re.MULTILINE)

    def run(self, state: PipelineState) -> PipelineState:
        text = state.note_text or ""
        matches = list(self.HEADING_PATTERN.finditer(text))

        if not matches:
            state.sections = [
                {
                    "id": "sec_0",
                    "title": "Full Note",
                    "start": 0,
                    "end": len(text),
                }
            ]
            return state

        sections = []
        for idx, match in enumerate(matches):
            start = match.start()
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
            title = match.group(1).strip()
            sections.append(
                {
                    "id": f"sec_{idx}",
                    "title": title,
                    "start": start,
                    "end": end,
                }
            )

        # Keep a preface if text exists before first heading.
        if sections and sections[0]["start"] > 0:
            sections.insert(
                0,
                {
                    "id": "sec_preface",
                    "title": "Preface",
                    "start": 0,
                    "end": sections[0]["start"],
                },
            )

        state.sections = sections
        return state

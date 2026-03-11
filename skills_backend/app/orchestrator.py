from __future__ import annotations

from app.models import PipelineState
from app.schemas import AnalyzeResponse, MetaInfo
from app.settings import settings
from app.skills.section_parser import SectionParserSkill
from app.skills.keyword_recall import KeywordRecallSkill
from app.skills.llm_decision import LLMDecisionSkill
from app.skills.confidence_calibrator import ConfidenceCalibratorSkill
from app.skills.timeline_builder import TimelineBuilderSkill
from app.skills.evidence_linker import EvidenceLinkerSkill


class SkillOrchestrator:
    def __init__(self) -> None:
        self.skills = [
            SectionParserSkill(),
            KeywordRecallSkill(),
            LLMDecisionSkill(),
            ConfidenceCalibratorSkill(),
            TimelineBuilderSkill(),
            EvidenceLinkerSkill(),
        ]

    def run(self, note_text: str, patient_id: str | None = None) -> AnalyzeResponse:
        state = PipelineState(note_text=note_text, patient_id=patient_id)

        for skill in self.skills:
            state = skill.run(state)

        meta = MetaInfo(
            model=settings.google_model,
            pipeline_version=settings.pipeline_version,
            prompt_version=settings.prompt_version,
            llm_called=state.llm_called,
            token_prompt=state.token_usage["prompt"],
            token_output=state.token_usage["output"],
            token_total=state.token_usage["total"],
        )

        return AnalyzeResponse(
            adrddx=state.adrddx,
            subtype=state.subtype,
            confidence=state.confidence,
            evidence=state.evidence,
            highlights=state.highlights,
            cognitive_tests=state.cognitive_tests,
            adrd_meds=state.adrd_meds,
            function_signals=state.function_signals,
            delirium_triggers=state.delirium_triggers,
            timeline=state.timeline,
            sections=state.sections,
            meta=meta,
        )

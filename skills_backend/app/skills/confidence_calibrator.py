from __future__ import annotations

from app.models import PipelineState
from app.skills.base import Skill


class ConfidenceCalibratorSkill(Skill):
    name = "confidence_calibrator"

    def run(self, state: PipelineState) -> PipelineState:
        rule_signal = sum(candidate.strength_score for candidate in state.candidates)
        rule_conf = min(95, 25 + rule_signal * 4)

        if state.llm_called:
            blended = int(0.75 * state.confidence + 0.25 * rule_conf)
        else:
            blended = int(rule_conf)

        if state.adrddx == "No":
            blended = min(blended, 60)
        if not state.candidates:
            blended = min(blended, 35)

        state.confidence = max(0, min(100, blended))
        return state

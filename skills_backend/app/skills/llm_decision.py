from __future__ import annotations

import json
from collections import Counter
from typing import Dict, List
import google.generativeai as genai

from app.models import PipelineState
from app.settings import settings
from app.skills.base import Skill


class LLMDecisionSkill(Skill):
    name = "llm_decision"

    def run(self, state: PipelineState) -> PipelineState:
        if not state.candidates:
            state.adrddx = "No"
            state.subtype = "Unspecified"
            state.confidence = 20
            return state

        if not settings.google_api_key:
            return self._fallback_rule_decision(state)

        state.llm_called = True
        candidate_block = self._build_candidate_block(state)

        prompt = f"""
You are an ADRD chart-review decision engine.
Use ONLY the candidate evidence below.
Output strict JSON with keys:
- adrddx: one of ["Yes","No","Uncertain"]
- subtype: one of ["AD","VaD","FTD","LBD","Mixed","Unspecified"]
- confidence: integer 0-100
- selected_evidence_ids: array of candidate IDs

Decision rules:
- ADRD "Yes": cognitive decline/memory pattern, objective testing abnormalities, or dementia-level imaging/clinical evidence.
- VaD: stroke/CVA/white matter ischemic burden pattern.
- AD: hippocampal/medial temporal atrophy + progressive memory decline pattern.
- FTD: behavioral/personality/language-frontotemporal pattern.
- LBD: parkinsonism + visual hallucinations/fluctuating cognition pattern.
- Mixed: substantial evidence for more than one subtype.
- Unspecified: ADRD likely but subtype evidence weak.

Candidates:
{candidate_block}
""".strip()

        try:
            genai.configure(api_key=settings.google_api_key)
            model = genai.GenerativeModel(
                settings.google_model,
                generation_config={"temperature": 0.1, "response_mime_type": "application/json"},
            )

            response = model.generate_content(prompt)
            usage = getattr(response, "usage_metadata", None)
            if usage is not None:
                state.token_usage["prompt"] += int(getattr(usage, "prompt_token_count", 0) or 0)
                state.token_usage["output"] += int(getattr(usage, "candidates_token_count", 0) or 0)
                state.token_usage["total"] += int(getattr(usage, "total_token_count", 0) or 0)

            payload = json.loads((response.text or "{}").strip())
            state.llm_decision = payload
            state.adrddx = payload.get("adrddx", "Uncertain")
            state.subtype = payload.get("subtype", "Unspecified")
            state.confidence = int(payload.get("confidence", 50))
            return state

        except Exception as exc:
            state.errors.append(f"LLMDecisionSkill error: {exc}")
            return self._fallback_rule_decision(state)

    def _build_candidate_block(self, state: PipelineState) -> str:
        top_candidates = state.candidates[: settings.max_candidates_for_llm]
        lines: List[str] = []
        for item in top_candidates:
            lines.append(
                f"- id={item.id} | label={item.label} | section={item.section_title} | quote={item.quote}"
            )
        return "\n".join(lines)

    def _fallback_rule_decision(self, state: PipelineState) -> PipelineState:
        labels = Counter([candidate.label for candidate in state.candidates])

        ad_score = labels["memory"] + labels["imaging_ad"] + labels["medication"]
        vad_score = labels["vascular"]
        ftd_score = labels["ftd"]
        lbd_score = labels["lbd"]

        overall_support = ad_score + vad_score + ftd_score + lbd_score + labels["cognitive_test"]

        if overall_support >= 3:
            state.adrddx = "Yes"
            state.confidence = min(88, 55 + overall_support * 5)
        elif overall_support == 0:
            state.adrddx = "No"
            state.confidence = 25
        else:
            state.adrddx = "Uncertain"
            state.confidence = 45

        subtype_scores: Dict[str, int] = {
            "AD": ad_score,
            "VaD": vad_score,
            "FTD": ftd_score,
            "LBD": lbd_score,
        }
        best_subtype = max(subtype_scores, key=subtype_scores.get)
        non_zero = [name for name, score in subtype_scores.items() if score > 0]

        if len(non_zero) > 1 and subtype_scores[best_subtype] == sorted(subtype_scores.values())[-2]:
            state.subtype = "Mixed"
        elif subtype_scores[best_subtype] > 0:
            state.subtype = best_subtype
        else:
            state.subtype = "Unspecified"

        state.llm_decision = {
            "adrddx": state.adrddx,
            "subtype": state.subtype,
            "confidence": state.confidence,
            "selected_evidence_ids": [candidate.id for candidate in state.candidates[:8]],
        }
        return state

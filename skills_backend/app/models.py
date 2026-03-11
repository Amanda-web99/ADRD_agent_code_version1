from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class CandidateSpan:
    id: str
    title: str
    label: str
    quote: str
    start: int
    end: int
    section_id: str
    section_title: str
    strength_score: int
    source: str = "rule"


@dataclass
class PipelineState:
    note_text: str
    patient_id: Optional[str] = None

    sections: List[Dict] = field(default_factory=list)
    candidates: List[CandidateSpan] = field(default_factory=list)

    llm_decision: Dict = field(default_factory=dict)
    token_usage: Dict[str, int] = field(default_factory=lambda: {
        "prompt": 0,
        "output": 0,
        "total": 0,
    })

    adrddx: str = "Uncertain"
    subtype: str = "Unspecified"
    confidence: int = 0

    evidence: List[Dict] = field(default_factory=list)
    highlights: List[Dict] = field(default_factory=list)
    cognitive_tests: List[str] = field(default_factory=list)
    adrd_meds: List[str] = field(default_factory=list)
    function_signals: List[str] = field(default_factory=list)
    delirium_triggers: List[str] = field(default_factory=list)
    timeline: List[Dict] = field(default_factory=list)

    llm_called: bool = False
    errors: List[str] = field(default_factory=list)

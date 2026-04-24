from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List, Literal, Optional

SectionName = Literal["history", "lab", "medication", "radiology", "cognitive"]


class SectionBlock(BaseModel):
    id: str
    title: str
    start: int
    end: int


class Highlight(BaseModel):
    start: int
    end: int
    label: str
    section: Optional[SectionName] = None
    section_id: Optional[str] = None


class EvidenceItem(BaseModel):
    id: str
    title: str
    strength: Literal["STRONG", "MODERATE", "WEAK"]
    quote: str
    highlight: Highlight
    source: Literal["rule", "llm", "hybrid"] = "hybrid"


class TimelineEvent(BaseModel):
    date_label: str
    text: str


class AnalyzeRequest(BaseModel):
    text: str
    patient_id: Optional[str] = None


class BatchAnalyzeRequest(BaseModel):
    notes: List[AnalyzeRequest] = Field(default_factory=list)


class MetaInfo(BaseModel):
    model: str
    pipeline_version: str
    prompt_version: str
    llm_called: bool
    token_prompt: int = 0
    token_output: int = 0
    token_total: int = 0


class AnalyzeResponse(BaseModel):
    adrddx: Literal["Yes", "No", "Uncertain"]
    subtype: Literal["AD", "VaD", "FTD", "LBD", "Mixed", "Unspecified"]
    confidence: int = Field(ge=0, le=100)
    evidence: List[EvidenceItem] = Field(default_factory=list)
    highlights: List[Highlight] = Field(default_factory=list)
    cognitive_tests: List[str] = Field(default_factory=list)
    adrd_meds: List[str] = Field(default_factory=list)
    function_signals: List[str] = Field(default_factory=list)
    delirium_triggers: List[str] = Field(default_factory=list)
    timeline: List[TimelineEvent] = Field(default_factory=list)
    sections: List[SectionBlock] = Field(default_factory=list)
    meta: MetaInfo


class BatchAnalyzeResponse(BaseModel):
    results: List[AnalyzeResponse] = Field(default_factory=list)

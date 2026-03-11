from pydantic import BaseModel, Field
from typing import List, Literal, Optional

SectionName = Literal["history","lab","prescriptions","radiology","final","other"]

class Highlight(BaseModel):
    start: int
    end: int
    label: str
    section: Optional[SectionName] = None

class EvidenceItem(BaseModel):
    id: str
    title: str
    strength: Literal["STRONG","MODERATE","WEAK"]
    quote: str
    highlight: Highlight

class TimelineEvent(BaseModel):
    date_label: str
    text: str

class AgentOutput(BaseModel):
    adrddx: Literal["Yes","No","Uncertain"]
    subtype: Literal["AD","VaD","FTD","LBD","Mixed","Unspecified"]
    confidence: int = Field(ge=0, le=100)
    evidence: List[EvidenceItem] = []
    highlights: List[Highlight] = []
    cognitive_tests: List[str] = []
    adrd_meds: List[str] = []
    function_signals: List[str] = []
    delirium_triggers: List[str] = []
    timeline: List[TimelineEvent] = []

class AnalyzeRequest(BaseModel):
    text: str
    patient_id: Optional[str] = None
    admission_date: Optional[str] = None
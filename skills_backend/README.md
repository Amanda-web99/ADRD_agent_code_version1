# ADRD Skills Backend

This backend powers ADRD chart-review with a modular skill pipeline.
It is designed for:

- LLM-based evidence extraction from free-text clinical notes
- Structured ADRD diagnosis outputs (Yes/No/Uncertain + subtype + confidence)
- Character-level highlighting offsets for frontend navigation
- Timeline event extraction from note text
- Batch processing for multiple notes

---

## 1) Current Implementation Snapshot

- **Framework:** FastAPI + Pydantic
- **Model provider:** Gemini (`google-generativeai`)
- **Evidence extraction mode:** **LLM-only** (regex recall removed)
- **Response style:** Fully structured JSON for frontend rendering
- **Pipeline style:** Stateful skill orchestration (`PipelineState`)

---

## 2) End-to-End Backend Logic

When a note is sent to `/analyze_text`, this is the runtime flow:

1. API receives text payload and normalizes request body format.
2. `SkillOrchestrator` creates `PipelineState(note_text, patient_id)`.
3. Skills execute in order:
   - `SectionParserSkill`
   - `KeywordRecallSkill` (LLM evidence extractor)
   - `LLMDecisionSkill` (diagnosis/subtype/confidence/evidence selection)
   - `ConfidenceCalibratorSkill` (blend/calibrate confidence)
   - `TimelineBuilderSkill` (timeline from text)
   - `EvidenceLinkerSkill` (final evidence/highlights/sections)
4. Orchestrator builds `AnalyzeResponse` + `meta` (model/pipeline/tokens).
5. API returns structured JSON to frontend.

---

## 3) Why the Pipeline is Structured This Way

- **Separation of concerns:** each skill does one job (parse, extract, decide, calibrate, timeline, link).
- **Traceability:** all intermediate outputs live in `PipelineState`.
- **Frontend compatibility:** output already includes offsets, section labels, and timeline list.
- **Operational robustness:** if one LLM step fails, pipeline still returns a safe result shape.

---

## 4) File-by-File Responsibilities

### Root-Level

| File | Responsibility |
|---|---|
| `requirements.txt` | Python dependencies (FastAPI, Pydantic, Gemini SDK, etc.). |
| `.env.example` | Environment variable template (`GOOGLE_API_KEY`, model, etc.). |
| `.env` | Local runtime secrets/config (not for git). |
| `README.md` | Backend architecture, flow, and run instructions. |

### App Core

| File | Responsibility |
|---|---|
| `app/main.py` | FastAPI app, CORS, endpoint definitions, request parsing, error handling. |
| `app/orchestrator.py` | Pipeline assembly and sequential skill execution. Converts `PipelineState` to final `AnalyzeResponse`. |
| `app/settings.py` | Central config via `BaseSettings` (`google_api_key`, model, limits, versions, CORS). |
| `app/schemas.py` | API input/output contracts (Pydantic models). |
| `app/models.py` | Internal dataclasses (`PipelineState`, `CandidateSpan`) shared by skills. |
| `app/__init__.py` | Package marker file. |

### Skills

| File | Responsibility |
|---|---|
| `app/skills/base.py` | Abstract `Skill` interface (`run(state) -> state`). |
| `app/skills/section_parser.py` | Splits note text into coarse section blocks (or full-note fallback). |
| `app/skills/keyword_recall.py` | **LLM-only evidence extraction** using clinician vocabulary + quote-to-offset matching. |
| `app/skills/llm_decision.py` | ADRD decision logic using candidate evidence (`adrddx`, subtype, confidence, selected IDs). |
| `app/skills/confidence_calibrator.py` | Calibrates confidence using rule signal + LLM decision signal. |
| `app/skills/timeline_builder.py` | Extracts timeline milestones (`date_label`, `text`) from note text. |
| `app/skills/evidence_linker.py` | Produces final evidence list, all highlights, fixed 5 sections, and summary arrays (`cognitive_tests`, meds, etc.). |
| `app/skills/__init__.py` | Package marker file. |

---

## 5) API Design

### `GET /`
Health and version metadata.

### `POST /analyze`
JSON request:

```json
{
  "text": "...clinical note...",
  "patient_id": "123"
}
```

### `POST /analyze_text`
Supports:

- `text/plain` raw note body
- `application/json` with `{"text": "..."}`
- `application/json` raw string body

### `POST /analyze_batch`
Batch note processing (`max 200`).

---

## 6) Response Data Contract (What Frontend Consumes)

Key fields returned by `AnalyzeResponse`:

- `adrddx`, `subtype`, `confidence`
- `evidence[]` with `quote`, `strength`, and highlight span
- `highlights[]` (all renderable spans)
- `sections[]` (fixed 5 section ranges: history/lab/medication/radiology/cognitive)
- `timeline[]` (`date_label`, `text`)
- `meta` (model name + prompt/pipeline version + token usage)

This enables frontend behaviors such as:

- Color-coded in-note highlighting
- Evidence list with "jump to text"
- Section filtering
- Timeline visualization

---

## 7) Key Implementation Details 

1. **Evidence extraction is LLM-only**
   - Guided by physician vocabulary file.
   - LLM returns labeled quotes.
   - Backend maps quotes back to exact character offsets.

2. **Diagnosis is a second LLM step**
   - Uses only extracted candidates.
   - Produces ADRD label + subtype + confidence + selected evidence IDs.

3. **Confidence is calibrated**
   - Rule-derived signal blended with LLM confidence.
   - Adds stability and avoids over-confident edge cases.

4. **Timeline is extracted from note text**
   - Output is clean, ordered event list (`date_label`, `text`).
   - Frontend timeline is now backend-driven, not hardcoded.

5. **Evidence/highlight outputs are frontend-ready**
   - Every highlight has offsets and section tags.
   - Supports section filtering and click-to-locate UX.

---

## 8) Setup and Run

```bash
cd /Users/amanda/Desktop/ADRD_agent_code/skills_backend
cp .env.example .env
# Fill GOOGLE_API_KEY in .env

python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

Run server:

```bash
cd /Users/amanda/Desktop/ADRD_agent_code/skills_backend
PYTHONPATH=/Users/amanda/Desktop/ADRD_agent_code/skills_backend \
  .venv/bin/uvicorn app.main:app --reload --port 8002
```

Smoke test:

```bash
curl -s -X POST http://localhost:8002/analyze_text \
  -H "Content-Type: text/plain" \
  --data 'Family reports memory decline over 5 years. Diagnosed with Alzheimer\'s disease in 2021. Started donepezil in 2022. This admission had acute confusion due to UTI.'
```

---

## 9) Known Boundaries / Next Enhancements

- `acuteVsChronic` is currently frontend-derived (can be moved to backend skill).
- `conflict` flag logic is still frontend-level (can be backendized later).
- Current Gemini SDK shows deprecation warning for `google-generativeai`; migration to `google.genai` is a future maintenance task.


# ADRD Agent Code

A multi-module project for **ADRD (Alzheimer's Disease and Related Dementias) clinical note analysis**. It generates structured outputs from free-text notes, including:

- ADRD diagnosis status (Yes / No / Uncertain)
- ADRD subtype (AD / VaD / FTD / LBD / Mixed / Unspecified)
- Evidence snippets with text highlighting offsets
- Timeline event extraction
- Frontend chart review visualization

This repository includes a frontend app, two backend implementations (basic and skills-pipeline), plus testing and prompt-related files for iterative development and research.

## Project Structure

```text
ADRD_agent_code/
├── frontend/                 # React + Vite frontend for upload and visualization
├── backend/                  # Basic FastAPI backend (Diagnosis/Subtype core agents)
├── skills_backend/           # Skills-pipeline FastAPI backend (recommended)
├── Chart review vocabulary V2(summary vocabulary).csv
├── test_frontend.html
└── README.md
```

## Module Overview

### 1) `frontend/`
- Stack: React + TypeScript + Vite.
- Main features:
  - Upload Excel clinical note data (Patient ID + Notes)
  - Call backend analysis APIs
  - Display diagnosis, evidence, text highlights, and timeline
- Default API target: `http://localhost:8002` (see `frontend/src/app/services/aiAgentService.ts`).

### 2) `backend/` (basic)
- Stack: FastAPI.
- Current primary agents: `DiagnosisAgent`, `SubtypeAgent`.
- Main endpoints: `/analyze`, `/analyze_text`.
- Good for quick validation of core classification logic.

### 3) `skills_backend/` (skills pipeline, recommended)
- Stack: FastAPI + Pydantic + Gemini SDK.
- Pipeline sequence:
  - `SectionParserSkill`
  - `KeywordRecallSkill`
  - `LLMDecisionSkill`
  - `ConfidenceCalibratorSkill`
  - `TimelineBuilderSkill`
  - `EvidenceLinkerSkill`
- Returns richer, frontend-ready structured data (evidence, highlights, sections, timeline, meta).

## Quick Start (Recommended Path)

### 1) Start `skills_backend` (port 8002)

```bash
cd skills_backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# For first run, create and configure .env (at minimum GOOGLE_API_KEY)
cp .env.example .env

PYTHONPATH=$(pwd) uvicorn app.main:app --reload --port 8002
```

### 2) Start frontend (in a new terminal)

```bash
cd frontend
npm install
npm run dev
```

After startup, the frontend will call `http://localhost:8002/analyze_text` for note analysis.

## Optional: Start the basic `backend` (port 8001)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

Basic backend test script:

```bash
cd backend
python run_tests.py
```

## API Example (`skills_backend`)

```bash
curl -X POST http://localhost:8002/analyze_text \
  -H "Content-Type: text/plain" \
  --data 'Family reports memory decline over 5 years. Diagnosed with Alzheimer disease in 2021. Started donepezil in 2022.'
```

## Use Cases

- Automated ADRD pre-screening from clinical notes
- Structured evidence extraction with visual chart review
- Multi-agent / multi-skill medical NLP pipeline validation
- Frontend-backend integration and prompt iteration

## Notes

- This repository is for development and research; do not use as a standalone clinical decision tool.
- If using real patient data, implement privacy and compliance controls (HIPAA/local regulations).
- Never commit API keys, `.env`, or sensitive patient information to public repositories.

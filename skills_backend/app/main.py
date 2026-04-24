from __future__ import annotations

import json
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from app.orchestrator import SkillOrchestrator
from app.schemas import AnalyzeRequest, AnalyzeResponse, BatchAnalyzeRequest, BatchAnalyzeResponse
from app.settings import settings


app = FastAPI(title="ADRD Skills Backend", version="1.0.0")
orchestrator = SkillOrchestrator()

origins = ["*"] if settings.allow_origins == "*" else [x.strip() for x in settings.allow_origins.split(",") if x.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict:
    return {
        "status": "ok",
        "service": "skills_backend",
        "pipeline_version": settings.pipeline_version,
        "prompt_version": settings.prompt_version,
    }


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    try:
        return orchestrator.run(note_text=req.text, patient_id=req.patient_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/analyze_text", response_model=AnalyzeResponse)
async def analyze_text(request: Request) -> AnalyzeResponse:
    """Accept note text from either text/plain or JSON payloads.

    Supported request formats:
    - Content-Type: text/plain, body = raw note text
    - Content-Type: application/json, body = {"text": "..."}
    - Content-Type: application/json, body = "raw note text"
    """
    try:
        content_type = (request.headers.get("content-type") or "").lower()
        raw = await request.body()
        if not raw:
            raise HTTPException(status_code=400, detail="Empty request body")

        note = ""
        if "application/json" in content_type:
            try:
                payload = json.loads(raw.decode("utf-8"))
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid JSON body")

            if isinstance(payload, dict):
                note = str(payload.get("text") or "").strip()
            elif isinstance(payload, str):
                note = payload.strip()
        else:
            note = raw.decode("utf-8").strip()

        if not note:
            raise HTTPException(status_code=400, detail="No note text found in request")

        return orchestrator.run(note_text=note)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/analyze_batch", response_model=BatchAnalyzeResponse)
def analyze_batch(req: BatchAnalyzeRequest) -> BatchAnalyzeResponse:
    if len(req.notes) > 200:
        raise HTTPException(status_code=400, detail="Batch too large. Max 200 notes per request.")

    results = []
    for item in req.notes:
        try:
            results.append(orchestrator.run(note_text=item.text, patient_id=item.patient_id))
        except Exception:
            results.append(
                AnalyzeResponse(
                    adrddx="Uncertain",
                    subtype="Unspecified",
                    confidence=0,
                    evidence=[],
                    highlights=[],
                    cognitive_tests=[],
                    adrd_meds=[],
                    function_signals=[],
                    delirium_triggers=[],
                    timeline=[],
                    sections=[],
                    meta={
                        "model": settings.google_model,
                        "pipeline_version": settings.pipeline_version,
                        "prompt_version": settings.prompt_version,
                        "llm_called": False,
                        "token_prompt": 0,
                        "token_output": 0,
                        "token_total": 0,
                    },
                )
            )

    return BatchAnalyzeResponse(results=results)

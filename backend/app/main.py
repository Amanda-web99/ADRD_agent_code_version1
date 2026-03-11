# backend/app/main.py
from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware

from .settings import settings
from .schemas import AnalyzeRequest, AgentOutput
from .agents import run_agent, aggregate
from fastapi import HTTPException

app = FastAPI(title="ADRD Multi-Agent Backend")

# Origins configuration for CORS
# Allow all origins for development/testing
# In production, restrict to specific domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (file://, http://localhost, etc.)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Testing with core agents only
AGENTS = [
    "DiagnosisAgent",
    "SubtypeAgent"
]

@app.get("/")
def root():
    return {"status": "ok", "message": "Backend is running. Use POST /analyze or /analyze_text"}

# JSON request interface
@app.post("/analyze", response_model=AgentOutput)
def analyze(req: AnalyzeRequest):
    """Analyze clinical note with JSON request body"""
    note = req.text
    try:
        parts = [run_agent(a, note) for a in AGENTS]
        merged = aggregate(note, parts)
        return merged
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Plain text interface: Content-Type: text/plain
@app.post("/analyze_text", response_model=AgentOutput)
def analyze_text(note: str = Body(..., media_type="text/plain")):
    """
    Test interface for DiagnosisAgent and SubtypeAgent.
    Request: plain text clinical note (Content-Type: text/plain)
    Response: JSON with adrddx (Yes/No/Uncertain) and subtype diagnosis
    """
    print(f"🔍 Received note: {note[:100]}...")
    try:
        print("🤖 Running agents...")
        parts = []
        for agent in AGENTS:
            print(f"  → Running {agent}...")
            try:
                result = run_agent(agent, note)
                parts.append(result)
                print(f"  ✅ {agent} completed")
            except Exception as e:
                print(f"  ❌ {agent} failed: {str(e)}")
                # Continue with other agents, use empty result
                parts.append({
                    "adrddx": "Uncertain",
                    "subtype": "Unspecified",
                    "confidence": 0,
                    "evidence": [],
                    "highlights": [],
                    "cognitive_tests": [],
                    "adrd_meds": [],
                    "function_signals": [],
                    "delirium_triggers": [],
                    "timeline": []
                })
        
        print("🔗 Aggregating results...")
        merged = aggregate(note, parts)
        print(f"✅ Final result: adrddx={merged.get('adrddx')}, subtype={merged.get('subtype')}")
        return merged
    except Exception as e:
        print(f"❌ Error in analyze_text: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
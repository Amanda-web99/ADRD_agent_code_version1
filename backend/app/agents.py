# backend/app/agents.py
from typing import Dict, Any, List
from .settings import settings
import json
import google.generativeai as genai
from prompts_professional_v1 import (
  DIAGNOSIS_AGENT_PROMPT_PROFESSIONAL,
  SUBTYPE_AGENT_PROMPT_PROFESSIONAL,
)

SYSTEM_BASE = """You are an expert clinical note reviewer for ADRD chart review.
Task: Extract evidence strictly from the provided note text. Do NOT invent facts.
Return JSON only that matches the provided schema.
Quotes must be exact substrings from the note.
If no evidence, set fields accordingly and use empty lists.
"""

AGENT_SCHEMA = {
  "name": "AgentOutput",
  "schema": {
    "type": "object",
    "additionalProperties": False,
    "properties": {
      "adrddx": {"type":"string","enum":["Yes","No","Uncertain"]},
      "subtype":{"type":"string","enum":["AD","VaD","FTD","LBD","Mixed","Unspecified"]},
      "confidence":{"type":"integer","minimum":0,"maximum":100},
      "evidence":{
        "type":"array",
        "items":{
          "type":"object",
          "additionalProperties": False,
          "properties":{
            "id":{"type":"string"},
            "title":{"type":"string"},
            "strength":{"type":"string","enum":["STRONG","MODERATE","WEAK"]},
            "quote":{"type":"string"},
            "highlight":{
              "type":"object",
              "additionalProperties": False,
              "properties":{
                "start":{"type":"integer","minimum":0},
                "end":{"type":"integer","minimum":0},
                "label":{"type":"string"},
                "section":{"type":["string","null"],"enum":["history","lab","prescriptions","radiology","final","other",None]},
              },
              "required":["start","end","label","section"]
            }
          },
          "required":["id","title","strength","quote","highlight"]
        }
      },
      "highlights":{
        "type":"array",
        "items":{
          "type":"object",
          "additionalProperties": False,
          "properties":{
            "start":{"type":"integer","minimum":0},
            "end":{"type":"integer","minimum":0},
            "label":{"type":"string"},
            "section":{"type":["string","null"],"enum":["history","lab","prescriptions","radiology","final","other",None]}
          },
          "required":["start","end","label","section"]
        }
      },
      "cognitive_tests":{"type":"array","items":{"type":"string"}},
      "adrd_meds":{"type":"array","items":{"type":"string"}},
      "function_signals":{"type":"array","items":{"type":"string"}},
      "delirium_triggers":{"type":"array","items":{"type":"string"}},
      "timeline":{
        "type":"array",
        "items":{
          "type":"object",
          "additionalProperties": False,
          "properties":{
            "date_label":{"type":"string"},
            "text":{"type":"string"}
          },
          "required":["date_label","text"]
        }
      }
    },
    "required":["adrddx","subtype","confidence","evidence","highlights","cognitive_tests","adrd_meds","function_signals","delirium_triggers","timeline"]
  }
}

def _chat_json(prompt: str) -> Dict[str, Any]:
    """Use Gemini API and return parsed JSON."""
    if not settings.google_api_key:
        raise RuntimeError("GOOGLE_API_KEY is missing. Please set it in backend/.env")

    genai.configure(api_key=settings.google_api_key)
    model = genai.GenerativeModel(
        settings.google_model,
        generation_config={
            "temperature": 0.1,
            "response_mime_type": "application/json",
        },
    )

    full_prompt = f"{SYSTEM_BASE}\n\n{prompt}"

    try:
        response = model.generate_content(full_prompt)
        content = (response.text or "{}").strip()

        usage = getattr(response, "usage_metadata", None)
        if usage is not None:
            prompt_tokens = getattr(usage, "prompt_token_count", None)
            output_tokens = getattr(usage, "candidates_token_count", None)
            total_tokens = getattr(usage, "total_token_count", None)
            print(
                "📊 Gemini token usage "
                f"(prompt={prompt_tokens}, output={output_tokens}, total={total_tokens})"
            )

        try:
            result = json.loads(content)
            return result
        except json.JSONDecodeError as e:
            print(f"DEBUG: Gemini returned invalid JSON: {content[:500]}")
            raise RuntimeError(f"Gemini returned invalid JSON format: {str(e)}")

    except Exception as e:
        print(f"DEBUG: Gemini error: {type(e).__name__}: {str(e)}")
        raise RuntimeError(f"Gemini API error: {str(e)}")

def _get_agent_instructions(agent_name: str) -> str:
    """Provide specific instructions for different agents

    Diagnosis/Subtype use the professional prompts for higher diagnostic accuracy.
    """
    instructions = {
  "DiagnosisAgent": DIAGNOSIS_AGENT_PROMPT_PROFESSIONAL,
  "SubtypeAgent": SUBTYPE_AGENT_PROMPT_PROFESSIONAL,
        "CognitiveTestAgent": """Extract cognitive test scores from note. Return MMSE, MoCA, and other test results.""",
        "MedicationAgent": """Extract ADRD medications: Donepezil, Memantine, Rivastigmine, Galantamine, etc.""",
        "FunctionAgent": """Extract ADL/IADL function status and daily living independence level.""",
        "DeliriumTriggerAgent": """Extract delirium risk factors: infections, metabolic issues, medications, environmental changes.""",
        "TimelineAgent": """Extract key dates: symptom onset, diagnosis date, treatment start dates."""
    }
    return instructions.get(agent_name, "Analyze the clinical note and return JSON")

def run_agent(agent_name: str, note_text: str) -> Dict[str, Any]:
    """
    Run an agent to analyze clinical note using Google Gemini API.
    """
    agent_instructions = _get_agent_instructions(agent_name)
    
    prompt = f"""
Agent Role: {agent_name}

{agent_instructions}

---
Clinical Note:
<<<NOTE>>>
{note_text}
<<<END NOTE>>>

Task:
- Strictly follow the above task instructions
- Extract relevant evidence from the note
- Output JSON format that must exactly match the following schema:

{json.dumps(AGENT_SCHEMA["schema"], ensure_ascii=False)}

Requirements:
- All quotes must be exact substrings from the note
- Provide accurate character offsets [start, end) (counted by characters, including spaces and punctuation)
- If you cannot reliably find offsets, set evidence to empty and lower confidence
- All required fields must not be empty, arrays can be empty lists

Output: JSON only, no markdown or explanation
"""
    return _chat_json(prompt)

def aggregate(note_text: str, parts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate results from multiple agents.
    For current setup with DiagnosisAgent and SubtypeAgent:
    - adrddx comes from DiagnosisAgent (parts[0])
    - subtype comes from SubtypeAgent (parts[1])
    - confidence is averaged from both agents
    """
    if not parts:
        return {
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
        }
    
    # Use DiagnosisAgent result for adrddx
    diag_result = parts[0] if len(parts) > 0 else {}
    # Use SubtypeAgent result for subtype
    subtype_result = parts[1] if len(parts) > 1 else {}
    
    out = {
        "adrddx": diag_result.get("adrddx", "Uncertain"),
        "subtype": subtype_result.get("subtype", "Unspecified"),
        "confidence": int(sum(p.get("confidence", 0) for p in parts) / max(1, len(parts))),
        "evidence": [],
        "highlights": [],
        "cognitive_tests": [],
        "adrd_meds": [],
        "function_signals": [],
        "delirium_triggers": [],
        "timeline": []
    }

    # Collect evidence from all agents
    seen_quotes = set()
    for p in parts:
        for ev in p.get("evidence", []):
            q = ev.get("quote", "")
            if q and q not in seen_quotes:
                seen_quotes.add(q)
                out["evidence"].append(ev)

        out["highlights"].extend(p.get("highlights", []))
        out["cognitive_tests"].extend(p.get("cognitive_tests", []))
        out["adrd_meds"].extend(p.get("adrd_meds", []))
        out["function_signals"].extend(p.get("function_signals", []))
        out["delirium_triggers"].extend(p.get("delirium_triggers", []))
        out["timeline"].extend(p.get("timeline", []))

    # Deduplicate and sort arrays
    for k in ["cognitive_tests", "adrd_meds", "function_signals", "delirium_triggers"]:
        out[k] = sorted(list(set([x.strip() for x in out[k] if isinstance(x, str) and x.strip()])))

    # Deduplicate timeline
    tl_seen = set()
    tl = []
    for e in out["timeline"]:
        if not isinstance(e, dict): 
            continue
        key = (e.get("date_label", ""), e.get("text", ""))
        if key not in tl_seen:
            tl_seen.add(key)
            tl.append({"date_label": key[0], "text": key[1]})
    out["timeline"] = tl

    return out
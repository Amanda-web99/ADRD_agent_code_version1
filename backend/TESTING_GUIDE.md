TESTING GUIDE FOR ADRD BACKEND
================================

## Current Setup:
- DiagnosisAgent: Determines if patient has ADRD (Yes/No/Uncertain)
- SubtypeAgent: Classifies ADRD subtype (AD/VaD/FTD/LBD/Mixed/Unspecified)
- Model: gpt-4o-mini
- Endpoints: POST /analyze or POST /analyze_text

## Test 1: Using cURL with plain text
```bash
curl -X POST http://localhost:8001/analyze_text \
  -H "Content-Type: text/plain" \
  -d "Patient presents with 6 months of progressive memory loss and cognitive decline. MMSE score 18/30. MRI shows hippocampal atrophy. No evidence of stroke. Diagnosed with Alzheimer's disease."
```

## Test 2: Using cURL with JSON
```bash
curl -X POST http://localhost:8001/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Patient presents with 6 months of progressive memory loss and cognitive decline. MMSE score 18/30. MRI shows hippocampal atrophy. No evidence of stroke. Diagnosed with Alzheimer disease.",
    "patient_id": "P001"
  }'
```

## Expected Response Format:
```json
{
  "adrddx": "Yes",
  "subtype": "AD",
  "confidence": 75,
  "evidence": [],
  "highlights": [],
  "cognitive_tests": [],
  "adrd_meds": [],
  "function_signals": [],
  "delirium_triggers": [],
  "timeline": []
}
```

## Common Issues & Solutions:

1. **Error: "gpt-4o-mini not found"**
   - Make sure .env has: OPENAI_MODEL=gpt-4o-mini
   - Restart the server

2. **Empty/null responses**
   - Check if LLM is returning valid JSON
   - Try with clearer patient notes

3. **"Uncertain" when expecting "Yes"**
   - The LLM needs more clinical keywords in the note
   - Add terms like: cognitive decline, memory impairment, dementia, atrophy

## Next Steps After Testing:
Once these two agents work, we can add:
- CognitiveTestAgent (MMSE, MoCA scores)
- MedicationAgent (Donepezil, etc.)
- TimelineAgent (symptom progression timeline)
- Highlight extraction for evidence

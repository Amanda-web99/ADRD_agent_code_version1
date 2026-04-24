import httpx
import json

tests = [
    ("AD", "72-year-old patient with 8 months progressive memory loss. MMSE score 18/30 indicating significant cognitive impairment. Brain MRI shows prominent bilateral hippocampal atrophy. No evidence of stroke on imaging. CSF biomarkers with elevated phosphorylated tau and low amyloid-beta levels. Patient started on Donepezil (Aricept). Clinical diagnosis of Alzheimer's disease established."),
    ("VaD", "70-year-old patient with acute onset cognitive decline following multiple strokes. Brain MRI shows multiple cerebral infarctions in different vascular territories with stepwise progression of cognitive deficits. Chronic white matter microangiopathy noted on imaging. History of hypertension and atrial fibrillation. MMSE 20/30. Cognitive decline occurred acutely after each CVA event. Diagnosed with vascular dementia secondary to cerebrovascular disease."),
    ("FTD", "68-year-old patient presenting with early behavioral and language changes. Family reports significant personality changes, inappropriate social behavior, and loss of inhibition over past year. Speech is dysarthric and mostly unintelligible at times. Patient shows language problems with word-finding difficulty. Brain MRI demonstrates anterior temporal and prefrontal lobe atrophy bilaterally. MMSE 22/30. MoCA 18/30 with executive function significantly impaired. Clinical diagnosis of Frontotemporal Dementia."),
    ("Normal", "65-year-old patient with normal cognitive function. MMSE score 29/30 and MoCA 28/30, both within normal limits. Brain imaging completely normal with no atrophy. No memory complaints. Patient reports normal daily functioning and independent activities of daily living. No dementia diagnosis. Neurological examination normal. Patient is cognitively intact with normal orientation x3.")
]

url = "http://localhost:8001/analyze_text"

client = httpx.Client(timeout=180.0)  # Increased from 30 to 180 seconds for Ollama

for name, text in tests:
    print('\n' + '='*20 + f' Test: {name} ' + '='*20)
    try:
        r = client.post(url, headers={'Content-Type':'text/plain'}, content=text)
        try:
            data = r.json()
            print(json.dumps(data, indent=2, ensure_ascii=False))
        except Exception as e:
            print('Response not JSON:', r.text)
    except Exception as e:
        print('Request failed:', str(e))

client.close()

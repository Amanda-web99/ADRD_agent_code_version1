# Professional ADRD Diagnostic Prompts (Version 1)
# These are the original detailed medical prompts designed for high-accuracy diagnosis
# Use these when switching to more capable LLMs (GPT-4, Claude, etc.)
# Current simplified versions are in app/agents.py for local Ollama compatibility

DIAGNOSIS_AGENT_PROMPT_PROFESSIONAL = """
Your task: Determine whether the patient has ADRD (Alzheimer's Disease and Related Dementias)

POSITIVE INDICATORS OF ADRD (Look for these keywords):
History Section:
- Dementia diagnosis (any type)
- Memory loss, memory impairment, worsening memory
- Cognitive decline, cognitive impairment, increasing confusion
- Lethargy, altered mental status
- Gait disturbance, functional decline, fall(s)
- Stroke (CVA): supports vascular contribution
- Confusion, confusion at baseline
- Bedridden, not coherently, unable to answer questions
- Urinary incontinence (late stage indicator)

Physical Exam & Cognitive Signals:
- Cognitive impairment, chronic cognitive impairment
- Oriented x1 or Oriented to person only (vs normal "Oriented x3")
- Speech is dysarthric, unintelligible, slurred
- Unable to follow commands or answers questions appropriately
- Redirection needed (sign of confusion)
- Confabulation present
- Delirium (ONLY if context shows underlying dementia, not just acute delirium)

Radiology Findings:
- Atrophy (cortical, cerebral, or general brain atrophy)
- Hippocampal atrophy (strong AD indicator)
- White matter changes, chronic white matter microangiopathy (VaD indicator)

Lab Results:
- B12 deficiency (if also cognitive symptoms)
- Thyroid abnormality/TSH/T4 abnormal (rule out thyroid dementia)
- Phosphorylated tau elevated (AD biomarker)

Cognitive Tests with SCORES:
- MMSE score <24 (abnormal, supports cognitive impairment)
- MoCA score <26 (abnormal)
- Other tests: Mini-Cog, SLUMS, AD8, CDR, BIMS

Medications:
- Dementia medications present (Donepezil, Memantine, etc.)

EXCLUSION CRITERIA (Lower confidence for "No"):
- All cognitive tests normal (MMSE >27, MoCA >25)
- No atrophy on imaging
- Normal thyroid/B12
- Active delirium from infections/metabolic (without baseline dementia diagnosis)
- On antipsychotics only (not dementia meds)

CONFIDENCE SCORING:
- "Yes" with high confidence (80-100): Clear diagnosis + multiple supporting findings
- "Yes" with moderate confidence (60-80): Clinical diagnosis + some findings
- "Uncertain" (40-60): Mixed findings or incomplete information
- "No" (0-40): No dementia diagnosis, normal cognition, all tests normal

Make your judgment based on the keywords found, imaging results, test scores, and clinical context.
"""

SUBTYPE_AGENT_PROMPT_PROFESSIONAL = """
Your task: Determine the specific ADRD subtype based on clinical evidence

DIAGNOSTIC CRITERIA FOR EACH SUBTYPE:

=== AD (ALZHEIMER'S DISEASE) ===
PRIMARY INDICATORS (Pick this if ANY are strong):
Imaging:
- Hippocampal atrophy (MOST SPECIFIC for AD)
- Cortical atrophy, generalcortical atrophy
- Medial temporal lobe atrophy

Memory Pattern:
- Memory loss, memory impairment, worsening memory (cardinal feature)
- Progressive memory decline (6+ months)
- Memory problems early in disease course

Biomarkers:
- Elevated phosphorylated tau (p-tau)
- Low amyloid-beta (A-beta)
- Abnormal CSF biomarkers

Cognitive Tests:
- Very low MMSE (<18) with memory emphasis
- Low MoCA with memory domain affected

Medications:
- Donepezil (Aricept) prescribed (used for AD)
- Memantine (Namenda) prescribed (used for moderate-severe AD)

=== VaD (VASCULAR DEMENTIA) ===
PRIMARY INDICATORS (Pick this if ANY are strong):
Vascular Events:
- CVA (Cerebrovascular accident) history
- Stroke, multiple strokes mentioned
- History of TIA(s)

Imaging:
- Cerebral infarction (acute or chronic)
- White matter changes, white matter disease
- Chronic white matter microangiopathy
- Multiple lacunar infarcts

Pattern of Decline:
- Stepwise progression (cognitive decline in steps, not gradual)
- Cognitive decline following stroke event(s)

Risk Factors:
- Hypertension, diabetes, atrial fibrillation
- History of cardiovascular disease

=== FTD (FRONTOTEMPORAL DEMENTIA) ===
PRIMARY INDICATORS (Pick this if BEHAVIOR or LANGUAGE changes prominent):
Behavioral Changes:
- Behavioral problems, inappropriate behavior
- Personality changes
- Loss of inhibition, disinhibition
- Agitation, aggression (early in course)

Language Problems:
- Speech is dysarthric, slurred, dysphasia (language impairment)
- Speech is very dysarthric and mostly unintelligible
- Language decline, word-finding difficulty
- Non-fluent speech, progressive aphasia

Imaging:
- Prefrontal atrophy, frontal lobe atrophy
- Anterior temporal atrophy, temporal lobe atrophy
- Focal frontal or temporal degeneration

Personality/Social:
- Loss of empathy, apathy
- Socially inappropriate behavior
- Lack of awareness of deficits

=== LBD (LEWY BODY DEMENTIA) ===
PRIMARY INDICATORS (Pick this if Motor + Cognitive symptoms):
Movement Disorders:
- Parkinsonian symptoms (rigidity, tremor, bradykinesia)
- Levodopa mentioned (used for Parkinson symptoms)
- Gait disturbance, balance problems
- Movement problems, shuffling gait

Visual Symptoms:
- Visual hallucinations (seeing things not there)
- Hallucinations (visual, not auditory)

Cognitive Pattern:
- Fluctuating cognition, cognitive fluctuations
- Attention/executive dysfunction more than memory
- Delirium-like episodes, acute confusion

=== MIXED ===
Indicators (Pick this if features of MULTIPLE subtypes):
- Multiple AD AND VaD features present
- Evidence of both hippocampal atrophy AND cerebral infarcts
- Both memory problems AND stroke history
- FTD + Parkinson features

=== UNSPECIFIED ===
Indicators (Pick this if):
- Clear ADRD diagnosis but no clear subtype markers
- Insufficient neuroimaging
- Only cognitive test scores, no other specifics
- Generic dementia diagnosis without subtype mentioned

DECISION PROCESS:
1. Count which subtype(s) have the MOST matching indicators
2. Look for "cardinal features" (especially strong indicators):
   - Hippocampal atrophy → AD
   - CVA/stroke history → VaD
   - Behavioral/language changes → FTD
   - Movement problems + visual hallucinations → LBD
3. If TWO or more subtypes equally present → Mark as Mixed
4. If no clear subtype → Mark as Unspecified
5. Set confidence based on strength and number of indicators:
   - High confidence (80-100): Cardinal features + multiple supporting findings
   - Moderate confidence (60-80): Clear features of specific subtype
   - Low confidence (40-60): Only one or two indicators
"""

# 使用说明
"""
迁移到更强的LLM时（如GPT-4, Claude, Qwen等）：

1. 在 app/agents.py 的 _get_agent_instructions 函数中
2. 替换 "DiagnosisAgent" 对应的 prompt，使用 DIAGNOSIS_AGENT_PROMPT_PROFESSIONAL
3. 替换 "SubtypeAgent" 对应的 prompt，使用 SUBTYPE_AGENT_PROMPT_PROFESSIONAL

修改示例：
from prompts_professional_v1 import DIAGNOSIS_AGENT_PROMPT_PROFESSIONAL, SUBTYPE_AGENT_PROMPT_PROFESSIONAL

instructions = {
    "DiagnosisAgent": DIAGNOSIS_AGENT_PROMPT_PROFESSIONAL,
    "SubtypeAgent": SUBTYPE_AGENT_PROMPT_PROFESSIONAL,
    ...
}
"""

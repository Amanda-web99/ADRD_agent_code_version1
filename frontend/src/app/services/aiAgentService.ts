export type HighlightCategory =
  | "history"
  | "lab"
  | "medication"
  | "radiology"
  | "cognitive"

export interface TextSpan {
  id: string;
  start: number;
  end: number;
  text: string;
  category: HighlightCategory;
  evidenceId?: number;
}

export interface Evidence {
  id: number;
  type: string;
  displayText: string;
  spanText: string;
  source: string;
  strength: "STRONG" | "MODERATE" | "WEAK";
  category: HighlightCategory;
  spanId: string;
}

export interface TimelineEvent {
  id: string;
  year: string;
  event: string;
  description: string;
  type: "onset" | "diagnosis" | "treatment" | "progression" | "current";
}

export interface ClinicalNote {
  patientId: string;
  notes: string;
  admissionDate?: string;
}

export interface AnalysisResult {
  patientId: string;
  admissionDate: string;
  rawNotes: string;
  diagnosis: {
    hasADRD: "Yes" | "No" | "Uncertain";
    subtype: "AD" | "VaD" | "FTD" | "LBD" | "Mixed" | "Unspecified" | null;
    confidence: number;
  };
  spans: TextSpan[];
  evidence: Evidence[];
  timeline: TimelineEvent[];
  acuteVsChronic: string;
  hasConflict: boolean;
  hasDelirium: boolean;
}

interface BackendHighlight {
  start: number;
  end: number;
  label: string;
  section?: "history" | "lab" | "medication" | "radiology" | "cognitive" | string;
}

interface BackendEvidence {
  id: string;
  title: string;
  strength: "STRONG" | "MODERATE" | "WEAK";
  quote: string;
  source?: string;
  highlight: BackendHighlight;
}

interface BackendTimeline {
  date_label: string;
  text: string;
}

interface BackendResponse {
  adrddx: "Yes" | "No" | "Uncertain";
  subtype: "AD" | "VaD" | "FTD" | "LBD" | "Mixed" | "Unspecified";
  confidence: number;
  evidence: BackendEvidence[];
  highlights: BackendHighlight[];
  cognitive_tests: string[];
  adrd_meds: string[];
  function_signals: string[];
  delirium_triggers: string[];
  timeline: BackendTimeline[];
}

const API_URL =
  (globalThis as { __API_BASE_URL__?: string }).__API_BASE_URL__ ||
  "http://localhost:8002";

function normalizeCategory(label: string): HighlightCategory {
  const key = (label || "").toLowerCase();
  if (key.includes("cognitive") || key.includes("mmse") || key.includes("moca") || key.includes("slums") || key.includes("ad8") || key.includes("cdr")) return "cognitive";
  if (key.includes("med") || key.includes("prescription") || key.includes("donepezil") || key.includes("memantine") || key.includes("rivastigmine") || key.includes("galantamine") || key.includes("aricept") || key.includes("namenda")) return "medication";
  if (key.includes("radiology") || key.includes("mri") || key.includes("ct") || key.includes("atrophy") || key.includes("white matter") || key.includes("microangiopathy")) return "radiology";
  if (key.includes("lab") || key.includes("b12") || key.includes("tsh") || key.includes("t4") || key.includes("rpr") || key.includes("hiv") || key.includes("tau")) return "lab";
  return "history";
}

function normalizeCategoryFromBackend(
  section: BackendHighlight["section"] | undefined,
  label: string,
  title: string
): HighlightCategory {
  const sec = (section || "").toLowerCase();
  if (sec === "history" || sec === "lab" || sec === "medication" || sec === "radiology" || sec === "cognitive") {
    return sec as HighlightCategory;
  }
  return normalizeCategory(`${label} ${title}`);
}

function mapTimeline(raw: BackendTimeline[], admissionDate: string): TimelineEvent[] {
  if (!raw || raw.length === 0) return [];

  return raw.map((ev, idx) => ({
    id: `ev-${idx + 1}`,
    year: ev.date_label || admissionDate,
    event: ev.text,
    description: "",
    type: idx === raw.length - 1 ? "current" : "progression",
  }));
}

function deriveAcuity(noteText: string): string {
  const n = noteText.toLowerCase();
  if (n.includes("progressive") || n.includes("years") || n.includes("chronic")) {
    return "Chronic neurodegenerative process – pre-existing dementia likely";
  }
  if (n.includes("acute") || n.includes("sudden") || n.includes("delirium") || n.includes("infection")) {
    return "Acute-on-chronic – consider superimposed delirium";
  }
  return "Insufficient data to classify acuity";
}

function sanitizeRange(start: number, end: number, textLength: number): { start: number; end: number } | null {
  const safeStart = Math.max(0, Math.min(textLength, start));
  const safeEnd = Math.max(0, Math.min(textLength, end));
  if (!Number.isFinite(safeStart) || !Number.isFinite(safeEnd) || safeEnd <= safeStart) return null;
  return { start: safeStart, end: safeEnd };
}

function resolveOverlaps(spans: TextSpan[]): TextSpan[] {
  const sorted = [...spans].sort((a, b) => {
    if (a.start !== b.start) return a.start - b.start;
    const aHasEvidence = a.evidenceId != null ? 1 : 0;
    const bHasEvidence = b.evidenceId != null ? 1 : 0;
    if (aHasEvidence !== bHasEvidence) return bHasEvidence - aHasEvidence;
    return (b.end - b.start) - (a.end - a.start);
  });

  const accepted: TextSpan[] = [];
  for (const span of sorted) {
    const last = accepted[accepted.length - 1];
    if (!last || span.start >= last.end) {
      accepted.push(span);
    }
  }
  return accepted;
}

function mapBackendToAnalysisResult(
  clinicalNote: ClinicalNote,
  backend: BackendResponse
): AnalysisResult {
  const admissionDate = clinicalNote.admissionDate || new Date().toISOString().split("T")[0];
  const textLength = clinicalNote.notes.length;
  const evidence = backend.evidence || [];

  const mappedEvidence: Evidence[] = evidence.map((ev, idx) => {
    const category = normalizeCategoryFromBackend(ev.highlight?.section, ev.highlight?.label || "", ev.title || "");
    const spanId = `span-${idx + 1}`;
    return {
      id: idx + 1,
      type: ev.title || "Evidence",
      displayText: `${ev.title || "Evidence"}: "${ev.quote || ""}"`,
      spanText: ev.quote || "",
      source: ev.source || "Clinical Note",
      strength: ev.strength || "MODERATE",
      category,
      spanId,
    };
  });

  const evidenceSpanIndex = new Map<string, { evidenceId: number; spanId: string }>();
  mappedEvidence.forEach((ev, idx) => {
    const h = evidence[idx]?.highlight;
    if (!h || !Number.isInteger(h.start) || !Number.isInteger(h.end)) return;
    const category = normalizeCategoryFromBackend(h.section, h.label || "", ev.type || "");
    evidenceSpanIndex.set(`${h.start}:${h.end}:${category}`, { evidenceId: ev.id, spanId: ev.spanId });
  });

  const evidenceHighlights = evidence
    .map((ev) => ev.highlight)
    .filter((h): h is BackendHighlight => Boolean(h));

  const rawHighlights = [
    ...(backend.highlights || []),
    ...evidenceHighlights,
  ];

  const candidateSpans: TextSpan[] = rawHighlights
    .map((h, idx) => {
      if (!Number.isInteger(h.start) || !Number.isInteger(h.end)) return null;
      const safe = sanitizeRange(h.start, h.end, textLength);
      if (!safe) return null;

      const category = normalizeCategoryFromBackend(h.section, h.label || "", "");
      const key = `${safe.start}:${safe.end}:${category}`;
      const mapped = evidenceSpanIndex.get(key);

      return {
        id: mapped?.spanId || `span-h-${idx + 1}`,
        start: safe.start,
        end: safe.end,
        text: clinicalNote.notes.slice(safe.start, safe.end),
        category,
        evidenceId: mapped?.evidenceId,
      } as TextSpan;
    })
    .filter((span): span is TextSpan => span !== null);

  const spans = resolveOverlaps(candidateSpans);

  const hasDelirium = (backend.delirium_triggers || []).length > 0;
  const hasConflict = backend.adrddx === "Yes" && hasDelirium;

  return {
    patientId: clinicalNote.patientId,
    admissionDate,
    rawNotes: clinicalNote.notes,
    diagnosis: {
      hasADRD: backend.adrddx,
      subtype: backend.subtype || "Unspecified",
      confidence: Math.max(0, Math.min(100, Number(backend.confidence || 0))),
    },
    spans,
    evidence: mappedEvidence,
    timeline: mapTimeline(backend.timeline || [], admissionDate),
    acuteVsChronic: deriveAcuity(clinicalNote.notes),
    hasConflict,
    hasDelirium,
  };
}

export class MultiAgentAnalyzer {
  async analyze(clinicalNote: ClinicalNote): Promise<AnalysisResult> {
    const response = await fetch(`${API_URL}/analyze_text`, {
      method: "POST",
      headers: {
        "Content-Type": "text/plain",
      },
      body: clinicalNote.notes,
    });

    if (!response.ok) {
      const txt = await response.text();
      throw new Error(`Backend request failed (${response.status}): ${txt}`);
    }

    const data = (await response.json()) as BackendResponse;
    return mapBackendToAnalysisResult(clinicalNote, data);
  }
}

import { useState, useRef, useEffect, useCallback } from "react";
import { AlertTriangle, HelpCircle, User, ChevronRight, CheckCircle } from "lucide-react";

// ─── Types ────────────────────────────────────────────────────
type Category = "diagnosis" | "cognitive" | "medication" | "function" | "history" | "acute";
type ADRDOption = "Yes" | "No" | "Uncertain";
type SubtypeOption = "AD" | "VaD" | "FTD" | "LBD" | "Mixed" | "Unspecified";
type Strength = "STRONG" | "MODERATE" | "WEAK" | null;

// ─── Highlight colours — mirror section navigator dots ─────────
const CAT: Record<Category, { bg: string; text: string }> = {
  diagnosis:  { bg: "bg-blue-100",    text: "text-blue-900"    }, // History → blue
  history:    { bg: "bg-blue-100",    text: "text-blue-900"    }, // History → blue
  function:   { bg: "bg-blue-100",    text: "text-blue-900"    }, // History → blue
  medication: { bg: "bg-purple-100",  text: "text-purple-900"  }, // Medications → purple
  cognitive:  { bg: "bg-rose-100",    text: "text-rose-900"    }, // Cognitive Tests → rose
  acute:      { bg: "bg-emerald-100", text: "text-emerald-900" }, // Lab → emerald
};

const STRENGTH_CLS: Record<string, string> = {
  STRONG:   "text-green-600",
  MODERATE: "text-amber-600",
  WEAK:     "text-red-500",
};

// ─── Left section navigator ───────────────────────────────────
const LEFT_NAV = [
  { key: "history",   label: "History",        dot: "bg-blue-500"    },
  { key: "lab",       label: "Lab",            dot: "bg-emerald-500" },
  { key: "meds",      label: "Medications",    dot: "bg-purple-500"  },
  { key: "radiology", label: "Radiology",      dot: "bg-orange-500"  },
  { key: "cognitive", label: "Cognitive Tests",dot: "bg-rose-500"    },
];

// ─── Top tab bar: clinical note sections ─────────────────────
const NOTE_SECTIONS = [
  { key: "cc",       label: "Chief Complaint"             },
  { key: "hpi",      label: "History of Present Illness"  },
  { key: "pmh",      label: "Past Medical History"        },
  { key: "pe",       label: "Physical Exam"               },
  { key: "pr",       label: "Pertinent Results"           },
  { key: "bhc",      label: "Brief Hospital Course"       },
  { key: "dd",       label: "Discharge Diagnosis"         },
  { key: "dc",       label: "Discharge Condition"         },
  { key: "medssec",  label: "Medications"                 },
];

// ─── Evidence panel data ──────────────────────────────────────
const EVIDENCE: {
  id: number; type: string; strength: Strength;
  desc: string; spanId: string;
}[] = [
  { id: 1, type: "Diagnosis Evidence",  strength: "STRONG",   desc: '"history of progressive dementia" (HPI)',       spanId: "s1"  },
  { id: 2, type: "Cognitive Test",      strength: "MODERATE", desc: "MMSE 18/30 (Pertinent Results)",                spanId: "s3"  },
  { id: 3, type: "Medication",          strength: "MODERATE", desc: "donepezil 10mg daily (Medications)",            spanId: "s5"  },
  { id: 4, type: "Functional Decline",  strength: "MODERATE", desc: "assistance with ADLs (Physical Exam)",          spanId: "s6"  },
  { id: 5, type: "Chronicity",          strength: null,       desc: "progressive course over years (HPI)",           spanId: "s1"  },
  { id: 6, type: "Delirium Trigger",    strength: "WEAK",     desc: "acute confusion with UTI (Hospital Course)",    spanId: "s8"  },
];

// ─── Timeline data ────────────────────────────────────────────
const TIMELINE = [
  { year: "2019",           dot: "bg-blue-500",   label: "Memory decline"      },
  { year: "2021",           dot: "bg-green-500",  label: "Started donepezil"   },
  { year: "2024",           dot: "bg-gray-400",   label: "Worsening confusion" },
  { year: "This admission", dot: "bg-blue-500",   label: "UTI >\ndelirium"     },
];

// ─── Main component ───────────────────────────────────────────
export default function ADRDReview() {
  const [activeLeftNav, setActiveLeftNav]     = useState("history");
  const [activeNoteSection, setActiveNoteSection] = useState("cc");
  const [activeSpan, setActiveSpan]           = useState<string | null>(null);
  const [activeEv, setActiveEv]               = useState<number | null>(null);
  const [adrd, setAdrd]                       = useState<ADRDOption>("Yes");
  const [subtype, setSubtype]                 = useState<SubtypeOption>("AD");

  const middleRef  = useRef<HTMLDivElement>(null);
  const tabBarRef  = useRef<HTMLDivElement>(null);

  // ── IntersectionObserver: update active tab as user scrolls ──
  useEffect(() => {
    const root = middleRef.current;
    if (!root) return;
    const observer = new IntersectionObserver(
      (entries) => {
        // Pick the first entry that is intersecting
        const visible = entries.find((e) => e.isIntersecting);
        if (visible) {
          const key = visible.target.id.replace("note-", "");
          setActiveNoteSection(key);
          // Scroll the corresponding tab into view
          const tabEl = document.getElementById(`tab-${key}`);
          tabEl?.scrollIntoView({ inline: "nearest", block: "nearest" });
        }
      },
      { root, threshold: 0.25 }
    );
    NOTE_SECTIONS.forEach(({ key }) => {
      const el = document.getElementById(`note-${key}`);
      if (el) observer.observe(el);
    });
    return () => observer.disconnect();
  }, []);

  // ── Click tab → scroll to note section ───────────────────────
  const scrollToNoteSection = useCallback((key: string) => {
    setActiveNoteSection(key);
    const el = document.getElementById(`note-${key}`);
    if (el && middleRef.current) {
      middleRef.current.scrollTo({ top: (el as HTMLElement).offsetTop - 8, behavior: "smooth" });
    }
  }, []);

  // ── Click left nav → same scroll ─────────────────────────────
  const scrollToLeftNav = useCallback((key: string) => {
    setActiveLeftNav(key);
    // Map left nav keys to note section keys
    const map: Record<string, string> = {
      history: "hpi", lab: "pr", meds: "medssec", radiology: "pr", cognitive: "pr",
    };
    scrollToNoteSection(map[key] || "hpi");
  }, [scrollToNoteSection]);

  // ── Jump from evidence → highlighted span ────────────────────
  const jumpToSpan = (spanId: string, evId: number) => {
    setActiveSpan(spanId);
    setActiveEv(evId);
    setTimeout(() => {
      document.getElementById(spanId)?.scrollIntoView({ behavior: "smooth", block: "center" });
    }, 50);
  };

  // ── Click a highlight → focus evidence ───────────────────────
  const onSpanClick = (spanId: string, evId?: number) => {
    setActiveSpan(spanId);
    if (evId) {
      setActiveEv(evId);
      setTimeout(() => {
        document.getElementById(`ev-${evId}`)?.scrollIntoView({ behavior: "smooth", block: "nearest" });
      }, 50);
    }
  };

  // ── Inline highlight component ────────────────────────────────
  const H = ({ id, cat, evId, children }: {
    id: string; cat: Category; evId?: number; children: string;
  }) => {
    const isActive = activeSpan === id;
    return (
      <span
        id={id}
        onClick={() => onSpanClick(id, evId)}
        className={`${CAT[cat].bg} ${CAT[cat].text} px-0.5 rounded-sm cursor-pointer
          transition-all duration-150 ${isActive ? "ring-2 ring-blue-400 ring-offset-1" : ""}`}
      >
        {children}
      </span>
    );
  };

  // ── Note section wrapper ──────────────────────────────────────
  const NoteSection = ({ id, title, children }: {
    id: string; title: string; children: React.ReactNode;
  }) => (
    <section id={`note-${id}`} className="mb-7">
      <h3 className="text-sm font-bold text-gray-700 uppercase tracking-wide mb-2 pb-1 border-b border-gray-200">
        {title}
      </h3>
      {children}
    </section>
  );

  return (
    <div className="h-screen flex flex-col bg-white text-gray-900 overflow-hidden">

      {/* ════════════ HEADER ════════════ */}
      <header className="flex-none border-b border-gray-200 px-5 py-3">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-xl font-bold text-gray-900 leading-tight tracking-tight">
              AI-Powered ADRD Chart Review Interface
            </h1>
            <p className="text-xs text-gray-500 mt-0.5">
              Patient ID:&nbsp;<span className="text-gray-700 font-medium">1002345</span>
              &nbsp;|&nbsp;Admission Date:&nbsp;<span className="text-gray-700 font-medium">2024-04-10</span>
            </p>
          </div>
          <div className="flex items-center gap-2 mt-1">
            <span className="inline-flex items-center gap-1.5 text-xs text-orange-700 bg-orange-50 border border-orange-200 px-3 py-1 rounded-md">
              <AlertTriangle className="w-3.5 h-3.5" />
              Conflict Alert
            </span>
            <span className="inline-flex items-center text-xs text-gray-700 bg-white border border-gray-300 px-3 py-1 rounded-md">
              Delirium Warning
            </span>
            <button className="w-7 h-7 flex items-center justify-center rounded-full border border-gray-300 text-gray-500 hover:bg-gray-50">
              <HelpCircle className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      {/* ════════════ 3-COLUMN BODY ════════════ */}
      <div className="flex flex-1 overflow-hidden">

        {/* ── LEFT: Section Navigator ── */}
        <aside className="w-44 flex-none border-r border-gray-200 bg-white flex flex-col">
          <div className="px-4 pt-3 pb-1.5">
            <p className="text-xs font-semibold text-gray-700">Section Navigator</p>
          </div>
          <nav className="flex-1 overflow-y-auto">
            {LEFT_NAV.map((sec) => {
              const isActive = activeLeftNav === sec.key;
              return (
                <button
                  key={sec.key}
                  onClick={() => scrollToLeftNav(sec.key)}
                  className={`w-full flex items-center gap-2 px-4 py-2.5 text-sm text-left transition-colors
                    ${isActive ? "bg-gray-100" : "hover:bg-gray-50"}`}
                >
                  <span className={`w-2 h-2 rounded-full shrink-0 ${sec.dot}`} />
                  <span className={`flex-1 ${isActive ? "font-medium text-gray-900" : "text-gray-600"}`}>
                    {sec.label}
                  </span>
                  <ChevronRight className={`w-3 h-3 ${isActive ? "text-gray-500" : "text-gray-300"}`} />
                </button>
              );
            })}
          </nav>
        </aside>

        {/* ── MIDDLE: Clinical Note ── */}
        <main ref={middleRef} className="flex-1 overflow-y-auto border-r border-gray-200 flex flex-col">

          {/* ── Sticky top tab bar ── */}
          <div className="sticky top-0 z-10 bg-white border-b border-gray-200">
            <div
              ref={tabBarRef}
              className="flex overflow-x-auto scrollbar-hide px-4 gap-0"
              style={{ scrollbarWidth: "none" }}
            >
              {NOTE_SECTIONS.map((sec) => {
                const active = activeNoteSection === sec.key;
                return (
                  <button
                    key={sec.key}
                    id={`tab-${sec.key}`}
                    onClick={() => scrollToNoteSection(sec.key)}
                    className={`shrink-0 text-xs px-3 py-2.5 border-b-2 whitespace-nowrap transition-colors ${
                      active
                        ? "border-blue-500 text-blue-600 font-medium"
                        : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                    }`}
                  >
                    {sec.label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* ── Note content ── */}
          <div className="px-6 py-5 flex-1">
            <h2 className="text-base font-semibold text-gray-900 mb-5">
              Clinical Note with AI Highlights
            </h2>

            {/* 1. Chief Complaint */}
            <NoteSection id="cc" title="Chief Complaint">
              <p className="text-sm text-gray-800 leading-relaxed">
                Acute confusion and generalized weakness.
              </p>
            </NoteSection>

            {/* 2. History of Present Illness */}
            <NoteSection id="hpi" title="History of Present Illness">
              <p className="text-sm text-gray-800 leading-relaxed mb-3">
                Patient is an 81-year-old female with a history of{" "}
                <H id="s1" cat="diagnosis" evId={1}>progressive memory decline</H>
                {" "}for the past 5 years. Family reports worsening{" "}
                <H id="s2" cat="history">confusion</H>
                {" "}and difficulty managing finances. No prior psychiatric history.
              </p>
              <p className="text-sm text-gray-800 leading-relaxed">
                Baseline per family: oriented to person only, needs help with all
                instrumental ADLs.
              </p>
            </NoteSection>

            {/* 3. Past Medical History */}
            <NoteSection id="pmh" title="Past Medical History">
              <ul className="text-sm text-gray-800 leading-relaxed space-y-1 list-none">
                <li>1.&nbsp;
                  <H id="s4" cat="diagnosis" evId={1}>Alzheimer's disease</H>
                  {" "}— diagnosed approximately 3 years ago
                </li>
                <li>2. Hypertension — on lisinopril</li>
                <li>3. Hyperlipidemia — on atorvastatin</li>
                <li>4. Osteoporosis</li>
              </ul>
            </NoteSection>

            {/* 4. Physical Exam */}
            <NoteSection id="pe" title="Physical Exam">
              <p className="text-sm text-gray-800 leading-relaxed mb-2">
                <span className="font-medium">Vitals:</span> T 38.1°C, HR 102, BP 118/72, RR 18, SpO₂ 96% on room air.
              </p>
              <p className="text-sm text-gray-800 leading-relaxed mb-2">
                <span className="font-medium">General:</span> Elderly female, appears uncomfortable, mildly agitated.
              </p>
              <p className="text-sm text-gray-800 leading-relaxed mb-2">
                <span className="font-medium">Neuro:</span> Alert but disoriented to time and place. No focal neurological deficits. Commands followed inconsistently.
              </p>
              <p className="text-sm text-gray-800 leading-relaxed">
                <span className="font-medium">Functional:</span> Requires{" "}
                <H id="s6" cat="function" evId={4}>assistance with bathing</H>
                {" "}and{" "}
                <H id="s7" cat="function" evId={4}>dressing</H>
                {" "}per caregiver report. Able to feed herself. Ambulates with a walker.
              </p>
            </NoteSection>

            {/* 5. Pertinent Results */}
            <NoteSection id="pr" title="Pertinent Results">
              <p className="text-sm text-gray-800 leading-relaxed mb-2">
                <span className="font-medium">Urinalysis:</span> Positive for nitrites and leukocyte esterase, &gt;100 WBC/hpf. Consistent with{" "}
                <H id="s9" cat="acute" evId={6}>UTI</H>.
              </p>
              <p className="text-sm text-gray-800 leading-relaxed mb-2">
                <span className="font-medium">Blood cultures:</span> 2/2 bottles positive for <em>E. coli</em> — meeting{" "}
                <H id="s10" cat="acute" evId={6}>sepsis</H>
                {" "}criteria.
              </p>
              <p className="text-sm text-gray-800 leading-relaxed mb-2">
                <span className="font-medium">BMP:</span> Na 134, K 4.1, BUN 28, Cr 1.1 (at baseline).
              </p>
              <p className="text-sm text-gray-800 leading-relaxed mb-2">
                <span className="font-medium">CBC:</span> WBC 14.2 × 10³/µL (elevated).
              </p>
              <p className="text-sm text-gray-800 leading-relaxed">
                <span className="font-medium">Cognitive assessment:</span>{" "}
                <H id="s3" cat="cognitive" evId={2}>MMSE 18/30</H>
                {" "}on admission (prior baseline 22/30, 6 months ago).
              </p>
            </NoteSection>

            {/* 6. Brief Hospital Course */}
            <NoteSection id="bhc" title="Brief Hospital Course">
              <p className="text-sm text-gray-800 leading-relaxed mb-2">
                Patient admitted for{" "}
                <H id="s8" cat="acute" evId={6}>acute confusion</H>
                {" "}and weakness in the setting of UTI and sepsis. Initiated IV ceftriaxone with subsequent transition to oral ciprofloxacin on hospital day 3.
              </p>
              <p className="text-sm text-gray-800 leading-relaxed">
                <H id="s11" cat="cognitive" evId={2}>Mental status improved</H>
                {" "}significantly over hospital days 2–4, though not yet returned to prior baseline. Geriatrics and cognitive neurology consulted for delirium management and long-term ADRD care planning.
              </p>
            </NoteSection>

            {/* 7. Discharge Diagnosis */}
            <NoteSection id="dd" title="Discharge Diagnosis">
              <ul className="text-sm text-gray-800 leading-relaxed space-y-1 list-none">
                <li>1. Delirium superimposed on Alzheimer's disease dementia</li>
                <li>2. Urinary tract infection / urosepsis — resolved</li>
                <li>3. Generalized weakness, improved</li>
              </ul>
            </NoteSection>

            {/* 8. Discharge Condition */}
            <NoteSection id="dc" title="Discharge Condition">
              <p className="text-sm text-gray-800 leading-relaxed mb-2">
                Stable. Oriented to person and place. Tolerating oral intake. Ambulating with walker.
              </p>
              <div className="flex items-center gap-2 mt-3">
                <CheckCircle className="w-4 h-4 text-green-500 shrink-0" />
                <span className="text-sm">
                  <span className="font-medium text-gray-700">Acute vs Chronic:&nbsp;</span>
                  <span className="text-gray-600">Chronic neurodegenerative process likely — acute delirium superimposed on pre-existing ADRD</span>
                </span>
              </div>
            </NoteSection>

            {/* 9. Medications */}
            <NoteSection id="medssec" title="Medications">
              <p className="text-sm text-gray-700 mb-1.5 font-medium">Continued home medications:</p>
              <ul className="text-sm text-gray-800 leading-relaxed space-y-1 mb-3 list-none">
                <li>—&nbsp;
                  <H id="s5" cat="medication" evId={3}>donepezil 10 mg daily</H>
                  {" "}(Alzheimer's disease)
                </li>
                <li>— Lisinopril 5 mg daily (hypertension)</li>
                <li>— Atorvastatin 40 mg nightly (hyperlipidemia)</li>
              </ul>
              <p className="text-sm text-gray-700 mb-1.5 font-medium">New medications:</p>
              <ul className="text-sm text-gray-800 leading-relaxed space-y-1 list-none">
                <li>— Ciprofloxacin 500 mg BID × 7 days (complete course for UTI)</li>
              </ul>
            </NoteSection>

            {/* Timeline */}
            <div className="mb-6">
              <p className="text-sm font-bold text-gray-700 uppercase tracking-wide mb-4 pb-1 border-b border-gray-200">
                Disease Timeline
              </p>
              <div className="relative">
                <div
                  className="absolute bg-gray-300 h-px"
                  style={{ top: 32, left: "12.5%", right: "12.5%", zIndex: 0 }}
                />
                <div className="relative flex" style={{ zIndex: 1 }}>
                  {TIMELINE.map((item, idx) => (
                    <div key={idx} className="flex-1 flex flex-col items-center">
                      <span className="text-xs text-gray-600 font-medium mb-2 text-center whitespace-nowrap">
                        {item.year}
                      </span>
                      <div className={`w-4 h-4 rounded-full ${item.dot} mb-2 shrink-0`} />
                      <p className="text-xs text-gray-700 text-center leading-snug whitespace-pre-line">
                        {item.label}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>

          </div>
        </main>

        {/* ── RIGHT: Structured Decision Panel ── */}
        <aside className="w-72 flex-none bg-white overflow-y-auto">
          <div className="flex items-center justify-between px-5 py-3 border-b border-gray-100">
            <span className="text-sm font-semibold text-gray-800">Structured Decision Panel</span>
            <div className="flex items-center gap-2">
              <button className="text-gray-400 hover:text-gray-600">
                <HelpCircle className="w-4 h-4" />
              </button>
              <div className="w-7 h-7 rounded-full bg-gray-200 flex items-center justify-center">
                <User className="w-4 h-4 text-gray-500" />
              </div>
            </div>
          </div>

          <div className="px-5 py-4">
            {/* ADRD Diagnosis */}
            <p className="text-sm font-semibold text-gray-900 mb-3">ADRD Diagnosis</p>

            <div className="flex items-center gap-3 mb-2">
              <span className="text-xs text-gray-500 w-14 shrink-0">ADRD:</span>
              <div className="flex gap-1.5">
                {(["Yes", "No", "Uncertain"] as ADRDOption[]).map((opt) => (
                  <button key={opt} onClick={() => setAdrd(opt)}
                    className={`text-xs px-2.5 py-1 rounded border transition-all ${
                      adrd === opt
                        ? "border-blue-500 text-blue-700 bg-blue-50"
                        : "border-gray-300 text-gray-500 hover:border-gray-400 bg-white"
                    }`}>
                    {opt}
                  </button>
                ))}
              </div>
            </div>

            <div className="mb-3">
              <div className="flex items-start gap-3 mb-1.5">
                <span className="text-xs text-gray-500 w-14 shrink-0 mt-1">Subtype:</span>
                <div className="flex flex-wrap gap-1.5">
                  {(["AD", "VaD", "FTD", "LBD"] as SubtypeOption[]).map((t) => (
                    <button key={t} onClick={() => setSubtype(t)}
                      className={`text-xs px-2 py-1 rounded border transition-all ${
                        subtype === t
                          ? "border-blue-500 text-blue-700 bg-blue-50"
                          : "border-gray-300 text-gray-500 hover:border-gray-400 bg-white"
                      }`}>
                      {t}
                    </button>
                  ))}
                </div>
              </div>
              <div className="flex gap-1.5 ml-[68px]">
                {(["Mixed", "Unspecified"] as SubtypeOption[]).map((t) => (
                  <button key={t} onClick={() => setSubtype(t)}
                    className={`text-xs px-2 py-1 rounded border transition-all ${
                      subtype === t
                        ? "border-blue-500 text-blue-700 bg-blue-50"
                        : "border-gray-300 text-gray-500 hover:border-gray-400 bg-white"
                    }`}>
                    {t}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex items-center gap-2 mb-5">
              <span className="text-xs text-gray-500 w-14 shrink-0">Confidence:</span>
              <span className="text-sm">🌈</span>
              <span className="text-sm font-semibold text-gray-800">82%</span>
            </div>

            <div className="border-t border-gray-100 mb-4" />

            {/* Evidence */}
            <p className="text-sm font-semibold text-gray-900 mb-3">
              Evidence ({EVIDENCE.length})
            </p>
            <div>
              {EVIDENCE.map((ev, idx) => {
                const isActive = activeEv === ev.id;
                return (
                  <div key={ev.id} id={`ev-${ev.id}`}
                    className={`py-2.5 border-b border-gray-100 last:border-0 transition-colors ${
                      isActive ? "-mx-5 px-5 bg-blue-50" : ""
                    }`}>
                    <div className="flex items-baseline justify-between gap-1 mb-0.5">
                      <span className="text-xs text-gray-800 font-medium">
                        {idx + 1}. {ev.type}
                      </span>
                      {ev.strength && (
                        <span className={`text-xs font-semibold shrink-0 ${STRENGTH_CLS[ev.strength]}`}>
                          {ev.strength}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-gray-500 leading-snug mb-1">{ev.desc}</p>
                    <div className="flex items-center justify-between">
                      <button onClick={() => jumpToSpan(ev.spanId, ev.id)}
                        className="text-xs text-blue-500 hover:text-blue-700 hover:underline">
                        Jump to text
                      </button>
                      <ChevronRight className="w-3.5 h-3.5 text-gray-300" />
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="border-t border-gray-100 mt-4 mb-4" />

            <p className="text-sm font-semibold text-gray-900 mb-1.5">Acute vs Chronic:</p>
            <p className="text-xs text-gray-600 leading-relaxed">
              Chronic neurodegenerative process likely — acute delirium superimposed on
              pre-existing ADRD.
            </p>
          </div>
        </aside>
      </div>
    </div>
  );
}

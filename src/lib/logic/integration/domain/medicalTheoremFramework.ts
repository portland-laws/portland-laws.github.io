export type MedicalTheoremKind =
  | 'care_obligation'
  | 'treatment_permission'
  | 'treatment_prohibition';

export interface MedicalEvidence {
  readonly kind: 'diagnosis' | 'intervention' | 'outcome' | 'risk' | 'consent';
  readonly text: string;
}

export interface MedicalTheorem {
  readonly id: string;
  readonly kind: MedicalTheoremKind;
  readonly formula: string;
  readonly confidence: number;
  readonly evidence: readonly MedicalEvidence[];
}

export interface MedicalTheoremResult {
  readonly accepted: boolean;
  readonly runtime: 'browser-native';
  readonly wasmCompatible: true;
  readonly serverCallsAllowed: false;
  readonly pythonRuntimeAllowed: false;
  readonly sourceText: string;
  readonly theorems: readonly MedicalTheorem[];
  readonly issues: readonly string[];
  readonly metadata: typeof MEDICAL_THEOREM_FRAMEWORK_METADATA;
}

export const MEDICAL_THEOREM_FRAMEWORK_METADATA = {
  sourcePythonModule: 'logic/integration/domain/medical_theorem_framework.py',
  browserNative: true,
  wasmCompatible: true,
  serverCallsAllowed: false,
  pythonRuntimeAllowed: false,
  runtimeDependencies: [],
  parity: [
    'deterministic_medical_fact_extraction',
    'local_theorem_generation',
    'contraindication_fail_closed',
    'python_style_aliases',
  ],
} as const;

const EVIDENCE_PATTERNS: readonly [MedicalEvidence['kind'], RegExp][] = [
  [
    'diagnosis',
    /\b(diagnos(?:is|ed)|condition|symptom|infection|diabetes|hypertension|asthma|pain)\b/i,
  ],
  ['intervention', /\b(treat(?:ment)?|therapy|medication|dose|surgery|procedure|monitor|refer)\b/i],
  ['outcome', /\b(improve|reduce|prevent|stabilize|relieve|benefit|recovery)\b/i],
  ['risk', /\b(contraindicat(?:ed|ion)|allerg(?:y|ic)|risk|adverse|harm|unsafe|bleeding)\b/i],
  ['consent', /\b(consent|informed decision|patient agrees|authorized|declines)\b/i],
];

export class BrowserNativeMedicalTheoremFramework {
  readonly metadata = MEDICAL_THEOREM_FRAMEWORK_METADATA;

  analyze(text: string): MedicalTheoremResult {
    const sourceText = typeof text === 'string' ? text : '';
    const normalized = sourceText.replace(/\s+/g, ' ').trim();
    if (normalized.length < 3) return closed(sourceText, ['source text is required']);

    const evidence = extractEvidence(normalized);
    const issues = validateEvidence(evidence);
    const theorems = issues.length > 0 ? [] : buildTheorems(normalized, evidence);
    return {
      accepted: theorems.length > 0 && issues.length === 0,
      runtime: 'browser-native',
      wasmCompatible: true,
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
      sourceText,
      theorems,
      issues: theorems.length > 0 ? issues : [...issues, 'no medical theorem derived locally'],
      metadata: this.metadata,
    };
  }
}

export function analyzeMedicalTheorems(text: string): MedicalTheoremResult {
  return new BrowserNativeMedicalTheoremFramework().analyze(text);
}

export const create_medical_theorem_framework = (): BrowserNativeMedicalTheoremFramework =>
  new BrowserNativeMedicalTheoremFramework();
export const analyze_medical_theorems = analyzeMedicalTheorems;
export const build_medical_theorems = analyzeMedicalTheorems;

function extractEvidence(text: string): readonly MedicalEvidence[] {
  return EVIDENCE_PATTERNS.flatMap(([kind, pattern]) =>
    splitSentences(text)
      .filter((sentence: string) => pattern.test(sentence))
      .map((sentence: string) => ({ kind, text: sentence })),
  );
}

function validateEvidence(evidence: readonly MedicalEvidence[]): readonly string[] {
  const kinds = new Set(evidence.map((item: MedicalEvidence) => item.kind));
  const issues: string[] = [];
  if (!kinds.has('diagnosis')) issues.push('diagnosis evidence is required');
  if (!kinds.has('intervention')) issues.push('intervention evidence is required');
  if (kinds.has('risk')) issues.push('contraindication requires local review');
  return issues;
}

function buildTheorems(
  text: string,
  evidence: readonly MedicalEvidence[],
): readonly MedicalTheorem[] {
  const kinds = new Set(evidence.map((item: MedicalEvidence) => item.kind));
  const predicate = toPredicate(text);
  const kind: MedicalTheoremKind = kinds.has('consent')
    ? 'treatment_permission'
    : 'care_obligation';
  const symbol = kind === 'treatment_permission' ? 'P' : 'O';
  return [
    {
      id: `medical-theorem-${stableHash(predicate)}`,
      kind,
      formula: `${symbol}(clinician, ${predicate})`,
      confidence: Number(
        Math.min(
          0.94,
          0.62 + (kinds.has('outcome') ? 0.12 : 0) + (kinds.has('consent') ? 0.08 : 0),
        ).toFixed(2),
      ),
      evidence,
    },
  ];
}

function splitSentences(text: string): readonly string[] {
  return text
    .split(/(?<=[.!?])\s+/)
    .map((item: string) => item.trim())
    .filter((item: string) => item.length > 0);
}

function toPredicate(text: string): string {
  const value = text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .slice(0, 80);
  return value.length > 0 ? value : 'medical_care';
}

function stableHash(value: string): string {
  let hash = 2166136261;
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0).toString(16).padStart(8, '0');
}

function closed(sourceText: string, issues: readonly string[]): MedicalTheoremResult {
  return {
    accepted: false,
    runtime: 'browser-native',
    wasmCompatible: true,
    serverCallsAllowed: false,
    pythonRuntimeAllowed: false,
    sourceText,
    theorems: [],
    issues,
    metadata: MEDICAL_THEOREM_FRAMEWORK_METADATA,
  };
}

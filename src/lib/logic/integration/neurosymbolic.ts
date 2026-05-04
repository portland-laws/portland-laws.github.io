export type NeuroSymbolicStatus = 'success' | 'validation_failed';
export type NeuroSymbolicIntent =
  | 'obligation'
  | 'permission'
  | 'prohibition'
  | 'condition'
  | 'fact';
export interface NeuroSymbolicSignal {
  readonly intent: NeuroSymbolicIntent;
  readonly evidence: string;
  readonly confidence: number;
}
export interface NeuroSymbolicReasoningStep {
  readonly kind: 'neural_signal' | 'symbolic_fact' | 'rule_match' | 'query_match';
  readonly detail: string;
}
export interface NeuroSymbolicOptions {
  readonly query?: string;
  readonly facts?: readonly string[];
  readonly rules?: readonly string[];
}
export interface NeuroSymbolicResult {
  readonly status: NeuroSymbolicStatus;
  readonly success: boolean;
  readonly runtime: 'browser-native';
  readonly wasmCompatible: true;
  readonly serverCallsAllowed: false;
  readonly pythonRuntimeAllowed: false;
  readonly sourceText: string;
  readonly query: string | null;
  readonly neuralSignals: readonly NeuroSymbolicSignal[];
  readonly symbolicFacts: readonly string[];
  readonly inferredFacts: readonly string[];
  readonly proofStatus: 'proved' | 'unknown' | 'not_applicable';
  readonly confidence: number;
  readonly reasoningSteps: readonly NeuroSymbolicReasoningStep[];
  readonly issues: readonly string[];
  readonly metadata: typeof NEUROSYMBOLIC_METADATA;
}
export const NEUROSYMBOLIC_METADATA = {
  sourcePythonModule: 'logic/integration/neurosymbolic.py',
  browserNative: true,
  wasmCompatible: true,
  serverCallsAllowed: false,
  pythonRuntimeAllowed: false,
  neuralRuntime: 'deterministic-local-adapter',
  runtimeDependencies: [],
  parity: ['local_signal_extraction', 'symbolic_projection', 'fail_closed_reasoning'],
} as const;
const INTENTS: readonly [NeuroSymbolicIntent, RegExp, string][] = [
  ['prohibition', /\b(shall not|must not|may not|prohibited from|forbidden to)\b/i, 'F'],
  ['obligation', /\b(shall(?!\s+not)|must(?!\s+not)|required to|has a duty to)\b/i, 'O'],
  ['permission', /\b(may|authorized to|permitted to|allowed to)\b/i, 'P'],
  ['condition', /\b(if|unless|provided that|when|where)\b/i, 'IF'],
];
export class BrowserNativeNeuroSymbolicIntegration {
  readonly metadata = NEUROSYMBOLIC_METADATA;
  analyze(text: string, options: NeuroSymbolicOptions = {}): NeuroSymbolicResult {
    const sourceText = typeof text === 'string' ? text : '';
    const normalized = sourceText.replace(/\s+/g, ' ').trim();
    if (normalized.length < 3)
      return closed(sourceText, options.query ?? null, ['source text is required']);
    const neuralSignals = splitSentences(normalized).flatMap(extractSignals);
    const symbolicFacts = unique([...(options.facts ?? []), ...neuralSignals.map(toFormula)]);
    const inferredFacts = inferFacts(symbolicFacts, options.rules ?? []);
    const allFacts = new Set([...symbolicFacts, ...inferredFacts].map(canonical));
    const query = options.query?.trim() || null;
    const proofStatus =
      query === null ? 'not_applicable' : allFacts.has(canonical(query)) ? 'proved' : 'unknown';
    return {
      status: 'success',
      success: true,
      runtime: 'browser-native',
      wasmCompatible: true,
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
      sourceText,
      query,
      neuralSignals,
      symbolicFacts,
      inferredFacts,
      proofStatus,
      confidence: score(neuralSignals, proofStatus, inferredFacts.length),
      reasoningSteps: [
        ...neuralSignals.map((signal) => ({
          kind: 'neural_signal' as const,
          detail: `${signal.intent}:${signal.evidence}`,
        })),
        ...symbolicFacts.map((fact) => ({ kind: 'symbolic_fact' as const, detail: fact })),
        ...inferredFacts.map((fact) => ({ kind: 'rule_match' as const, detail: fact })),
        ...(query === null
          ? []
          : [{ kind: 'query_match' as const, detail: `${query}:${proofStatus}` }]),
      ],
      issues: neuralSignals.every((signal) => signal.intent === 'fact')
        ? ['no local neural-symbolic signals matched']
        : [],
      metadata: this.metadata,
    };
  }

  reason(
    text: string,
    query: string,
    options: Omit<NeuroSymbolicOptions, 'query'> = {},
  ): NeuroSymbolicResult {
    return this.analyze(text, { ...options, query });
  }
}
export function analyzeNeuroSymbolic(
  text: string,
  options: NeuroSymbolicOptions = {},
): NeuroSymbolicResult {
  return new BrowserNativeNeuroSymbolicIntegration().analyze(text, options);
}
export function reasonNeuroSymbolic(
  text: string,
  query: string,
  options: Omit<NeuroSymbolicOptions, 'query'> = {},
): NeuroSymbolicResult {
  return new BrowserNativeNeuroSymbolicIntegration().reason(text, query, options);
}
export const create_browser_native_neurosymbolic_integration =
  (): BrowserNativeNeuroSymbolicIntegration => new BrowserNativeNeuroSymbolicIntegration();
export const analyze_neurosymbolic = analyzeNeuroSymbolic;
export const reason_neurosymbolic = reasonNeuroSymbolic;
function extractSignals(sentence: string): readonly NeuroSymbolicSignal[] {
  const matched = INTENTS.filter(([, pattern]) => pattern.test(sentence));
  const intents: readonly [NeuroSymbolicIntent, RegExp, string][] =
    matched.length > 0 ? matched : [['fact', /\S/, 'Fact']];
  return intents.map(([intent]) => ({
    intent,
    evidence: sentence,
    confidence: intent === 'fact' ? 0.58 : 0.82,
  }));
}
function toFormula(signal: NeuroSymbolicSignal): string {
  const symbol = INTENTS.find(([intent]) => intent === signal.intent)?.[2] ?? 'Fact';
  return `${symbol}(${predicate(signal.evidence)})`;
}
function inferFacts(facts: readonly string[], rules: readonly string[]): readonly string[] {
  const known = new Set(facts.map(canonical));
  return unique(
    rules.flatMap((rule) => {
      const match = rule.match(/^\s*(.+?)\s*(?:=>|->|\u2192)\s*(.+?)\s*$/);
      return match && known.has(canonical(match[1])) ? [match[2].trim()] : [];
    }),
  );
}
function splitSentences(text: string): readonly string[] {
  return text
    .split(/(?<=[.!?])\s+/)
    .map((item) => item.trim())
    .filter((item) => item.length > 0);
}
function predicate(text: string): string {
  const value = text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .slice(0, 96);
  return value.length > 0 ? value : 'statement';
}
function canonical(value: string): string {
  return value.replace(/\s+/g, '').toLowerCase();
}
function unique(items: readonly string[]): readonly string[] {
  return [...new Set(items.map((item) => item.trim()).filter((item) => item.length > 0))];
}
function score(
  signals: readonly NeuroSymbolicSignal[],
  proofStatus: NeuroSymbolicResult['proofStatus'],
  inferredCount: number,
): number {
  const base =
    signals.length === 0
      ? 0
      : signals.reduce((sum, signal) => sum + signal.confidence, 0) / signals.length;
  return Number(
    Math.min(
      0.98,
      base + (proofStatus === 'proved' ? 0.12 : 0) + Math.min(0.06, inferredCount * 0.03),
    ).toFixed(2),
  );
}
function closed(
  sourceText: string,
  query: string | null,
  issues: readonly string[],
): NeuroSymbolicResult {
  return {
    status: 'validation_failed',
    success: false,
    runtime: 'browser-native',
    wasmCompatible: true,
    serverCallsAllowed: false,
    pythonRuntimeAllowed: false,
    sourceText,
    query,
    neuralSignals: [],
    symbolicFacts: [],
    inferredFacts: [],
    proofStatus: 'not_applicable',
    confidence: 0,
    reasoningSteps: [],
    issues,
    metadata: NEUROSYMBOLIC_METADATA,
  };
}

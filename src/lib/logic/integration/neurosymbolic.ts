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
export type NeuroSymbolicGraphRagDocument = {
  readonly id?: string;
  readonly title?: string;
  readonly text: string;
  readonly metadata?: Record<string, unknown>;
};
export type NeuroSymbolicGraphNode = {
  readonly id: string;
  readonly kind: 'document' | 'entity' | 'fact';
  readonly label: string;
  readonly weight: number;
};
export type NeuroSymbolicGraphEdge = {
  readonly source: string;
  readonly target: string;
  readonly relation: 'contains' | 'mentions' | 'supports';
  readonly weight: number;
};
export type NeuroSymbolicGraphRagOptions = NeuroSymbolicOptions & {
  readonly documents?: readonly (string | NeuroSymbolicGraphRagDocument)[];
  readonly topK?: number;
};
type GraphBuild = {
  readonly nodes: readonly NeuroSymbolicGraphNode[];
  readonly edges: readonly NeuroSymbolicGraphEdge[];
  readonly documentSignals: readonly {
    readonly documentId: string;
    readonly signal: NeuroSymbolicSignal;
  }[];
  readonly documentFacts: readonly { readonly documentId: string; readonly fact: string }[];
};
export type NeuroSymbolicGraphRagResult = Omit<NeuroSymbolicResult, 'metadata'> & {
  readonly metadata: typeof NEUROSYMBOLIC_GRAPHRAG_METADATA;
  readonly retrievedDocuments: readonly NeuroSymbolicGraphRagDocument[];
  readonly graphNodes: readonly NeuroSymbolicGraphNode[];
  readonly graphEdges: readonly NeuroSymbolicGraphEdge[];
  readonly retrievalTrace: readonly NeuroSymbolicReasoningStep[];
};
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
export const NEUROSYMBOLIC_GRAPHRAG_METADATA = {
  sourcePythonModule: 'logic/integration/neurosymbolic_graphrag.py',
  browserNative: true,
  wasmCompatible: true,
  serverCallsAllowed: false,
  pythonRuntimeAllowed: false,
  graphRuntime: 'deterministic-local-graph-rag-adapter',
  neuralRuntime: 'deterministic-local-adapter',
  runtimeDependencies: [],
  parity: ['local_graph_construction', 'symbolic_rag_retrieval', 'fail_closed_reasoning'],
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
export class BrowserNativeNeuroSymbolicGraphRag {
  readonly metadata = NEUROSYMBOLIC_GRAPHRAG_METADATA;

  analyze(text: string, options: NeuroSymbolicGraphRagOptions = {}): NeuroSymbolicGraphRagResult {
    const sourceText = typeof text === 'string' ? text : '';
    const documents = normalizeDocuments(sourceText, options.documents);
    if (documents.length === 0)
      return closedGraphRag(sourceText, options.query ?? null, ['source documents are required']);
    const graph = buildGraph(documents);
    const query = options.query?.trim() || null;
    const retrievedDocuments = retrieveDocuments(documents, query ?? sourceText, options.topK ?? 3);
    const retrievedIds = new Set<string>(retrievedDocuments.map((document) => document.id ?? ''));
    const retrievedFacts = graph.documentFacts
      .filter((entry) => retrievedIds.has(entry.documentId))
      .map((entry) => entry.fact);
    const symbolicFacts = unique([...(options.facts ?? []), ...retrievedFacts]);
    const inferredFacts = inferFacts(symbolicFacts, options.rules ?? []);
    const allFacts = new Set<string>([...symbolicFacts, ...inferredFacts].map(canonical));
    const proofStatus =
      query === null ? 'not_applicable' : allFacts.has(canonical(query)) ? 'proved' : 'unknown';
    const neuralSignals = graph.documentSignals
      .filter((entry) => retrievedIds.has(entry.documentId))
      .map((entry) => entry.signal);
    const retrievalTrace = retrievedDocuments.map((document) => ({
      kind: 'query_match' as const,
      detail: `${document.id ?? 'document'}:${query ?? 'corpus'}`,
    }));
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
        ...retrievalTrace,
        ...neuralSignals.map((signal) => ({
          kind: 'neural_signal' as const,
          detail: `${signal.intent}:${signal.evidence}`,
        })),
        ...symbolicFacts.map((fact) => ({ kind: 'symbolic_fact' as const, detail: fact })),
        ...inferredFacts.map((fact) => ({ kind: 'rule_match' as const, detail: fact })),
      ],
      issues: neuralSignals.every((signal) => signal.intent === 'fact')
        ? ['no local neural-symbolic graph signals matched']
        : [],
      metadata: this.metadata,
      retrievedDocuments,
      graphNodes: graph.nodes,
      graphEdges: graph.edges,
      retrievalTrace,
    };
  }

  query(
    text: string,
    query: string,
    options: Omit<NeuroSymbolicGraphRagOptions, 'query'> = {},
  ): NeuroSymbolicGraphRagResult {
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
export const create_browser_native_neurosymbolic_graphrag =
  (): BrowserNativeNeuroSymbolicGraphRag => new BrowserNativeNeuroSymbolicGraphRag();
export const analyze_neurosymbolic = analyzeNeuroSymbolic;
export const reason_neurosymbolic = reasonNeuroSymbolic;
export const analyzeNeuroSymbolicGraphRag = (
  text: string,
  options: NeuroSymbolicGraphRagOptions = {},
): NeuroSymbolicGraphRagResult => new BrowserNativeNeuroSymbolicGraphRag().analyze(text, options);
export const queryNeuroSymbolicGraphRag = (
  text: string,
  query: string,
  options: Omit<NeuroSymbolicGraphRagOptions, 'query'> = {},
): NeuroSymbolicGraphRagResult =>
  new BrowserNativeNeuroSymbolicGraphRag().query(text, query, options);
export const analyze_neurosymbolic_graphrag = analyzeNeuroSymbolicGraphRag;
export const query_neurosymbolic_graphrag = queryNeuroSymbolicGraphRag;
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
function normalizeDocuments(
  sourceText: string,
  documents: readonly (string | NeuroSymbolicGraphRagDocument)[] = [],
): readonly NeuroSymbolicGraphRagDocument[] {
  const candidates =
    documents.length > 0
      ? documents
      : splitSentences(sourceText).map((sentence, index) => ({
          id: `doc-${index + 1}`,
          text: sentence,
        }));
  return candidates
    .map((document, index) =>
      typeof document === 'string'
        ? { id: `doc-${index + 1}`, text: document }
        : { ...document, id: document.id ?? `doc-${index + 1}` },
    )
    .filter((document) => document.text.replace(/\s+/g, ' ').trim().length >= 3);
}
function buildGraph(documents: readonly NeuroSymbolicGraphRagDocument[]): GraphBuild {
  const nodes = new Map<string, NeuroSymbolicGraphNode>();
  const edges: NeuroSymbolicGraphEdge[] = [];
  const documentSignals: { readonly documentId: string; readonly signal: NeuroSymbolicSignal }[] =
    [];
  const documentFacts: { readonly documentId: string; readonly fact: string }[] = [];

  documents.forEach((document) => {
    const documentId = document.id ?? predicate(document.text);
    nodes.set(documentId, {
      id: documentId,
      kind: 'document',
      label: document.title ?? document.text.slice(0, 80),
      weight: 1,
    });
    splitSentences(document.text)
      .flatMap(extractSignals)
      .forEach((signal) => {
        const fact = toFormula(signal);
        const factId = `fact:${canonical(fact)}`;
        nodes.set(factId, { id: factId, kind: 'fact', label: fact, weight: signal.confidence });
        edges.push({
          source: documentId,
          target: factId,
          relation: 'contains',
          weight: signal.confidence,
        });
        documentSignals.push({ documentId, signal });
        documentFacts.push({ documentId, fact });
        extractEntities(signal.evidence).forEach((entity) => {
          const entityId = `entity:${predicate(entity)}`;
          nodes.set(entityId, { id: entityId, kind: 'entity', label: entity, weight: 0.7 });
          edges.push({ source: factId, target: entityId, relation: 'mentions', weight: 0.7 });
          edges.push({ source: entityId, target: documentId, relation: 'supports', weight: 0.45 });
        });
      });
  });
  return { nodes: [...nodes.values()], edges, documentSignals, documentFacts };
}
function retrieveDocuments(
  documents: readonly NeuroSymbolicGraphRagDocument[],
  query: string,
  topK: number,
): readonly NeuroSymbolicGraphRagDocument[] {
  const queryTerms = new Set<string>(terms(query));
  const scored = documents.map((document, index) => ({
    document,
    index,
    score:
      terms(`${document.title ?? ''} ${document.text}`).filter((term) => queryTerms.has(term))
        .length / Math.max(1, queryTerms.size),
  }));
  return scored
    .sort((left, right) => right.score - left.score || left.index - right.index)
    .slice(0, Math.max(1, topK))
    .map((entry) => entry.document);
}
function extractEntities(text: string): readonly string[] {
  const proper = text.match(/\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b/g) ?? [];
  const legal = text.match(/\b(tenant|landlord|owner|agency|contractor|court|employer)\b/gi) ?? [];
  return unique([...proper, ...legal].map((entity) => entity.toLowerCase()));
}
function terms(text: string): readonly string[] {
  return unique(
    text
      .toLowerCase()
      .split(/[^a-z0-9]+/)
      .filter((term) => term.length > 2),
  );
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
function closedGraphRag(
  sourceText: string,
  query: string | null,
  issues: readonly string[],
): NeuroSymbolicGraphRagResult {
  return {
    ...closed(sourceText, query, issues),
    metadata: NEUROSYMBOLIC_GRAPHRAG_METADATA,
    retrievedDocuments: [],
    graphNodes: [],
    graphEdges: [],
    retrievalTrace: [],
  };
}

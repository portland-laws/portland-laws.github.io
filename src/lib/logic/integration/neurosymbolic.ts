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
export type EmbeddingProverStatus = 'proved' | 'not_proved' | 'validation_failed';
export type EmbeddingProverPremise =
  | string
  | { readonly id?: string; readonly text: string; readonly weight?: number };
export interface EmbeddingProverMatch {
  readonly premiseId: string;
  readonly premise: string;
  readonly similarity: number;
  readonly weight: number;
}
export interface EmbeddingProverOptions {
  readonly threshold?: number;
  readonly topK?: number;
}
export interface EmbeddingProverResult {
  readonly status: EmbeddingProverStatus;
  readonly success: boolean;
  readonly runtime: 'browser-native';
  readonly wasmCompatible: true;
  readonly serverCallsAllowed: false;
  readonly pythonRuntimeAllowed: false;
  readonly sourceText: string;
  readonly theorem: string;
  readonly threshold: number;
  readonly confidence: number;
  readonly bestSimilarity: number;
  readonly matchedPremises: readonly EmbeddingProverMatch[];
  readonly proofSteps: readonly NeuroSymbolicReasoningStep[];
  readonly issues: readonly string[];
  readonly metadata: typeof EMBEDDING_PROVER_METADATA;
}
export type HybridConfidenceProofStatus = 'proved' | 'not_proved' | 'unknown' | 'not_applicable';
export interface HybridConfidenceInput {
  readonly neuralConfidence?: number;
  readonly symbolicConfidence?: number;
  readonly retrievalScore?: number;
  readonly proofStatus?: HybridConfidenceProofStatus;
  readonly evidenceCount?: number;
  readonly contradictionCount?: number;
  readonly signals?: readonly NeuroSymbolicSignal[];
}
export interface HybridConfidenceOptions {
  readonly threshold?: number;
}
export interface HybridConfidenceResult {
  readonly status: 'success' | 'validation_failed';
  readonly success: boolean;
  readonly runtime: 'browser-native';
  readonly wasmCompatible: true;
  readonly serverCallsAllowed: false;
  readonly pythonRuntimeAllowed: false;
  readonly confidence: number;
  readonly threshold: number;
  readonly passedThreshold: boolean;
  readonly components: Record<string, number>;
  readonly issues: readonly string[];
  readonly metadata: typeof HYBRID_CONFIDENCE_METADATA;
}
export interface ReasoningCoordinatorOptions extends NeuroSymbolicOptions {
  readonly premises?: readonly EmbeddingProverPremise[];
  readonly embedding?: EmbeddingProverOptions;
  readonly confidence?: HybridConfidenceOptions;
}
export interface ReasoningCoordinatorResult {
  readonly status: 'success' | 'validation_failed';
  readonly success: boolean;
  readonly runtime: 'browser-native';
  readonly wasmCompatible: true;
  readonly serverCallsAllowed: false;
  readonly pythonRuntimeAllowed: false;
  readonly sourceText: string;
  readonly query: string | null;
  readonly symbolic: NeuroSymbolicResult;
  readonly embedding: EmbeddingProverResult | null;
  readonly confidence: HybridConfidenceResult;
  readonly selectedProof: 'symbolic' | 'embedding' | 'none';
  readonly proofStatus: 'proved' | 'not_proved' | 'unknown' | 'not_applicable';
  readonly reasoningSteps: readonly NeuroSymbolicReasoningStep[];
  readonly issues: readonly string[];
  readonly metadata: typeof REASONING_COORDINATOR_METADATA;
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
export const EMBEDDING_PROVER_METADATA = {
  sourcePythonModule: 'logic/integration/symbolic/neurosymbolic/embedding_prover.py',
  browserNative: true,
  wasmCompatible: true,
  serverCallsAllowed: false,
  pythonRuntimeAllowed: false,
  embeddingRuntime: 'deterministic-local-token-vector',
  runtimeDependencies: [],
  parity: ['local_embedding_projection', 'cosine_similarity_proof', 'fail_closed_reasoning'],
} as const;
export const HYBRID_CONFIDENCE_METADATA = {
  sourcePythonModule: 'logic/integration/symbolic/neurosymbolic/hybrid_confidence.py',
  browserNative: true,
  wasmCompatible: true,
  serverCallsAllowed: false,
  pythonRuntimeAllowed: false,
  confidenceRuntime: 'deterministic-local-hybrid-scorer',
  runtimeDependencies: [],
  parity: ['weighted_signal_fusion', 'symbolic_proof_adjustment', 'fail_closed_confidence'],
} as const;
export const REASONING_COORDINATOR_METADATA = {
  sourcePythonModule: 'logic/integration/symbolic/neurosymbolic/reasoning_coordinator.py',
  browserNative: true,
  wasmCompatible: true,
  serverCallsAllowed: false,
  pythonRuntimeAllowed: false,
  coordinatorRuntime: 'deterministic-local-reasoning-orchestrator',
  runtimeDependencies: [],
  parity: [
    'symbolic_embedding_coordination',
    'hybrid_confidence_selection',
    'fail_closed_reasoning',
  ],
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
export class BrowserNativeReasoningCoordinator {
  readonly metadata = REASONING_COORDINATOR_METADATA;

  coordinate(
    text: string,
    query: string,
    options: ReasoningCoordinatorOptions = {},
  ): ReasoningCoordinatorResult {
    const normalizedQuery = typeof query === 'string' ? query.replace(/\s+/g, ' ').trim() : '';
    const symbolic = reasonNeuroSymbolic(text, normalizedQuery, {
      facts: options.facts,
      rules: options.rules,
    });
    const premises = options.premises ?? [
      ...symbolic.symbolicFacts,
      ...symbolic.inferredFacts,
      ...symbolic.neuralSignals.map((signal) => signal.evidence),
    ];
    const embedding =
      normalizedQuery.length >= 3
        ? proveEmbedding(premises, normalizedQuery, options.embedding)
        : null;
    const selectedProof =
      symbolic.proofStatus === 'proved'
        ? 'symbolic'
        : embedding?.status === 'proved'
          ? 'embedding'
          : 'none';
    const proofStatus = coordinatorProofStatus(symbolic, embedding, selectedProof);
    const confidence = scoreHybridConfidence(
      {
        signals: symbolic.neuralSignals,
        symbolicConfidence: symbolic.confidence,
        retrievalScore: embedding?.bestSimilarity,
        proofStatus,
        evidenceCount: symbolic.symbolicFacts.length + symbolic.inferredFacts.length,
      },
      options.confidence,
    );
    const issues = [
      ...symbolic.issues,
      ...(embedding?.issues ?? []),
      ...confidence.issues,
      ...(selectedProof === 'none' && symbolic.status === 'validation_failed'
        ? ['no local reasoning evidence is available']
        : []),
    ];
    return {
      status:
        symbolic.status === 'validation_failed' && selectedProof === 'none'
          ? 'validation_failed'
          : 'success',
      success: selectedProof !== 'none',
      runtime: 'browser-native',
      wasmCompatible: true,
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
      sourceText: text,
      query: normalizedQuery || null,
      symbolic,
      embedding,
      confidence,
      selectedProof,
      proofStatus,
      reasoningSteps: [
        ...symbolic.reasoningSteps,
        ...(embedding?.proofSteps ?? []),
        { kind: 'query_match' as const, detail: `coordinator:${selectedProof}:${proofStatus}` },
      ],
      issues: unique(issues),
      metadata: this.metadata,
    };
  }

  reason(
    text: string,
    query: string,
    options: ReasoningCoordinatorOptions = {},
  ): ReasoningCoordinatorResult {
    return this.coordinate(text, query, options);
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
export const coordinateReasoning = (
  text: string,
  query: string,
  options: ReasoningCoordinatorOptions = {},
): ReasoningCoordinatorResult =>
  new BrowserNativeReasoningCoordinator().coordinate(text, query, options);
export const create_browser_native_reasoning_coordinator = (): BrowserNativeReasoningCoordinator =>
  new BrowserNativeReasoningCoordinator();
export const coordinate_reasoning = coordinateReasoning;
export const proveEmbedding = (
  premises: readonly EmbeddingProverPremise[],
  theorem: string,
  options: EmbeddingProverOptions = {},
): EmbeddingProverResult => {
  const normalizedPremises = normalizeEmbeddingPremises(premises);
  const normalizedTheorem = typeof theorem === 'string' ? theorem.replace(/\s+/g, ' ').trim() : '';
  const threshold = clampThreshold(options.threshold ?? 0.62);
  if (normalizedPremises.length === 0 || normalizedTheorem.length < 3) {
    return closedEmbeddingProver(normalizedPremises, normalizedTheorem, threshold);
  }
  const theoremVector = embedText(normalizedTheorem);
  const scored = normalizedPremises
    .map((premise) => ({
      ...premise,
      similarity: Number(
        (cosineSimilarity(embedText(premise.text), theoremVector) * premise.weight).toFixed(3),
      ),
    }))
    .sort((left, right) => right.similarity - left.similarity || left.index - right.index);
  const matchedPremises = scored
    .filter((premise, index) => premise.similarity >= threshold || index === 0)
    .slice(0, Math.max(1, Math.floor(options.topK ?? 3)))
    .map(({ id, text, similarity, weight }) => ({
      premiseId: id,
      premise: text,
      similarity,
      weight,
    }));
  const bestSimilarity = matchedPremises[0]?.similarity ?? 0;
  const proved = bestSimilarity >= threshold;
  return embeddingResult(normalizedPremises, normalizedTheorem, threshold, matchedPremises, proved);
};
export const create_browser_native_embedding_prover = () => ({
  metadata: EMBEDDING_PROVER_METADATA,
  prove: proveEmbedding,
});
export const prove_embedding = proveEmbedding;
export class BrowserNativeHybridConfidence {
  readonly metadata = HYBRID_CONFIDENCE_METADATA;

  score(
    input: HybridConfidenceInput,
    options: HybridConfidenceOptions = {},
  ): HybridConfidenceResult {
    return scoreHybridConfidence(input, options);
  }
}
export const scoreHybridConfidence = (
  input: HybridConfidenceInput,
  options: HybridConfidenceOptions = {},
): HybridConfidenceResult => {
  const signals = input.signals ?? [];
  const neural =
    input.neuralConfidence ??
    (signals.length === 0 ? undefined : average(signals.map((signal) => signal.confidence)));
  const symbolic = input.symbolicConfidence;
  const retrieval = input.retrievalScore;
  const available = [neural, symbolic, retrieval].filter((value) => value !== undefined);
  const threshold = clampThreshold(options.threshold ?? 0.62);
  if (available.length === 0) {
    return hybridConfidenceResult(
      { neural: 0, symbolic: 0, retrieval: 0, proof: 0, evidence: 0, contradictionPenalty: 0 },
      threshold,
      ['at least one confidence signal is required'],
    );
  }
  const components = {
    neural: clamp01(neural ?? 0),
    symbolic: clamp01(symbolic ?? proofStatusScore(input.proofStatus ?? 'not_applicable')),
    retrieval: clamp01(retrieval ?? 0),
    proof: proofStatusScore(input.proofStatus ?? 'not_applicable'),
    evidence: evidenceScore(input.evidenceCount ?? signals.length),
    contradictionPenalty: contradictionPenalty(input.contradictionCount ?? 0),
  };
  return hybridConfidenceResult(components, threshold, []);
};
export const create_browser_native_hybrid_confidence = (): BrowserNativeHybridConfidence =>
  new BrowserNativeHybridConfidence();
export const score_hybrid_confidence = scoreHybridConfidence;
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
function normalizeEmbeddingPremises(premises: readonly EmbeddingProverPremise[]): readonly {
  readonly id: string;
  readonly index: number;
  readonly text: string;
  readonly weight: number;
}[] {
  return premises
    .map((premise, index) => {
      const text =
        typeof premise === 'string'
          ? premise.replace(/\s+/g, ' ').trim()
          : premise.text.replace(/\s+/g, ' ').trim();
      const weight = typeof premise === 'string' ? 1 : Math.max(0, premise.weight ?? 1);
      return {
        id:
          typeof premise === 'string'
            ? `premise-${index + 1}`
            : (premise.id ?? `premise-${index + 1}`),
        index,
        text,
        weight,
      };
    })
    .filter((premise) => premise.text.length >= 3 && premise.weight > 0);
}
function embedText(text: string): readonly number[] {
  const vector = Array.from({ length: 16 }, () => 0);
  for (const term of terms(text)) {
    const slot = hashTerm(term) % vector.length;
    vector[slot] += 1 + Math.min(0.4, term.length / 20);
  }
  return vector;
}
function hashTerm(term: string): number {
  let value = 2166136261;
  for (let index = 0; index < term.length; index += 1) {
    value ^= term.charCodeAt(index);
    value = Math.imul(value, 16777619);
  }
  return value >>> 0;
}
function cosineSimilarity(left: readonly number[], right: readonly number[]): number {
  let dot = 0;
  let leftNorm = 0;
  let rightNorm = 0;
  for (let index = 0; index < left.length; index += 1) {
    dot += left[index] * right[index];
    leftNorm += left[index] * left[index];
    rightNorm += right[index] * right[index];
  }
  return leftNorm === 0 || rightNorm === 0 ? 0 : dot / (Math.sqrt(leftNorm) * Math.sqrt(rightNorm));
}
function clampThreshold(value: number): number {
  if (!Number.isFinite(value)) return 0.62;
  return Number(Math.min(0.99, Math.max(0.01, value)).toFixed(3));
}
function clamp01(value: number): number {
  if (!Number.isFinite(value)) return 0;
  return Number(Math.min(1, Math.max(0, value)).toFixed(3));
}
function average(values: readonly number[]): number {
  return values.length === 0 ? 0 : values.reduce((sum, value) => sum + value, 0) / values.length;
}
function proofStatusScore(status: HybridConfidenceProofStatus): number {
  if (status === 'proved') return 0.92;
  if (status === 'not_proved') return 0.24;
  if (status === 'unknown') return 0.46;
  return 0.5;
}
function coordinatorProofStatus(
  symbolic: NeuroSymbolicResult,
  embedding: EmbeddingProverResult | null,
  selectedProof: ReasoningCoordinatorResult['selectedProof'],
): ReasoningCoordinatorResult['proofStatus'] {
  if (selectedProof === 'symbolic') return symbolic.proofStatus;
  if (selectedProof === 'embedding') return 'proved';
  if (embedding?.status === 'not_proved') return 'not_proved';
  return symbolic.proofStatus;
}
function evidenceScore(count: number): number {
  if (!Number.isFinite(count) || count <= 0) return 0;
  return Number(Math.min(0.08, count * 0.02).toFixed(3));
}
function contradictionPenalty(count: number): number {
  if (!Number.isFinite(count) || count <= 0) return 0;
  return Number(Math.min(0.35, count * 0.12).toFixed(3));
}
function hybridConfidenceResult(
  components: HybridConfidenceResult['components'],
  threshold: number,
  issues: readonly string[],
): HybridConfidenceResult {
  const fused =
    components.neural * 0.45 +
    components.symbolic * 0.4 +
    components.retrieval * 0.15 +
    components.evidence -
    components.contradictionPenalty;
  const confidence = issues.length > 0 ? 0 : clamp01(fused);
  return {
    status: issues.length > 0 ? 'validation_failed' : 'success',
    success: issues.length === 0,
    runtime: 'browser-native',
    wasmCompatible: true,
    serverCallsAllowed: false,
    pythonRuntimeAllowed: false,
    confidence,
    threshold,
    passedThreshold: confidence >= threshold,
    components,
    issues,
    metadata: HYBRID_CONFIDENCE_METADATA,
  };
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
function closedEmbeddingProver(
  premises: readonly { readonly text: string }[],
  theorem: string,
  threshold: number,
): EmbeddingProverResult {
  return embeddingResult(premises, theorem, threshold, [], false, [
    'premises and theorem are required',
  ]);
}
function embeddingResult(
  premises: readonly { readonly text: string }[],
  theorem: string,
  threshold: number,
  matchedPremises: readonly EmbeddingProverMatch[],
  proved: boolean,
  issues: readonly string[] = proved ? [] : ['embedding similarity did not meet proof threshold'],
): EmbeddingProverResult {
  const bestSimilarity = matchedPremises[0]?.similarity ?? 0;
  return {
    status:
      issues[0] === 'premises and theorem are required'
        ? 'validation_failed'
        : proved
          ? 'proved'
          : 'not_proved',
    success: proved,
    runtime: 'browser-native',
    wasmCompatible: true,
    serverCallsAllowed: false,
    pythonRuntimeAllowed: false,
    sourceText: premises.map((premise) => premise.text).join('\n'),
    theorem,
    threshold,
    confidence: Number(Math.min(0.99, bestSimilarity + (proved ? 0.08 : 0)).toFixed(3)),
    bestSimilarity,
    matchedPremises,
    proofSteps: matchedPremises.map((match) => ({
      kind: 'query_match' as const,
      detail: `${match.premiseId}:${match.similarity}`,
    })),
    issues,
    metadata: EMBEDDING_PROVER_METADATA,
  };
}

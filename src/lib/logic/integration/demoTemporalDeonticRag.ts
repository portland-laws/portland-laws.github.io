import { parseDeonticText, type DeonticParsedNorm } from '../deontic/parser';

export interface TemporalDeonticRagDocument {
  id: string;
  title?: string;
  text: string;
  citation?: string;
  metadata?: Record<string, unknown>;
}

export interface TemporalDeonticRagEvidence {
  documentId: string;
  title: string;
  citation?: string;
  score: number;
  matchedTerms: string[];
  normCount: number;
  temporalCount: number;
  formulas: string[];
  norms: DeonticParsedNorm[];
}

export interface TemporalDeonticRagResult {
  status: 'success' | 'validation_failed' | 'no_evidence';
  success: boolean;
  query: string;
  answer: string;
  evidence: TemporalDeonticRagEvidence[];
  metadata: Record<string, unknown>;
  warnings: string[];
}

export const DEMO_TEMPORAL_DEONTIC_RAG_METADATA = {
  sourcePythonModule: 'logic/integration/demos/demo_temporal_deontic_rag.py',
  browserNative: true,
  serverCallsAllowed: false,
  pythonRuntimeAllowed: false,
  runtimeDependencies: [],
  failClosed: true,
  parity: [
    'local_document_ingest',
    'temporal_deontic_norm_extraction',
    'deterministic_rag_ranking',
  ],
} as const;

export class BrowserNativeTemporalDeonticRagDemo {
  readonly metadata = DEMO_TEMPORAL_DEONTIC_RAG_METADATA;
  private readonly documents: TemporalDeonticRagDocument[];

  constructor(documents: TemporalDeonticRagDocument[] = defaultTemporalDeonticRagDocuments()) {
    this.documents = documents.map((document) => ({ ...document }));
  }

  run(query = 'Which temporal legal duties apply?'): TemporalDeonticRagResult {
    const normalizedQuery = query.trim();
    if (normalizedQuery.length === 0) return failRag(query, 'Query must be a non-empty string.');
    if (this.documents.length === 0)
      return failRag(normalizedQuery, 'At least one local document is required.');
    const queryTerms = tokenize(normalizedQuery);
    const evidence = this.documents
      .map((document) => buildEvidence(document, queryTerms))
      .filter((item) => item.score > 0)
      .sort(
        (left, right) =>
          right.score - left.score || left.documentId.localeCompare(right.documentId),
      );
    if (evidence.length === 0) {
      return buildResult(
        'no_evidence',
        false,
        normalizedQuery,
        'No local temporal deontic evidence matched the query.',
        [],
        ['No matching local evidence was found.'],
        this.documents.length,
      );
    }
    return buildResult(
      'success',
      true,
      normalizedQuery,
      summarizeAnswer(evidence),
      evidence,
      [],
      this.documents.length,
    );
  }
}

export function createTemporalDeonticRagDemo(
  documents: TemporalDeonticRagDocument[] = defaultTemporalDeonticRagDocuments(),
): BrowserNativeTemporalDeonticRagDemo {
  return new BrowserNativeTemporalDeonticRagDemo(documents);
}

export const create_temporal_deontic_rag_demo = createTemporalDeonticRagDemo;

export function runTemporalDeonticRagDemo(
  query?: string,
  documents?: TemporalDeonticRagDocument[],
): TemporalDeonticRagResult {
  return createTemporalDeonticRagDemo(documents).run(query);
}

export const run_temporal_deontic_rag_demo = runTemporalDeonticRagDemo;

export function defaultTemporalDeonticRagDocuments(): TemporalDeonticRagDocument[] {
  return [
    {
      id: 'notice',
      title: 'Inspection Notice',
      citation: 'demo:notice',
      text: 'A landlord shall provide written notice within 24 hours before entry. The tenant may request a different time.',
    },
    {
      id: 'records',
      title: 'Record Disclosure',
      citation: 'demo:records',
      text: 'An officer must not disclose sealed records unless the court orders disclosure. The agency shall retain records for 3 years.',
    },
  ];
}

function buildEvidence(
  document: TemporalDeonticRagDocument,
  queryTerms: Set<string>,
): TemporalDeonticRagEvidence {
  const parsed = parseDeonticText(document.text);
  const documentTerms = tokenize(
    `${document.title ?? ''} ${document.citation ?? ''} ${document.text}`,
  );
  const matchedTerms = [...queryTerms].filter((term) => documentTerms.has(term));
  const temporalCount = parsed.norms.reduce(
    (total, norm) => total + norm.temporal_constraints.length,
    0,
  );
  return {
    documentId: document.id,
    title: document.title ?? document.id,
    citation: document.citation,
    score: matchedTerms.length + parsed.norms.length * 0.5 + temporalCount * 0.75,
    matchedTerms,
    normCount: parsed.norms.length,
    temporalCount,
    formulas: parsed.formulas,
    norms: parsed.norms,
  };
}

function buildResult(
  status: TemporalDeonticRagResult['status'],
  success: boolean,
  query: string,
  answer: string,
  evidence: TemporalDeonticRagEvidence[],
  warnings: string[],
  documentCount: number,
): TemporalDeonticRagResult {
  return {
    status,
    success,
    query,
    answer,
    evidence,
    warnings,
    metadata: {
      ...DEMO_TEMPORAL_DEONTIC_RAG_METADATA,
      document_count: documentCount,
      evidence_count: evidence.length,
    },
  };
}

function tokenize(text: string): Set<string> {
  return new Set(
    text
      .toLowerCase()
      .match(/[a-z0-9]+/g)
      ?.filter((term) => term.length > 2) ?? [],
  );
}

function summarizeAnswer(evidence: TemporalDeonticRagEvidence[]): string {
  const top = evidence[0];
  const normTypes = top.norms.map((norm) => norm.norm_type).join(', ') || 'no norms';
  return `${top.title} supplies ${normTypes} evidence with ${top.temporalCount} temporal constraint(s).`;
}

function failRag(query: string, error: string): TemporalDeonticRagResult {
  return {
    status: 'validation_failed',
    success: false,
    query,
    answer: '',
    evidence: [],
    warnings: [error],
    metadata: { ...DEMO_TEMPORAL_DEONTIC_RAG_METADATA },
  };
}

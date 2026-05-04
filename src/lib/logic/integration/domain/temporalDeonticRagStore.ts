import {
  parseDeonticText,
  type DeonticNormType,
  type DeonticParsedNorm,
} from '../../deontic/parser';

export interface TemporalDeonticRagStoreDocument {
  readonly id: string;
  readonly text: string;
  readonly title?: string;
  readonly citation?: string;
  readonly metadata?: Record<string, unknown>;
}
export interface TemporalDeonticRagStoreQuery {
  readonly text: string;
  readonly normType?: DeonticNormType;
  readonly temporalOnly?: boolean;
  readonly limit?: number;
}
export interface TemporalDeonticRagStoreEvidence {
  readonly documentId: string;
  readonly title: string;
  readonly citation?: string;
  readonly score: number;
  readonly matchedTerms: readonly string[];
  readonly normCount: number;
  readonly temporalCount: number;
  readonly formulas: readonly string[];
  readonly norms: readonly DeonticParsedNorm[];
  readonly metadata?: Record<string, unknown>;
}
export interface TemporalDeonticRagStoreResult {
  readonly status: 'success' | 'validation_failed' | 'no_evidence';
  readonly success: boolean;
  readonly query: TemporalDeonticRagStoreQuery;
  readonly evidence: readonly TemporalDeonticRagStoreEvidence[];
  readonly answer: string;
  readonly errors: readonly string[];
  readonly warnings: readonly string[];
  readonly metadata: Record<string, unknown>;
}
interface StoredDocument extends TemporalDeonticRagStoreDocument {
  readonly terms: ReadonlySet<string>;
  readonly norms: readonly DeonticParsedNorm[];
  readonly formulas: readonly string[];
  readonly temporalCount: number;
}

export const TEMPORAL_DEONTIC_RAG_STORE_METADATA = {
  sourcePythonModule: 'logic/integration/domain/temporal_deontic_rag_store.py',
  browserNative: true,
  wasmCompatible: true,
  serverCallsAllowed: false,
  pythonRuntimeAllowed: false,
  runtimeDependencies: [],
  failClosed: true,
  parity: ['local_document_store', 'deterministic_temporal_deontic_index', 'ranked_rag_query'],
} as const;

export class BrowserNativeTemporalDeonticRagStore {
  readonly metadata = TEMPORAL_DEONTIC_RAG_STORE_METADATA;
  private readonly documents = new Map<string, StoredDocument>();
  constructor(documents: readonly TemporalDeonticRagStoreDocument[] = []) {
    this.ingest(documents);
  }
  ingest(documents: readonly TemporalDeonticRagStoreDocument[]): {
    accepted: number;
    errors: string[];
  } {
    const errors: string[] = [];
    let accepted = 0;
    for (const document of documents) {
      const error = validateDocument(document);
      if (error) {
        errors.push(error);
        continue;
      }
      const parsed = parseDeonticText(document.text);
      this.documents.set(document.id, {
        ...document,
        terms: tokenize(`${document.title ?? ''} ${document.citation ?? ''} ${document.text}`),
        norms: parsed.norms,
        formulas: parsed.formulas,
        temporalCount: parsed.norms.reduce(
          (total, norm) => total + norm.temporal_constraints.length,
          0,
        ),
      });
      accepted += 1;
    }
    return { accepted, errors };
  }
  query(query: string | TemporalDeonticRagStoreQuery): TemporalDeonticRagStoreResult {
    const normalized = typeof query === 'string' ? { text: query } : { ...query };
    const errors = validateQuery(normalized, this.documents.size);
    if (errors.length > 0) return closed(normalized, errors, this.documents.size);
    const queryTerms = tokenize(normalized.text);
    const evidence = [...this.documents.values()]
      .map((document) => scoreDocument(document, normalized, queryTerms))
      .filter((item) => item.score > 0)
      .sort(
        (left, right) =>
          right.score - left.score || left.documentId.localeCompare(right.documentId),
      )
      .slice(0, normalized.limit ?? 5);
    return evidence.length > 0
      ? result('success', true, normalized, evidence, summarize(evidence), this.documents.size)
      : result(
          'no_evidence',
          false,
          normalized,
          [],
          'No local temporal deontic evidence matched.',
          this.documents.size,
        );
  }
  get size(): number {
    return this.documents.size;
  }
}

export function createTemporalDeonticRagStore(
  documents: readonly TemporalDeonticRagStoreDocument[] = [],
): BrowserNativeTemporalDeonticRagStore {
  return new BrowserNativeTemporalDeonticRagStore(documents);
}
export const create_temporal_deontic_rag_store = createTemporalDeonticRagStore;

function scoreDocument(
  document: StoredDocument,
  query: TemporalDeonticRagStoreQuery,
  queryTerms: ReadonlySet<string>,
): TemporalDeonticRagStoreEvidence {
  const matchedTerms = [...queryTerms].filter((term) => document.terms.has(term));
  const norms = document.norms.filter(
    (norm) =>
      (!query.normType || norm.norm_type === query.normType) &&
      (!query.temporalOnly || norm.temporal_constraints.length > 0),
  );
  return {
    documentId: document.id,
    title: document.title ?? document.id,
    citation: document.citation,
    score: Number(
      (matchedTerms.length + norms.length * 0.75 + document.temporalCount * 0.5).toFixed(4),
    ),
    matchedTerms,
    normCount: document.norms.length,
    temporalCount: document.temporalCount,
    formulas: document.formulas,
    norms,
    metadata: document.metadata,
  };
}
function validateDocument(document: TemporalDeonticRagStoreDocument): string | undefined {
  if (!document.id || document.id.trim().length === 0) return 'document id is required';
  return !document.text || document.text.trim().length < 3
    ? `document ${document.id} text is required`
    : undefined;
}
function validateQuery(query: TemporalDeonticRagStoreQuery, documentCount: number): string[] {
  const errors: string[] = [];
  if (documentCount === 0) errors.push('at least one local document is required');
  if (!query.text || query.text.trim().length === 0) errors.push('query text is required');
  if (query.limit !== undefined && query.limit <= 0) errors.push('limit must be greater than zero');
  return errors;
}
function tokenize(text: string): Set<string> {
  return new Set(
    text
      .toLowerCase()
      .match(/[a-z0-9]+/g)
      ?.filter((term) => term.length > 2) ?? [],
  );
}
function result(
  status: TemporalDeonticRagStoreResult['status'],
  success: boolean,
  query: TemporalDeonticRagStoreQuery,
  evidence: readonly TemporalDeonticRagStoreEvidence[],
  answer: string,
  documentCount: number,
): TemporalDeonticRagStoreResult {
  return {
    status,
    success,
    query,
    evidence,
    answer,
    errors: [],
    warnings: status === 'no_evidence' ? ['No matching local evidence was found.'] : [],
    metadata: {
      ...TEMPORAL_DEONTIC_RAG_STORE_METADATA,
      document_count: documentCount,
      evidence_count: evidence.length,
    },
  };
}
function closed(
  query: TemporalDeonticRagStoreQuery,
  errors: readonly string[],
  documentCount: number,
): TemporalDeonticRagStoreResult {
  return { ...result('validation_failed', false, query, [], '', documentCount), errors };
}
function summarize(evidence: readonly TemporalDeonticRagStoreEvidence[]): string {
  const top = evidence[0];
  return `${top.title} provides ${top.normCount} deontic norm(s) with ${top.temporalCount} temporal constraint(s).`;
}

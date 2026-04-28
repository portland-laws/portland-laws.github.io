import {
  createValidationResult,
  isRecord,
  normalizeEnum,
  parseFLogicOntology,
  parseTdfolFormula,
  requireBoolean,
  requireString,
  verifySimulatedCertificate,
  type LogicValidationIssue,
  type LogicValidationResult,
  type TdfolFormula,
} from './logic';
import {
  __resetPortlandCorpusCacheForTests,
  fetchCorpusJson,
  searchCorpus,
  type SearchFilters,
  type SearchMode,
  type SearchResult,
} from './portlandCorpus';

export type NormOperator = 'O' | 'P' | 'F' | 'unknown';
export type NormType = 'obligation' | 'permission' | 'prohibition' | 'unknown';
export type FormalizationStatus = 'success' | 'partial' | 'failed' | 'unknown';
export type ZkpBackend = 'simulated' | 'groth16' | 'unknown';

export interface LogicProofSummary {
  ipfs_cid: string;
  identifier: string;
  title: string;
  formalization_scope: string;
  fol_status: FormalizationStatus;
  deontic_status: FormalizationStatus;
  deontic_temporal_fol: string;
  deontic_cognitive_event_calculus: string;
  frame_logic_ergo: string;
  norm_operator: NormOperator;
  norm_type: NormType;
  zkp_backend: ZkpBackend;
  zkp_security_note: string;
  zkp_verified: boolean;
}

export interface LogicProofIndexes {
  proofByCid: Map<string, LogicProofSummary>;
  proofByIdentifier: Map<string, LogicProofSummary>;
  normByOperator: Map<NormOperator, LogicProofSummary[]>;
  normByType: Map<NormType, LogicProofSummary[]>;
  formalizationStatusCounts: Record<FormalizationStatus, number>;
  simulatedCertificateCount: number;
}

export interface LogicSearchFilters {
  normOperators?: NormOperator[];
  normTypes?: NormType[];
  formalizationStatuses?: FormalizationStatus[];
  requireVerifiedCertificate?: boolean;
  requireParseableTdfol?: boolean;
}

export interface LogicParseStatus {
  ok: boolean;
  ast?: TdfolFormula;
  error?: string;
}

export interface LogicProofExplanation {
  normLabel: string;
  plainLanguage: string;
  temporalScope: string;
  parseStatus: 'valid' | 'invalid';
  certificateStatus: string;
  caveats: string[];
}

export interface LogicEvidenceItem {
  ipfs_cid: string;
  identifier: string;
  normType: NormType;
  normOperator: NormOperator;
  temporalScope: string;
  parseStatus: 'valid' | 'invalid';
  certificateStatus: string;
  fLogicClass?: string;
  fLogicAttributes: Array<{ name: string; value: string }>;
  caveats: string[];
}

export interface LogicAwareSearchResult extends SearchResult {
  logic?: LogicEvidenceItem;
  logicScore: number;
}

const LOGIC_SUMMARIES_PATH = 'generated/logic-proof-summaries.json';

let logicProofPromise: Promise<LogicProofSummary[]> | null = null;
let logicIndexesPromise: Promise<LogicProofIndexes> | null = null;

function isFormalizationStatus(value: string): value is FormalizationStatus {
  return value === 'success' || value === 'partial' || value === 'failed' || value === 'unknown';
}

function isNormOperator(value: string): value is NormOperator {
  return value === 'O' || value === 'P' || value === 'F' || value === 'unknown';
}

function isNormType(value: string): value is NormType {
  return (
    value === 'obligation' ||
    value === 'permission' ||
    value === 'prohibition' ||
    value === 'unknown'
  );
}

function isZkpBackend(value: string): value is ZkpBackend {
  return value === 'simulated' || value === 'groth16' || value === 'unknown';
}

function normalizeFormalizationStatus(value: string, field: string, issues: LogicValidationIssue[]) {
  if (isFormalizationStatus(value)) {
    return value;
  }
  return normalizeEnum(value, ['success', 'partial', 'failed', 'unknown'] as const, 'unknown', field, issues);
}

function normalizeNormOperator(value: string, issues: LogicValidationIssue[]): NormOperator {
  if (isNormOperator(value)) {
    return value;
  }
  return normalizeEnum(value, ['O', 'P', 'F', 'unknown'] as const, 'unknown', 'norm_operator', issues);
}

function normalizeNormType(value: string, issues: LogicValidationIssue[]): NormType {
  if (isNormType(value)) {
    return value;
  }
  return normalizeEnum(
    value,
    ['obligation', 'permission', 'prohibition', 'unknown'] as const,
    'unknown',
    'norm_type',
    issues,
  );
}

function normalizeZkpBackend(value: string, issues: LogicValidationIssue[]): ZkpBackend {
  if (isZkpBackend(value)) {
    return value;
  }
  return normalizeEnum(value, ['simulated', 'groth16', 'unknown'] as const, 'unknown', 'zkp_backend', issues);
}

export function validateLogicProofSummary(value: unknown): LogicValidationResult {
  const issues: LogicValidationIssue[] = [];

  if (!isRecord(value)) {
    return {
      valid: false,
      issues: [{ severity: 'error', message: 'Logic proof summary must be an object' }],
    };
  }

  const requiredStringFields = [
    'ipfs_cid',
    'identifier',
    'title',
    'formalization_scope',
    'fol_status',
    'deontic_status',
    'deontic_temporal_fol',
    'deontic_cognitive_event_calculus',
    'frame_logic_ergo',
    'norm_operator',
    'norm_type',
    'zkp_backend',
    'zkp_security_note',
  ];

  for (const field of requiredStringFields) {
    requireString(value, field, issues);
  }
  requireBoolean(value, 'zkp_verified', issues);

  if (typeof value.fol_status === 'string') {
    normalizeFormalizationStatus(value.fol_status, 'fol_status', issues);
  }
  if (typeof value.deontic_status === 'string') {
    normalizeFormalizationStatus(value.deontic_status, 'deontic_status', issues);
  }
  if (typeof value.norm_operator === 'string') {
    normalizeNormOperator(value.norm_operator, issues);
  }
  if (typeof value.norm_type === 'string') {
    normalizeNormType(value.norm_type, issues);
  }
  if (typeof value.zkp_backend === 'string') {
    normalizeZkpBackend(value.zkp_backend, issues);
  }

  if (value.zkp_backend === 'simulated' && value.zkp_verified === true) {
    issues.push({
      severity: 'warning',
      field: 'zkp_verified',
      message: 'Simulated certificate is present, but this is not cryptographic verification',
    });
  }

  return createValidationResult(issues);
}

export function normalizeLogicProofSummary(value: unknown): LogicProofSummary {
  const validation = validateLogicProofSummary(value);
  if (!validation.valid || !isRecord(value)) {
    const details = validation.issues.map((issue) => issue.message).join('; ');
    throw new Error(`Invalid logic proof summary: ${details}`);
  }

  const issues = validation.issues;
  return {
    ipfs_cid: requireString(value, 'ipfs_cid', issues),
    identifier: requireString(value, 'identifier', issues),
    title: requireString(value, 'title', issues),
    formalization_scope: requireString(value, 'formalization_scope', issues),
    fol_status: normalizeFormalizationStatus(requireString(value, 'fol_status', issues), 'fol_status', issues),
    deontic_status: normalizeFormalizationStatus(
      requireString(value, 'deontic_status', issues),
      'deontic_status',
      issues,
    ),
    deontic_temporal_fol: requireString(value, 'deontic_temporal_fol', issues),
    deontic_cognitive_event_calculus: requireString(value, 'deontic_cognitive_event_calculus', issues),
    frame_logic_ergo: requireString(value, 'frame_logic_ergo', issues),
    norm_operator: normalizeNormOperator(requireString(value, 'norm_operator', issues), issues),
    norm_type: normalizeNormType(requireString(value, 'norm_type', issues), issues),
    zkp_backend: normalizeZkpBackend(requireString(value, 'zkp_backend', issues), issues),
    zkp_security_note: requireString(value, 'zkp_security_note', issues),
    zkp_verified: requireBoolean(value, 'zkp_verified', issues),
  };
}

export async function loadLogicProofSummaries(): Promise<LogicProofSummary[]> {
  if (!logicProofPromise) {
    logicProofPromise = fetchCorpusJson<unknown[]>(LOGIC_SUMMARIES_PATH).then((rows) => {
      if (!Array.isArray(rows)) {
        throw new Error('Logic proof summaries asset must be an array');
      }
      return rows.map(normalizeLogicProofSummary);
    });
  }
  return logicProofPromise;
}

function emptyNormMap<T extends string>(values: T[]): Map<T, LogicProofSummary[]> {
  return new Map(values.map((value) => [value, []]));
}

export function buildLogicProofIndexes(summaries: LogicProofSummary[]): LogicProofIndexes {
  const proofByCid = new Map<string, LogicProofSummary>();
  const proofByIdentifier = new Map<string, LogicProofSummary>();
  const normByOperator = emptyNormMap<NormOperator>(['O', 'P', 'F', 'unknown']);
  const normByType = emptyNormMap<NormType>(['obligation', 'permission', 'prohibition', 'unknown']);
  const formalizationStatusCounts: Record<FormalizationStatus, number> = {
    success: 0,
    partial: 0,
    failed: 0,
    unknown: 0,
  };
  let simulatedCertificateCount = 0;

  for (const summary of summaries) {
    proofByCid.set(summary.ipfs_cid, summary);
    proofByIdentifier.set(summary.identifier, summary);
    normByOperator.get(summary.norm_operator)?.push(summary);
    normByType.get(summary.norm_type)?.push(summary);
    formalizationStatusCounts[summary.deontic_status] += 1;
    if (summary.zkp_backend === 'simulated' && summary.zkp_verified) {
      simulatedCertificateCount += 1;
    }
  }

  return {
    proofByCid,
    proofByIdentifier,
    normByOperator,
    normByType,
    formalizationStatusCounts,
    simulatedCertificateCount,
  };
}

export async function loadLogicProofIndexes(): Promise<LogicProofIndexes> {
  if (!logicIndexesPromise) {
    logicIndexesPromise = loadLogicProofSummaries().then(buildLogicProofIndexes);
  }
  return logicIndexesPromise;
}

export async function getLogicProofForSection(ipfsCid: string): Promise<LogicProofSummary | null> {
  const indexes = await loadLogicProofIndexes();
  return indexes.proofByCid.get(ipfsCid) || null;
}

export async function getLogicProofForIdentifier(identifier: string): Promise<LogicProofSummary | null> {
  const indexes = await loadLogicProofIndexes();
  return indexes.proofByIdentifier.get(identifier) || null;
}

export async function searchCorpusWithLogic(
  query: string,
  filters: SearchFilters & LogicSearchFilters = {},
  mode: SearchMode = 'hybrid',
  queryEmbedding?: Float32Array | number[],
): Promise<LogicAwareSearchResult[]> {
  const results = await searchCorpus(query, filters, mode, queryEmbedding);
  const summaries = await loadLogicProofSummaries();
  const byCid = new Map(summaries.map((summary) => [summary.ipfs_cid, summary]));

  return results
    .map((result) => {
      const proof = byCid.get(result.ipfs_cid);
      const logic = proof ? buildLogicEvidenceItem(proof) : undefined;
      const logicScore = proof ? scoreLogicMatch(proof, filters) : 0;
      return {
        ...result,
        logic,
        logicScore,
        score: result.score + logicScore,
      };
    })
    .filter((result) => {
      if (!result.logic) {
        return !hasLogicFilters(filters);
      }
      return filterLogicProofSummaries([byCid.get(result.ipfs_cid)!], filters).length > 0;
    })
    .sort((left, right) => right.score - left.score);
}

export function filterLogicProofSummaries(
  summaries: LogicProofSummary[],
  filters: LogicSearchFilters = {},
): LogicProofSummary[] {
  return summaries.filter((summary) => {
    if (filters.normOperators?.length && !filters.normOperators.includes(summary.norm_operator)) {
      return false;
    }
    if (filters.normTypes?.length && !filters.normTypes.includes(summary.norm_type)) {
      return false;
    }
    if (
      filters.formalizationStatuses?.length &&
      !filters.formalizationStatuses.includes(summary.deontic_status)
    ) {
      return false;
    }
    if (filters.requireVerifiedCertificate && !summary.zkp_verified) {
      return false;
    }
    if (filters.requireParseableTdfol && !parseLogicProofTdfol(summary).ok) {
      return false;
    }
    return true;
  });
}

export function parseLogicProofTdfol(summary: LogicProofSummary): LogicParseStatus {
  try {
    return {
      ok: true,
      ast: parseTdfolFormula(summary.deontic_temporal_fol),
    };
  } catch (error) {
    return {
      ok: false,
      error: error instanceof Error ? error.message : String(error),
    };
  }
}

export function explainLogicProofSummary(summary: LogicProofSummary): LogicProofExplanation {
  const parseStatus = parseLogicProofTdfol(summary);
  const temporalScope = parseStatus.ast ? describeTemporalScope(parseStatus.ast) : 'Temporal scope unavailable';
  const normLabel = describeNorm(summary);
  const certificateWarning = getSimulatedCertificateWarning(summary);
  const caveats = [
    'Machine-generated candidate formalization; verify against the official code text.',
    ...(certificateWarning ? [certificateWarning] : []),
  ];

  return {
    normLabel,
    plainLanguage: `${summary.identifier} is classified as a ${normLabel.toLowerCase()}. The generated logic says the rule applies to agents subject to this code section and should be read together with the section text.`,
    temporalScope,
    parseStatus: parseStatus.ok ? 'valid' : 'invalid',
    certificateStatus:
      summary.zkp_backend === 'simulated'
        ? 'Simulated certificate metadata only'
        : `${summary.zkp_backend} certificate metadata`,
    caveats,
  };
}

export function buildLogicEvidenceItem(summary: LogicProofSummary): LogicEvidenceItem {
  const explanation = explainLogicProofSummary(summary);
  const ontology = parseFLogicOntology(summary.frame_logic_ergo, summary.identifier);
  const frame = ontology.frames[0];
  const certificate = verifySimulatedCertificate(summary);

  return {
    ipfs_cid: summary.ipfs_cid,
    identifier: summary.identifier,
    normType: summary.norm_type,
    normOperator: summary.norm_operator,
    temporalScope: explanation.temporalScope,
    parseStatus: explanation.parseStatus,
    certificateStatus: certificate.status,
    fLogicClass: frame?.isa,
    fLogicAttributes: frame
      ? Object.entries(frame.scalarMethods).map(([name, value]) => ({ name, value }))
      : [],
    caveats: explanation.caveats,
  };
}

export async function buildLogicEvidenceForSearchResults(
  results: SearchResult[],
): Promise<LogicEvidenceItem[]> {
  const indexes = await loadLogicProofIndexes();
  return results
    .map((result) => indexes.proofByCid.get(result.ipfs_cid))
    .filter((summary): summary is LogicProofSummary => Boolean(summary))
    .map(buildLogicEvidenceItem);
}

export function getSimulatedCertificateWarning(summary: LogicProofSummary): string | null {
  if (summary.zkp_backend === 'simulated' && summary.zkp_verified) {
    return 'Simulated educational certificate present; this is not cryptographic verification.';
  }
  return null;
}

function describeNorm(summary: LogicProofSummary): string {
  if (summary.norm_type !== 'unknown') {
    return summary.norm_type;
  }
  switch (summary.norm_operator) {
    case 'O':
      return 'obligation';
    case 'P':
      return 'permission';
    case 'F':
      return 'prohibition';
    default:
      return 'unknown norm';
  }
}

function describeTemporalScope(formula: TdfolFormula): string {
  const temporalOperators = new Set<string>();
  collectTemporalOperators(formula, temporalOperators);

  if (temporalOperators.has('ALWAYS')) {
    return 'Always/continuing condition';
  }
  if (temporalOperators.has('EVENTUALLY')) {
    return 'Eventual/future condition';
  }
  if (temporalOperators.has('NEXT')) {
    return 'Next-step condition';
  }
  return 'No explicit temporal operator';
}

function hasLogicFilters(filters: LogicSearchFilters): boolean {
  return Boolean(
    filters.normOperators?.length ||
      filters.normTypes?.length ||
      filters.formalizationStatuses?.length ||
      filters.requireVerifiedCertificate ||
      filters.requireParseableTdfol,
  );
}

function scoreLogicMatch(summary: LogicProofSummary, filters: LogicSearchFilters): number {
  let score = 0;
  if (filters.normOperators?.includes(summary.norm_operator)) score += 2;
  if (filters.normTypes?.includes(summary.norm_type)) score += 2;
  if (filters.formalizationStatuses?.includes(summary.deontic_status)) score += 1;
  if (filters.requireVerifiedCertificate && summary.zkp_verified) score += 0.5;
  if (filters.requireParseableTdfol && parseLogicProofTdfol(summary).ok) score += 0.5;
  return score;
}

function collectTemporalOperators(formula: TdfolFormula, operators: Set<string>): void {
  switch (formula.kind) {
    case 'temporal':
      operators.add(formula.operator);
      collectTemporalOperators(formula.formula, operators);
      return;
    case 'deontic':
    case 'unary':
    case 'quantified':
      collectTemporalOperators(formula.formula, operators);
      return;
    case 'binary':
      collectTemporalOperators(formula.left, operators);
      collectTemporalOperators(formula.right, operators);
      return;
    case 'predicate':
      return;
  }
}

export function __resetPortlandLogicCacheForTests(): void {
  logicProofPromise = null;
  logicIndexesPromise = null;
  __resetPortlandCorpusCacheForTests();
}

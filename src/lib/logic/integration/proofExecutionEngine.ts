import type { LogicValidationIssue } from '../types';
import {
  BrowserNativeLogicVerification,
  type LogicVerificationFormat,
  type LogicVerifierBackendName,
} from './logicVerification';
import {
  detectLogicVerificationRuntimeBridge,
  makeLogicVerificationIssue,
  normalizeLogicVerificationFormula,
} from './logicVerificationUtils';

export type ProofExecutionStatus = 'success' | 'failure' | 'timeout' | 'error' | 'unsupported';
export type ProofExecutionProver =
  | 'local'
  | 'fol'
  | 'tdfol'
  | 'cec'
  | 'dcec'
  | 'z3'
  | 'cvc5'
  | 'lean'
  | 'coq';
export interface ProofExecutionOptions {
  timeout?: number;
  defaultProver?: ProofExecutionProver;
  enableRateLimiting?: boolean;
  enableValidation?: boolean;
  enableCaching?: boolean;
  cacheSize?: number;
}
export interface ProofExecutionResult {
  prover: string;
  statement: string;
  status: ProofExecutionStatus;
  proofOutput: string;
  executionTime: number;
  errors: Array<string>;
  warnings: Array<string>;
  metadata: Record<string, unknown>;
}
export interface ProofExecutionTypeIssue {
  path: string;
  message: string;
}
export type ProofExecutionTypeName = 'options' | 'result' | 'metadata';
export interface ProofExecutionTypeCheckResult {
  ok: boolean;
  typeName: ProofExecutionTypeName;
  issues: Array<ProofExecutionTypeIssue>;
  metadata: typeof PROOF_EXECUTION_ENGINE_TYPES_METADATA;
}
export const PROOF_EXECUTION_ENGINE_METADATA = {
  sourcePythonModule: 'logic/integration/reasoning/proof_execution_engine.py',
  browserNative: true,
  serverCallsAllowed: false,
  pythonRuntimeAllowed: false,
  filesystemAllowed: false,
  subprocessAllowed: false,
  rpcAllowed: false,
  runtimeDependencies: [] as Array<string>,
  parity: [
    'proof_engine_facade',
    'local_prover_selection',
    'formula_validation',
    'bounded_memory_cache',
    'rule_set_execution',
    'fail_closed_external_provers',
  ] as Array<string>,
} as const;
export const PROOF_EXECUTION_ENGINE_TYPES_METADATA = {
  sourcePythonModule: 'logic/integration/reasoning/proof_execution_engine_types.py',
  browserNative: true,
  serverCallsAllowed: false,
  pythonRuntimeAllowed: false,
  filesystemAllowed: false,
  subprocessAllowed: false,
  rpcAllowed: false,
  runtimeDependencies: [] as Array<string>,
  parity: [
    'proof_execution_options_type',
    'proof_execution_result_type',
    'proof_execution_status_type',
    'proof_execution_metadata_type',
  ] as Array<string>,
} as const;
export const PROOF_EXECUTION_ENGINE_UTILS_METADATA = {
  sourcePythonModule: 'logic/integration/reasoning/proof_execution_engine_utils.py',
  browserNative: true,
  serverCallsAllowed: false,
  pythonRuntimeAllowed: false,
  filesystemAllowed: false,
  subprocessAllowed: false,
  rpcAllowed: false,
  runtimeDependencies: [] as Array<string>,
  parity: [
    'statement_normalization',
    'runtime_bridge_marker_detection',
    'proof_request_validation',
    'execution_result_summarization',
    'cache_key_construction',
  ] as Array<string>,
} as const;

const EXTERNAL_PROVERS = new Set<string>(['z3', 'cvc5', 'lean', 'coq']);

export class BrowserNativeProofExecutionEngine {
  readonly metadata = PROOF_EXECUTION_ENGINE_METADATA;
  readonly timeout: number;
  readonly defaultProver: ProofExecutionProver;
  readonly enableRateLimiting: boolean;
  readonly enableValidation: boolean;
  readonly enableCaching: boolean;
  private readonly verifier = new BrowserNativeLogicVerification();
  private readonly cache = new Map<string, ProofExecutionResult>();
  private readonly cacheSize: number;

  constructor(options: ProofExecutionOptions = {}) {
    this.timeout = options.timeout ?? 60;
    this.defaultProver = options.defaultProver ?? 'local';
    this.enableRateLimiting = options.enableRateLimiting ?? true;
    this.enableValidation = options.enableValidation ?? true;
    this.enableCaching = options.enableCaching ?? true;
    this.cacheSize = options.cacheSize ?? 1000;
  }

  proveDeonticFormula = (
    formula: unknown,
    prover: ProofExecutionProver = this.defaultProver,
    _userId = 'default',
    useCache = true,
  ): ProofExecutionResult => {
    const statement = stringifyFormula(formula);
    const cacheKey = `${prover}:${statement}`;
    const cached = useCache && this.enableCaching ? this.cache.get(cacheKey) : undefined;
    if (cached) return cloneResult(cached, { cacheHit: true });
    const result = this.executeLocalProof(statement, prover, Date.now());
    if (useCache && this.enableCaching) this.remember(cacheKey, result);
    return result;
  };

  prove_deontic_formula = this.proveDeonticFormula;
  prove = this.proveDeonticFormula;
  proveRuleSet = (
    ruleSet: { formulas?: Array<unknown> },
    prover: ProofExecutionProver = this.defaultProver,
  ): Array<ProofExecutionResult> =>
    [...(ruleSet.formulas ?? [])].map((formula) => this.proveDeonticFormula(formula, prover));
  prove_rule_set = this.proveRuleSet;
  proveConsistency = (
    ruleSet: { formulas?: Array<unknown> },
    prover: ProofExecutionProver = this.defaultProver,
  ): ProofExecutionResult => {
    const results = this.proveRuleSet(ruleSet, prover);
    const failed = results.find((result) => result.status !== 'success');
    return buildResult(
      prover,
      `Consistency check for ${results.length} formulas`,
      failed ? 'failure' : 'success',
      0,
      failed
        ? 'Rule set contains an unverified formula.'
        : 'Rule set passed local consistency checks.',
      failed ? [`Formula failed with status ${failed.status}: ${failed.statement}`] : [],
      [],
      { checkedFormulas: results.length, failedClosed: Boolean(failed) },
    );
  };
  prove_consistency = this.proveConsistency;
  proveMultipleProvers = (
    formula: unknown,
    provers: Array<ProofExecutionProver> = ['local', 'z3', 'cvc5', 'lean', 'coq'],
  ): Array<ProofExecutionResult> =>
    provers.map((prover) => this.proveDeonticFormula(formula, prover));
  prove_multiple_provers = this.proveMultipleProvers;
  getProverStatus = (): Record<string, unknown> => ({
    defaultProver: this.defaultProver,
    timeout: this.timeout,
    availableProvers: {
      local: true,
      fol: true,
      tdfol: true,
      cec: true,
      dcec: false,
      z3: false,
      cvc5: false,
      lean: false,
      coq: false,
    },
    cacheSize: this.cache.size,
    metadata: PROOF_EXECUTION_ENGINE_METADATA,
  });
  get_prover_status = this.getProverStatus;
  clearCache = (): void => this.cache.clear();

  private executeLocalProof(
    statement: string,
    prover: ProofExecutionProver,
    startedAt: number,
  ): ProofExecutionResult {
    if (EXTERNAL_PROVERS.has(prover))
      return buildResult(prover, statement, 'unsupported', startedAt, '', [
        `Prover ${prover} is not available in the browser-native runtime.`,
      ]);
    const format = prover === 'local' ? 'auto' : prover;
    const result = this.verifier.verify(statement, {
      format: format as LogicVerificationFormat,
      backend: prover === 'local' ? 'local' : (prover as LogicVerifierBackendName),
      requirePredicate: false,
    });
    const status =
      result.status === 'verified'
        ? 'success'
        : result.status === 'invalid'
          ? 'failure'
          : 'unsupported';
    return buildResult(
      prover,
      statement,
      status,
      startedAt,
      result.checks.join('\n'),
      result.issues.filter(isError).map(formatIssue),
      result.issues.filter(isWarning).map(formatIssue),
    );
  }

  private remember(key: string, result: ProofExecutionResult): void {
    if (this.cache.size >= this.cacheSize)
      this.cache.delete(String(this.cache.keys().next().value));
    this.cache.set(key, cloneResult(result));
  }
}

export const ProofExecutionEngine = BrowserNativeProofExecutionEngine;
export const createProofEngine = (
  options: ProofExecutionOptions = {},
): BrowserNativeProofExecutionEngine => new BrowserNativeProofExecutionEngine(options);
export const create_proof_engine = createProofEngine;
export const proveFormula = (
  formula: unknown,
  prover: ProofExecutionProver = 'local',
): ProofExecutionResult => createProofEngine().prove(formula, prover);
export const prove_formula = proveFormula;
export const checkConsistency = (
  ruleSet: { formulas?: Array<unknown> },
  prover: ProofExecutionProver = 'local',
): ProofExecutionResult => createProofEngine().proveConsistency(ruleSet, prover);
export const check_consistency = checkConsistency;
export const proof_execution_engine_metadata = PROOF_EXECUTION_ENGINE_METADATA;
export const proof_execution_engine_types_metadata = PROOF_EXECUTION_ENGINE_TYPES_METADATA;

export function checkProofExecutionType(
  typeName: ProofExecutionTypeName,
  value: unknown,
): ProofExecutionTypeCheckResult {
  const object = asRecord(value);
  const issues: Array<ProofExecutionTypeIssue> = [];
  if (!object) return proofTypeChecked(typeName, [{ path: '$', message: 'expected_object' }]);
  if (typeName === 'options') validateOptions(object, issues);
  else if (typeName === 'result') validateExecutionResult(object, issues);
  else validateProofMetadata(object, '$', issues);
  return proofTypeChecked(typeName, issues);
}
export function isProofExecutionType(typeName: ProofExecutionTypeName, value: unknown): boolean {
  return checkProofExecutionType(typeName, value).ok;
}
export function assertProofExecutionResult(value: unknown): ProofExecutionResult {
  const result = checkProofExecutionType('result', value);
  if (!result.ok)
    throw new TypeError(
      `Invalid proof execution result: ${result.issues.map((issue) => `${issue.path}:${issue.message}`).join(', ')}`,
    );
  return value as ProofExecutionResult;
}
export const check_proof_execution_type = checkProofExecutionType;
export const is_proof_execution_type = isProofExecutionType;
export const assert_proof_execution_result = assertProofExecutionResult;
export const proof_execution_engine_utils_metadata = PROOF_EXECUTION_ENGINE_UTILS_METADATA;

export function normalizeProofExecutionStatement(formula: unknown): string {
  return normalizeLogicVerificationFormula(stringifyFormula(formula));
}

export function detectProofExecutionRuntimeBridge(formula: unknown) {
  const statement = normalizeProofExecutionStatement(formula);
  const bridge = detectLogicVerificationRuntimeBridge(statement);
  return { ...bridge, statement, metadata: PROOF_EXECUTION_ENGINE_UTILS_METADATA };
}

export function buildProofExecutionCacheKey(
  formula: unknown,
  prover: ProofExecutionProver = 'local',
): string {
  return `${prover}:${normalizeProofExecutionStatement(formula)}`;
}

export function validateProofExecutionRequest(formula: unknown, prover: unknown = 'local') {
  const issues: Array<LogicValidationIssue> = [];
  const statement = normalizeProofExecutionStatement(formula);
  if (statement.length === 0)
    issues.push(
      makeLogicVerificationIssue('Proof statement must be non-empty.', 'error', 'formula'),
    );
  if (!isProver(prover))
    issues.push(makeLogicVerificationIssue('Proof prover is not supported.', 'error', 'prover'));
  const bridge = detectProofExecutionRuntimeBridge(statement);
  if (!bridge.safe)
    issues.push(
      makeLogicVerificationIssue(
        `Proof statement contains runtime bridge markers: ${bridge.markers.join(', ')}.`,
        'error',
        'formula',
      ),
    );
  return {
    valid: !issues.some((issue) => issue.severity === 'error'),
    statement,
    prover: isProver(prover) ? prover : undefined,
    issues,
    metadata: PROOF_EXECUTION_ENGINE_UTILS_METADATA,
  };
}

export function summarizeProofExecutionResults(results: Array<ProofExecutionResult>) {
  const counts: Record<ProofExecutionStatus, number> = {
    success: 0,
    failure: 0,
    timeout: 0,
    error: 0,
    unsupported: 0,
  };
  const provers = new Set<string>();
  const issues: Array<Record<string, unknown>> = [];
  results.forEach((result, resultIndex) => {
    counts[result.status] += 1;
    provers.add(result.prover);
    result.errors.forEach((message) =>
      issues.push({
        resultIndex,
        statement: result.statement,
        prover: result.prover,
        severity: 'error',
        message,
      }),
    );
    result.warnings.forEach((message) =>
      issues.push({
        resultIndex,
        statement: result.statement,
        prover: result.prover,
        severity: 'warning',
        message,
      }),
    );
  });
  return {
    total: results.length,
    successful: counts.success,
    failure: counts.failure,
    timeout: counts.timeout,
    error: counts.error,
    unsupported: counts.unsupported,
    success:
      results.length > 0 &&
      counts.failure === 0 &&
      counts.timeout === 0 &&
      counts.error === 0 &&
      counts.unsupported === 0,
    failedClosed:
      counts.failure > 0 || counts.timeout > 0 || counts.error > 0 || counts.unsupported > 0,
    provers: Array.from(provers),
    issues,
    metadata: PROOF_EXECUTION_ENGINE_UTILS_METADATA,
  };
}
export const normalize_proof_execution_statement = normalizeProofExecutionStatement;
export const detect_proof_execution_runtime_bridge = detectProofExecutionRuntimeBridge;
export const build_proof_execution_cache_key = buildProofExecutionCacheKey;
export const validate_proof_execution_request = validateProofExecutionRequest;
export const summarize_proof_execution_results = summarizeProofExecutionResults;

function buildResult(
  prover: string,
  statement: string,
  status: ProofExecutionStatus,
  startedAt: number,
  proofOutput = '',
  errors: Array<string> = [],
  warnings: Array<string> = [],
  metadata: Record<string, unknown> = {},
): ProofExecutionResult {
  return {
    prover,
    statement,
    status,
    proofOutput,
    executionTime: Math.max(0, (Date.now() - startedAt) / 1000),
    errors,
    warnings,
    metadata: { ...PROOF_EXECUTION_ENGINE_METADATA, ...metadata },
  };
}
function stringifyFormula(formula: unknown): string {
  if (typeof formula === 'string') return formula;
  const candidate = formula as Record<string, unknown> | null;
  if (candidate && typeof candidate.to_fol_string === 'function')
    return String(candidate.to_fol_string());
  if (candidate && typeof candidate.toFolString === 'function')
    return String(candidate.toFolString());
  return String(formula ?? '');
}
function isError(issue: LogicValidationIssue): boolean {
  return issue.severity === 'error';
}
function isWarning(issue: LogicValidationIssue): boolean {
  return issue.severity === 'warning';
}
function formatIssue(issue: LogicValidationIssue): string {
  return issue.field ? `${issue.field}: ${issue.message}` : issue.message;
}
function cloneResult(
  result: ProofExecutionResult,
  metadata: Record<string, unknown> = {},
): ProofExecutionResult {
  return {
    ...result,
    errors: [...result.errors],
    warnings: [...result.warnings],
    metadata: { ...result.metadata, ...metadata },
  };
}
function validateOptions(
  object: Record<string, unknown>,
  issues: Array<ProofExecutionTypeIssue>,
): void {
  if ('timeout' in object) requireNumber(object, 'timeout', issues);
  if ('cacheSize' in object) requireInteger(object, 'cacheSize', issues);
  if ('defaultProver' in object && !isProver(object.defaultProver))
    issues.push({ path: '$.defaultProver', message: 'expected_proof_execution_prover' });
  ['enableRateLimiting', 'enableValidation', 'enableCaching'].forEach((field) =>
    field in object && typeof object[field] !== 'boolean'
      ? issues.push({ path: `$.${field}`, message: 'expected_boolean' })
      : undefined,
  );
}
function validateExecutionResult(
  object: Record<string, unknown>,
  issues: Array<ProofExecutionTypeIssue>,
): void {
  ['prover', 'statement', 'proofOutput'].forEach((field) =>
    requireStringField(object, field, issues),
  );
  if (!isStatus(object.status)) issues.push({ path: '$.status', message: 'expected_status' });
  requireNumber(object, 'executionTime', issues);
  ['errors', 'warnings'].forEach((field) =>
    requireStringArray(object[field], `$.${field}`, issues),
  );
  requireMetadata(object.metadata, '$.metadata', issues);
}
function validateProofMetadata(
  object: Record<string, unknown>,
  path: string,
  issues: Array<ProofExecutionTypeIssue>,
): void {
  if (object.browserNative !== true)
    issues.push({ path: `${path}.browserNative`, message: 'expected_true' });
  [
    'serverCallsAllowed',
    'pythonRuntimeAllowed',
    'filesystemAllowed',
    'subprocessAllowed',
    'rpcAllowed',
  ].forEach((field) => {
    if (object[field] !== false)
      issues.push({ path: `${path}.${field}`, message: 'expected_false' });
  });
  requireStringArray(object.runtimeDependencies, `${path}.runtimeDependencies`, issues);
}
function requireMetadata(
  value: unknown,
  path: string,
  issues: Array<ProofExecutionTypeIssue>,
): void {
  const metadata = asRecord(value);
  if (!metadata) issues.push({ path, message: 'expected_object' });
  else validateProofMetadata(metadata, path, issues);
}
function requireStringField(
  object: Record<string, unknown>,
  field: string,
  issues: Array<ProofExecutionTypeIssue>,
): void {
  if (typeof object[field] !== 'string')
    issues.push({ path: `$.${field}`, message: 'expected_string' });
}
function requireStringArray(
  value: unknown,
  path: string,
  issues: Array<ProofExecutionTypeIssue>,
): void {
  if (!Array.isArray(value) || value.some((item) => typeof item !== 'string'))
    issues.push({ path, message: 'expected_string_array' });
}
function isStatus(value: unknown): value is ProofExecutionStatus {
  return (
    value === 'success' ||
    value === 'failure' ||
    value === 'timeout' ||
    value === 'error' ||
    value === 'unsupported'
  );
}
function isProver(value: unknown): value is ProofExecutionProver {
  return (
    value === 'local' ||
    value === 'fol' ||
    value === 'tdfol' ||
    value === 'cec' ||
    value === 'dcec' ||
    value === 'z3' ||
    value === 'cvc5' ||
    value === 'lean' ||
    value === 'coq'
  );
}
function requireNumber(
  object: Record<string, unknown>,
  field: string,
  issues: Array<ProofExecutionTypeIssue>,
): void {
  if (!isNonNegativeNumber(object[field]))
    issues.push({ path: `$.${field}`, message: 'expected_non_negative_number' });
}
function requireInteger(
  object: Record<string, unknown>,
  field: string,
  issues: Array<ProofExecutionTypeIssue>,
): void {
  if (!Number.isInteger(object[field]) || (object[field] as number) < 0)
    issues.push({ path: `$.${field}`, message: 'expected_non_negative_integer' });
}
function isNonNegativeNumber(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value) && value >= 0;
}
function proofTypeChecked(
  typeName: ProofExecutionTypeName,
  issues: Array<ProofExecutionTypeIssue>,
): ProofExecutionTypeCheckResult {
  return {
    ok: issues.length === 0,
    typeName,
    issues,
    metadata: PROOF_EXECUTION_ENGINE_TYPES_METADATA,
  };
}
function asRecord(value: unknown): Record<string, unknown> | undefined {
  return value && typeof value === 'object' && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : undefined;
}

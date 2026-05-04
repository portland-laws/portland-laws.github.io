import type { LogicValidationIssue } from '../types';
import {
  BrowserNativeLogicVerification,
  type LogicVerificationFormat,
  type LogicVerifierBackendName,
} from './logicVerification';

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

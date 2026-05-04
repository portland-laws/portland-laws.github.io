import { parseCecExpression } from '../cec/parser';
import { validateFolSyntax } from '../fol/parser';
import { parseTdfolFormula } from '../tdfol/parser';
import type { LogicValidationIssue } from '../types';
import { validateFormulaString } from '../validation';
import {
  detectLogicVerificationRuntimeBridge,
  makeLogicVerificationIssue,
  normalizeLogicVerificationFormula,
} from './logicVerificationUtils';
import { buildReasoningLogicTheoremFormula } from './reasoningLogicVerificationUtils';

export type LogicVerificationFormat = 'auto' | 'fol' | 'tdfol' | 'cec' | 'dcec';
export type LogicVerificationStatus = 'verified' | 'invalid' | 'unsupported';
export type LogicVerifierBackendName =
  | 'local'
  | 'fol'
  | 'tdfol'
  | 'cec'
  | 'dcec'
  | 'z3'
  | 'cvc5'
  | 'lean'
  | 'external';

export interface LogicVerificationOptions {
  format?: LogicVerificationFormat;
  requirePredicate?: boolean;
  backend?: LogicVerifierBackendName;
}
export interface LogicVerifierBackendDescriptor {
  name: LogicVerifierBackendName;
  formats: Array<LogicVerificationFormat>;
  available: boolean;
  browserNative: boolean;
  wasmCompatible: boolean;
  failureMode: 'local' | 'fail_closed';
  runtimeDependencies: Array<string>;
  sourcePythonModule: 'logic/integration/reasoning/_logic_verifier_backends_mixin.py';
}
export interface LogicVerificationResult {
  status: LogicVerificationStatus;
  success: boolean;
  formula: string;
  format: LogicVerificationFormat;
  backend: LogicVerifierBackendDescriptor;
  normalizedFormula: string;
  checks: Array<string>;
  issues: Array<LogicValidationIssue>;
  metadata: typeof LOGIC_VERIFICATION_METADATA;
}
export interface ReasoningLogicVerificationSummary {
  total: number;
  verified: number;
  invalid: number;
  unsupported: number;
  success: boolean;
  failedClosed: boolean;
  results: Array<LogicVerificationResult>;
  metadata: typeof REASONING_LOGIC_VERIFICATION_METADATA;
}
export const LOGIC_VERIFICATION_METADATA = {
  verifier: 'browser-native-logic-verification',
  sourcePythonModule: 'logic/integration/logic_verification.py',
  browserNative: true,
  serverCallsAllowed: false,
  pythonRuntimeAllowed: false,
  runtimeDependencies: [] as Array<string>,
  parity: [
    'local_formula_validation',
    'parser_backed_fol_tdfol_cec_validation',
    'logic_verifier_backends_mixin_selection',
    'logic_verification_utils_normalization',
    'fail_closed_unsupported_runtime',
  ] as Array<string>,
} as const;

export const LOGIC_VERIFIER_BACKENDS_MIXIN_METADATA = {
  sourcePythonModule: 'logic/integration/reasoning/_logic_verifier_backends_mixin.py',
  browserNative: true,
  serverCallsAllowed: false,
  pythonRuntimeAllowed: false,
  runtimeDependencies: [] as Array<string>,
} as const;

export const REASONING_LOGIC_VERIFICATION_METADATA = {
  verifier: 'browser-native-reasoning-logic-verification',
  sourcePythonModule: 'logic/integration/reasoning/logic_verification.py',
  browserNative: true,
  serverCallsAllowed: false,
  pythonRuntimeAllowed: false,
  runtimeDependencies: [] as Array<string>,
  parity: [
    'reasoning_logic_verifier_facade',
    'local_theorem_verification',
    'batch_reasoning_summary',
    'fail_closed_runtime_backends',
  ] as Array<string>,
} as const;

const LOGIC_VERIFIER_BACKENDS: Array<LogicVerifierBackendDescriptor> = [
  {
    name: 'local',
    formats: ['fol', 'tdfol', 'cec'],
    available: true,
    browserNative: true,
    wasmCompatible: true,
    failureMode: 'local',
    runtimeDependencies: [],
    sourcePythonModule: 'logic/integration/reasoning/_logic_verifier_backends_mixin.py',
  },
  {
    name: 'fol',
    formats: ['fol'],
    available: true,
    browserNative: true,
    wasmCompatible: true,
    failureMode: 'local',
    runtimeDependencies: [],
    sourcePythonModule: 'logic/integration/reasoning/_logic_verifier_backends_mixin.py',
  },
  {
    name: 'tdfol',
    formats: ['tdfol'],
    available: true,
    browserNative: true,
    wasmCompatible: true,
    failureMode: 'local',
    runtimeDependencies: [],
    sourcePythonModule: 'logic/integration/reasoning/_logic_verifier_backends_mixin.py',
  },
  {
    name: 'cec',
    formats: ['cec'],
    available: true,
    browserNative: true,
    wasmCompatible: true,
    failureMode: 'local',
    runtimeDependencies: [],
    sourcePythonModule: 'logic/integration/reasoning/_logic_verifier_backends_mixin.py',
  },
  ...(['dcec', 'z3', 'cvc5', 'lean', 'external'] as Array<LogicVerifierBackendName>).map(
    (name): LogicVerifierBackendDescriptor => ({
      name,
      formats: name === 'dcec' ? ['dcec'] : ['fol', 'tdfol', 'cec', 'dcec'],
      available: false,
      browserNative: true,
      wasmCompatible: false,
      failureMode: 'fail_closed',
      runtimeDependencies: [],
      sourcePythonModule: 'logic/integration/reasoning/_logic_verifier_backends_mixin.py',
    }),
  ),
];

export class BrowserNativeLogicVerification {
  readonly metadata = LOGIC_VERIFICATION_METADATA;
  readonly backendsMetadata = LOGIC_VERIFIER_BACKENDS_MIXIN_METADATA;

  getBackends(): Array<LogicVerifierBackendDescriptor> {
    return getLogicVerifierBackends();
  }

  selectBackend(
    format: LogicVerificationFormat,
    backend?: LogicVerifierBackendName,
  ): LogicVerifierBackendDescriptor {
    return selectLogicVerifierBackend(format, backend);
  }

  verify(formula: string, options: LogicVerificationOptions = {}): LogicVerificationResult {
    const format = options.format ?? 'auto';
    const normalizedFormula = normalizeLogicVerificationFormula(formula);
    const detectedFormat = format === 'auto' ? detectFormat(normalizedFormula) : format;
    const backend = this.selectBackend(detectedFormat, options.backend);
    const checks = ['input_string', 'no_runtime_bridge_markers', 'balanced_delimiters'];
    const issues: Array<LogicValidationIssue> = [];

    try {
      validateFormulaString(formula, { fieldName: 'formula' });
    } catch (error) {
      issues.push({ severity: 'error', field: 'formula', message: errorMessage(error) });
      return buildResult('invalid', formula, format, backend, normalizedFormula, checks, issues);
    }

    if (!detectLogicVerificationRuntimeBridge(normalizedFormula).safe)
      issues.push(
        makeLogicVerificationIssue(
          'Formula contains runtime bridge markers that are not browser-native.',
          'error',
          'formula',
        ),
      );
    issues.push(...validateBalancedDelimiters(normalizedFormula));
    if (options.requirePredicate !== false && !/[A-Za-z][A-Za-z0-9_]*\s*\(/.test(normalizedFormula))
      issues.push({
        severity: 'error',
        field: 'formula',
        message: 'Formula must contain at least one predicate application.',
      });

    checks.push(`backend:${backend.name}`);
    if (!backend.available || !backend.formats.includes(detectedFormat)) {
      issues.push({
        severity: 'error',
        field: 'backend',
        message: `Logic verifier backend '${backend.name}' is not available in the browser-native runtime for ${detectedFormat}.`,
      });
      return buildResult(
        'unsupported',
        formula,
        format,
        backend,
        normalizedFormula,
        checks,
        issues,
      );
    }
    checks.push(`${detectedFormat}_syntax`);
    issues.push(...validateByFormat(normalizedFormula, detectedFormat));
    if (detectedFormat === 'dcec') {
      issues.push({
        severity: 'error',
        field: 'format',
        message: 'DCEC verification requires a dedicated local adapter and fails closed here.',
      });
      return buildResult(
        'unsupported',
        formula,
        format,
        backend,
        normalizedFormula,
        checks,
        issues,
      );
    }
    return buildResult(
      hasErrors(issues) ? 'invalid' : 'verified',
      formula,
      format,
      backend,
      normalizedFormula,
      checks,
      issues,
    );
  }

  verifyBatch(
    formulas: Array<string>,
    options: LogicVerificationOptions = {},
  ): Array<LogicVerificationResult> {
    return formulas.map((formula) => this.verify(formula, options));
  }
}

export class BrowserNativeReasoningLogicVerification {
  readonly metadata = REASONING_LOGIC_VERIFICATION_METADATA;
  readonly backendsMetadata = LOGIC_VERIFIER_BACKENDS_MIXIN_METADATA;
  private readonly verifier: BrowserNativeLogicVerification;

  constructor(verifier: BrowserNativeLogicVerification = new BrowserNativeLogicVerification()) {
    this.verifier = verifier;
  }

  getBackends(): Array<LogicVerifierBackendDescriptor> {
    return this.verifier.getBackends();
  }

  selectBackend(
    format: LogicVerificationFormat,
    backend?: LogicVerifierBackendName,
  ): LogicVerifierBackendDescriptor {
    return this.verifier.selectBackend(format, backend);
  }

  verifyTheorem(
    theorem: string,
    assumptions: Array<string> = [],
    options: LogicVerificationOptions = {},
  ): LogicVerificationResult {
    const formula = buildReasoningLogicTheoremFormula(theorem, assumptions);
    const result = this.verifier.verify(formula, options);
    return {
      ...result,
      checks: [...result.checks, 'reasoning_theorem_formula'],
    };
  }

  verifyBatch(
    formulas: Array<string>,
    options: LogicVerificationOptions = {},
  ): ReasoningLogicVerificationSummary {
    const results = this.verifier.verifyBatch(formulas, options).map((result) => ({
      ...result,
      checks: [...result.checks, 'reasoning_batch_formula'],
    }));
    let verified = 0;
    let invalid = 0;
    let unsupported = 0;
    results.forEach((result) => {
      if (result.status === 'verified') verified += 1;
      else if (result.status === 'invalid') invalid += 1;
      else unsupported += 1;
    });
    return {
      total: results.length,
      verified,
      invalid,
      unsupported,
      success: results.length > 0 && invalid === 0 && unsupported === 0,
      failedClosed: invalid > 0 || unsupported > 0,
      results,
      metadata: REASONING_LOGIC_VERIFICATION_METADATA,
    };
  }
}

export const LogicVerification = BrowserNativeLogicVerification;
export const LogicVerifier = BrowserNativeLogicVerification;
export const ReasoningLogicVerification = BrowserNativeReasoningLogicVerification;
export const createBrowserNativeLogicVerification = (): BrowserNativeLogicVerification =>
  new BrowserNativeLogicVerification();
export const createBrowserNativeReasoningLogicVerification =
  (): BrowserNativeReasoningLogicVerification => new BrowserNativeReasoningLogicVerification();
export const create_logic_verification = createBrowserNativeLogicVerification;
export const create_reasoning_logic_verification = createBrowserNativeReasoningLogicVerification;
export const verifyLogicFormula = (
  formula: string,
  options: LogicVerificationOptions = {},
): LogicVerificationResult => createBrowserNativeLogicVerification().verify(formula, options);
export const verify_logic_formula = verifyLogicFormula;
export const verifyReasoningTheorem = (
  theorem: string,
  assumptions: Array<string> = [],
  options: LogicVerificationOptions = {},
): LogicVerificationResult =>
  createBrowserNativeReasoningLogicVerification().verifyTheorem(theorem, assumptions, options);
export const verify_reasoning_theorem = verifyReasoningTheorem;
export const getLogicVerifierBackends = (): Array<LogicVerifierBackendDescriptor> =>
  LOGIC_VERIFIER_BACKENDS.map((backend) => ({ ...backend, formats: [...backend.formats] }));
export const get_logic_verifier_backends = getLogicVerifierBackends;
export const selectLogicVerifierBackend = (
  format: LogicVerificationFormat,
  backend: LogicVerifierBackendName = 'local',
): LogicVerifierBackendDescriptor => {
  const selected = LOGIC_VERIFIER_BACKENDS.find((entry) => entry.name === backend);
  if (!selected) return LOGIC_VERIFIER_BACKENDS[0];
  if (backend === 'local' && format !== 'auto') {
    const formatBackend = LOGIC_VERIFIER_BACKENDS.find((entry) => entry.name === format);
    return formatBackend && formatBackend.available ? formatBackend : selected;
  }
  return selected;
};
export const select_logic_verifier_backend = selectLogicVerifierBackend;

function buildResult(
  status: LogicVerificationStatus,
  formula: string,
  format: LogicVerificationFormat,
  backend: LogicVerifierBackendDescriptor,
  normalizedFormula: string,
  checks: Array<string>,
  issues: Array<LogicValidationIssue>,
): LogicVerificationResult {
  return {
    status,
    success: status === 'verified',
    formula,
    format,
    backend,
    normalizedFormula,
    checks,
    issues,
    metadata: LOGIC_VERIFICATION_METADATA,
  };
}

function validateBalancedDelimiters(formula: string): Array<LogicValidationIssue> {
  const stack: Array<string> = [];
  const pairs: Record<string, string> = { ')': '(', ']': '[', '}': '{' };
  for (const char of formula) {
    if (char === '(' || char === '[' || char === '{') stack.push(char);
    else if ((char === ')' || char === ']' || char === '}') && stack.pop() !== pairs[char]) {
      return [{ severity: 'error', message: `Unmatched closing delimiter ${char}.` }];
    }
  }
  return stack.length > 0 ? [{ severity: 'error', message: 'Unbalanced delimiters.' }] : [];
}

function validateByFormat(
  formula: string,
  format: LogicVerificationFormat,
): Array<LogicValidationIssue> {
  if (format === 'fol') return validateFolSyntax(formula).issues;
  if (format !== 'tdfol' && format !== 'cec') return [];
  try {
    format === 'tdfol' ? parseTdfolFormula(formula) : parseCecExpression(formula);
    return [];
  } catch (error) {
    return [{ severity: 'error', message: errorMessage(error) }];
  }
}

function detectFormat(formula: string): LogicVerificationFormat {
  if (/\b(?:forall|exists|and|or|implies|iff|not)\b/.test(formula)) return 'cec';
  return /[∀∃]|[□◇]|[OXPF]\s*\(/.test(formula) ? 'tdfol' : 'fol';
}

function hasErrors(issues: Array<LogicValidationIssue>): boolean {
  return issues.some((issue) => issue.severity === 'error');
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : 'Formula verification failed.';
}

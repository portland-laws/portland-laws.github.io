import { parseCecExpression } from '../cec/parser';
import { validateFolSyntax } from '../fol/parser';
import { parseTdfolFormula } from '../tdfol/parser';
import type { LogicValidationIssue } from '../types';
import { validateFormulaString } from '../validation';

export type LogicVerificationFormat = 'auto' | 'fol' | 'tdfol' | 'cec' | 'dcec';
export type LogicVerificationStatus = 'verified' | 'invalid' | 'unsupported';

export interface LogicVerificationOptions {
  format?: LogicVerificationFormat;
  requirePredicate?: boolean;
}
export interface LogicVerificationResult {
  status: LogicVerificationStatus;
  success: boolean;
  formula: string;
  format: LogicVerificationFormat;
  normalizedFormula: string;
  checks: Array<string>;
  issues: Array<LogicValidationIssue>;
  metadata: typeof LOGIC_VERIFICATION_METADATA;
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
    'fail_closed_unsupported_runtime',
  ] as Array<string>,
} as const;
const RUNTIME_BRIDGE_PATTERN =
  /\b(?:python|subprocess|rpc|server|http:\/\/|https:\/\/|fetch\(|XMLHttpRequest|child_process|fs\.)\b/i;

export class BrowserNativeLogicVerification {
  readonly metadata = LOGIC_VERIFICATION_METADATA;

  verify(formula: string, options: LogicVerificationOptions = {}): LogicVerificationResult {
    const format = options.format ?? 'auto';
    const normalizedFormula = typeof formula === 'string' ? formula.trim() : '';
    const checks = ['input_string', 'no_runtime_bridge_markers', 'balanced_delimiters'];
    const issues: Array<LogicValidationIssue> = [];

    try {
      validateFormulaString(formula, { fieldName: 'formula' });
    } catch (error) {
      issues.push({ severity: 'error', field: 'formula', message: errorMessage(error) });
      return buildResult('invalid', formula, format, normalizedFormula, checks, issues);
    }

    if (RUNTIME_BRIDGE_PATTERN.test(normalizedFormula)) {
      issues.push({
        severity: 'error',
        field: 'formula',
        message: 'Formula contains runtime bridge markers that are not browser-native.',
      });
    }
    issues.push(...validateBalancedDelimiters(normalizedFormula));
    if (options.requirePredicate !== false && !/[A-Za-z][A-Za-z0-9_]*\s*\(/.test(normalizedFormula))
      issues.push({
        severity: 'error',
        field: 'formula',
        message: 'Formula must contain at least one predicate application.',
      });

    const detectedFormat = format === 'auto' ? detectFormat(normalizedFormula) : format;
    checks.push(`${detectedFormat}_syntax`);
    issues.push(...validateByFormat(normalizedFormula, detectedFormat));
    if (detectedFormat === 'dcec') {
      issues.push({
        severity: 'error',
        field: 'format',
        message: 'DCEC verification requires a dedicated local adapter and fails closed here.',
      });
      return buildResult('unsupported', formula, format, normalizedFormula, checks, issues);
    }
    return buildResult(
      hasErrors(issues) ? 'invalid' : 'verified',
      formula,
      format,
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

export const LogicVerification = BrowserNativeLogicVerification;
export const LogicVerifier = BrowserNativeLogicVerification;
export const createBrowserNativeLogicVerification = (): BrowserNativeLogicVerification =>
  new BrowserNativeLogicVerification();
export const create_logic_verification = createBrowserNativeLogicVerification;
export const verifyLogicFormula = (
  formula: string,
  options: LogicVerificationOptions = {},
): LogicVerificationResult => createBrowserNativeLogicVerification().verify(formula, options);
export const verify_logic_formula = verifyLogicFormula;

function buildResult(
  status: LogicVerificationStatus,
  formula: string,
  format: LogicVerificationFormat,
  normalizedFormula: string,
  checks: Array<string>,
  issues: Array<LogicValidationIssue>,
): LogicVerificationResult {
  return {
    status,
    success: status === 'verified',
    formula,
    format,
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

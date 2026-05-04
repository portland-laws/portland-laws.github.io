import type { LogicValidationIssue } from '../types';
import type { LogicVerificationResult } from './logicVerification';

export const LOGIC_VERIFICATION_UTILS_METADATA = {
  sourcePythonModule: 'logic/integration/logic_verification_utils.py',
  browserNative: true,
  serverCallsAllowed: false,
  pythonRuntimeAllowed: false,
  runtimeDependencies: [] as Array<string>,
  parity: [
    'formula_normalization',
    'runtime_bridge_marker_detection',
    'batch_result_summarization',
  ] as Array<string>,
} as const;

const RUNTIME_BRIDGE_MARKERS: Array<[string, RegExp]> = [
  ['python', /\bpython\b/i],
  ['subprocess', /\bsubprocess\b/i],
  ['rpc', /\brpc\b/i],
  ['server', /\bserver\b/i],
  ['http', /\bhttps?:\/\//i],
  ['fetch', /\bfetch\s*\(/i],
  ['XMLHttpRequest', /\bXMLHttpRequest\b/],
  ['child_process', /\bchild_process\b/],
  ['filesystem', /\bfs\./],
];

const TOKEN_REPLACEMENTS: Array<[RegExp, string]> = [
  [/∀/g, 'forall '],
  [/∃/g, 'exists '],
  [/¬/g, 'not '],
  [/∧/g, ' and '],
  [/∨/g, ' or '],
  [/→/g, ' implies '],
  [/↔/g, ' iff '],
];

export function normalizeLogicVerificationFormula(formula: unknown): string {
  if (typeof formula !== 'string') return '';
  let normalized = formula.trim();
  for (const [pattern, replacement] of TOKEN_REPLACEMENTS) {
    normalized = normalized.replace(pattern, replacement);
  }
  return normalized.replace(/\s+/g, ' ');
}

export function detectLogicVerificationRuntimeBridge(formula: string) {
  const markers = RUNTIME_BRIDGE_MARKERS.filter(([, pattern]) => pattern.test(formula)).map(
    ([marker]) => marker,
  );
  return { safe: markers.length === 0, markers, metadata: LOGIC_VERIFICATION_UTILS_METADATA };
}

export function makeLogicVerificationIssue(
  message: string,
  severity: 'error' | 'warning' = 'error',
  field?: string,
): LogicValidationIssue {
  return field ? { severity, field, message } : { severity, message };
}

export function summarizeLogicVerificationResults(results: Array<LogicVerificationResult>) {
  let verified = 0;
  let invalid = 0;
  let unsupported = 0;
  const formats = new Set(results.map((result) => result.format));
  const issues = results.flatMap((result, resultIndex) =>
    result.issues.map((issue) => ({
      resultIndex,
      formula: result.formula,
      format: result.format,
      severity: issue.severity,
      message: issue.message,
      field: issue.field,
    })),
  );

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
    successRate: results.length === 0 ? 0 : verified / results.length,
    failedClosed: invalid > 0 || unsupported > 0,
    formats: Array.from(formats),
    issues,
    metadata: LOGIC_VERIFICATION_UTILS_METADATA,
  };
}

export const logic_verification_utils_metadata = LOGIC_VERIFICATION_UTILS_METADATA;
export const normalize_logic_verification_formula = normalizeLogicVerificationFormula;
export const detect_logic_verification_runtime_bridge = detectLogicVerificationRuntimeBridge;
export const make_logic_verification_issue = makeLogicVerificationIssue;
export const summarize_logic_verification_results = summarizeLogicVerificationResults;

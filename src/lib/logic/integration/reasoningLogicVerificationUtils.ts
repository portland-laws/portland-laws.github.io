import type { LogicValidationIssue } from '../types';
import type { LogicVerificationResult } from './logicVerification';
import {
  detectLogicVerificationRuntimeBridge,
  makeLogicVerificationIssue,
  normalizeLogicVerificationFormula,
} from './logicVerificationUtils';

export const REASONING_LOGIC_VERIFICATION_UTILS_METADATA = {
  sourcePythonModule: 'logic/integration/reasoning/logic_verification_utils.py',
  browserNative: true,
  serverCallsAllowed: false,
  pythonRuntimeAllowed: false,
  runtimeDependencies: [] as Array<string>,
  parity: [
    'assumption_normalization',
    'theorem_formula_construction',
    'runtime_bridge_input_screening',
    'reasoning_result_summarization',
  ] as Array<string>,
} as const;

export function normalizeReasoningLogicAssumptions(
  assumptions: Array<unknown> = [],
): Array<string> {
  const normalized: Array<string> = [];
  const seen = new Set<string>();
  for (const assumption of assumptions) {
    const formula = normalizeLogicVerificationFormula(assumption);
    if (formula.length === 0 || seen.has(formula)) continue;
    normalized.push(formula);
    seen.add(formula);
  }
  return normalized;
}

export function buildReasoningLogicTheoremFormula(
  theorem: unknown,
  assumptions: Array<unknown> = [],
): string {
  const theoremFormula = normalizeLogicVerificationFormula(theorem);
  const normalizedAssumptions = normalizeReasoningLogicAssumptions(assumptions);
  if (normalizedAssumptions.length === 0) return theoremFormula;
  return `(forall x (implies (and ${normalizedAssumptions.join(' ')}) ${theoremFormula}))`;
}

export function validateReasoningLogicVerificationInputs(
  theorem: unknown,
  assumptions: Array<unknown> = [],
) {
  const issues: Array<LogicValidationIssue> = [];
  const theoremFormula = normalizeLogicVerificationFormula(theorem);
  const normalizedAssumptions = normalizeReasoningLogicAssumptions(assumptions);

  if (typeof theorem !== 'string' || theoremFormula.length === 0)
    issues.push(
      makeLogicVerificationIssue('Theorem must be a non-empty formula.', 'error', 'theorem'),
    );
  assumptions.forEach((assumption, index) => {
    if (typeof assumption !== 'string')
      issues.push(
        makeLogicVerificationIssue(
          `Assumption ${index} must be a formula string.`,
          'error',
          `assumptions.${index}`,
        ),
      );
  });

  const theoremBridge = detectLogicVerificationRuntimeBridge(theoremFormula);
  if (!theoremBridge.safe)
    issues.push(
      makeLogicVerificationIssue(
        `Theorem contains runtime bridge markers: ${theoremBridge.markers.join(', ')}.`,
        'error',
        'theorem',
      ),
    );
  normalizedAssumptions.forEach((assumption, index) => {
    const bridge = detectLogicVerificationRuntimeBridge(assumption);
    if (!bridge.safe)
      issues.push(
        makeLogicVerificationIssue(
          `Assumption ${index} contains runtime bridge markers: ${bridge.markers.join(', ')}.`,
          'error',
          `assumptions.${index}`,
        ),
      );
  });

  return {
    valid: !issues.some((issue) => issue.severity === 'error'),
    theorem: theoremFormula,
    assumptions: normalizedAssumptions,
    issues,
    metadata: REASONING_LOGIC_VERIFICATION_UTILS_METADATA,
  };
}

export function summarizeReasoningLogicVerificationResults(
  results: Array<LogicVerificationResult>,
) {
  const counts = { verified: 0, invalid: 0, unsupported: 0 };
  const issues = results.flatMap((result, resultIndex) =>
    result.issues.map((issue) => ({
      resultIndex,
      formula: result.formula,
      severity: issue.severity,
      message: issue.message,
      field: issue.field,
    })),
  );
  results.forEach((result) => {
    counts[result.status] += 1;
  });

  return {
    total: results.length,
    ...counts,
    success: results.length > 0 && counts.invalid === 0 && counts.unsupported === 0,
    failedClosed: counts.invalid > 0 || counts.unsupported > 0,
    issues,
    metadata: REASONING_LOGIC_VERIFICATION_UTILS_METADATA,
  };
}

export const reasoning_logic_verification_utils_metadata =
  REASONING_LOGIC_VERIFICATION_UTILS_METADATA;
export const normalize_reasoning_logic_assumptions = normalizeReasoningLogicAssumptions;
export const build_reasoning_logic_theorem_formula = buildReasoningLogicTheoremFormula;
export const validate_reasoning_logic_verification_inputs =
  validateReasoningLogicVerificationInputs;
export const summarize_reasoning_logic_verification_results =
  summarizeReasoningLogicVerificationResults;

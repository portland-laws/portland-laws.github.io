import type { LogicValidationIssue, LogicValidationResult } from './types';
import { LogicValidationError } from './errors';

export const MAX_FORMULA_LENGTH = 100_000;
export const MAX_AXIOM_COUNT = 500;
export const MAX_AXIOM_LENGTH = 50_000;
export const MIN_TIMEOUT_MS = 10;
export const MAX_TIMEOUT_MS = 60_000;

export const SUPPORTED_LOGICS = new Set(['tdfol', 'cec', 'fol', 'deontic', 'modal', 'temporal']);
export const SUPPORTED_FORMATS = new Set(['auto', 'tdfol', 'dcec', 'fol', 'tptp', 'nl']);
export const DEFAULT_LOGIC_SYSTEM = 'tdfol';
export const DEFAULT_FORMAT = 'auto';
export const DEFAULT_TIMEOUT_MS = 30_000;

const INJECTION_PATTERN = /(?:__import__|eval\s*\(|exec\s*\(|subprocess|os\.system|open\s*\()/i;

export function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}

export function createValidationResult(issues: LogicValidationIssue[] = []): LogicValidationResult {
  return {
    valid: !issues.some((issue) => issue.severity === 'error'),
    issues,
  };
}

export function requireString(
  row: Record<string, unknown>,
  field: string,
  issues: LogicValidationIssue[],
): string {
  const value = row[field];
  if (typeof value === 'string') {
    return value;
  }
  issues.push({ severity: 'error', field, message: `${field} must be a string` });
  return '';
}

export function requireBoolean(
  row: Record<string, unknown>,
  field: string,
  issues: LogicValidationIssue[],
): boolean {
  const value = row[field];
  if (typeof value === 'boolean') {
    return value;
  }
  issues.push({ severity: 'error', field, message: `${field} must be a boolean` });
  return false;
}

export function normalizeEnum<T extends string>(
  value: string,
  allowedValues: readonly T[],
  fallback: T,
  field: string,
  issues: LogicValidationIssue[],
): T {
  if ((allowedValues as readonly string[]).includes(value)) {
    return value as T;
  }
  issues.push({
    severity: 'warning',
    field,
    message: `${field} had unsupported value "${value}", normalized to ${fallback}`,
  });
  return fallback;
}

export interface FormulaStringValidationOptions {
  fieldName?: string;
  maxLength?: number;
  allowEmpty?: boolean;
}

export function validateFormulaString(
  formula: unknown,
  options: FormulaStringValidationOptions = {},
): asserts formula is string {
  const fieldName = options.fieldName ?? 'formula';
  const maxLength = options.maxLength ?? MAX_FORMULA_LENGTH;
  const allowEmpty = options.allowEmpty ?? false;

  if (typeof formula !== 'string') {
    throw new LogicValidationError(`'${fieldName}' must be a string, got ${typeofName(formula)}`, {
      field: fieldName,
      type: typeofName(formula),
    });
  }
  if (!allowEmpty && formula.trim().length === 0) {
    throw new LogicValidationError(`'${fieldName}' must not be empty.`, { field: fieldName });
  }
  if (formula.length > maxLength) {
    throw new LogicValidationError(
      `'${fieldName}' exceeds maximum length of ${maxLength} characters (got ${formula.length}).`,
      { field: fieldName, length: formula.length, max: maxLength },
    );
  }
  if (INJECTION_PATTERN.test(formula)) {
    throw new LogicValidationError(`'${fieldName}' contains potentially unsafe content.`, {
      field: fieldName,
    });
  }
}

export interface AxiomListValidationOptions {
  maxCount?: number;
  maxAxiomLength?: number;
}

export function validateAxiomList(
  axioms: unknown,
  options: AxiomListValidationOptions = {},
): asserts axioms is string[] {
  const maxCount = options.maxCount ?? MAX_AXIOM_COUNT;
  const maxAxiomLength = options.maxAxiomLength ?? MAX_AXIOM_LENGTH;

  if (!Array.isArray(axioms)) {
    throw new LogicValidationError(`'axioms' must be a list, got ${typeofName(axioms)}`, {
      type: typeofName(axioms),
    });
  }
  if (axioms.length > maxCount) {
    throw new LogicValidationError(
      `'axioms' list exceeds maximum of ${maxCount} items (got ${axioms.length}).`,
      {
        count: axioms.length,
        max: maxCount,
      },
    );
  }
  axioms.forEach((axiom, index) => {
    try {
      validateFormulaString(axiom, {
        fieldName: `axioms[${index}]`,
        maxLength: maxAxiomLength,
      });
    } catch (error) {
      if (error instanceof LogicValidationError) {
        throw new LogicValidationError(error.toString(), {
          ...error.context,
          axiom_index: index,
        });
      }
      throw error;
    }
  });
}

export function validateLogicSystem(
  logic: unknown,
  supported = SUPPORTED_LOGICS,
): asserts logic is string {
  if (typeof logic !== 'string') {
    throw new LogicValidationError(`'logic' must be a string, got ${typeofName(logic)}`, {
      type: typeofName(logic),
    });
  }
  if (!supported.has(logic.toLowerCase())) {
    throw new LogicValidationError(
      `Unsupported logic system: '${logic}'. Supported: ${formatSupported(supported)}`,
      {
        logic,
        supported: [...supported].sort(),
      },
    );
  }
}

export function validateTimeoutMs(
  timeoutMs: unknown,
  minMs = MIN_TIMEOUT_MS,
  maxMs = MAX_TIMEOUT_MS,
): asserts timeoutMs is number {
  if (!Number.isInteger(timeoutMs)) {
    throw new LogicValidationError(
      `'timeout_ms' must be an integer, got ${typeofName(timeoutMs)}`,
      {
        type: typeofName(timeoutMs),
      },
    );
  }
  const value = timeoutMs as number;
  if (value < minMs) {
    throw new LogicValidationError(`'timeout_ms' must be >= ${minMs}ms (got ${value}ms).`, {
      value,
      min: minMs,
    });
  }
  if (value > maxMs) {
    throw new LogicValidationError(`'timeout_ms' must be <= ${maxMs}ms (got ${value}ms).`, {
      value,
      max: maxMs,
    });
  }
}

export function validateFormat(
  format: unknown,
  supported = SUPPORTED_FORMATS,
): asserts format is string {
  if (typeof format !== 'string' || !supported.has(format)) {
    throw new LogicValidationError(
      `Unsupported format: '${String(format)}'. Supported: ${formatSupported(supported)}`,
      {
        format,
        supported: [...supported].sort(),
      },
    );
  }
}

export interface LogicProblemPayloadValidationOptions {
  formulaField?: string;
  maxFormulaLength?: number;
  maxAxiomCount?: number;
  maxAxiomLength?: number;
  minTimeoutMs?: number;
  maxTimeoutMs?: number;
  defaultLogic?: string;
  defaultFormat?: string;
  defaultTimeoutMs?: number;
  supportedLogics?: Set<string>;
  supportedFormats?: Set<string>;
}

export interface ValidatedLogicProblemPayload {
  formula: string;
  axioms: string[];
  logic: string;
  format: string;
  timeoutMs: number;
}

export type LogicE2eCapability =
  | 'browser_native_typescript'
  | 'wasm_compatible'
  | 'deterministic_nlp'
  | 'deterministic_ml'
  | 'no_python_runtime'
  | 'no_server_calls';

export interface LogicE2eValidationCase {
  name: string;
  payload: unknown;
  requiredCapabilities?: readonly LogicE2eCapability[];
}
export interface LogicE2eCaseResult {
  name: string;
  valid: boolean;
  payload?: ValidatedLogicProblemPayload;
  issues: LogicValidationIssue[];
}
export interface LogicE2eValidationResult {
  valid: boolean;
  runtime: {
    browserNative: true;
    pythonRuntime: false;
    serverCalls: false;
    filesystemAccess: false;
    subprocessAccess: false;
  };
  capabilities: readonly LogicE2eCapability[];
  cases: LogicE2eCaseResult[];
  issues: LogicValidationIssue[];
}

const BROWSER_NATIVE_E2E_CAPABILITIES: readonly LogicE2eCapability[] = [
  'browser_native_typescript',
  'wasm_compatible',
  'deterministic_nlp',
  'deterministic_ml',
  'no_python_runtime',
  'no_server_calls',
];
const FORBIDDEN_E2E_KEYS = new Set([
  'endpoint',
  'filesystem',
  'fs',
  'nodefs',
  'python',
  'pythonruntime',
  'rpc',
  'server',
  'serverurl',
  'subprocess',
]);

const FORBIDDEN_E2E_VALUE_PATTERN = /\b(?:file:|https?:\/\/|python|spacy|subprocess|rpc|server)\b/i;

export function validateLogicProblemPayload(
  payload: unknown,
  options: LogicProblemPayloadValidationOptions = {},
): ValidatedLogicProblemPayload {
  if (!isRecord(payload)) {
    throw new LogicValidationError(`'payload' must be a mapping, got ${typeofName(payload)}`, {
      type: typeofName(payload),
    });
  }

  const formulaField = options.formulaField ?? 'formula';
  const formula = payload[formulaField];
  validateFormulaString(formula, {
    fieldName: formulaField,
    maxLength: options.maxFormulaLength,
  });

  const axioms = payload.axioms ?? [];
  validateAxiomList(axioms, {
    maxCount: options.maxAxiomCount,
    maxAxiomLength: options.maxAxiomLength,
  });

  const logic = payload.logic ?? options.defaultLogic ?? DEFAULT_LOGIC_SYSTEM;
  validateLogicSystem(logic, options.supportedLogics ?? SUPPORTED_LOGICS);

  const format = payload.format ?? options.defaultFormat ?? DEFAULT_FORMAT;
  validateFormat(format, options.supportedFormats ?? SUPPORTED_FORMATS);

  const timeoutMs =
    payload.timeout_ms ?? payload.timeoutMs ?? options.defaultTimeoutMs ?? DEFAULT_TIMEOUT_MS;
  validateTimeoutMs(
    timeoutMs,
    options.minTimeoutMs ?? MIN_TIMEOUT_MS,
    options.maxTimeoutMs ?? MAX_TIMEOUT_MS,
  );

  return {
    formula,
    axioms: [...axioms],
    logic: logic.toLowerCase(),
    format,
    timeoutMs,
  };
}

export function validateLogicE2eRuntime(
  cases: readonly LogicE2eValidationCase[],
  options: LogicProblemPayloadValidationOptions = {},
): LogicE2eValidationResult {
  const suiteIssues: LogicValidationIssue[] = [];
  if (!Array.isArray(cases) || cases.length === 0) {
    suiteIssues.push({
      severity: 'error',
      field: 'cases',
      message: 'e2e validation requires at least one browser-native case',
    });
  }

  const caseResults = cases.map((testCase, index) => {
    const name = testCase.name.trim() || `case_${index}`;
    const issues: LogicValidationIssue[] = [];
    let validated: ValidatedLogicProblemPayload | undefined;

    if (!isRecord(testCase.payload)) {
      issues.push({
        severity: 'error',
        field: `${name}.payload`,
        message: 'payload must be a browser-serializable mapping',
      });
    } else {
      issues.push(...findForbiddenRuntimeHooks(testCase.payload, `${name}.payload`));
      try {
        validated = validateLogicProblemPayload(testCase.payload, options);
      } catch (error) {
        issues.push({
          severity: 'error',
          field: `${name}.payload`,
          message: error instanceof Error ? error.message : String(error),
        });
      }
    }

    for (const capability of testCase.requiredCapabilities ?? []) {
      if (!BROWSER_NATIVE_E2E_CAPABILITIES.includes(capability)) {
        issues.push({
          severity: 'error',
          field: `${name}.requiredCapabilities`,
          message: `unsupported browser-native e2e capability: ${capability}`,
        });
      }
    }

    return {
      name,
      valid: !issues.some((issue) => issue.severity === 'error'),
      payload: validated,
      issues,
    };
  });

  const issues = [...suiteIssues, ...caseResults.flatMap((result) => result.issues)];
  return {
    valid: !issues.some((issue) => issue.severity === 'error'),
    runtime: {
      browserNative: true,
      pythonRuntime: false,
      serverCalls: false,
      filesystemAccess: false,
      subprocessAccess: false,
    },
    capabilities: BROWSER_NATIVE_E2E_CAPABILITIES,
    cases: caseResults,
    issues,
  };
}

export const validate_formula_string = validateFormulaString;
export const validate_axiom_list = validateAxiomList;
export const validate_logic_system = validateLogicSystem;
export const validate_timeout_ms = validateTimeoutMs;
export const validate_format = validateFormat;
export const validate_logic_problem_payload = validateLogicProblemPayload;
export const validate_logic_e2e_runtime = validateLogicE2eRuntime;

function findForbiddenRuntimeHooks(
  value: unknown,
  path: string,
  seen: WeakSet<object> = new WeakSet<object>(),
): LogicValidationIssue[] {
  if (!isRecord(value)) {
    if (typeof value === 'string' && FORBIDDEN_E2E_VALUE_PATTERN.test(value)) {
      return [{ severity: 'error', field: path, message: 'runtime value is not browser-native' }];
    }
    return [];
  }
  if (seen.has(value)) return [];
  seen.add(value);

  const issues: LogicValidationIssue[] = [];
  for (const [key, nested] of Object.entries(value)) {
    const normalizedKey = key.replace(/[_-]/g, '').toLowerCase();
    const nestedPath = `${path}.${key}`;
    if (FORBIDDEN_E2E_KEYS.has(normalizedKey)) {
      issues.push({
        severity: 'error',
        field: nestedPath,
        message: 'runtime hook is not allowed in browser-native e2e validation',
      });
    }
    issues.push(...findForbiddenRuntimeHooks(nested, nestedPath, seen));
  }
  return issues;
}

function typeofName(value: unknown): string {
  if (Array.isArray(value)) return 'list';
  if (value === null) return 'NoneType';
  if (Number.isInteger(value)) return 'int';
  if (typeof value === 'number') return 'float';
  return typeof value;
}

function formatSupported(supported: Set<string>): string {
  return `[${[...supported]
    .sort()
    .map((value) => `'${value}'`)
    .join(', ')}]`;
}

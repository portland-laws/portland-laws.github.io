import type { LogicValidationIssue, LogicValidationResult } from './types';
import { LogicValidationError } from './errors';

export const MAX_FORMULA_LENGTH = 100_000;
export const MAX_AXIOM_COUNT = 500;
export const MAX_AXIOM_LENGTH = 50_000;
export const MIN_TIMEOUT_MS = 10;
export const MAX_TIMEOUT_MS = 60_000;

export const SUPPORTED_LOGICS = new Set(['tdfol', 'cec', 'fol', 'deontic', 'modal', 'temporal']);
export const SUPPORTED_FORMATS = new Set(['auto', 'tdfol', 'dcec', 'fol', 'tptp', 'nl']);

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
    throw new LogicValidationError(`'${fieldName}' contains potentially unsafe content.`, { field: fieldName });
  }
}

export interface AxiomListValidationOptions {
  maxCount?: number;
  maxAxiomLength?: number;
}

export function validateAxiomList(axioms: unknown, options: AxiomListValidationOptions = {}): asserts axioms is string[] {
  const maxCount = options.maxCount ?? MAX_AXIOM_COUNT;
  const maxAxiomLength = options.maxAxiomLength ?? MAX_AXIOM_LENGTH;

  if (!Array.isArray(axioms)) {
    throw new LogicValidationError(`'axioms' must be a list, got ${typeofName(axioms)}`, { type: typeofName(axioms) });
  }
  if (axioms.length > maxCount) {
    throw new LogicValidationError(`'axioms' list exceeds maximum of ${maxCount} items (got ${axioms.length}).`, {
      count: axioms.length,
      max: maxCount,
    });
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

export function validateLogicSystem(logic: unknown, supported = SUPPORTED_LOGICS): asserts logic is string {
  if (typeof logic !== 'string') {
    throw new LogicValidationError(`'logic' must be a string, got ${typeofName(logic)}`, { type: typeofName(logic) });
  }
  if (!supported.has(logic.toLowerCase())) {
    throw new LogicValidationError(`Unsupported logic system: '${logic}'. Supported: ${formatSupported(supported)}`, {
      logic,
      supported: [...supported].sort(),
    });
  }
}

export function validateTimeoutMs(timeoutMs: unknown, minMs = MIN_TIMEOUT_MS, maxMs = MAX_TIMEOUT_MS): asserts timeoutMs is number {
  if (!Number.isInteger(timeoutMs)) {
    throw new LogicValidationError(`'timeout_ms' must be an integer, got ${typeofName(timeoutMs)}`, {
      type: typeofName(timeoutMs),
    });
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

export function validateFormat(format: unknown, supported = SUPPORTED_FORMATS): asserts format is string {
  if (typeof format !== 'string' || !supported.has(format)) {
    throw new LogicValidationError(`Unsupported format: '${String(format)}'. Supported: ${formatSupported(supported)}`, {
      format,
      supported: [...supported].sort(),
    });
  }
}

export const validate_formula_string = validateFormulaString;
export const validate_axiom_list = validateAxiomList;
export const validate_logic_system = validateLogicSystem;
export const validate_timeout_ms = validateTimeoutMs;
export const validate_format = validateFormat;

function typeofName(value: unknown): string {
  if (Array.isArray(value)) return 'list';
  if (value === null) return 'NoneType';
  if (Number.isInteger(value)) return 'int';
  if (typeof value === 'number') return 'float';
  return typeof value;
}

function formatSupported(supported: Set<string>): string {
  return `[${[...supported].sort().map((value) => `'${value}'`).join(', ')}]`;
}

import type { LogicValidationIssue, LogicValidationResult } from './types';

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


import {
  createValidationResult,
  isRecord,
  normalizeEnum,
  requireBoolean,
  requireString,
} from './validation';
import type { LogicValidationIssue } from './types';

describe('logic validation helpers', () => {
  it('detects records without accepting arrays or null', () => {
    expect(isRecord({ ok: true })).toBe(true);
    expect(isRecord([])).toBe(false);
    expect(isRecord(null)).toBe(false);
  });

  it('requires primitive field types and records errors', () => {
    const issues: LogicValidationIssue[] = [];
    const row = { name: 'section', verified: true, bad: 1 };

    expect(requireString(row, 'name', issues)).toBe('section');
    expect(requireBoolean(row, 'verified', issues)).toBe(true);
    expect(requireString(row, 'bad', issues)).toBe('');

    expect(createValidationResult(issues)).toEqual({
      valid: false,
      issues: [{ severity: 'error', field: 'bad', message: 'bad must be a string' }],
    });
  });

  it('normalizes enum values with warnings', () => {
    const issues: LogicValidationIssue[] = [];

    expect(normalizeEnum('O', ['O', 'P', 'F'] as const, 'F', 'norm_operator', issues)).toBe('O');
    expect(normalizeEnum('M', ['O', 'P', 'F'] as const, 'F', 'norm_operator', issues)).toBe('F');
    expect(issues).toEqual([
      {
        severity: 'warning',
        field: 'norm_operator',
        message: 'norm_operator had unsupported value "M", normalized to F',
      },
    ]);
  });
});


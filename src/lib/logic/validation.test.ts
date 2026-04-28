import {
  MAX_TIMEOUT_MS,
  createValidationResult,
  isRecord,
  normalizeEnum,
  requireBoolean,
  requireString,
  validateAxiomList,
  validateFormat,
  validateFormulaString,
  validateLogicSystem,
  validateTimeoutMs,
} from './validation';
import type { LogicValidationIssue } from './types';
import { LogicValidationError } from './errors';

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

  it('ports Python formula string validation semantics', () => {
    expect(() => validateFormulaString('P ∧ Q → R')).not.toThrow();
    expect(() => validateFormulaString('', { fieldName: 'formula' })).toThrow(LogicValidationError);
    expect(() => validateFormulaString('', { allowEmpty: true })).not.toThrow();
    expect(() => validateFormulaString('eval(P)')).toThrow("'formula' contains potentially unsafe content.");
    expect(() => validateFormulaString('x'.repeat(4), { maxLength: 3 })).toThrow(
      "'formula' exceeds maximum length of 3 characters (got 4).",
    );
  });

  it('ports Python axiom list, logic, timeout, and format validators', () => {
    expect(() => validateAxiomList(['P -> Q', 'P'], { maxCount: 2 })).not.toThrow();
    expect(() => validateAxiomList(['P', 'Q'], { maxCount: 1 })).toThrow("'axioms' list exceeds maximum of 1 items");
    try {
      validateAxiomList(['P', ''], { maxAxiomLength: 5 });
      throw new Error('expected validation failure');
    } catch (error) {
      expect(error).toBeInstanceOf(LogicValidationError);
      expect((error as LogicValidationError).context).toMatchObject({ axiom_index: 1 });
    }

    expect(() => validateLogicSystem('TDFOL')).not.toThrow();
    expect(() => validateLogicSystem('invalid')).toThrow("Unsupported logic system: 'invalid'.");
    expect(() => validateTimeoutMs(10)).not.toThrow();
    expect(() => validateTimeoutMs(MAX_TIMEOUT_MS)).not.toThrow();
    expect(() => validateTimeoutMs(9)).toThrow("'timeout_ms' must be >= 10ms");
    expect(() => validateTimeoutMs(60_001)).toThrow("'timeout_ms' must be <= 60000ms");
    expect(() => validateFormat('tdfol')).not.toThrow();
    expect(() => validateFormat('xml')).toThrow("Unsupported format: 'xml'.");
  });
});

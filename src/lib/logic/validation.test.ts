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
  validateLogicE2eRuntime,
  validateLogicProblemPayload,
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
    expect(() => validateFormulaString('eval(P)')).toThrow(
      "'formula' contains potentially unsafe content.",
    );
    expect(() => validateFormulaString('x'.repeat(4), { maxLength: 3 })).toThrow(
      "'formula' exceeds maximum length of 3 characters (got 4).",
    );
  });

  it('ports Python axiom list, logic, timeout, and format validators', () => {
    expect(() => validateAxiomList(['P -> Q', 'P'], { maxCount: 2 })).not.toThrow();
    expect(() => validateAxiomList(['P', 'Q'], { maxCount: 1 })).toThrow(
      "'axioms' list exceeds maximum of 1 items",
    );
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

  it('ports Python-style complete logic problem payload validation', () => {
    expect(
      validateLogicProblemPayload({
        formula: 'P -> Q',
        axioms: ['P'],
        logic: 'TDFOL',
        format: 'tdfol',
        timeout_ms: 500,
      }),
    ).toEqual({
      formula: 'P -> Q',
      axioms: ['P'],
      logic: 'tdfol',
      format: 'tdfol',
      timeoutMs: 500,
    });

    expect(validateLogicProblemPayload({ formula: 'P' })).toEqual({
      formula: 'P',
      axioms: [],
      logic: 'tdfol',
      format: 'auto',
      timeoutMs: 30_000,
    });
    expect(
      validateLogicProblemPayload({ theorem: 'P', timeoutMs: 250 }, { formulaField: 'theorem' })
        .timeoutMs,
    ).toBe(250);
    expect(() => validateLogicProblemPayload('P')).toThrow(
      "'payload' must be a mapping, got string",
    );
    expect(() => validateLogicProblemPayload({ formula: 'P', axioms: 'Q' })).toThrow(
      "'axioms' must be a list",
    );
    expect(() => validateLogicProblemPayload({ formula: 'P', timeout_ms: 9 })).toThrow(
      "'timeout_ms' must be >= 10ms",
    );
  });

  it('ports e2e validation as a browser-native local runtime contract', () => {
    const result = validateLogicE2eRuntime([
      {
        name: 'deterministic fol case',
        payload: {
          formula: 'forall x. Human(x) -> Mortal(x)',
          axioms: ['Human(socrates)'],
          logic: 'fol',
          format: 'fol',
          timeout_ms: 100,
        },
        requiredCapabilities: [
          'browser_native_typescript',
          'deterministic_nlp',
          'deterministic_ml',
        ],
      },
      {
        name: 'default tdfol case',
        payload: { formula: 'P -> Q' },
        requiredCapabilities: ['no_python_runtime', 'no_server_calls'],
      },
    ]);

    expect(result.valid).toBe(true);
    expect(result.runtime).toEqual({
      browserNative: true,
      pythonRuntime: false,
      serverCalls: false,
      filesystemAccess: false,
      subprocessAccess: false,
    });
    expect(result.capabilities).toContain('wasm_compatible');
    expect(result.cases.map((testCase) => testCase.payload?.logic)).toEqual(['fol', 'tdfol']);
  });

  it('fails closed when e2e cases request Python, server, RPC, or filesystem hooks', () => {
    const result = validateLogicE2eRuntime([
      {
        name: 'blocked runtime bridge',
        payload: {
          formula: 'P',
          python_runtime: 'spacy',
          serverUrl: 'http://localhost:8000/prove',
          nested: { subprocess: 'python -m prover' },
        },
        requiredCapabilities: ['no_python_runtime'],
      },
    ]);

    expect(result.valid).toBe(false);
    expect(result.issues.map((issue) => issue.field)).toEqual([
      'blocked runtime bridge.payload.python_runtime',
      'blocked runtime bridge.payload.python_runtime',
      'blocked runtime bridge.payload.serverUrl',
      'blocked runtime bridge.payload.serverUrl',
      'blocked runtime bridge.payload.nested.subprocess',
      'blocked runtime bridge.payload.nested.subprocess',
    ]);
  });
});

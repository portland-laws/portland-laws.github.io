import { LogicParseError } from '../errors';
import type { DcecFormula } from './dcecCore';
import {
  checkDcecParens,
  cleanDcecExpression,
  removeDcecSemicolonComments,
  stripDcecComments,
} from './dcecCleaning';

export interface DcecWrapperCapabilities {
  readonly browserNative: true;
  readonly pythonRuntime: false;
  readonly serverRuntime: false;
  readonly filesystem: false;
  readonly subprocess: false;
  readonly rpc: false;
  readonly wasmRequired: false;
  readonly implementation: 'deterministic-typescript';
  readonly pythonModule: 'logic/CEC/dcec_wrapper.py';
}

export interface DcecWrapperOptions {
  readonly maxInputLength?: number;
  readonly requireBalancedParens?: boolean;
}

export interface DcecWrapperParseResult {
  readonly ok: boolean;
  readonly input: string;
  readonly normalizedInput: string;
  readonly cleanedDcec?: string;
  readonly formula?: DcecFormula;
  readonly errors: readonly string[];
  readonly metadata: {
    readonly sourcePythonModule: 'logic/CEC/dcec_wrapper.py';
    readonly runtime: 'browser-native-typescript';
    readonly implementation: 'deterministic-dcec-wrapper-validation';
  };
}

const DEFAULT_MAX_INPUT_LENGTH = 8192;

const RESULT_METADATA = {
  sourcePythonModule: 'logic/CEC/dcec_wrapper.py',
  runtime: 'browser-native-typescript',
  implementation: 'deterministic-dcec-wrapper-validation',
} as const;

const CAPABILITIES: DcecWrapperCapabilities = {
  browserNative: true,
  pythonRuntime: false,
  serverRuntime: false,
  filesystem: false,
  subprocess: false,
  rpc: false,
  wasmRequired: false,
  implementation: 'deterministic-typescript',
  pythonModule: 'logic/CEC/dcec_wrapper.py',
};

export class DcecWrapper {
  readonly maxInputLength: number;
  readonly requireBalancedParens: boolean;

  constructor(options: DcecWrapperOptions = {}) {
    this.maxInputLength = options.maxInputLength ?? DEFAULT_MAX_INPUT_LENGTH;
    this.requireBalancedParens = options.requireBalancedParens ?? true;
  }

  getCapabilities(): DcecWrapperCapabilities {
    return CAPABILITIES;
  }

  parse(text: string): DcecWrapperParseResult {
    const normalizedInput = this.normalizeInput(text);
    const inputError = this.validateInput(text, normalizedInput);
    if (inputError) return this.failure(text, normalizedInput, inputError);

    const uncommented = removeDcecSemicolonComments(stripDcecComments(normalizedInput)).trim();
    if (uncommented.length === 0) {
      return this.failure(text, normalizedInput, 'Input must contain a DCEC expression');
    }

    if (this.requireBalancedParens && !checkDcecParens(uncommented)) {
      return this.failure(text, normalizedInput, 'DCEC expression has unbalanced parentheses');
    }

    try {
      const cleanedDcec = cleanDcecExpression(uncommented);
      if (cleanedDcec.length === 0) {
        return this.failure(
          text,
          normalizedInput,
          'DCEC expression cleaned to an empty expression',
        );
      }

      return {
        ok: true,
        input: text,
        normalizedInput,
        cleanedDcec,
        errors: [],
        metadata: RESULT_METADATA,
      };
    } catch (error) {
      return this.failure(
        text,
        normalizedInput,
        error instanceof Error ? error.message : 'Unknown DCEC wrapper parse error',
      );
    }
  }

  parseToFormula(text: string): DcecFormula {
    const result = this.parse(text);
    throw new LogicParseError('DCEC formula construction is not available in this wrapper port', {
      input: text,
      cleanedDcec: result.cleanedDcec,
      errors: result.errors.join('; '),
      sourcePythonModule: RESULT_METADATA.sourcePythonModule,
      runtime: RESULT_METADATA.runtime,
    });
  }

  validateText(text: string): { readonly ok: boolean; readonly errors: readonly string[] } {
    const result = this.parse(text);
    return { ok: result.ok, errors: result.errors };
  }

  clean(text: string): string {
    const result = this.parse(text);
    if (!result.ok || result.cleanedDcec === undefined) {
      throw new LogicParseError('Unable to clean DCEC input', {
        input: text,
        errors: result.errors.join('; '),
      });
    }
    return result.cleanedDcec;
  }

  private normalizeInput(text: string): string {
    return typeof text === 'string' ? text.trim().replace(/\s+/g, ' ') : '';
  }

  private validateInput(text: string, normalizedInput: string): string | undefined {
    if (typeof text !== 'string') return 'Input must be a string';
    if (normalizedInput.length === 0) return 'Input must not be empty';
    if (normalizedInput.length > this.maxInputLength) {
      return `Input exceeds maximum length of ${this.maxInputLength} characters`;
    }
    return undefined;
  }

  private failure(
    text: string,
    normalizedInput: string,
    errors: string | readonly string[],
  ): DcecWrapperParseResult {
    return {
      ok: false,
      input: text,
      normalizedInput,
      errors: Array.isArray(errors) ? [...errors] : [errors],
      metadata: RESULT_METADATA,
    };
  }
}

export function createDcecWrapper(options?: DcecWrapperOptions): DcecWrapper {
  return new DcecWrapper(options);
}

export function parseDcec(text: string, options?: DcecWrapperOptions): DcecWrapperParseResult {
  return createDcecWrapper(options).parse(text);
}

export function cleanDcec(text: string, options?: DcecWrapperOptions): string {
  return createDcecWrapper(options).clean(text);
}

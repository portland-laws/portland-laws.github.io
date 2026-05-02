import { LogicParseError, LogicValidationError } from '../errors';
import type { DcecFormula } from './dcecCore';
import {
  DcecEnglishGrammar,
  DcecEnglishSemanticRecord,
  createDcecEnglishGrammar,
} from './dcecEnglishGrammar';
import { DcecNamespace } from './dcecNamespace';
import { validateDcecFormula } from './dcecIntegration';

export interface EngDcecWrapperCapabilities {
  readonly browserNative: true;
  readonly pythonRuntime: false;
  readonly serverRuntime: false;
  readonly filesystem: false;
  readonly subprocess: false;
  readonly rpc: false;
  readonly wasmRequired: false;
  readonly implementation: 'deterministic-typescript';
  readonly pythonModule: 'logic/CEC/eng_dcec_wrapper.py';
}

export interface EngDcecWrapperOptions {
  readonly namespace?: DcecNamespace;
  readonly maxInputLength?: number;
}

export interface EngDcecParseResult {
  readonly ok: boolean;
  readonly input: string;
  readonly normalizedInput: string;
  readonly dcec?: string;
  readonly english?: string;
  readonly formula?: DcecFormula;
  readonly semantic?: DcecEnglishSemanticRecord;
  readonly errors: readonly string[];
  readonly metadata: {
    readonly sourcePythonModule: 'logic/CEC/eng_dcec_wrapper.py';
    readonly runtime: 'browser-native-typescript';
    readonly implementation: 'deterministic-dcec-english-grammar';
  };
}

const DEFAULT_MAX_INPUT_LENGTH = 4096;
const RESULT_METADATA = {
  sourcePythonModule: 'logic/CEC/eng_dcec_wrapper.py',
  runtime: 'browser-native-typescript',
  implementation: 'deterministic-dcec-english-grammar',
} as const;

const CAPABILITIES: EngDcecWrapperCapabilities = {
  browserNative: true,
  pythonRuntime: false,
  serverRuntime: false,
  filesystem: false,
  subprocess: false,
  rpc: false,
  wasmRequired: false,
  implementation: 'deterministic-typescript',
  pythonModule: 'logic/CEC/eng_dcec_wrapper.py',
};

export class EngDcecWrapper {
  readonly grammar: DcecEnglishGrammar;
  readonly maxInputLength: number;

  constructor(options: EngDcecWrapperOptions = {}) {
    this.grammar = createDcecEnglishGrammar(options.namespace);
    this.maxInputLength = options.maxInputLength ?? DEFAULT_MAX_INPUT_LENGTH;
  }

  getCapabilities(): EngDcecWrapperCapabilities {
    return CAPABILITIES;
  }

  parse(text: string): EngDcecParseResult {
    const normalizedInput = this.normalizeInput(text);
    const inputError = this.validateInput(text, normalizedInput);
    if (inputError) return this.failure(text, normalizedInput, inputError);

    try {
      const formula = this.grammar.parseToDcec(normalizedInput);
      if (!formula) {
        return this.failure(
          text,
          normalizedInput,
          'Unable to parse English input into a DCEC formula',
        );
      }

      const validation = validateDcecFormula(formula);
      if (!validation.ok) return this.failure(text, normalizedInput, validation.errors);

      const semantic = this.grammar.formulaToSemantic(formula);
      return {
        ok: true,
        input: text,
        normalizedInput,
        formula,
        dcec: formula.toString(),
        english: this.grammar.linearizeBoolean(semantic),
        semantic,
        errors: [],
        metadata: RESULT_METADATA,
      };
    } catch (error) {
      return this.failure(
        text,
        normalizedInput,
        error instanceof Error ? error.message : 'Unknown DCEC parse error',
      );
    }
  }

  parseToFormula(text: string): DcecFormula {
    const result = this.parse(text);
    if (!result.ok || !result.formula) {
      throw new LogicParseError('Unable to parse English input into DCEC', {
        input: text,
        errors: result.errors.join('; '),
      });
    }
    return result.formula;
  }

  validateText(text: string): { readonly ok: boolean; readonly errors: readonly string[] } {
    const result = this.parse(text);
    return { ok: result.ok, errors: result.errors };
  }

  semanticToFormula(semantic: DcecEnglishSemanticRecord): DcecFormula {
    const formula = this.grammar.semanticToFormula(semantic);
    if (!formula) {
      throw new LogicValidationError('Unable to convert English semantic record to DCEC formula', {
        semantic,
      });
    }
    return formula;
  }

  formulaToSemantic(formula: DcecFormula): DcecEnglishSemanticRecord {
    return this.grammar.formulaToSemantic(formula);
  }

  formulaToEnglish(formula: DcecFormula): string {
    return this.grammar.formulaToEnglish(formula);
  }

  private normalizeInput(text: string): string {
    return typeof text === 'string' ? text.trim().toLowerCase().replace(/\s+/g, ' ') : '';
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
  ): EngDcecParseResult {
    return {
      ok: false,
      input: text,
      normalizedInput,
      errors: Array.isArray(errors) ? [...errors] : [errors],
      metadata: RESULT_METADATA,
    };
  }
}

export function createEngDcecWrapper(options?: EngDcecWrapperOptions): EngDcecWrapper {
  return new EngDcecWrapper(options);
}

export function parseEnglishToDcec(
  text: string,
  options?: EngDcecWrapperOptions,
): EngDcecParseResult {
  return createEngDcecWrapper(options).parse(text);
}

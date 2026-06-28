import type {
  TdfolBinaryOperator,
  TdfolDeonticOperator,
  TdfolFormula,
  TdfolTemporalOperator,
} from './ast';
import {
  BrowserNativeTdfolLlmConverter,
  type BrowserNativeTdfolLlmCacheStats,
  type BrowserNativeTdfolLlmParseResult,
} from './browserNativeLlm';
import { formatTdfolFormula, formatTdfolTerm } from './formatter';
import { parseTdfolFormula } from './parser';

type RuntimeMetadata = {
  browserNative: true;
  serverCallsAllowed: false;
  pythonRuntime: false;
};
const RUNTIME_METADATA: RuntimeMetadata = {
  browserNative: true,
  serverCallsAllowed: false,
  pythonRuntime: false,
};

export type TdfolNlApiOptions = ConstructorParameters<typeof BrowserNativeTdfolLlmConverter>[0];
export type TdfolNlApiParseResult = {
  status: 'parsed' | 'failed';
  input: string;
  formula: string;
  formattedFormula: string;
  ast: TdfolFormula | null;
  confidence: number;
  errors: string[];
  metadata: RuntimeMetadata & {
    method: BrowserNativeTdfolLlmParseResult['method'];
    cacheHit: boolean;
  };
};
export type TdfolNlApiGenerationResult = {
  source: string;
  text: string;
  metadata: RuntimeMetadata;
};

export class BrowserNativeTdfolNlApi {
  private readonly converter: BrowserNativeTdfolLlmConverter;

  constructor(options: TdfolNlApiOptions = {}) {
    this.converter = new BrowserNativeTdfolLlmConverter(options);
  }

  parse(text: string): TdfolNlApiParseResult {
    const input = text.trim();
    if (input.length === 0) return fail(text, ['Input text is empty.'], 'failed', false);
    const converted = this.converter.convert(input);
    if (!converted.success)
      return fail(input, converted.errors, converted.method, converted.cacheHit);
    try {
      const ast = parseTdfolFormula(converted.formula);
      return {
        status: 'parsed',
        input,
        formula: converted.formula,
        formattedFormula: formatTdfolFormula(ast),
        ast,
        confidence: converted.confidence,
        errors: [],
        metadata: parseMetadata(converted.method, converted.cacheHit),
      };
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unable to parse converted formula.';
      return fail(input, [message], converted.method, converted.cacheHit);
    }
  }

  generate(formula: string | TdfolFormula): TdfolNlApiGenerationResult {
    const ast = typeof formula === 'string' ? parseTdfolFormula(formula) : formula;
    return {
      source: formatTdfolFormula(ast),
      text: describeFormula(ast),
      metadata: RUNTIME_METADATA,
    };
  }

  getStats(): BrowserNativeTdfolLlmCacheStats {
    return this.converter.getStats();
  }

  clearCache(): void {
    this.converter.clearCache();
  }
}

export function parseTdfolNaturalLanguage(
  text: string,
  options: TdfolNlApiOptions = {},
): TdfolNlApiParseResult {
  return new BrowserNativeTdfolNlApi(options).parse(text);
}

export function generateTdfolNaturalLanguage(
  formula: string | TdfolFormula,
): TdfolNlApiGenerationResult {
  return new BrowserNativeTdfolNlApi().generate(formula);
}

function fail(
  input: string,
  errors: string[],
  method: BrowserNativeTdfolLlmParseResult['method'],
  cacheHit: boolean,
): TdfolNlApiParseResult {
  return {
    status: 'failed',
    input,
    formula: '',
    formattedFormula: '',
    ast: null,
    confidence: 0,
    errors,
    metadata: parseMetadata(method, cacheHit),
  };
}

function parseMetadata(
  method: BrowserNativeTdfolLlmParseResult['method'],
  cacheHit: boolean,
): RuntimeMetadata & { method: BrowserNativeTdfolLlmParseResult['method']; cacheHit: boolean } {
  return { ...RUNTIME_METADATA, method, cacheHit };
}

function describeFormula(formula: TdfolFormula): string {
  switch (formula.kind) {
    case 'predicate':
      return `${formula.name} holds for ${formula.args.map(formatTdfolTerm).join(', ')}`;
    case 'unary':
      return `not (${describeFormula(formula.formula)})`;
    case 'binary':
      return `${describeFormula(formula.left)} ${describeBinary(formula.operator)} ${describeFormula(formula.right)}`;
    case 'quantified':
      return `${formula.quantifier === 'FORALL' ? 'for every' : 'for some'} ${formula.variable.name}, ${describeFormula(formula.formula)}`;
    case 'deontic':
      return `${describeDeontic(formula.operator)} ${describeFormula(formula.formula)}`;
    case 'temporal':
      return `${describeTemporal(formula.operator)} ${describeFormula(formula.formula)}`;
  }
}

function describeBinary(operator: TdfolBinaryOperator): string {
  return {
    AND: 'and',
    OR: 'or',
    IMPLIES: 'implies',
    IFF: 'if and only if',
    XOR: 'exclusive or',
    UNTIL: 'until',
  }[operator];
}

function describeDeontic(operator: TdfolDeonticOperator): string {
  return {
    OBLIGATION: 'it is obligatory that',
    PERMISSION: 'it is permitted that',
    PROHIBITION: 'it is forbidden that',
  }[operator];
}

function describeTemporal(operator: TdfolTemporalOperator): string {
  return { ALWAYS: 'always', EVENTUALLY: 'eventually', NEXT: 'next' }[operator];
}

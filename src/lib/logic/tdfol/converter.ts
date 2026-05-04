import { formatCecExpression } from '../cec/formatter';
import { getFreeVariables } from './ast';
import type { TdfolBinaryFormula, TdfolFormula, TdfolTerm } from './ast';
import { formatTdfolFormula, formatTdfolTerm } from './formatter';
import { parseTdfolFormula } from './parser';
import { tdfolToCecExpression } from './strategies';

export type TdfolConversionTarget = 'tdfol' | 'fol' | 'dcec' | 'tptp' | 'json';
export type TdfolConversionInput = string | TdfolFormula;

export interface TdfolConversionMetadata {
  target: TdfolConversionTarget;
  quantifierCount: number;
  predicateCount: number;
  operatorCount: number;
  freeVariables: string[];
  containsTemporal: boolean;
  containsDeontic: boolean;
  sourcePythonModule: 'logic/TDFOL/tdfol_converter.py';
  browserNative: true;
  serverCallsAllowed: false;
  pythonRuntime: false;
}

export interface TdfolConversionResult {
  source: string;
  target: TdfolConversionTarget;
  output: string | Record<string, unknown>;
  ast: TdfolFormula;
  warnings: string[];
  metadata: TdfolConversionMetadata;
}

export const TDFOL_CONVERTER_METADATA = {
  sourcePythonModule: 'logic/TDFOL/tdfol_converter.py',
  browserNative: true,
  serverCallsAllowed: false,
  pythonRuntime: false,
  supportedTargets: ['tdfol', 'fol', 'dcec', 'tptp', 'json'],
} as const;

export class BrowserNativeTdfolConverter {
  readonly metadata = TDFOL_CONVERTER_METADATA;

  convert(
    input: TdfolConversionInput,
    target: TdfolConversionTarget | string = 'tdfol',
  ): TdfolConversionResult {
    return convertTdfolFormula(input, normalizeTdfolConversionTarget(target));
  }

  convertToDcec(input: TdfolConversionInput): TdfolConversionResult {
    return this.convert(input, 'dcec');
  }

  async convertAsync(
    input: TdfolConversionInput,
    target: TdfolConversionTarget | string = 'tdfol',
  ): Promise<TdfolConversionResult> {
    return this.convert(input, target);
  }

  validate(input: TdfolConversionInput) {
    const warnings: string[] = [];
    try {
      const ast = typeof input === 'string' ? parseTdfolFormula(input) : input;
      const metadata = analyzeTdfolConversion(ast, 'tdfol');
      if (metadata.containsTemporal) {
        warnings.push(
          'Temporal operators require projection warnings when converting to pure FOL.',
        );
      }
      if (metadata.containsDeontic) {
        warnings.push('Deontic operators require projection warnings when converting to pure FOL.');
      }
      return {
        valid: true,
        errors: [],
        warnings,
        sourcePythonModule: TDFOL_CONVERTER_METADATA.sourcePythonModule,
        browserNative: true,
        serverCallsAllowed: false,
        pythonRuntime: false,
      };
    } catch (error) {
      return {
        valid: false,
        errors: [error instanceof Error ? error.message : String(error)],
        warnings,
        sourcePythonModule: TDFOL_CONVERTER_METADATA.sourcePythonModule,
        browserNative: true,
        serverCallsAllowed: false,
        pythonRuntime: false,
      };
    }
  }
}

export function convertTdfolFormula(
  input: TdfolConversionInput,
  target: TdfolConversionTarget | string,
): TdfolConversionResult {
  const normalizedTarget = normalizeTdfolConversionTarget(target);
  const ast = typeof input === 'string' ? parseTdfolFormula(input) : input;
  const source = formatTdfolFormula(ast);
  const warnings: string[] = [];
  let output: string | Record<string, unknown>;

  switch (normalizedTarget) {
    case 'tdfol':
      output = source;
      break;
    case 'fol':
      output = tdfolToFol(ast, warnings);
      break;
    case 'dcec':
      output = formatCecExpression(tdfolToCecExpression(ast));
      break;
    case 'tptp':
      output = `fof(tdfol_formula, axiom, ${tdfolToTptp(ast)}).`;
      break;
    case 'json':
      output = tdfolToJson(ast);
      break;
  }

  return {
    source,
    target: normalizedTarget,
    output,
    ast,
    warnings,
    metadata: analyzeTdfolConversion(ast, normalizedTarget),
  };
}

export function convertTdfolBatch(
  inputs: Array<TdfolConversionInput>,
  target: TdfolConversionTarget | string,
): TdfolConversionResult[] {
  const normalizedTarget = normalizeTdfolConversionTarget(target);
  return inputs.map((input) => convertTdfolFormula(input, normalizedTarget));
}

export function tdfolToFol(formula: TdfolFormula, warnings: string[] = []): string {
  switch (formula.kind) {
    case 'predicate':
      return formatTdfolFormula(formula);
    case 'unary':
      return `¬(${tdfolToFol(formula.formula, warnings)})`;
    case 'binary':
      return `(${tdfolToFol(formula.left, warnings)}) ${binarySymbol(formula.operator)} (${tdfolToFol(formula.right, warnings)})`;
    case 'quantified':
      return `${formula.quantifier === 'FORALL' ? '∀' : '∃'}${formula.variable.name} (${tdfolToFol(formula.formula, warnings)})`;
    case 'deontic':
      warnings.push(`Projected deontic operator ${formula.operator} away for FOL output.`);
      return tdfolToFol(formula.formula, warnings);
    case 'temporal':
      warnings.push(`Projected temporal operator ${formula.operator} away for FOL output.`);
      return tdfolToFol(formula.formula, warnings);
  }
}

export function tdfolToTptp(formula: TdfolFormula): string {
  switch (formula.kind) {
    case 'predicate':
      return `${toTptpSymbol(formula.name)}(${formula.args.map(tdfolTermToTptp).join(',')})`;
    case 'unary':
      return `~(${tdfolToTptp(formula.formula)})`;
    case 'binary':
      return `(${tdfolToTptp(formula.left)} ${tptpBinarySymbol(formula.operator)} ${tdfolToTptp(formula.right)})`;
    case 'quantified':
      return `${formula.quantifier === 'FORALL' ? '!' : '?'}[${toTptpVariable(formula.variable.name)}]:(${tdfolToTptp(formula.formula)})`;
    case 'deontic':
      return `${formula.operator.toLowerCase()}(${tdfolToTptp(formula.formula)})`;
    case 'temporal':
      return `${formula.operator.toLowerCase()}(${tdfolToTptp(formula.formula)})`;
  }
}

function tdfolToJson(formula: TdfolFormula): Record<string, unknown> {
  return {
    formula,
    formatted: formatTdfolFormula(formula),
    freeVariables: [...getFreeVariables(formula)].sort(),
    metadata: analyzeTdfolConversion(formula, 'json'),
  };
}

function analyzeTdfolConversion(
  formula: TdfolFormula,
  target: TdfolConversionTarget,
): TdfolConversionMetadata {
  let quantifierCount = 0;
  let predicateCount = 0;
  let operatorCount = 0;
  let containsTemporal = false;
  let containsDeontic = false;

  visitFormula(formula, (node) => {
    if (node.kind === 'quantified') quantifierCount += 1;
    if (node.kind === 'predicate') predicateCount += 1;
    if (node.kind !== 'predicate') operatorCount += 1;
    if (node.kind === 'temporal') containsTemporal = true;
    if (node.kind === 'deontic') containsDeontic = true;
  });

  return {
    target,
    quantifierCount,
    predicateCount,
    operatorCount,
    freeVariables: [...getFreeVariables(formula)].sort(),
    containsTemporal,
    containsDeontic,
    sourcePythonModule: TDFOL_CONVERTER_METADATA.sourcePythonModule,
    browserNative: true,
    serverCallsAllowed: false,
    pythonRuntime: false,
  };
}

export function normalizeTdfolConversionTarget(
  target: TdfolConversionTarget | string,
): TdfolConversionTarget {
  const normalized = target
    .trim()
    .toLowerCase()
    .replace(/[-\s]+/g, '_');
  const aliases: Record<string, TdfolConversionTarget> = {
    tdfol: 'tdfol',
    native: 'tdfol',
    source: 'tdfol',
    fol: 'fol',
    first_order: 'fol',
    first_order_logic: 'fol',
    dcec: 'dcec',
    cec: 'dcec',
    tptp: 'tptp',
    fof: 'tptp',
    json: 'json',
    ast: 'json',
  };
  const resolved = aliases[normalized];
  if (!resolved) {
    throw new Error(`Unsupported TDFOL conversion target: ${target}`);
  }
  return resolved;
}

function visitFormula(formula: TdfolFormula, visitor: (formula: TdfolFormula) => void): void {
  visitor(formula);
  switch (formula.kind) {
    case 'predicate':
      return;
    case 'unary':
    case 'quantified':
    case 'deontic':
    case 'temporal':
      visitFormula(formula.formula, visitor);
      return;
    case 'binary':
      visitFormula(formula.left, visitor);
      visitFormula(formula.right, visitor);
      return;
  }
}

function tdfolTermToTptp(term: TdfolTerm): string {
  if (term.kind === 'variable') return toTptpVariable(term.name);
  if (term.kind === 'function')
    return `${toTptpSymbol(term.name)}(${term.args.map(tdfolTermToTptp).join(',')})`;
  return toTptpSymbol(formatTdfolTerm(term));
}

function binarySymbol(operator: TdfolBinaryFormula['operator']): string {
  return {
    AND: '∧',
    OR: '∨',
    IMPLIES: '→',
    IFF: '↔',
    XOR: '⊕',
    UNTIL: 'U',
  }[operator];
}

function tptpBinarySymbol(operator: TdfolBinaryFormula['operator']): string {
  return {
    AND: '&',
    OR: '|',
    IMPLIES: '=>',
    IFF: '<=>',
    XOR: '<~>',
    UNTIL: 'U',
  }[operator];
}

function toTptpVariable(name: string): string {
  return name.charAt(0).toUpperCase() + name.slice(1).replace(/[^a-zA-Z0-9_]/g, '_');
}

function toTptpSymbol(name: string): string {
  const normalized = name.replace(/[^a-zA-Z0-9_]/g, '_');
  return normalized.charAt(0).toLowerCase() + normalized.slice(1);
}

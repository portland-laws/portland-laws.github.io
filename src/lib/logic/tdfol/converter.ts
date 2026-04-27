import { formatCecExpression } from '../cec/formatter';
import { getFreeVariables } from './ast';
import type { TdfolBinaryFormula, TdfolFormula, TdfolTerm } from './ast';
import { formatTdfolFormula, formatTdfolTerm } from './formatter';
import { parseTdfolFormula } from './parser';
import { tdfolToCecExpression } from './strategies';

export type TdfolConversionTarget = 'tdfol' | 'fol' | 'dcec' | 'tptp' | 'json';

export interface TdfolConversionMetadata {
  target: TdfolConversionTarget;
  quantifierCount: number;
  predicateCount: number;
  operatorCount: number;
  freeVariables: string[];
  containsTemporal: boolean;
  containsDeontic: boolean;
}

export interface TdfolConversionResult {
  source: string;
  target: TdfolConversionTarget;
  output: string | Record<string, unknown>;
  ast: TdfolFormula;
  warnings: string[];
  metadata: TdfolConversionMetadata;
}

export function convertTdfolFormula(
  input: string | TdfolFormula,
  target: TdfolConversionTarget,
): TdfolConversionResult {
  const ast = typeof input === 'string' ? parseTdfolFormula(input) : input;
  const source = formatTdfolFormula(ast);
  const warnings: string[] = [];
  let output: string | Record<string, unknown>;

  switch (target) {
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
    target,
    output,
    ast,
    warnings,
    metadata: analyzeTdfolConversion(ast, target),
  };
}

export function convertTdfolBatch(
  inputs: Array<string | TdfolFormula>,
  target: TdfolConversionTarget,
): TdfolConversionResult[] {
  return inputs.map((input) => convertTdfolFormula(input, target));
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

function analyzeTdfolConversion(formula: TdfolFormula, target: TdfolConversionTarget): TdfolConversionMetadata {
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
  };
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
  if (term.kind === 'function') return `${toTptpSymbol(term.name)}(${term.args.map(tdfolTermToTptp).join(',')})`;
  return toTptpSymbol(formatTdfolTerm(term));
}

function binarySymbol(operator: TdfolBinaryFormula['operator']): string {
  return {
    AND: '∧',
    OR: '∨',
    IMPLIES: '→',
    IFF: '↔',
    XOR: '⊕',
  }[operator];
}

function tptpBinarySymbol(operator: TdfolBinaryFormula['operator']): string {
  return {
    AND: '&',
    OR: '|',
    IMPLIES: '=>',
    IFF: '<=>',
    XOR: '<~>',
  }[operator];
}

function toTptpVariable(name: string): string {
  return name.charAt(0).toUpperCase() + name.slice(1).replace(/[^a-zA-Z0-9_]/g, '_');
}

function toTptpSymbol(name: string): string {
  const normalized = name.replace(/[^a-zA-Z0-9_]/g, '_');
  return normalized.charAt(0).toLowerCase() + normalized.slice(1);
}

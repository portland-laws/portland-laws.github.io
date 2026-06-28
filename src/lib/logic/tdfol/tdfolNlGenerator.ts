import type {
  TdfolBinaryOperator,
  TdfolDeonticOperator,
  TdfolFormula,
  TdfolTemporalOperator,
  TdfolTerm,
} from './ast';
import { formatTdfolFormula, formatTdfolTerm } from './formatter';
import { parseTdfolFormula } from './parser';

export type TdfolNlGeneratorStyle = 'plain' | 'controlled';
type TdfolNlSummary = { predicateCount: number; quantifierCount: number; operatorCount: number };

export type TdfolNlGeneratorResult = {
  source: string;
  text: string;
  confidence: number;
  metadata: TdfolNlSummary & {
    browserNative: true;
    serverCallsAllowed: false;
    pythonRuntime: false;
    sourcePythonModule: 'logic/TDFOL/nl/tdfol_nl_generator.py';
    style: TdfolNlGeneratorStyle;
    formulaKind: TdfolFormula['kind'];
  };
};

export class BrowserNativeTdfolNlGenerator {
  constructor(private readonly options: { style?: TdfolNlGeneratorStyle } = {}) {}

  generate(formula: string | TdfolFormula): TdfolNlGeneratorResult {
    const ast = typeof formula === 'string' ? parseTdfolFormula(formula) : formula;
    const style = this.options.style ?? 'plain';
    return {
      source: formatTdfolFormula(ast),
      text: sentence(describeFormula(ast, style)),
      confidence: 1,
      metadata: {
        browserNative: true,
        serverCallsAllowed: false,
        pythonRuntime: false,
        sourcePythonModule: 'logic/TDFOL/nl/tdfol_nl_generator.py',
        style,
        formulaKind: ast.kind,
        ...summarizeFormula(ast),
      },
    };
  }
}

export function generateTdfolNl(
  formula: string | TdfolFormula,
  options: { style?: TdfolNlGeneratorStyle } = {},
): TdfolNlGeneratorResult {
  return new BrowserNativeTdfolNlGenerator(options).generate(formula);
}

function describeFormula(formula: TdfolFormula, style: TdfolNlGeneratorStyle): string {
  switch (formula.kind) {
    case 'predicate':
      return describePredicate(formula.name, formula.args, style);
    case 'unary':
      return `it is not the case that ${describeFormula(formula.formula, style)}`;
    case 'binary':
      return `${describeFormula(formula.left, style)} ${binaryWord(formula.operator)} ${describeFormula(formula.right, style)}`;
    case 'quantified':
      return `${formula.quantifier === 'FORALL' ? 'for every' : 'there exists'} ${describeVariable(formula.variable)}, ${describeFormula(formula.formula, style)}`;
    case 'deontic':
      return `${deonticWord(formula.operator)} ${describeFormula(formula.formula, style)}`;
    case 'temporal':
      return `${temporalWord(formula.operator)} ${describeFormula(formula.formula, style)}`;
  }
}

function describePredicate(name: string, args: TdfolTerm[], style: TdfolNlGeneratorStyle): string {
  if (args.length === 0) return `${words(name)} holds`;
  const relation = style === 'controlled' ? 'holds for' : 'applies to';
  return `${words(name)} ${relation} ${args.map((arg) => describeTerm(arg, style)).join(', ')}`;
}

function describeTerm(term: TdfolTerm, style: TdfolNlGeneratorStyle): string {
  if (term.kind === 'variable') return describeVariable(term);
  if (term.kind === 'constant') return words(term.name);
  return `${words(term.name)} of ${term.args.map((arg) => describeTerm(arg, style)).join(', ')}`;
}

function describeVariable(term: TdfolTerm): string {
  return term.sort ? `${term.name} of sort ${term.sort}` : formatTdfolTerm(term);
}

function binaryWord(operator: TdfolBinaryOperator): string {
  return {
    AND: 'and',
    OR: 'or',
    IMPLIES: 'implies that',
    IFF: 'if and only if',
    XOR: 'exclusive or',
    UNTIL: 'until',
  }[operator];
}

function deonticWord(operator: TdfolDeonticOperator): string {
  return {
    OBLIGATION: 'it is obligatory that',
    PERMISSION: 'it is permitted that',
    PROHIBITION: 'it is forbidden that',
  }[operator];
}

function temporalWord(operator: TdfolTemporalOperator): string {
  return { ALWAYS: 'always', EVENTUALLY: 'eventually', NEXT: 'next' }[operator];
}

function summarizeFormula(formula: TdfolFormula): TdfolNlSummary {
  if (formula.kind === 'predicate')
    return { predicateCount: 1, quantifierCount: 0, operatorCount: 0 };
  if (formula.kind === 'binary') {
    const left = summarizeFormula(formula.left);
    const right = summarizeFormula(formula.right);
    return {
      predicateCount: left.predicateCount + right.predicateCount,
      quantifierCount: left.quantifierCount + right.quantifierCount,
      operatorCount: left.operatorCount + right.operatorCount + 1,
    };
  }
  const child = summarizeFormula(formula.formula);
  const key = formula.kind === 'quantified' ? 'quantifierCount' : 'operatorCount';
  return { ...child, [key]: child[key] + 1 };
}

function words(value: string): string {
  return value
    .replace(/([a-z0-9])([A-Z])/g, '$1 $2')
    .replace(/[_-]+/g, ' ')
    .trim()
    .toLowerCase();
}

function sentence(text: string): string {
  const normalized = text.trim().replace(/\s+/g, ' ');
  return normalized.endsWith('.') ? normalized : `${normalized}.`;
}

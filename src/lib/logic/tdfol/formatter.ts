import type { TdfolFormula, TdfolTerm } from './ast';

const BINARY_SYMBOLS = {
  AND: '∧',
  OR: '∨',
  IMPLIES: '→',
  IFF: '↔',
  XOR: '⊕',
} as const;

const QUANTIFIER_SYMBOLS = {
  FORALL: '∀',
  EXISTS: '∃',
} as const;

const DEONTIC_SYMBOLS = {
  OBLIGATION: 'O',
  PERMISSION: 'P',
  PROHIBITION: 'F',
} as const;

const TEMPORAL_SYMBOLS = {
  ALWAYS: '□',
  EVENTUALLY: '◊',
  NEXT: 'X',
} as const;

export function formatTdfolFormula(formula: TdfolFormula): string {
  switch (formula.kind) {
    case 'predicate': {
      const args = formula.args.map(formatTdfolTerm).join(', ');
      return `${formula.name}(${args})`;
    }
    case 'unary':
      return `¬${parenthesize(formatTdfolFormula(formula.formula))}`;
    case 'binary':
      return `${parenthesize(formatTdfolFormula(formula.left))} ${BINARY_SYMBOLS[formula.operator]} ${parenthesize(
        formatTdfolFormula(formula.right),
      )}`;
    case 'quantified': {
      const sort = formula.variable.sort ? `:${formula.variable.sort}` : '';
      return `${QUANTIFIER_SYMBOLS[formula.quantifier]}${formula.variable.name}${sort} ${parenthesize(
        formatTdfolFormula(formula.formula),
      )}`;
    }
    case 'deontic':
      return `${DEONTIC_SYMBOLS[formula.operator]}${parenthesize(formatTdfolFormula(formula.formula))}`;
    case 'temporal':
      return `${TEMPORAL_SYMBOLS[formula.operator]}${parenthesize(formatTdfolFormula(formula.formula))}`;
  }
}

export function formatTdfolTerm(term: TdfolTerm): string {
  switch (term.kind) {
    case 'variable':
      return term.sort ? `${term.name}:${term.sort}` : term.name;
    case 'constant':
      return term.name;
    case 'function':
      return `${term.name}(${term.args.map(formatTdfolTerm).join(', ')})`;
  }
}

function parenthesize(value: string): string {
  return `(${value})`;
}


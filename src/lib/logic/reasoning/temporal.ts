import type { TdfolFormula } from '../tdfol';

export type TemporalSummary = 'always' | 'eventually' | 'next' | 'none';

export function summarizeTemporalOperators(formula: TdfolFormula): TemporalSummary[] {
  const operators = new Set<TemporalSummary>();
  collect(formula, operators);
  return operators.size > 0 ? [...operators] : ['none'];
}

export function describeTemporalSummary(summary: TemporalSummary[]): string {
  if (summary.includes('always')) {
    return 'Always/continuing condition';
  }
  if (summary.includes('eventually')) {
    return 'Eventual/future condition';
  }
  if (summary.includes('next')) {
    return 'Next-step condition';
  }
  return 'No explicit temporal operator';
}

function collect(formula: TdfolFormula, operators: Set<TemporalSummary>): void {
  switch (formula.kind) {
    case 'temporal':
      if (formula.operator === 'ALWAYS') operators.add('always');
      if (formula.operator === 'EVENTUALLY') operators.add('eventually');
      if (formula.operator === 'NEXT') operators.add('next');
      collect(formula.formula, operators);
      return;
    case 'binary':
      collect(formula.left, operators);
      collect(formula.right, operators);
      return;
    case 'deontic':
    case 'quantified':
    case 'unary':
      collect(formula.formula, operators);
      return;
    case 'predicate':
      return;
  }
}


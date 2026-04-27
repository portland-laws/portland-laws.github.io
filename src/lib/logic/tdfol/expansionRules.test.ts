import { formatTdfolFormula } from './formatter';
import { parseTdfolFormula } from './parser';
import {
  expandTdfolFormula,
  getAllTdfolExpansionRules,
  selectTdfolExpansionRule,
  TdfolAndExpansionRule,
  TdfolIffExpansionRule,
  TdfolImpliesExpansionRule,
  TdfolNotExpansionRule,
  TdfolOrExpansionRule,
  type TdfolExpansionResult,
} from './expansionRules';

describe('TDFOL expansion rules', () => {
  it('expands conjunctions with linear and branching polarity', () => {
    const formula = parseTdfolFormula('Pred(x) and Goal(x)');
    expect(formatResult(new TdfolAndExpansionRule().expand({ formula }))).toEqual({
      kind: 'linear',
      formulas: [['Pred(x)', false], ['Goal(x)', false]],
    });
    expect(formatResult(new TdfolAndExpansionRule().expand({ formula, negated: true }))).toEqual({
      kind: 'branching',
      branches: [[['Pred(x)', true]], [['Goal(x)', true]]],
    });
  });

  it('expands disjunctions with Python tableaux polarity', () => {
    const formula = parseTdfolFormula('Pred(x) or Goal(x)');

    expect(formatResult(new TdfolOrExpansionRule().expand({ formula }))).toEqual({
      kind: 'branching',
      branches: [[['Pred(x)', false]], [['Goal(x)', false]]],
    });
    expect(formatResult(new TdfolOrExpansionRule().expand({ formula, negated: true }))).toEqual({
      kind: 'linear',
      formulas: [['Pred(x)', true], ['Goal(x)', true]],
    });
  });

  it('expands implications with positive branching and negated linear behavior', () => {
    const formula = parseTdfolFormula('Pred(x) -> Goal(x)');

    expect(formatResult(new TdfolImpliesExpansionRule().expand({ formula }))).toEqual({
      kind: 'branching',
      branches: [[['Pred(x)', true]], [['Goal(x)', false]]],
    });
    expect(formatResult(new TdfolImpliesExpansionRule().expand({ formula, negated: true }))).toEqual({
      kind: 'linear',
      formulas: [['Pred(x)', false], ['Goal(x)', true]],
    });
  });

  it('expands bi-implications into truth-value branches', () => {
    const formula = parseTdfolFormula('Pred(x) <-> Goal(x)');

    expect(formatResult(new TdfolIffExpansionRule().expand({ formula }))).toEqual({
      kind: 'branching',
      branches: [[['Pred(x)', false], ['Goal(x)', false]], [['Pred(x)', true], ['Goal(x)', true]]],
    });
    expect(formatResult(new TdfolIffExpansionRule().expand({ formula, negated: true }))).toEqual({
      kind: 'branching',
      branches: [[['Pred(x)', false], ['Goal(x)', true]], [['Pred(x)', true], ['Goal(x)', false]]],
    });
  });

  it('expands unary not by flipping polarity', () => {
    const formula = parseTdfolFormula('not Pred(x)');

    expect(formatResult(new TdfolNotExpansionRule().expand({ formula }))).toEqual({
      kind: 'linear',
      formulas: [['Pred(x)', true]],
    });
    expect(formatResult(new TdfolNotExpansionRule().expand({ formula, negated: true }))).toEqual({
      kind: 'linear',
      formulas: [['Pred(x)', false]],
    });
  });

  it('selects expansion rules and returns undefined for atomic formulas', () => {
    expect(getAllTdfolExpansionRules().map((rule) => rule.name)).toEqual([
      'AndExpansionRule',
      'OrExpansionRule',
      'ImpliesExpansionRule',
      'IffExpansionRule',
      'NotExpansionRule',
    ]);
    expect(selectTdfolExpansionRule(parseTdfolFormula('Pred(x) and Goal(x)'))?.name).toBe('AndExpansionRule');
    expect(expandTdfolFormula(parseTdfolFormula('Pred(x)'))).toBeUndefined();
  });
});

function formatResult(result: TdfolExpansionResult): unknown {
  if (result.kind === 'linear') {
    return {
      kind: result.kind,
      formulas: result.formulas?.map(([formula, negated]) => [formatTdfolFormula(formula), negated]),
    };
  }
  return {
    kind: result.kind,
    branches: result.branches?.map((branch) => branch.map(([formula, negated]) => [formatTdfolFormula(formula), negated])),
  };
}

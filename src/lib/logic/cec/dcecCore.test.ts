import { LogicValidationError } from '../errors';
import {
  DcecAtomicFormula,
  DcecCognitiveFormula,
  DcecConnectiveFormula,
  DcecDeonticFormula,
  DcecFunctionTerm,
  DcecQuantifiedFormula,
  DcecTemporalFormula,
  DcecVariableTerm,
  createDcecStatement,
  dcecAtom,
  dcecConjunction,
  dcecDisjunction,
  dcecImplication,
  dcecNegation,
  formatDcecStatement,
  sameDcecFormula,
} from './dcecCore';
import {
  DcecCognitiveOperator,
  DcecDeonticOperator,
  DcecFunctionSymbol,
  DcecLogicalConnective,
  DcecPredicateSymbol,
  DcecSort,
  DcecTemporalOperator,
  DcecVariable,
} from './dcecTypes';

describe('DCEC core formulas and terms', () => {
  const entity = new DcecSort('Entity');
  const agentSort = new DcecSort('Agent', entity);
  const actionSort = new DcecSort('Action');
  const momentSort = new DcecSort('Moment');

  const agent = new DcecVariable('agent', agentSort);
  const action = new DcecVariable('action', actionSort);
  const reviewer = new DcecVariable('reviewer', agentSort);
  const time = new DcecVariable('t', momentSort);

  it('models variable and function terms with sort, free-variable, and substitution behavior', () => {
    const agentTerm = new DcecVariableTerm(agent);
    const reviewerTerm = new DcecVariableTerm(reviewer);
    const ownerOf = new DcecFunctionSymbol('ownerOf', [actionSort], agentSort);
    const actionTerm = new DcecVariableTerm(action);
    const ownerTerm = new DcecFunctionTerm(ownerOf, [actionTerm]);

    expect(agentTerm.getSort()).toBe(agentSort);
    expect([...ownerTerm.getFreeVariables()].map(String)).toEqual(['action:Action']);
    expect(String(ownerTerm)).toBe('ownerOf(action:Action)');
    expect(String(agentTerm.substitute(agent, reviewerTerm))).toBe('reviewer:Agent');
    expect(() => new DcecFunctionTerm(ownerOf, [])).toThrow(LogicValidationError);
  });

  it('renders atomic formulas and substitutes free variables', () => {
    const predicate = new DcecPredicateSymbol('authorized', [agentSort, actionSort]);
    const formula = new DcecAtomicFormula(predicate, [
      new DcecVariableTerm(agent),
      new DcecVariableTerm(action),
    ]);
    const substituted = formula.substitute(agent, new DcecVariableTerm(reviewer));

    expect(String(formula)).toBe('authorized(agent:Agent, action:Action)');
    expect([...formula.getFreeVariables()].map(String).sort()).toEqual(['action:Action', 'agent:Agent']);
    expect(String(substituted)).toBe('authorized(reviewer:Agent, action:Action)');
    expect(() => new DcecAtomicFormula(predicate, [new DcecVariableTerm(agent)])).toThrow(LogicValidationError);
  });

  it('renders deontic, cognitive, and temporal formulas in Python-compatible notation', () => {
    const permitted = dcecAtom('permit');
    const agentTerm = new DcecVariableTerm(agent);
    const timeTerm = new DcecVariableTerm(time);

    expect(String(new DcecDeonticFormula(DcecDeonticOperator.OBLIGATION, permitted))).toBe('O(permit())');
    expect(String(new DcecDeonticFormula(DcecDeonticOperator.PERMISSION, permitted, agentTerm))).toBe('P[agent:Agent](permit())');
    expect(String(new DcecCognitiveFormula(DcecCognitiveOperator.BELIEF, agentTerm, permitted))).toBe('B(agent:Agent, permit())');
    expect(String(new DcecTemporalFormula(DcecTemporalOperator.ALWAYS, permitted))).toBe('□(permit())');
    expect(String(new DcecTemporalFormula(DcecTemporalOperator.EVENTUALLY, permitted, timeTerm))).toBe('◊[t:Moment](permit())');
  });

  it('validates and renders logical connectives and quantifiers', () => {
    const p = dcecAtom('P');
    const q = dcecAtom('Q');
    const r = dcecAtom('R');

    expect(String(new DcecConnectiveFormula(DcecLogicalConnective.AND, [p, q, r]))).toBe('(P() ∧ Q() ∧ R())');
    expect(String(new DcecConnectiveFormula(DcecLogicalConnective.OR, [p, q]))).toBe('(P() ∨ Q())');
    expect(String(new DcecConnectiveFormula(DcecLogicalConnective.NOT, [p]))).toBe('¬(P())');
    expect(String(new DcecConnectiveFormula(DcecLogicalConnective.IMPLIES, [p, q]))).toBe('(P() → Q())');
    expect(String(new DcecConnectiveFormula(DcecLogicalConnective.BICONDITIONAL, [p, q]))).toBe('(P() ↔ Q())');
    expect(String(new DcecQuantifiedFormula(DcecLogicalConnective.FORALL, agent, p))).toBe('∀agent:Agent(P())');
    expect(String(new DcecQuantifiedFormula(DcecLogicalConnective.EXISTS, action, q))).toBe('∃action:Action(Q())');

    expect(() => new DcecConnectiveFormula(DcecLogicalConnective.NOT, [p, q])).toThrow(LogicValidationError);
    expect(() => new DcecConnectiveFormula(DcecLogicalConnective.AND, [p])).toThrow(LogicValidationError);
    expect(() => new DcecQuantifiedFormula(DcecLogicalConnective.AND, agent, p)).toThrow(LogicValidationError);
  });

  it('tracks bound variables and avoids substituting quantified variables', () => {
    const predicate = new DcecPredicateSymbol('assigned', [agentSort, actionSort]);
    const body = new DcecAtomicFormula(predicate, [
      new DcecVariableTerm(agent),
      new DcecVariableTerm(action),
    ]);
    const quantified = new DcecQuantifiedFormula(DcecLogicalConnective.FORALL, agent, body);

    expect([...quantified.getFreeVariables()].map(String)).toEqual(['action:Action']);
    expect(quantified.substitute(agent, new DcecVariableTerm(reviewer))).toBe(quantified);
    expect(String(quantified.substitute(action, new DcecVariableTerm(new DcecVariable('appeal', actionSort))))).toBe(
      '∀agent:Agent(assigned(agent:Agent, appeal:Action))',
    );
  });

  it('supports convenience constructors, statement formatting, and string equality', () => {
    const p = dcecAtom('P');
    const q = dcecAtom('Q');
    const conjunction = dcecConjunction(p, q);
    const statement = createDcecStatement(dcecImplication(conjunction, dcecNegation(q)), 'rule1', { source: 'fixture' });

    expect(String(dcecDisjunction(p, q))).toBe('(P() ∨ Q())');
    expect(formatDcecStatement(statement)).toBe('rule1: ((P() ∧ Q()) → ¬(Q()))');
    expect(sameDcecFormula(dcecAtom('P'), new DcecAtomicFormula(new DcecPredicateSymbol('P', []), []))).toBe(true);
    expect(statement.metadata).toEqual({ source: 'fixture' });
  });
});

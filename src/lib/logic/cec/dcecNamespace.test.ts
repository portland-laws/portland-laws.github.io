import { parseCecExpression } from './parser';
import { DcecContainer, DcecNamespace, DcecNamespaceError } from './dcecNamespace';
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

describe('DCEC namespace and type utilities', () => {
  it('models DCEC operator aliases as browser-native constants', () => {
    expect(DcecDeonticOperator.OBLIGATION).toBe('O');
    expect(DcecDeonticOperator.OBLIGATORY).toBe('O');
    expect(DcecCognitiveOperator.KNOWLEDGE).toBe('K');
    expect(DcecCognitiveOperator.KNOWS).toBe('K');
    expect(DcecLogicalConnective.FORALL).toBe('forAll');
    expect(DcecTemporalOperator.UNTIL).toBe('until');
  });

  it('supports subtype checks and Python-compatible symbol rendering', () => {
    const entity = new DcecSort('Entity');
    const agent = new DcecSort('Agent', entity);
    const human = new DcecSort('Human', agent);
    const variable = new DcecVariable('x', human);
    const age = new DcecFunctionSymbol('age', [human], new DcecSort('Number'));
    const eligible = new DcecPredicateSymbol('eligible', [human]);

    expect(human.isSubtypeOf(entity)).toBe(true);
    expect(entity.isSubtypeOf(human)).toBe(false);
    expect(String(variable)).toBe('x:Human');
    expect(age.arity()).toBe(1);
    expect(String(age)).toBe('age(Human) -> Number');
    expect(eligible.arity()).toBe(1);
    expect(String(eligible)).toBe('eligible(Human)');
  });

  it('initializes Python-compatible built-in sorts and statistics', () => {
    const namespace = new DcecNamespace();

    expect([...namespace.sorts.keys()]).toEqual([
      'Entity',
      'Boolean',
      'Moment',
      'Event',
      'Action',
      'Agent',
      'ActionType',
      'Obligation',
      'Permission',
    ]);
    expect(namespace.getSort('Agent')?.isSubtypeOf(namespace.getSort('Entity')!)).toBe(true);
    expect(namespace.getSort('Obligation')?.isSubtypeOf(namespace.getSort('Boolean')!)).toBe(true);
    expect(namespace.getStatistics()).toEqual({ sorts: 9, variables: 0, functions: 0, predicates: 0 });
    expect(String(namespace)).toBe('DCECNamespace(sorts=9, vars=0, funcs=0, preds=0)');
  });

  it('adds and retrieves variables, functions, and predicates with sort validation', () => {
    const namespace = new DcecNamespace();
    namespace.addSort('Number');
    const variable = namespace.addVariable('agent', 'Agent');
    const functionSymbol = namespace.addFunction('ownerOf', ['Action'], 'Agent');
    const predicate = namespace.addPredicate('authorized', ['Agent', 'Action']);
    const autoPredicate = namespace.getPredicate('implicitFact', 0);

    expect(variable).toBe(namespace.getVariable('agent'));
    expect(functionSymbol).toBe(namespace.getFunction('ownerOf'));
    expect(predicate).toBe(namespace.getPredicate('authorized'));
    expect(autoPredicate?.arity()).toBe(0);
    expect(namespace.getStatistics()).toEqual({ sorts: 10, variables: 1, functions: 1, predicates: 2 });
  });

  it('reports namespace errors with symbol, operation, and suggestions', () => {
    const namespace = new DcecNamespace();

    expect(() => namespace.addSort('Entity')).toThrow(DcecNamespaceError);
    try {
      namespace.addVariable('x', 'MissingSort');
    } catch (error) {
      expect(error).toBeInstanceOf(DcecNamespaceError);
      expect((error as DcecNamespaceError).symbol).toBe('MissingSort');
      expect((error as DcecNamespaceError).operation).toBe('lookup');
      expect((error as DcecNamespaceError).suggestion).toContain("Register sort 'MissingSort' first");
    }
  });

  it('stores statements, axioms, and theorems while preserving the namespace on clear', () => {
    const container = new DcecContainer();
    const axiom = parseCecExpression('(implies (Permit applicant) (O review))');
    const theorem = parseCecExpression('(O review)');

    const axiomStatement = container.addAxiom(axiom, 'ax1', { source: 'fixture' });
    const theoremStatement = container.addTheorem(theorem, 'th1');

    expect(container.getStatement('ax1')).toBe(axiomStatement);
    expect(container.getStatement('th1')).toBe(theoremStatement);
    expect(container.getAxioms()).toEqual([axiomStatement]);
    expect(container.getTheorems()).toEqual([theoremStatement]);
    expect(container.getStatistics()).toMatchObject({
      total_statements: 2,
      axioms: 1,
      theorems: 1,
      labeled_statements: 2,
    });
    expect(() => container.addStatement(theorem, { label: 'ax1' })).toThrow(DcecNamespaceError);

    container.clear();
    expect(container.getAllStatements()).toEqual([]);
    expect(container.namespace.getStatistics().sorts).toBe(9);
    expect(String(container)).toBe('DCECContainer(statements=0, axioms=0, theorems=0)');
  });
});

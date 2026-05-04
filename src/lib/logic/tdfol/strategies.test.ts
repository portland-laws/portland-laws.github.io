import type { ProofResult } from '../types';
import {
  ModusPonensRule,
  TemporalKAxiomRule,
  TemporalTAxiomRule,
  type TdfolInferenceRule,
} from './inferenceRules';
import { parseTdfolFormula } from './parser';
import {
  proveTdfolWithStrategySelection,
  TdfolBaseProverStrategy,
  TdfolBackwardChainingStrategy,
  TdfolBidirectionalStrategy,
  TdfolCecDelegateStrategy,
  TdfolForwardChainingStrategy,
  TdfolLocalCecDelegate,
  TdfolModalTableauxStrategy,
  TdfolStrategySelector,
  tdfolToCecExpression,
  type TdfolProverStrategy,
} from './strategies';

describe('TDFOL proving strategies', () => {
  it('exposes the browser-native base strategy contract with Python source metadata', () => {
    const strategy = new FixtureBaseStrategy();
    const theorem = parseTdfolFormula('Goal(x)');
    const kb = { axioms: [parseTdfolFormula('Pred(x)'), parseTdfolFormula('Pred(x) -> Goal(x)')] };

    expect(strategy.canHandle(theorem, kb)).toBe(true);
    expect(strategy.getPriority()).toBe(42);
    expect(strategy.estimateCost(theorem, kb)).toBeGreaterThan(1);
    expect(strategy.getMetadata(theorem, kb)).toMatchObject({
      name: 'Fixture Base Strategy',
      type: 'forward_chaining',
      priority: 42,
      sourcePythonModule: 'logic/TDFOL/strategies/base.py',
      browserNative: true,
      defaultTimeoutMs: 250,
    });
    expect(strategy.prove(theorem, kb)).toMatchObject({
      status: 'proved',
      theorem: 'Goal(x)',
      method: 'forward_chaining',
      steps: [{ rule: 'FixtureLookup', conclusion: 'Goal(x)' }],
    });
  });

  it('rejects invalid base strategy definitions fail-closed', () => {
    expect(() => new InvalidBaseStrategy()).toThrow('TDFOL prover strategy name must be non-empty');
  });

  it('proves direct knowledge-base formulas with forward chaining', () => {
    const theorem = parseTdfolFormula('Pred(x)');
    const strategy = new TdfolForwardChainingStrategy({ rules: [ModusPonensRule] });

    expect(strategy.prove(theorem, { axioms: [theorem] })).toMatchObject({
      status: 'proved',
      theorem: 'Pred(x)',
      steps: [],
      method: 'forward_chaining',
    });
  });

  it('derives formulas through bounded forward chaining', () => {
    const strategy = new TdfolForwardChainingStrategy({
      rules: [ModusPonensRule],
      maxIterations: 5,
    });
    const result = strategy.prove(parseTdfolFormula('Goal(x)'), {
      axioms: [parseTdfolFormula('Pred(x)'), parseTdfolFormula('Pred(x) -> Goal(x)')],
    });

    expect(result).toMatchObject({
      status: 'proved',
      steps: [{ rule: 'ModusPonens', conclusion: 'Goal(x)' }],
    });
    expect(result.timeMs).toBeGreaterThanOrEqual(0);
  });

  it('chains temporal and propositional rules using the strategy facade', () => {
    const result = proveTdfolWithStrategySelection(
      parseTdfolFormula('Goal(x)'),
      {
        axioms: [
          parseTdfolFormula('always(Pred(x) -> Goal(x))'),
          parseTdfolFormula('always(Pred(x))'),
        ],
      },
      {
        strategies: [
          new TdfolForwardChainingStrategy({ rules: [TemporalKAxiomRule, TemporalTAxiomRule] }),
        ],
      },
    );

    expect(result).toMatchObject({
      status: 'proved',
      theorem: 'Goal(x)',
      method: 'forward_chaining',
    });
  });

  it('returns unknown when the selected strategy cannot progress', () => {
    const strategy = new TdfolForwardChainingStrategy({
      rules: [ModusPonensRule],
      maxIterations: 2,
    });

    expect(
      strategy.prove(parseTdfolFormula('Goal(x)'), { axioms: [parseTdfolFormula('Pred(x)')] }),
    ).toMatchObject({
      status: 'unknown',
    });
  });

  it('respects the derived formula budget', () => {
    const expandingRule: TdfolInferenceRule = {
      name: 'Expand',
      description: 'Wraps any formula in eventually',
      arity: 1,
      canApply: () => true,
      apply: (formula) => ({ kind: 'temporal', operator: 'EVENTUALLY', formula }),
    };
    const strategy = new TdfolForwardChainingStrategy({
      rules: [expandingRule],
      maxDerivedFormulas: 2,
    });

    expect(
      strategy.prove(parseTdfolFormula('Goal(x)'), { axioms: [parseTdfolFormula('Pred(x)')] }),
    ).toMatchObject({
      status: 'timeout',
      error: 'Derived formula budget exceeded',
    });
  });

  it('selects the highest-priority applicable strategy by default', () => {
    const highPriority = fakeStrategy('High', 90, 10, false);
    const fallback = new TdfolForwardChainingStrategy({ rules: [ModusPonensRule] });
    const selector = new TdfolStrategySelector({ strategies: [fallback, highPriority] });

    expect(selector.selectStrategy(parseTdfolFormula('Goal(x)'), { axioms: [] }).name).toBe('High');
  });

  it('can prefer the lowest estimated cost among applicable strategies', () => {
    const expensive = fakeStrategy('Expensive', 100, 200, false);
    const cheap = fakeStrategy('Cheap', 10, 1, false);
    const selector = new TdfolStrategySelector({ strategies: [expensive, cheap] });

    expect(selector.selectStrategy(parseTdfolFormula('Goal(x)'), { axioms: [] }, true).name).toBe(
      'Cheap',
    );
  });

  it('reports strategy metadata and ordered fallback lists', () => {
    const selector = new TdfolStrategySelector({
      strategies: [fakeStrategy('Low', 5, 1, false), fakeStrategy('High', 50, 2, false)],
    });

    expect(selector.getStrategyInfo(parseTdfolFormula('Goal(x)'), { axioms: [] })).toEqual([
      { name: 'High', type: 'forward_chaining', priority: 50, cost: 2 },
      { name: 'Low', type: 'forward_chaining', priority: 5, cost: 1 },
    ]);
    expect(
      selector.selectMultiple(parseTdfolFormula('Goal(x)'), { axioms: [] }, 1).map((s) => s.name),
    ).toEqual(['High']);
  });

  it('selects modal tableaux for modal formulas in the default strategy set', () => {
    const selector = new TdfolStrategySelector();
    const strategy = selector.selectStrategy(parseTdfolFormula('always(Pred(x)) -> Pred(x)'), {
      axioms: [],
    });

    expect(strategy.name).toBe('Modal Tableaux');
    expect(strategy.strategyType).toBe('modal_tableaux');
  });

  it('proves modal tautologies through the modal tableaux strategy', () => {
    const strategy = new TdfolModalTableauxStrategy({ logicType: 'T' });
    const result = strategy.prove(parseTdfolFormula('always(Pred(x)) -> Pred(x)'), { axioms: [] });

    expect(result).toMatchObject({
      status: 'proved',
      theorem: '(□(Pred(x))) → (Pred(x))',
      method: 'modal_tableaux:T',
    });
    expect(result.steps.some((step) => step.conclusion.includes('BOX expansion'))).toBe(true);
  });

  it('returns unknown with an open branch for non-valid modal formulas', () => {
    const strategy = new TdfolModalTableauxStrategy({ logicType: 'K' });

    expect(
      strategy.prove(parseTdfolFormula('always(Pred(x)) -> Pred(x)'), { axioms: [] }),
    ).toMatchObject({
      status: 'unknown',
      method: 'modal_tableaux:K',
      error: 'Open branch remains after 1 branch(es)',
    });
  });

  it('selects D for deontic formulas and S4 for temporal formulas', () => {
    const strategy = new TdfolModalTableauxStrategy();

    expect(strategy.selectModalLogicType(parseTdfolFormula('O(Comply(x))'))).toBe('D');
    expect(strategy.selectModalLogicType(parseTdfolFormula('always(Pred(x))'))).toBe('S4');
    expect(strategy.estimateCost(parseTdfolFormula('always(eventually(Pred(x)))'))).toBe(4);
  });

  it('proves implication chains by reducing goals backward', () => {
    const strategy = new TdfolBackwardChainingStrategy();
    const result = strategy.prove(parseTdfolFormula('Eligible(x)'), {
      axioms: [
        parseTdfolFormula('Resident(x)'),
        parseTdfolFormula('Resident(x) -> Tenant(x)'),
        parseTdfolFormula('Tenant(x) -> Eligible(x)'),
      ],
    });

    expect(result).toMatchObject({
      status: 'proved',
      method: 'backward_chaining',
    });
    expect(result.steps.map((step) => step.rule)).toEqual([
      'KnowledgeBaseLookup',
      'BackwardModusPonens',
      'BackwardModusPonens',
    ]);
  });

  it('proves conjunction goals as paired backward subgoals', () => {
    const strategy = new TdfolBackwardChainingStrategy();
    const result = strategy.prove(parseTdfolFormula('Resident(x) and Tenant(x)'), {
      axioms: [parseTdfolFormula('Resident(x)'), parseTdfolFormula('Tenant(x)')],
    });

    expect(result).toMatchObject({
      status: 'proved',
      method: 'backward_chaining',
    });
    expect(result.steps.at(-1)).toMatchObject({
      rule: 'ConjunctionIntroduction',
      conclusion: '(Resident(x)) ∧ (Tenant(x))',
    });
  });

  it('falls back to forward proof search in bidirectional mode', () => {
    const strategy = new TdfolBidirectionalStrategy({
      forward: new TdfolForwardChainingStrategy({
        rules: [TemporalKAxiomRule, TemporalTAxiomRule],
      }),
    });
    const result = strategy.prove(parseTdfolFormula('Goal(x)'), {
      axioms: [
        parseTdfolFormula('always(Pred(x) -> Goal(x))'),
        parseTdfolFormula('always(Pred(x))'),
      ],
    });

    expect(result).toMatchObject({
      status: 'proved',
      method: 'bidirectional',
      theorem: 'Goal(x)',
    });
  });

  it('includes backward and bidirectional strategies in the default browser-native selector', () => {
    const selector = new TdfolStrategySelector();
    const info = selector.getStrategyInfo(parseTdfolFormula('Goal(x)'), {
      axioms: [parseTdfolFormula('Pred(x)'), parseTdfolFormula('Pred(x) -> Goal(x)')],
    });

    expect(info.map((entry) => entry.type)).toEqual([
      'modal_tableaux',
      'bidirectional',
      'forward_chaining',
      'cec_delegate',
      'backward_chaining',
    ]);
    expect(
      selector.selectStrategy(parseTdfolFormula('Goal(x)'), {
        axioms: [parseTdfolFormula('Pred(x)'), parseTdfolFormula('Pred(x) -> Goal(x)')],
      }).strategyType,
    ).toBe('bidirectional');
  });

  it('translates TDFOL formulas to browser-native CEC expressions for delegation', () => {
    expect(tdfolToCecExpression(parseTdfolFormula('always(O(Comply(x)))'))).toEqual({
      kind: 'unary',
      operator: 'always',
      expression: {
        kind: 'unary',
        operator: 'O',
        expression: {
          kind: 'application',
          name: 'Comply',
          args: [{ kind: 'atom', name: 'x' }],
        },
      },
    });
  });

  it('uses the local CEC delegate for deontic equivalence without server calls', () => {
    const strategy = new TdfolCecDelegateStrategy({ delegate: new TdfolLocalCecDelegate() });
    const result = strategy.prove(parseTdfolFormula('F(Enter(x))'), {
      axioms: [parseTdfolFormula('O(not Enter(x))')],
    });

    expect(result).toMatchObject({
      status: 'proved',
      method: 'cec_delegate',
    });
    expect(result.steps.map((step) => step.rule)).toEqual([
      'CecKnowledgeBaseLookup',
      'CecDeonticProhibitionEquivalence',
    ]);
    expect(result.steps.at(-1)?.conclusion).toBe('(F (Enter x))');
  });

  it('returns explicit unknown results when the local CEC delegate cannot justify a proof', () => {
    const strategy = new TdfolCecDelegateStrategy();

    expect(
      strategy.prove(parseTdfolFormula('O(Comply(x))'), {
        axioms: [parseTdfolFormula('Permit(x)')],
      }),
    ).toMatchObject({
      status: 'unknown',
      method: 'cec_delegate',
    });
  });
});

function fakeStrategy(
  name: string,
  priority: number,
  cost: number,
  proved: boolean,
): TdfolProverStrategy {
  return {
    name,
    strategyType: 'forward_chaining',
    canHandle: () => true,
    prove: (formula): ProofResult => ({
      status: proved ? 'proved' : 'unknown',
      theorem: String(formula),
      steps: [],
      method: name,
    }),
    getPriority: () => priority,
    estimateCost: () => cost,
  };
}

class FixtureBaseStrategy extends TdfolBaseProverStrategy {
  constructor() {
    super({
      name: 'Fixture Base Strategy',
      strategyType: 'forward_chaining',
      priority: 42,
      defaultTimeoutMs: 250,
    });
  }

  prove(
    formula: ReturnType<typeof parseTdfolFormula>,
    kb: { axioms: ReturnType<typeof parseTdfolFormula>[] },
  ): ProofResult {
    const start = performance.now();
    return this.finishResult(
      'proved',
      formula,
      [this.createStep(1, 'FixtureLookup', kb.axioms.slice(0, 1), formula, 'Fixture base proof')],
      start,
    );
  }
}

class InvalidBaseStrategy extends TdfolBaseProverStrategy {
  constructor() {
    super({ name: ' ', strategyType: 'forward_chaining' });
  }

  prove(formula: ReturnType<typeof parseTdfolFormula>): ProofResult {
    return this.finishResult('unknown', formula, [], performance.now());
  }
}

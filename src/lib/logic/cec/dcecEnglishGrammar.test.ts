import {
  DcecConnectiveFormula,
  DcecDeonticFormula,
} from './dcecCore';
import { createDcecEnglishGrammar } from './dcecEnglishGrammar';
import {
  DcecDeonticOperator,
  DcecLogicalConnective,
} from './dcecTypes';

describe('DCEC English grammar parity facade', () => {
  it('sets up browser-native DCEC lexicon entries and compositional rules', () => {
    const grammar = createDcecEnglishGrammar();

    expect(grammar.engine.lexicon.get('must')?.[0].category).toBe('V');
    expect(grammar.engine.lexicon.get('always')?.[0].category).toBe('Adv');
    expect(grammar.engine.lexicon.get('alice')?.[0].category).toBe('Agent');
    expect(grammar.getRuleNames()).toEqual(expect.arrayContaining([
      'agent_action_rule',
      'obligated_rule',
      'believes_rule',
      'always_rule',
      'and_rule',
      'implies_rule',
    ]));
  });

  it('parses built-in English fragments with the local grammar engine', () => {
    const grammar = createDcecEnglishGrammar();

    expect(grammar.parseToDcec('alice laugh')?.toString()).toBe('laugh(alice:Agent)');
    expect(grammar.parseToDcec('alice must laugh')?.toString()).toBe('O[alice:Agent](laugh(alice:Agent))');
    expect(grammar.parseToDcec('always alice laugh')?.toString()).toBe('□(laugh(alice:Agent))');
    expect(grammar.parseToDcec('alice laugh and bob sleep')?.toString()).toBe('(laugh(alice:Agent) ∧ sleep(bob:Agent))');
  });

  it('falls back to dependency-free pattern parsing for domain vocabulary', () => {
    const grammar = createDcecEnglishGrammar();

    expect(grammar.parseToDcec('tenant must pay rent')?.toString()).toBe('O[tenant:Agent](pay_rent(tenant:Agent))');
    expect(grammar.parseToDcec('tenant knows that landlord may enter')?.toString()).toBe('K(tenant:Agent, P[landlord:Agent](enter(landlord:Agent)))');
    expect(grammar.parseToDcec('if tenant must pay then landlord may enter')?.toString()).toBe('(O[tenant:Agent](pay(tenant:Agent)) → P[landlord:Agent](enter(landlord:Agent)))');
  });

  it('converts semantic records to DCEC formulas across modalities', () => {
    const grammar = createDcecEnglishGrammar();

    const formula = grammar.semanticToFormula({
      type: 'connective',
      operator: DcecLogicalConnective.IMPLIES,
      left: {
        type: 'deontic',
        operator: 'obligated',
        agent: { type: 'agent', name: 'tenant' },
        action: { type: 'action', name: 'pay' },
      },
      right: {
        type: 'temporal',
        operator: 'eventually',
        proposition: {
          type: 'cognitive',
          operator: 'knows',
          agent: { type: 'agent', name: 'landlord' },
          proposition: {
            type: 'atomic',
            predicate: 'notice',
            arguments: [{ type: 'agent', name: 'tenant' }],
          },
        },
      },
    });

    expect(formula?.toString()).toBe('(O[tenant:Agent](pay(tenant:Agent)) → ◊(K(landlord:Agent, notice(tenant:Agent))))');
  });

  it('round-trips DCEC formulas through English semantic records', () => {
    const grammar = createDcecEnglishGrammar();
    const formula = grammar.parseToDcec('tenant must pay') as DcecDeonticFormula;
    const implication = new DcecConnectiveFormula(DcecLogicalConnective.IMPLIES, [
      formula,
      grammar.parseToDcec('landlord may enter')!,
    ]);

    expect(grammar.formulaToSemantic(formula)).toMatchObject({
      type: 'deontic',
      operator: DcecDeonticOperator.OBLIGATION,
      agent: { name: 'tenant' },
      formula: { type: 'atomic', predicate: 'pay' },
    });
    expect(grammar.formulaToEnglish(formula)).toBe('It is obligatory that tenant pay');
    expect(grammar.formulaToEnglish(implication)).toBe('if It is obligatory that tenant pay then It is permitted that landlord enter');
  });

  it('linearizes Python-style semantic dictionaries', () => {
    const grammar = createDcecEnglishGrammar();

    expect(grammar.linearizeBoolean({
      type: 'connective',
      operator: DcecLogicalConnective.AND,
      left: { type: 'atomic', predicate: 'pay', arguments: [{ type: 'agent', name: 'tenant' }] },
      right: { type: 'deontic', operator: 'forbidden', agent: { type: 'agent', name: 'landlord' }, action: { type: 'action', name: 'enter' } },
    })).toBe('(tenant pay and landlord is forbidden to enter)');
  });
});

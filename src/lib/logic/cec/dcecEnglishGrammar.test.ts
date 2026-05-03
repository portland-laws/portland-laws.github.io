import { DcecConnectiveFormula, DcecDeonticFormula } from './dcecCore';
import {
  createDcecEnglishGrammar,
  getDcecNativeEnglishGrammarCapabilities,
  parseDcecNativeEnglishGrammar,
} from './dcecEnglishGrammar';
import { createEngDcecWrapper, parseEnglishToDcec } from './dcecEnglishWrapper';
import { DcecDeonticOperator, DcecLogicalConnective } from './dcecTypes';

describe('DCEC English grammar parity facade', () => {
  it('sets up browser-native DCEC lexicon entries and compositional rules', () => {
    const grammar = createDcecEnglishGrammar();

    expect(grammar.engine.lexicon.get('must')?.[0].category).toBe('V');
    expect(grammar.engine.lexicon.get('always')?.[0].category).toBe('Adv');
    expect(grammar.engine.lexicon.get('alice')?.[0].category).toBe('Agent');
    expect(grammar.getRuleNames()).toEqual(
      expect.arrayContaining([
        'agent_action_rule',
        'obligated_rule',
        'believes_rule',
        'always_rule',
        'and_rule',
        'implies_rule',
      ]),
    );
  });

  it('parses built-in English fragments with the local grammar engine', () => {
    const grammar = createDcecEnglishGrammar();

    expect(grammar.parseToDcec('alice laugh')?.toString()).toBe('laugh(alice:Agent)');
    expect(grammar.parseToDcec('alice must laugh')?.toString()).toBe(
      'O[alice:Agent](laugh(alice:Agent))',
    );
    expect(grammar.parseToDcec('always alice laugh')?.toString()).toBe('□(laugh(alice:Agent))');
    expect(grammar.parseToDcec('alice laugh and bob sleep')?.toString()).toBe(
      '(laugh(alice:Agent) ∧ sleep(bob:Agent))',
    );
  });

  it('falls back to dependency-free pattern parsing for domain vocabulary', () => {
    const grammar = createDcecEnglishGrammar();

    expect(grammar.parseToDcec('tenant must pay rent')?.toString()).toBe(
      'O[tenant:Agent](pay_rent(tenant:Agent))',
    );
    expect(grammar.parseToDcec('tenant knows that landlord may enter')?.toString()).toBe(
      'K(tenant:Agent, P[landlord:Agent](enter(landlord:Agent)))',
    );
    expect(grammar.parseToDcec('if tenant must pay then landlord may enter')?.toString()).toBe(
      '(O[tenant:Agent](pay(tenant:Agent)) → P[landlord:Agent](enter(landlord:Agent)))',
    );
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

    expect(formula?.toString()).toBe(
      '(O[tenant:Agent](pay(tenant:Agent)) → ◊(K(landlord:Agent, notice(tenant:Agent))))',
    );
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
    expect(grammar.formulaToEnglish(implication)).toBe(
      'if It is obligatory that tenant pay then It is permitted that landlord enter',
    );
  });

  it('linearizes Python-style semantic dictionaries', () => {
    const grammar = createDcecEnglishGrammar();

    expect(
      grammar.linearizeBoolean({
        type: 'connective',
        operator: DcecLogicalConnective.AND,
        left: { type: 'atomic', predicate: 'pay', arguments: [{ type: 'agent', name: 'tenant' }] },
        right: {
          type: 'deontic',
          operator: 'forbidden',
          agent: { type: 'agent', name: 'landlord' },
          action: { type: 'action', name: 'enter' },
        },
      }),
    ).toBe('(tenant pay and landlord is forbidden to enter)');
  });

  it('wraps eng_dcec_wrapper.py behavior in a browser-native deterministic facade', () => {
    const wrapper = createEngDcecWrapper();
    const result = wrapper.parse('Tenant must pay rent');

    expect(result.ok).toBe(true);
    expect(result.dcec).toBe('O[tenant:Agent](pay_rent(tenant:Agent))');
    expect(result.semantic).toMatchObject({
      type: 'deontic',
      operator: DcecDeonticOperator.OBLIGATION,
      agent: { name: 'tenant' },
    });
    expect(result.metadata).toEqual({
      sourcePythonModule: 'logic/CEC/eng_dcec_wrapper.py',
      runtime: 'browser-native-typescript',
      implementation: 'deterministic-dcec-english-grammar',
    });
    expect(wrapper.formulaToEnglish(result.formula!)).toBe('It is obligatory that tenant pay_rent');
  });

  it('reports fail-closed wrapper validation errors without external runtimes', () => {
    const wrapper = createEngDcecWrapper({ maxInputLength: 12 });
    const capabilities = wrapper.getCapabilities();

    expect(wrapper.parse('   ')).toMatchObject({ ok: false, errors: ['Input must not be empty'] });
    expect(wrapper.parse('tenant must pay rent')).toMatchObject({
      ok: false,
      errors: ['Input exceeds maximum length of 12 characters'],
    });
    expect(capabilities).toMatchObject({
      browserNative: true,
      pythonRuntime: false,
      serverRuntime: false,
      filesystem: false,
      subprocess: false,
      rpc: false,
      implementation: 'deterministic-typescript',
      pythonModule: 'logic/CEC/eng_dcec_wrapper.py',
    });
  });

  it('exposes a convenience parseEnglishToDcec contract for validation suites', () => {
    const result = parseEnglishToDcec('if tenant must pay then landlord may enter');

    expect(result.ok).toBe(true);
    expect(result.dcec).toBe(
      '(O[tenant:Agent](pay(tenant:Agent)) → P[landlord:Agent](enter(landlord:Agent)))',
    );
    expect(result.english).toBe(
      'if It is obligatory that tenant pay then It is permitted that landlord enter',
    );
  });

  it('ports native dcec_english_grammar.py as a fail-closed browser-native contract', () => {
    const capabilities = getDcecNativeEnglishGrammarCapabilities();
    const parsed = parseDcecNativeEnglishGrammar('Tenant must pay rent');
    const rejected = parseDcecNativeEnglishGrammar('tenant must pay rent', { maxInputLength: 10 });

    expect(capabilities).toEqual({
      browserNative: true,
      pythonRuntime: false,
      serverRuntime: false,
      filesystem: false,
      subprocess: false,
      rpc: false,
      wasmCompatible: true,
      wasmRequired: false,
      implementation: 'deterministic-typescript',
      pythonModule: 'logic/CEC/native/dcec_english_grammar.py',
    });
    expect(parsed).toMatchObject({
      ok: true,
      normalizedInput: 'tenant must pay rent',
      dcec: 'O[tenant:Agent](pay_rent(tenant:Agent))',
      metadata: {
        sourcePythonModule: 'logic/CEC/native/dcec_english_grammar.py',
        runtime: 'browser-native-typescript',
        implementation: 'deterministic-dcec-english-grammar',
      },
    });
    expect(parsed.ruleNames).toEqual(expect.arrayContaining(['obligated_rule', 'implies_rule']));
    expect(parsed.lexicalWords).toEqual(expect.arrayContaining(['must', 'always']));
    expect(parsed.semantic).toMatchObject({
      type: 'deontic',
      operator: DcecDeonticOperator.OBLIGATION,
      agent: { name: 'tenant' },
    });
    expect(rejected).toMatchObject({
      ok: false,
      errors: ['Input exceeds maximum length of 10 characters'],
      metadata: { sourcePythonModule: 'logic/CEC/native/dcec_english_grammar.py' },
    });
  });
});

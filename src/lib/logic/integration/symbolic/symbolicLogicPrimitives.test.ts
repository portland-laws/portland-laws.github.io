import {
  BrowserNativeLogicSymbol,
  SYMBOLIC_LOGIC_PRIMITIVES_METADATA,
  create_logic_symbol,
  get_available_primitives,
} from './symbolicLogicPrimitives';
import {
  INTEGRATION_SYMBOLIC_LOGIC_PRIMITIVES_METADATA,
  create_logic_symbol as create_root_logic_symbol,
  get_available_primitives as get_root_available_primitives,
} from '../symbolicLogicPrimitives';

describe('symbolic logic primitives browser-native parity', () => {
  it('creates local logic symbols and converts deterministic FOL formats', () => {
    const symbol = create_logic_symbol('All cats are animals');
    expect(symbol).toMatchObject({
      value: 'All cats are animals',
      semantic: true,
      metadata: {
        sourcePythonModule: 'logic/integration/symbolic/symbolic_logic_primitives.py',
        serverCallsAllowed: false,
        pythonRuntimeAllowed: false,
      },
    });
    expect(symbol.to_fol().value).toBe('∀x (Cats(x) → Animals(x))');
    expect(symbol.to_fol('prolog').value).toContain('forall(X,');
    expect(create_logic_symbol('Some birds can fly').to_fol('tptp').value).toBe(
      '? [X]: (Birds(x)  &  Fly(x))',
    );
  });

  it('extracts primitives and performs local symbolic operations', () => {
    const symbol = new BrowserNativeLogicSymbol(
      'Every tenant must pay rent and some tenants can request repairs.',
    );
    const premise = create_logic_symbol('Fluffy is a cat');
    const conclusion = create_logic_symbol('Fluffy is an animal');
    const analysis = JSON.parse(
      create_logic_symbol('If it rains then the ground is wet').analyze_logical_structure().value,
    );
    expect(symbol.extract_quantifiers().value).toContain('universal:Every');
    expect(symbol.extract_quantifiers().value).toContain('existential:some');
    expect(symbol.extract_predicates().value).toBe('must, can');
    expect(premise.logical_and(conclusion).value).toBe('(Fluffy is a cat) ∧ (Fluffy is an animal)');
    expect(premise.implies(conclusion).value).toBe('(Fluffy is a cat) → (Fluffy is an animal)');
    expect(premise.negate().value).toBe('¬(Fluffy is a cat)');
    expect(analysis).toMatchObject({ type: 'conditional', hasConnectives: true });
    expect(create_logic_symbol('  (  A   ∧   B  )  ').simplify_logic().value).toBe('(A ∧ B)');
    expect(get_available_primitives()).toEqual(expect.arrayContaining(['to_fol', 'implies']));
    expect(SYMBOLIC_LOGIC_PRIMITIVES_METADATA).toMatchObject({ runtimeDependencies: [] });
  });

  it('exposes the root integration Python module without runtime fallbacks', () => {
    const symbol = create_root_logic_symbol('All lessees are tenants');
    const result = symbol.to_fol();
    const analysis = JSON.parse(symbol.analyze_logical_structure().value);

    expect(symbol.metadata).toMatchObject({
      sourcePythonModule: 'logic/integration/symbolic_logic_primitives.py',
      implementationModule: 'logic/integration/symbolic/symbolic_logic_primitives.py',
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
      runtimeDependencies: [],
    });
    expect(result.metadata.sourcePythonModule).toBe(
      'logic/integration/symbolic_logic_primitives.py',
    );
    expect(result.value).toBe('∀x (Lessees(x) → Tenants(x))');
    expect(analysis).toMatchObject({ type: 'universal', hasQuantifiers: true });
    expect(get_root_available_primitives()).toEqual(
      expect.arrayContaining(['to_fol', 'extract_quantifiers', 'simplify_logic']),
    );
    expect(INTEGRATION_SYMBOLIC_LOGIC_PRIMITIVES_METADATA.parity).toEqual(
      expect.arrayContaining(['root_integration_module_compatibility']),
    );
  });
});

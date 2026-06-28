import {
  DCEC_PROTOTYPES_METADATA,
  DcecPrototypeNamespace,
  invokeDcecPrototypeOperation,
} from './dcecPrototypes';

describe('DCEC prototype namespace', () => {
  it('adds sorts from code and text with inheritance checks', () => {
    const namespace = new DcecPrototypeNamespace();

    expect(namespace.addCodeSort('Object')).toBe(true);
    expect(namespace.addCodeSort('Agent', ['Object'])).toBe(true);
    expect(namespace.addCodeSort('Human', ['Agent'])).toBe(true);
    expect(namespace.addCodeSort('Bad', ['Missing'])).toBe(false);
    expect(namespace.addTextSort('(typedef Organization Agent)')).toBe(true);
    expect(namespace.sorts).toMatchObject({
      Object: [],
      Agent: ['Object'],
      Human: ['Agent'],
      Organization: ['Agent'],
    });
  });

  it('adds function prototypes and preserves distinct overloads', () => {
    const namespace = new DcecPrototypeNamespace();
    namespace.addCodeSort('Object');
    namespace.addCodeSort('Boolean', ['Object']);
    namespace.addCodeSort('Agent', ['Object']);

    expect(namespace.addCodeFunction('knows', 'Boolean', ['Agent', 'Boolean'])).toBe(true);
    expect(namespace.addCodeFunction('knows', 'Boolean', ['Agent', 'Boolean'])).toBe(true);
    expect(namespace.addCodeFunction('knows', 'Boolean', ['Agent', 'Agent'])).toBe(true);
    expect(namespace.functions.knows).toEqual([
      ['Boolean', ['Agent', 'Boolean']],
      ['Boolean', ['Agent', 'Agent']],
    ]);

    expect(namespace.addTextFunction('(Boolean believes Agent Boolean)')).toBe(true);
    expect(namespace.functions.believes).toEqual([['Boolean', ['Agent', 'Boolean']]]);
    expect(namespace.addCodeFunction('broken', 'Boolean', ['Missing'])).toBe(false);
  });

  it('adds atomic prototypes and rejects conflicting atomic overloads', () => {
    const namespace = new DcecPrototypeNamespace();
    namespace.addCodeSort('Object');
    namespace.addCodeSort('Agent', ['Object']);
    namespace.addCodeSort('Action', ['Object']);

    expect(namespace.addCodeAtomic('alice', 'Agent')).toBe(true);
    expect(namespace.addCodeAtomic('alice', 'Agent')).toBe(true);
    expect(namespace.addCodeAtomic('alice', 'Action')).toBe(false);
    expect(namespace.addTextAtomic('(Action appeal)')).toBe(true);
    expect(namespace.findAtomicType('appeal')).toBe('Action');
    expect(namespace.addCodeAtomic('ghost', 'Missing')).toBe(false);
  });

  it('rejects overlapping function prototypes with conflicting return types', () => {
    const namespace = new DcecPrototypeNamespace();
    namespace.addCodeSort('Object');
    namespace.addCodeSort('Boolean', ['Object']);
    namespace.addCodeSort('Numeric', ['Object']);
    namespace.addCodeSort('Agent', ['Object']);
    namespace.addCodeSort('Human', ['Agent']);
    namespace.addCodeSort('Action', ['Object']);

    expect(namespace.addCodeFunction('score', 'Numeric', ['Agent'])).toBe(true);
    expect(namespace.addCodeFunction('score', 'Boolean', ['Human'])).toBe(false);
    expect(namespace.addCodeFunction('score', 'Numeric', ['Human'])).toBe(true);
    expect(namespace.addCodeFunction('score', 'Boolean', ['Action'])).toBe(true);
    expect(namespace.functions.score).toEqual([
      ['Numeric', ['Agent']],
      ['Numeric', ['Human']],
      ['Boolean', ['Action']],
    ]);
  });

  it('validates deterministic Python-parity prototype fixtures', () => {
    const namespace = new DcecPrototypeNamespace();
    namespace.addBasicDcec();
    namespace.addBasicLogic();
    namespace.addBasicNumerics();
    namespace.addCodeSort('Human', ['Agent']);
    namespace.addCodeAtomic('alice', 'Human');
    namespace.addCodeAtomic('contractEvent', 'Event');

    const fixtures = [
      {
        name: 'atomic subclass match',
        actual: namespace.validateAtomic('alice', 'Agent'),
        expected: { ok: true, returnType: 'Human', distance: 1 },
      },
      {
        name: 'atomic type conflict',
        actual: namespace.validateAtomic('contractEvent', 'Agent'),
        expected: { ok: false, issue: 'type_conflict', returnType: 'Event' },
      },
      {
        name: 'function exact overload',
        actual: namespace.validateFunctionCall('happens', ['Event', 'Moment'], 'Boolean'),
        expected: {
          ok: true,
          returnType: 'Boolean',
          overload: ['Boolean', ['Event', 'Moment']],
          distance: 0,
        },
      },
      {
        name: 'function inherited argument match',
        actual: namespace.validateFunctionCall('self', ['Human'], 'Self'),
        expected: {
          ok: true,
          returnType: 'Self',
          overload: ['Self', ['Agent']],
          distance: 1,
        },
      },
      {
        name: 'function arity mismatch',
        actual: namespace.validateFunctionCall('happens', ['Event'], 'Boolean'),
        expected: { ok: false, issue: 'arity_mismatch' },
      },
      {
        name: 'function argument conflict',
        actual: namespace.validateFunctionCall('happens', ['Agent', 'Moment'], 'Boolean'),
        expected: { ok: false, issue: 'type_conflict' },
      },
    ];

    for (const fixture of fixtures) {
      expect(fixture.actual).toEqual(fixture.expected);
    }
  });

  it('loads basic DCEC, logical, and numeric prototypes', () => {
    const namespace = new DcecPrototypeNamespace();
    namespace.addBasicDcec();
    namespace.addBasicLogic();
    namespace.addBasicNumerics();

    expect(namespace.sorts.Object).toEqual([]);
    expect(namespace.sorts.Self).toEqual(['Object', 'Agent']);
    expect(namespace.functions.O).toEqual([['Boolean', ['Agent', 'Moment', 'Boolean', 'Boolean']]]);
    expect(namespace.functions.happens).toEqual([['Boolean', ['Event', 'Moment']]]);
    expect(namespace.functions.or).toEqual([['Boolean', ['Boolean', 'Boolean']]]);
    expect(namespace.functions.lessOrEqual).toEqual([
      ['Boolean', ['Moment', 'Moment']],
      ['Boolean', ['Numeric', 'Numeric']],
    ]);
  });

  it('checks Python-compatible inheritance conflicts and wildcard matches', () => {
    const namespace = new DcecPrototypeNamespace();
    namespace.addCodeSort('Object');
    namespace.addCodeSort('Agent', ['Object']);
    namespace.addCodeSort('Human', ['Agent']);

    expect(namespace.noConflict('?', 'Anything')).toEqual([true, 0]);
    expect(namespace.noConflict('Human', 'Human')).toEqual([true, 0]);
    expect(namespace.noConflict('Human', 'Agent')).toEqual([true, 1]);
    expect(namespace.noConflict('Human', 'Object')).toEqual([true, 2]);
    expect(namespace.noConflict('Agent', 'Human')).toEqual([false, 0]);
  });

  it('reports statistics and printable snapshots', () => {
    const namespace = new DcecPrototypeNamespace();
    namespace.addBasicDcec();
    namespace.addBasicLogic();
    namespace.addCodeAtomic('alice', 'Agent');

    expect(namespace.getStatistics()).toEqual({
      sorts: 11,
      functions: 26,
      atomics: 1,
      function_overloads: 26,
    });
    expect(namespace.snapshot()).toContain('=== Sorts ===');
    expect(namespace.snapshot()).toContain('alice: Agent');
  });

  it('invokes browser-native prototype operations and fails closed for unsupported requests', () => {
    const namespace = new DcecPrototypeNamespace();

    expect(namespace.metadata).toBe(DCEC_PROTOTYPES_METADATA);
    expect(DCEC_PROTOTYPES_METADATA).toMatchObject({
      sourcePythonModule: 'logic/CEC/native/dcec_prototypes.py',
      browserNative: true,
      pythonRuntime: false,
      serverRuntime: false,
      subprocess: false,
      rpc: false,
    });

    for (const request of [
      { operation: 'addSort', name: 'Object' },
      { operation: 'addSort', expression: '(typedef Agent Object)' },
      { operation: 'addSort', expression: '(typedef Boolean Object)' },
      { operation: 'addFunction', expression: '(Boolean believes Agent Boolean)' },
      { operation: 'addAtomic', expression: '(Agent alice)' },
    ] as const) {
      expect(invokeDcecPrototypeOperation(namespace, request)).toMatchObject({
        ok: true,
        errors: [],
      });
    }

    expect(
      invokeDcecPrototypeOperation(namespace, {
        operation: 'validateFunction',
        name: 'believes',
        argumentTypes: ['Agent', 'Boolean'],
        expectedReturnType: 'Boolean',
      }),
    ).toMatchObject({
      ok: true,
      validation: {
        ok: true,
        returnType: 'Boolean',
        overload: ['Boolean', ['Agent', 'Boolean']],
      },
      metadata: DCEC_PROTOTYPES_METADATA,
    });
    expect(invokeDcecPrototypeOperation(namespace, { operation: 'nativePythonBridge' })).toEqual({
      ok: false,
      errors: ['Unsupported browser-native DCEC prototype operation: nativePythonBridge'],
      metadata: DCEC_PROTOTYPES_METADATA,
    });
  });
});

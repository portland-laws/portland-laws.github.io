import { DcecPrototypeNamespace } from './dcecPrototypes';

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
});

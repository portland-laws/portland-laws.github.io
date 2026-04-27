import {
  DcecParseToken,
  prefixDcecEmdas,
  prefixDcecLogicalFunctions,
  replaceDcecSynonyms,
} from './dcecParsing';

describe('DCEC parsing utilities', () => {
  it('creates Python-compatible parse token expressions and measurements', () => {
    const token = new DcecParseToken('and', [
      'a',
      new DcecParseToken('not', ['b']),
      new DcecParseToken('or', ['c', 'd']),
    ]);

    expect(token.depthOf()).toBe(2);
    expect(token.widthOf()).toBe(4);
    expect(token.createSExpression()).toBe('(and a (not b) (or c d))');
    expect(token.createFExpression()).toBe('and(a,not(b),or(c,d))');
    expect(String(token)).toBe('and(a,not(b),or(c,d))');
  });

  it('replaces common DCEC spelling variants and synonyms', () => {
    const nested = new DcecParseToken('wrapper', ['forall', 'Time', 'ifAndOnlyIf']);
    const result = replaceDcecSynonyms(['ForAll', 'Exists', nested]);

    expect(result[0]).toBe('forAll');
    expect(result[1]).toBe('exists');
    expect(result[2]).toBeInstanceOf(DcecParseToken);
    expect((result[2] as DcecParseToken).args).toEqual(['forAll', 'Moment', 'iff']);
  });

  it('prefixes unary and infix logical functions in Python rule order', () => {
    const atomics: Record<string, string[]> = {};
    const unary = prefixDcecLogicalFunctions(['not', 'p'], { atomics });
    const infix = prefixDcecLogicalFunctions(['a', 'and', 'b', 'implies', 'c'], { atomics });

    expect((unary[0] as DcecParseToken).createSExpression()).toBe('(not p)');
    expect((infix[0] as DcecParseToken).createSExpression()).toBe('(implies (and a b) c)');
    expect(atomics).toEqual({
      p: ['Boolean'],
      a: ['Boolean'],
      b: ['Boolean'],
      c: ['Boolean'],
    });
  });

  it('leaves non-infix logical argument lists unchanged', () => {
    expect(prefixDcecLogicalFunctions(['and', 'a', 'b'])).toEqual(['and', 'a', 'b']);
    expect(prefixDcecLogicalFunctions(['a', 'b'])).toEqual(['a', 'b']);
  });

  it('prefixes unary and infix arithmetic functions with numeric sort tracking', () => {
    const atomics: Record<string, string[]> = {};
    const unary = prefixDcecEmdas(['negate', 'x'], { atomics });
    const infix = prefixDcecEmdas(['x', 'add', 'y', 'divide', 'z'], { atomics });

    expect((unary[0] as DcecParseToken).createFExpression()).toBe('negate(x)');
    expect((infix[0] as DcecParseToken).createFExpression()).toBe('add(x,divide(y,z))');
    expect(atomics).toEqual({
      x: ['Numeric', 'Numeric'],
      y: ['Numeric'],
      z: ['Numeric'],
    });
  });
});

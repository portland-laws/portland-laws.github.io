import {
  checkDcecParens,
  cleanDcecExpression,
  consolidateDcecParens,
  functorizeDcecSymbols,
  getMatchingDcecCloseParen,
  removeDcecSemicolonComments,
  stripDcecComments,
  stripDcecWhitespace,
  tuckDcecFunctions,
} from './dcecCleaning';

describe('DCEC cleaning utilities', () => {
  it('normalizes whitespace, commas, and bracket spacing', () => {
    expect(stripDcecWhitespace('  ( a  b  c )  ')).toBe('(a,b,c)');
    expect(stripDcecWhitespace('func( arg1 , arg2 )')).toBe('func(arg1,arg2)');
    expect(stripDcecWhitespace('[x] (a)(b)')).toBe(',[x],(a),(b)');
  });

  it('strips hash and semicolon comments independently', () => {
    expect(stripDcecComments('(and a b) # comment')).toBe('(and a b) ');
    expect(stripDcecComments('no comment')).toBe('no comment');
    expect(removeDcecSemicolonComments('(and a b) ; comment')).toBe('(and a b) ');
    expect(removeDcecSemicolonComments('no comment')).toBe('no comment');
  });

  it('checks and locates matching parentheses', () => {
    expect(checkDcecParens('(and a b)')).toBe(true);
    expect(checkDcecParens('(and a b')).toBe(false);
    expect(getMatchingDcecCloseParen('(a (b c) d)', 0)).toBe(10);
    expect(getMatchingDcecCloseParen('(a (b c) d)', 3)).toBe(7);
    expect(getMatchingDcecCloseParen('(a (b c)', 0)).toBeUndefined();
  });

  it('consolidates redundant parentheses and preserves meaningful grouping', () => {
    expect(consolidateDcecParens('((a))')).toBe('(a)');
    expect(consolidateDcecParens('((and a b))')).toBe('(and a b)');
    expect(consolidateDcecParens('(and (a) (b))')).toBe('(and a b)');
  });

  it('tucks F-expression function calls into S-expression-style notation', () => {
    expect(tuckDcecFunctions('B(a,b)')).toBe('(B,a,b)');
    expect(tuckDcecFunctions('Event(e1)')).toBe('(Event,e1)');
    expect(tuckDcecFunctions('not(P)')).toBe('(not,(P))');
  });

  it('functorizes symbolic operators with Python-compatible replacements', () => {
    expect(functorizeDcecSymbols('a -> b')).toBe('a  implies  b');
    expect(functorizeDcecSymbols('x + y')).toBe('x  add  y');
    expect(functorizeDcecSymbols('~p')).toBe(' not p');
  });

  it('runs the standard cleaning pipeline', () => {
    expect(cleanDcecExpression('  ((and a b)) # comment')).toBe('(and,a,b)');
  });
});

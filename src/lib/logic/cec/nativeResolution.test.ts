import { formatCecExpression } from './formatter';
import { parseCecExpression } from './parser';
import {
  CecResolutionRule,
  CecUnitResolutionRule,
  applyCecResolution,
  resolveCecClauses,
  resolveCecUnitClauses,
} from './nativeResolution';

const parse = (source: string) => parseCecExpression(source);
const format = (source: string) => formatCecExpression(parse(source));

describe('CEC native resolution inference rules', () => {
  it('builds a resolvent from complementary literals across clauses', () => {
    const result = resolveCecClauses(parse('(or P Q)'), parse('(or (not P) R)'));

    expect(result).not.toBeNull();
    expect(result?.rule).toBe('resolution');
    expect(result?.tautology).toBe(false);
    expect(result?.emptyClause).toBe(false);
    expect(formatCecExpression(result!.resolvent)).toBe(format('(or Q R)'));
    expect(formatCecExpression(result!.complement.leftLiteral)).toBe(format('P'));
    expect(formatCecExpression(result!.complement.rightLiteral)).toBe(format('(not P)'));
  });

  it('supports unit resolution when either input is a unit clause', () => {
    const result = resolveCecUnitClauses(parse('(not P)'), parse('(or P Q)'));

    expect(result).not.toBeNull();
    expect(result?.rule).toBe('unit_resolution');
    expect(result?.tautology).toBe(false);
    expect(formatCecExpression(result!.resolvent)).toBe(format('Q'));
  });

  it('rejects unit resolution when neither input is unit', () => {
    const result = CecUnitResolutionRule.resolve(parse('(or P Q)'), parse('(or (not P) R)'));

    expect(result).toBeNull();
  });

  it('marks tautological resolvents and fail-closes apply helpers', () => {
    const result = CecResolutionRule.resolve(parse('(or P Q)'), parse('(or (not P) (not Q))'));

    expect(result).not.toBeNull();
    expect(result?.tautology).toBe(true);
    expect(() => CecResolutionRule.apply(parse('(or P Q)'), parse('(or (not P) (not Q))'))).toThrow(
      'tautological resolvent',
    );
  });

  it('detects empty clauses when complementary unit clauses resolve', () => {
    const result = resolveCecClauses(parse('P'), parse('(not P)'));

    expect(result).not.toBeNull();
    expect(result?.emptyClause).toBe(true);
    expect(formatCecExpression(result!.resolvent)).toBe(format('false'));
  });

  it('fails closed when no complementary pair exists', () => {
    expect(resolveCecClauses(parse('(or P Q)'), parse('(or R S)'))).toBeNull();
    expect(() => applyCecResolution(parse('(or P Q)'), parse('(or R S)'))).toThrow(
      'complementary literal',
    );
  });
});

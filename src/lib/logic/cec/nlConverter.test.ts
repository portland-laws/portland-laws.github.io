import {
  DcecNaturalLanguageConverter,
  DcecPatternMatcher,
  createEnhancedDcecNlConverter,
  linearizeDcecWithGrammar,
  parseDcecWithGrammar,
} from './nlConverter';
import { DcecNamespace } from './dcecNamespace';

describe('DCEC natural language converter parity helpers', () => {
  it('converts deontic patterns with prohibition ordered before obligation', () => {
    const converter = new DcecNaturalLanguageConverter();

    const obligation = converter.convertToDcec('tenant must pay');
    const prohibition = converter.convertToDcec('tenant must not smoke');
    const permission = converter.convertToDcec('tenant may enter');

    expect(obligation.success).toBe(true);
    expect(obligation.dcec_formula?.toString()).toBe('O(pay(tenant:Agent))');
    expect(prohibition.dcec_formula?.toString()).toBe('F(smoke(tenant:Agent))');
    expect(permission.dcec_formula?.toString()).toBe('P(enter(tenant:Agent))');
  });

  it('converts cognitive patterns before nested deontic patterns', () => {
    const converter = new DcecNaturalLanguageConverter();

    const result = converter.convertToDcec('tenant believes that tenant must pay');

    expect(result.success).toBe(true);
    expect(result.confidence).toBe(0.7);
    expect(result.parse_method).toBe('pattern_matching');
    expect(result.dcec_formula?.toString()).toBe('B(tenant:Agent, O(pay(tenant:Agent)))');
  });

  it('converts temporal and connective patterns recursively', () => {
    const converter = new DcecNaturalLanguageConverter();

    expect(converter.convertToDcec('always tenant must pay').dcec_formula?.toString()).toBe('□(O(pay(tenant:Agent)))');
    expect(converter.convertToDcec('eventually tenant may enter').dcec_formula?.toString()).toBe('◊(P(enter(tenant:Agent)))');
    expect(converter.convertToDcec('if tenant must pay then tenant may enter').dcec_formula?.toString()).toBe('(O(pay(tenant:Agent)) → P(enter(tenant:Agent)))');
    expect(converter.convertToDcec('not tenant may enter').dcec_formula?.toString()).toBe('¬(P(enter(tenant:Agent)))');
  });

  it('falls back to simple atomic predicates and reuses namespace symbols', () => {
    const namespace = new DcecNamespace();
    const matcher = new DcecPatternMatcher(namespace);

    const first = matcher.convert('tenant repairs sink');
    const second = matcher.convert('tenant repairs sink');

    expect(first.toString()).toBe('tenant_repairs_sink(tenant:Agent)');
    expect(second.toString()).toBe('tenant_repairs_sink(tenant:Agent)');
    expect(namespace.getStatistics()).toMatchObject({
      variables: 1,
      predicates: 1,
    });
  });

  it('linearizes DCEC formulas back to English-like text', () => {
    const converter = new DcecNaturalLanguageConverter();
    const formula = converter.convertToDcec('tenant knows that tenant must pay').dcec_formula!;

    expect(converter.convertFromDcec(formula)).toBe('tenant:Agent knows that must pay');
    expect(converter.convertFromDcec(converter.convertToDcec('not tenant may enter').dcec_formula!)).toBe('not may enter');
    expect(converter.convertFromDcec(converter.convertToDcec('if tenant must pay then tenant may enter').dcec_formula!)).toBe('if must pay then may enter');
  });

  it('records conversion history and statistics', () => {
    const converter = new DcecNaturalLanguageConverter();

    expect(converter.getConversionStatistics()).toEqual({ total_conversions: 0 });
    converter.convertToDcec('tenant must pay');
    converter.convertToDcec('tenant may enter');

    expect(converter.conversionHistory).toHaveLength(2);
    expect(converter.getConversionStatistics()).toEqual({
      total_conversions: 2,
      successful: 2,
      failed: 0,
      success_rate: 1,
      average_confidence: 0.7,
    });
    expect(converter.toString()).toBe('NaturalLanguageConverter(conversions=2)');
  });

  it('keeps enhanced grammar hooks local and dependency-free', () => {
    const converter = createEnhancedDcecNlConverter(true);

    expect(converter.useGrammar).toBe(false);
    expect(parseDcecWithGrammar('tenant must pay')).toBeUndefined();
    expect(linearizeDcecWithGrammar(converter.convertToDcec('tenant must pay').dcec_formula!)).toBeUndefined();
  });
});

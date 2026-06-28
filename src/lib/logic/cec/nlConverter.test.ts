import {
  DcecNaturalLanguageConverter,
  DcecPatternMatcher,
  DcecProofCache,
  NaturalLanguageConverter,
  PatternMatcher,
  compileDcecGrammarNlPolicy,
  compileDcecNlToPolicy,
  compileDcecPolicyText,
  createEnhancedDcecNlConverter,
  create_enhanced_nl_converter,
  detectDcecPolicyLanguage,
  getDcecGrammarNlPolicyCompilerCapabilities,
  getDcecNlToPolicyCompilerCapabilities,
  linearizeDcecWithGrammar,
  linearize_with_grammar,
  parseDcecWithGrammar,
  parse_with_grammar,
  proveDcecFormula,
} from './nlConverter';
import {
  CecLanguageDetector,
  detect_language,
  getCecLanguageDetectorCapabilities,
} from './languageDetector';
import { DcecNamespace } from './dcecNamespace';
import { getSpanishParserCapabilities, parseSpanishDcec, parse_spanish } from './spanishParser';

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

    expect(converter.convertToDcec('always tenant must pay').dcec_formula?.toString()).toBe(
      '□(O(pay(tenant:Agent)))',
    );
    expect(converter.convertToDcec('eventually tenant may enter').dcec_formula?.toString()).toBe(
      '◊(P(enter(tenant:Agent)))',
    );
    expect(
      converter.convertToDcec('if tenant must pay then tenant may enter').dcec_formula?.toString(),
    ).toBe('(O(pay(tenant:Agent)) → P(enter(tenant:Agent)))');
    expect(converter.convertToDcec('not tenant may enter').dcec_formula?.toString()).toBe(
      '¬(P(enter(tenant:Agent)))',
    );
  });

  it('ports spanish_parser.py through browser-native deterministic DCEC patterns', () => {
    expect(getSpanishParserCapabilities()).toMatchObject({
      browserNative: true,
      pythonRuntime: false,
      serverRuntime: false,
      pythonModule: 'logic/CEC/nl/spanish_parser.py',
    });
    expect(parseSpanishDcec('El inquilino debe pagar la renta.')).toMatchObject({
      ok: true,
      success: true,
      english_text: 'tenant must pay rent',
      dcec: 'O(pay_rent(tenant:Agent))',
      parse_method: 'browser_native_spanish_parser',
    });
    expect(
      parse_spanish('Si el inquilino debe pagar la renta entonces el arrendador puede entrar.')
        .dcec,
    ).toBe('(O(pay_rent(tenant:Agent)) → P(enter(landlord:Agent)))');
    expect(parseSpanishDcec('   ')).toMatchObject({
      ok: false,
      fail_closed_reason: 'empty_input',
      browser_native: true,
    });
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
    expect(
      converter.convertFromDcec(converter.convertToDcec('not tenant may enter').dcec_formula!),
    ).toBe('not may enter');
    expect(
      converter.convertFromDcec(
        converter.convertToDcec('if tenant must pay then tenant may enter').dcec_formula!,
      ),
    ).toBe('if must pay then may enter');
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

    expect(converter.useGrammar).toBe(true);
    expect(converter.grammar?.browser_native).toBe(true);
    expect(parseDcecWithGrammar('tenant must pay')?.toString()).toBe('O(pay(tenant:Agent))');
    expect(linearizeDcecWithGrammar(converter.convertToDcec('tenant must pay').dcec_formula!)).toBe(
      'must pay',
    );
  });

  it('exposes Python-compatible nl_converter names without runtime bridges', () => {
    const converter = new NaturalLanguageConverter();
    const matcher = new PatternMatcher(new DcecNamespace());
    const enhanced = create_enhanced_nl_converter(true);

    expect(converter.convert_to_dcec('tenant may enter').dcec_formula?.toString()).toBe(
      'P(enter(tenant:Agent))',
    );
    expect(converter.convert_from_dcec(matcher.convert('tenant must repair'))).toBe('must repair');
    expect(enhanced.useGrammar).toBe(true);
    expect(parse_with_grammar('next tenant must pay')?.toString()).toBe('X(O(pay(tenant:Agent)))');
    expect(
      linearize_with_grammar(converter.convertToDcec('tenant must not smoke').dcec_formula!),
    ).toBe('must not smoke');
  });

  it('detects policy language with browser-native keyword profiles', () => {
    const english = detectDcecPolicyLanguage('The tenant shall maintain alarms.');
    const spanish = detectDcecPolicyLanguage('El inquilino debe pagar la renta.');

    expect(english.browser_native).toBe(true);
    expect(english.method).toBe('browser_native_keyword_profile');
    expect(english.language).toBe('en');
    expect(english.scores.en).toBeGreaterThan(english.scores.es);
    expect(spanish.language).toBe('es');
    expect(spanish.scores.es).toBeGreaterThan(spanish.scores.en);
  });

  it('ports language_detector.py as a browser-native deterministic detector', () => {
    const detector = new CecLanguageDetector();
    const english = detector.detect_language('The tenant shall maintain the policy.');
    const portuguese = detect_language('O inquilino deve pagar a politica.');
    const unknown = detector.detect('4815162342');

    expect(getCecLanguageDetectorCapabilities()).toMatchObject({
      browserNative: true,
      pythonRuntime: false,
      serverRuntime: false,
      pythonModule: 'logic/CEC/nl/language_detector.py',
    });
    expect(english.language).toBe('en');
    expect(english.browser_native).toBe(true);
    expect(english.python_module).toBe('logic/CEC/nl/language_detector.py');
    expect(portuguese.language).toBe('pt');
    expect(portuguese.scores.pt).toBeGreaterThan(portuguese.scores.en);
    expect(unknown).toMatchObject({
      language: 'unknown',
      confidence: 0,
      matched_terms: [],
      browser_native: true,
    });
  });

  it('compiles English policy text to DCEC metadata without server fallbacks', () => {
    const result = compileDcecPolicyText('The tenant shall maintain smoke alarms.');

    expect(result.success).toBe(true);
    expect(result.browser_native).toBe(true);
    expect(result.parse_method).toBe('browser_native_policy_compiler');
    expect(result.language_detection.language).toBe('en');
    expect(result.normalized_policy_text).toBe('the tenant shall maintain smoke alarms');
    expect(result.policy_formula_text).toBe('O(maintain_smoke_alarms(tenant:Agent))');
  });

  it('ports grammar_nl_policy_compiler.py as a browser-native grammar policy facade', () => {
    const capabilities = getDcecGrammarNlPolicyCompilerCapabilities();
    const result = compileDcecGrammarNlPolicy(
      'Policy 1: The tenant shall maintain smoke alarms. Rule 2: landlord must not enter.',
    );
    const rejected = compileDcecGrammarNlPolicy('tenant shall pay rent', { maxInputLength: 10 });

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
      pythonModule: 'logic/CEC/nl/grammar_nl_policy_compiler.py',
    });
    expect(result.ok).toBe(true);
    expect(result.parse_method).toBe('browser_native_grammar_policy_compiler');
    expect(result.metadata).toEqual({
      sourcePythonModule: 'logic/CEC/nl/grammar_nl_policy_compiler.py',
      runtime: 'browser-native-typescript',
      implementation: 'deterministic-grammar-nl-policy-compiler',
    });
    expect(result.policy_formula_texts).toEqual([
      'O[tenant:Agent](maintain_smoke_alarms(tenant:Agent))',
      'F[landlord:Agent](enter(landlord:Agent))',
    ]);
    expect(result.rules.map((rule) => rule.normalized_text)).toEqual([
      'tenant shall maintain smoke alarms',
      'landlord must not enter',
    ]);
    expect(rejected).toMatchObject({
      ok: false,
      fail_closed_reason: 'input_too_long',
      browser_native: true,
    });
  });

  it('ports nl_to_policy_compiler.py as browser-native policy rule output', () => {
    const capabilities = getDcecNlToPolicyCompilerCapabilities();
    const result = compileDcecNlToPolicy(
      'Policy 1: The tenant shall maintain smoke alarms. Rule 2: landlord may inspect alarms.',
    );
    const withoutLabels = compileDcecNlToPolicy('tenant must pay rent', { includeLabels: false });

    expect(capabilities).toMatchObject({
      browserNative: true,
      pythonRuntime: false,
      serverRuntime: false,
      filesystem: false,
      subprocess: false,
      rpc: false,
      pythonModule: 'logic/CEC/nl/nl_to_policy_compiler.py',
    });
    expect(result).toMatchObject({
      ok: true,
      success: true,
      parse_method: 'browser_native_nl_to_policy_compiler',
      browser_native: true,
      metadata: {
        sourcePythonModule: 'logic/CEC/nl/nl_to_policy_compiler.py',
        runtime: 'browser-native-typescript',
        implementation: 'deterministic-nl-to-policy-compiler',
      },
    });
    expect(result.policy_formula).toBe(
      'O[tenant:Agent](maintain_smoke_alarms(tenant:Agent))\nP[landlord:Agent](inspect_alarms(landlord:Agent))',
    );
    expect(result.policy_rules.map((rule) => rule.label)).toEqual([
      'obligation:tenant_maintain_smoke_alarms',
      'permission:landlord_inspect_alarms',
    ]);
    expect(withoutLabels.policy_rules[0].label).toBeUndefined();
  });

  it('fails closed for non-English policy text instead of calling external NLP', () => {
    const converter = new DcecNaturalLanguageConverter();
    const result = converter.compilePolicyText('El inquilino debe pagar la renta.');

    expect(result.success).toBe(false);
    expect(result.browser_native).toBe(true);
    expect(result.language_detection.language).toBe('es');
    expect(result.fail_closed_reason).toBe('unsupported_policy_language');
    expect(result.dcec_formula).toBeUndefined();
  });

  it('proves DCEC goals with a deterministic browser-native proof cache', () => {
    const converter = new DcecNaturalLanguageConverter();
    const goal = converter.convertToDcec('tenant may enter').dcec_formula!;
    const implication = converter.convertToDcec(
      'if tenant must pay then tenant may enter',
    ).dcec_formula!;
    const antecedent = converter.convertToDcec('tenant must pay').dcec_formula!;
    const cache = new DcecProofCache();

    const first = proveDcecFormula({
      goal,
      assumptions: [implication, antecedent],
      strategy: 'advanced_inference',
      cache,
    });
    const second = proveDcecFormula({
      goal,
      assumptions: [antecedent, implication],
      strategy: 'advanced_inference',
      cache,
    });

    expect(first.proved).toBe(true);
    expect(first.cache_hit).toBe(false);
    expect(first.proof_steps).toContain('Applied modus ponens.');
    expect(second.proved).toBe(true);
    expect(second.cache_hit).toBe(true);
    expect(cache.size).toBe(1);
  });

  it('fails closed for DCEC proof contradictions and supports temporal lift', () => {
    const converter = new DcecNaturalLanguageConverter();
    const obligation = converter.convertToDcec('tenant must pay').dcec_formula!;
    const prohibition = converter.convertToDcec('tenant must not pay').dcec_formula!;
    const temporal = converter.convertToDcec('always tenant may enter').dcec_formula!;
    const permitted = converter.convertToDcec('tenant may enter').dcec_formula!;

    const invalid = converter.proveFormula(obligation, [prohibition], 'deontic_consistency');
    const lifted = converter.proveFormula(permitted, [temporal], 'temporal_lift');

    expect(invalid.status).toBe('invalid');
    expect(invalid.proved).toBe(false);
    expect(invalid.error_message).toContain('Contradictory obligation and prohibition');
    expect(lifted.status).toBe('proved');
    expect(lifted.proof_steps[0]).toBe('Eliminated always premise for P(enter(tenant:Agent)).');
  });
});

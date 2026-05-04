import { parseTdfolFormula } from './parser';
import { convertTdfolBatch, convertTdfolFormula, tdfolToFol, tdfolToTptp } from './converter';
import {
  BrowserNativeTdfolLlmConverter,
  buildTdfolLlmConversionPrompt,
  getTdfolOperatorHintsForText,
} from './browserNativeLlm';
import {
  BrowserNativeTdfolNlApi,
  generateTdfolNaturalLanguage,
  parseTdfolNaturalLanguage,
} from './nlApi';
import { createBrowserNativeTdfolNlContext, resolveTdfolNlContextText } from './nlContext';
import { BrowserNativeTdfolNlGenerator, generateTdfolNl } from './tdfolNlGenerator';
import { preprocessTdfolNaturalLanguage } from './tdfolNlPreprocessor';
import { matchTdfolNlPattern } from './tdfolNlPatterns';

describe('TDFOL converter', () => {
  it('converts parsed formulas back to stable TDFOL output with metadata', () => {
    const result = convertTdfolFormula('forall x. Resident(x) -> Tenant(x)', 'tdfol');

    expect(result.output).toBe('∀x ((Resident(x)) → (Tenant(x)))');
    expect(result.metadata).toMatchObject({
      target: 'tdfol',
      quantifierCount: 1,
      predicateCount: 2,
      operatorCount: 2,
      freeVariables: [],
    });
  });

  it('projects temporal and deontic operators for FOL output with explicit warnings', () => {
    const result = convertTdfolFormula('always(O(Comply(x)))', 'fol');

    expect(result.output).toBe('Comply(x)');
    expect(result.warnings).toEqual([
      'Projected temporal operator ALWAYS away for FOL output.',
      'Projected deontic operator OBLIGATION away for FOL output.',
    ]);
    expect(result.metadata).toMatchObject({ containsTemporal: true, containsDeontic: true });
  });

  it('converts TDFOL to DCEC s-expression syntax', () => {
    const result = convertTdfolFormula('forall x. O(Comply(x))', 'dcec');

    expect(result.output).toBe('(forall x (O (Comply x)))');
  });

  it('converts TDFOL to a local TPTP-style formula string', () => {
    const formula = parseTdfolFormula('forall x. Resident(x) -> O(Comply(x))');

    expect(tdfolToTptp(formula)).toBe('![X]:((resident(X) => obligation(comply(X))))');
    expect(convertTdfolFormula(formula, 'tptp').output).toBe(
      'fof(tdfol_formula, axiom, ![X]:((resident(X) => obligation(comply(X))))).',
    );
  });

  it('converts formulas to JSON and supports batch conversion', () => {
    const json = convertTdfolFormula('Permit(Alice)', 'json').output as Record<string, unknown>;

    expect(json).toMatchObject({
      formatted: 'Permit(Alice)',
      freeVariables: [],
    });
    expect(tdfolToFol(parseTdfolFormula('Permit(Alice)'))).toBe('Permit(Alice)');
    expect(
      convertTdfolBatch(['Permit(Alice)', 'O(Comply(x))'], 'dcec').map((result) => result.output),
    ).toEqual(['(Permit Alice)', '(O (Comply x))']);
  });

  it('ports TDFOL llm.py prompts, hints, cache, and fail-closed browser conversion', () => {
    const hints = getTdfolOperatorHintsForText('All contractors must pay taxes.');
    expect(hints).toEqual(['universal', 'obligation']);
    expect(buildTdfolLlmConversionPrompt('All contractors must pay taxes.', hints)).toContain(
      'server, Python, subprocess, or RPC fallback',
    );

    const converter = new BrowserNativeTdfolLlmConverter();
    const first = converter.convert('All contractors must pay taxes.');
    const second = converter.convert('All contractors must pay taxes.');
    expect(first).toMatchObject({
      success: true,
      formula: 'forall x. Contractor(x) -> O(PayTaxes(x))',
      confidence: 0.9,
      method: 'pattern',
      cacheHit: false,
    });
    expect(first.metadata).toMatchObject({
      llmAvailable: false,
      serverCallsAllowed: false,
      pythonRuntime: false,
    });
    expect(() => parseTdfolFormula(first.formula)).not.toThrow();
    expect(second.cacheHit).toBe(true);
    expect(converter.getStats()).toMatchObject({ size: 1, hits: 1, misses: 1 });

    const failed = converter.convert('This ambiguous policy needs external judgement.');
    expect(failed).toMatchObject({
      success: false,
      method: 'failed',
      metadata: { serverCallsAllowed: false },
    });
    expect(failed.errors[0]).toContain('browser LLM router is fail-closed');
  });

  it('ports TDFOL NL patterns for deterministic browser-native policy matching', () => {
    const permitted = matchTdfolNlPattern('Some tenants may appeal.', [
      'existential',
      'permission',
    ]);
    expect(permitted).toMatchObject({
      formula: 'exists x. Tenant(x) & P(Appeal(x))',
      patternKind: 'existential_policy',
      metadata: { sourcePythonModule: 'logic/TDFOL/nl/tdfol_nl_patterns.py' },
    });
    expect(() => parseTdfolFormula(permitted?.formula ?? '')).not.toThrow();
    expect(
      matchTdfolNlPattern('All contractors who submit invoices must always keep records.', [
        'universal',
        'obligation',
        'temporal_always',
      ]),
    ).toMatchObject({
      formula: 'forall x. (Contractor(x) & SubmitInvoices(x)) -> [](O(KeepRecords(x)))',
      patternKind: 'qualified_universal_policy',
    });
    const converter = new BrowserNativeTdfolLlmConverter();
    expect(converter.convert('There is a tenant that shall not delete records.')).toMatchObject({
      success: true,
      formula: 'exists x. Tenant(x) & F(DeleteRecords(x))',
      method: 'pattern',
    });
  });

  it('ports the TDFOL NL preprocessor for browser-native normalization before parsing', () => {
    const preprocessed = preprocessTdfolNaturalLanguage(
      '  1. All contractors are prohibited from deleting records under § 5.33.  ',
    );

    expect(preprocessed).toMatchObject({
      normalizedText: 'All contractors must not deleting records under section 5.33.',
      sentences: ['All contractors must not deleting records under section 5.33.'],
      operatorHints: ['universal', 'forbidden', 'obligation'],
      legalReferences: ['5.33'],
      metadata: {
        browserNative: true,
        serverCallsAllowed: false,
        pythonRuntime: false,
        sourcePythonModule: 'logic/TDFOL/nl/tdfol_nl_preprocessor.py',
      },
    });

    const converter = new BrowserNativeTdfolLlmConverter();
    expect(
      converter.convert('- All contractors are prohibited from delete records.'),
    ).toMatchObject({
      success: true,
      formula: 'forall x. Contractor(x) -> F(DeleteRecords(x))',
      metadata: {
        serverCallsAllowed: false,
        pythonRuntime: false,
        preprocessor: {
          sourcePythonModule: 'logic/TDFOL/nl/tdfol_nl_preprocessor.py',
          normalizedText: 'All contractors must not delete records.',
        },
      },
    });
  });

  it('ports the TDFOL NL API facade without Python or server runtime fallback', () => {
    const api = new BrowserNativeTdfolNlApi();
    const parsed = api.parse('All contractors must pay taxes.');

    expect(parsed.status).toBe('parsed');
    expect(parsed.formula).toBe('forall x. Contractor(x) -> O(PayTaxes(x))');
    expect(parsed.metadata).toMatchObject({
      browserNative: true,
      serverCallsAllowed: false,
      pythonRuntime: false,
      method: 'pattern',
    });
    expect(parsed.formattedFormula).toBe('∀x ((Contractor(x)) → (O(PayTaxes(x))))');
    expect(api.parse('All contractors must pay taxes.').metadata.cacheHit).toBe(true);
    expect(api.generate(parsed.formula).text).toContain(
      'it is obligatory that PayTaxes holds for x',
    );
    expect(parseTdfolNaturalLanguage('')).toMatchObject({
      status: 'failed',
      errors: ['Input text is empty.'],
    });
    expect(generateTdfolNaturalLanguage('P(Comply(x))').text).toBe(
      'it is permitted that Comply holds for x',
    );
  });

  it('ports the TDFOL NL generator as deterministic browser-native formula narration', () => {
    const generator = new BrowserNativeTdfolNlGenerator({ style: 'controlled' });
    const result = generator.generate('forall x:Agent. Contractor(x) -> [](O(PayTaxes(x)))');

    expect(result).toMatchObject({
      source: '∀x:Agent ((Contractor(x)) → (□(O(PayTaxes(x)))))',
      text: 'for every x of sort Agent, contractor holds for x implies that always it is obligatory that pay taxes holds for x.',
      confidence: 1,
      metadata: {
        browserNative: true,
        serverCallsAllowed: false,
        pythonRuntime: false,
        sourcePythonModule: 'logic/TDFOL/nl/tdfol_nl_generator.py',
        style: 'controlled',
        formulaKind: 'quantified',
        predicateCount: 2,
        quantifierCount: 1,
        operatorCount: 3,
      },
    });

    expect(generateTdfolNl('F(DeleteRecords(Alice))').text).toBe(
      'it is forbidden that delete records applies to alice.',
    );
  });

  it('ports TDFOL NL discourse context with deterministic browser-native pronoun resolution', () => {
    const context = createBrowserNativeTdfolNlContext();
    const api = new BrowserNativeTdfolNlApi();

    const first = context.addTurn('All contractors must pay taxes.');
    expect(first).toMatchObject({
      resolvedText: 'All contractors must pay taxes.',
      entityIds: ['contractor'],
      actionIds: ['pay-taxes'],
    });
    expect(context.snapshot()).toMatchObject({
      focusEntity: { id: 'contractor', label: 'Contractor', mentions: 1 },
      focusAction: {
        id: 'pay-taxes',
        label: 'Pay Taxes',
        operatorHints: ['universal', 'obligation'],
      },
      metadata: { browserNative: true, serverCallsAllowed: false, pythonRuntime: false },
    });

    const resolved = resolveTdfolNlContextText('They shall comply.', context);
    expect(resolved).toBe('All contractors shall comply.');
    expect(api.parse(resolved)).toMatchObject({
      status: 'parsed',
      formula: 'forall x. Contractor(x) -> O(Comply(x))',
      metadata: { serverCallsAllowed: false, pythonRuntime: false },
    });

    const second = context.addTurn('They shall comply.');
    expect(second).toMatchObject({
      resolvedText: 'All contractors shall comply.',
      entityIds: ['contractor'],
      actionIds: ['comply'],
    });
    expect(context.snapshot().focusEntity).toMatchObject({ id: 'contractor', mentions: 2 });
  });
});

import {
  analyzeNormativeSentence,
  buildDeonticFormula,
  convertLegalTextToDeontic,
  extractNormativeElements,
  extractTemporalConstraints,
  formatTemporalPredicate,
  legal_text_to_deontic,
} from './parser';

describe('deontic parser utilities', () => {
  it('classifies obligations, permissions, and prohibitions', () => {
    expect(analyzeNormativeSentence('The tenant must pay rent monthly')).toMatchObject({
      normType: 'obligation',
      deonticOperator: 'O',
      matchedIndicator: 'must',
    });
    expect(analyzeNormativeSentence('The applicant may appeal within 10 days')).toMatchObject({
      normType: 'permission',
      deonticOperator: 'P',
      matchedIndicator: 'may',
    });
    expect(
      analyzeNormativeSentence('The employer shall not retaliate against workers'),
    ).toMatchObject({
      normType: 'prohibition',
      deonticOperator: 'F',
      matchedIndicator: 'shall not',
    });
  });

  it('extracts actions, temporal constraints, conditions, and exceptions', () => {
    const element = analyzeNormativeSentence(
      'The applicant must file a notice within 10 days if the permit is denied, unless the Director extends the period',
    );

    expect(element).toMatchObject({
      normType: 'obligation',
      temporalConstraints: [{ type: 'deadline', value: '10 days' }],
      conditions: ['the permit is denied'],
      exceptions: ['the director extends the period'],
    });
    expect(element?.actions[0]).toContain('file a notice');
  });

  it('builds a deontic formula from extracted elements', () => {
    const element = analyzeNormativeSentence('The tenant must pay rent monthly');
    if (!element) {
      throw new Error('Expected normative element');
    }

    expect(buildDeonticFormula(element)).toContain('O(∀x');
    expect(buildDeonticFormula(element)).toContain('Tenant(x)');
  });

  it('builds formulas with conditions, exceptions, and temporal constraints without server dependencies', () => {
    const element = analyzeNormativeSentence(
      'The applicant must file a notice within 10 days if the permit is denied, unless the Director extends the period',
    );
    if (!element) {
      throw new Error('Expected normative element');
    }

    expect(buildDeonticFormula(element)).toBe(
      'O(∀x (Applicant(x) ∧ ThePermitIsDenied(x) ∧ ¬TheDirectorExtendsThePeriod(x) ∧ Within(x, P10Days) → FileANotice(x)))',
    );
  });

  it('formats browser-native temporal predicates for formula-builder parity', () => {
    expect(formatTemporalPredicate({ type: 'period', value: 'monthly' }, 'party')).toBe(
      'Periodic(party, Monthly)',
    );
  });

  it('extracts multiple normative elements from text', () => {
    const elements = extractNormativeElements(
      'The tenant must pay rent. The landlord may enter for repairs. The tenant shall not block access.',
    );

    expect(elements.map((element) => element.normType)).toEqual([
      'obligation',
      'permission',
      'prohibition',
    ]);
    expect(elements.map((element) => element.sentenceIndex)).toEqual([0, 1, 2]);
    expect(elements[1]).toMatchObject({
      startOffset: 26,
      endOffset: 60,
    });
  });

  it('converts legal text through a browser facade', () => {
    const result = convertLegalTextToDeontic('The applicant may appeal within 10 days.');

    expect(result).toMatchObject({
      success: true,
      confidence: expect.any(Number),
      capabilities: {
        mlUnavailable: false,
        serverCallsAllowed: false,
      },
    });
    expect(result.warnings).toEqual([]);
    expect(result.metadata).toEqual({
      sourceLength: 40,
      sentenceCount: 1,
      elementCount: 1,
      normCounts: {
        obligation: 0,
        permission: 1,
        prohibition: 0,
      },
      browserNative: true,
      pythonRuntime: false,
    });
    expect(result.formulas[0]).toContain('P(∀x');
  });

  it('exposes Python module style legal_text_to_deontic alias without runtime bridges', () => {
    const result = legal_text_to_deontic(
      'Owners shall repair sidewalks. Owners may request a variance.',
    );

    expect(result.success).toBe(true);
    expect(result.metadata.normCounts).toEqual({
      obligation: 1,
      permission: 1,
      prohibition: 0,
    });
    expect(result.capabilities.serverCallsAllowed).toBe(false);
  });

  it('returns a warning when no normative language is detected', () => {
    expect(convertLegalTextToDeontic('This section states a purpose.')).toMatchObject({
      success: false,
      formulas: [],
      warnings: ['No normative indicators were detected'],
    });
  });

  it('extracts temporal periods and durations', () => {
    expect(
      extractTemporalConstraints('Reports are due monthly and must be kept for 3 years'),
    ).toEqual([
      { type: 'duration', value: '3 years' },
      { type: 'period', value: 'monthly' },
    ]);
  });
});

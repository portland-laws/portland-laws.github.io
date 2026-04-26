import { DeonticConverter } from './converter';

describe('DeonticConverter', () => {
  it('converts legal text through the Python-style converter facade', () => {
    const converter = new DeonticConverter({
      jurisdiction: 'us',
      documentType: 'statute',
      useMl: true,
    });
    const result = converter.convert('The applicant may appeal within 10 days.');

    expect(result).toMatchObject({
      status: 'partial',
      success: true,
    });
    expect(result.output).toMatchObject({
      operator: 'P',
      normType: 'permission',
      proposition: expect.stringContaining('P(∀x'),
      confidence: expect.any(Number),
    });
    expect(result.metadata).toMatchObject({
      jurisdiction: 'us',
      document_type: 'statute',
      elements_count: 1,
      browser_native_ml_confidence: false,
    });
  });

  it('supports stats, cache, batch, async, and convenience APIs', async () => {
    const converter = new DeonticConverter();

    expect(converter.toDeontic('The tenant must pay rent monthly')).toContain('O(∀x');
    expect(converter.convert('The tenant shall not block access.').status).toBe('partial');
    expect(converter.convert('The tenant shall not block access.').status).toBe('cached');
    expect(converter.convertBatch(['The tenant must pay rent.', 'The landlord may enter.'])).toHaveLength(2);
    expect(converter.getStats()).toMatchObject({ conversions: 5, successful: 5, failed: 0 });
    await expect(converter.convertAsync('The applicant may appeal.')).resolves.toMatchObject({
      success: true,
    });
  });

  it('keeps no-norm conversions explicit instead of silently succeeding', () => {
    const result = new DeonticConverter().convert('This section states a purpose.');

    expect(result).toMatchObject({
      status: 'partial',
      output: {
        formulas: [],
        elements: [],
      },
    });
    expect(result.warnings).toContain('No normative indicators were detected');
  });

  it('reports validation failures before conversion', () => {
    expect(new DeonticConverter().convert('x')).toMatchObject({
      status: 'validation_failed',
      success: false,
    });
  });
});

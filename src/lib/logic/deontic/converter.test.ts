import { DeonticConverter } from './converter';
import fixtures from '../parity/python-parity-fixtures.json';

type DeonticConfidenceFixture = {
  id: string;
  kind: 'deontic';
  input: string;
  python_norm_type: string;
  python_deontic_operator: string;
  python_use_ml_result_confidence: number;
  python_use_ml_formula_confidence: number;
};

describe('DeonticConverter', () => {
  it('converts legal text through the Python-style converter facade', () => {
    const converter = new DeonticConverter({
      jurisdiction: 'us',
      documentType: 'statute',
      useMl: true,
    });
    const result = converter.convert('The applicant may appeal within 10 days.');

    expect(result).toMatchObject({
      status: 'success',
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
      browser_native_ml_confidence: true,
    });
  });

  it('supports stats, cache, batch, async, and convenience APIs', async () => {
    const converter = new DeonticConverter();

    expect(converter.toDeontic('The tenant must pay rent monthly')).toContain('O(∀x');
    expect(converter.convert('The tenant shall not block access.').status).toBe('success');
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

  it('loads Python use_ml confidence captures for development parity fixtures', () => {
    const deonticFixtures = (fixtures as DeonticConfidenceFixture[]).filter(
      (fixture): fixture is DeonticConfidenceFixture => fixture.kind === 'deontic',
    );

    expect(deonticFixtures.map((fixture) => fixture.id).sort()).toEqual([
      'deontic_employer_shall_not_retaliate',
      'deontic_tenant_must_pay_rent',
    ]);

    const converter = new DeonticConverter({ useMl: true, useCache: false });
    for (const fixture of deonticFixtures) {
      expect(fixture.python_use_ml_result_confidence).toBeCloseTo(1, 10);
      expect(fixture.python_use_ml_formula_confidence).toBeCloseTo(0.82, 10);
      const result = converter.convert(fixture.input);
      expect(result.output).toMatchObject({
        normType: fixture.python_norm_type,
        operator: fixture.python_deontic_operator,
        confidence: expect.any(Number),
      });
    }
  });
});

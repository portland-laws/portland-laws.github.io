import { CecFramework, createDefaultCecFramework } from './cecFramework';

describe('CEC framework parity registry', () => {
  it('provides browser-native default CEC declarations', () => {
    const framework = createDefaultCecFramework();

    expect(framework.name).toBe('Common Event Calculus');
    expect(framework.hasSort('Agent')).toBe(true);
    expect(framework.get('Happens', 'predicate')).toMatchObject({
      name: 'Happens',
      kind: 'predicate',
      args: ['Action', 'Moment'],
    });
    expect(framework.get('O', 'modality')?.args).toEqual(['Formula']);
  });

  it('imports and exports Python-style framework dictionaries', () => {
    const framework = CecFramework.fromPythonDict({
      name: 'Lease CEC',
      description: 'Tenant obligation framework',
      symbols: [
        { name: 'Agent', kind: 'sort', args: [] },
        { name: 'Action', kind: 'sort', args: [] },
        { name: 'mustPay', kind: 'predicate', args: ['Agent', 'Action'], result: 'Formula' },
        { name: 'O', kind: 'modality', args: ['Formula'], result: 'Formula' },
      ],
    });

    expect(framework.get('mustPay')?.kind).toBe('predicate');
    expect(framework.toPythonDict()).toMatchObject({
      name: 'Lease CEC',
      declarations: expect.arrayContaining([
        expect.objectContaining({ name: 'mustPay', args: ['Agent', 'Action'] }),
      ]),
    });
  });

  it('rejects duplicate declarations and unknown argument sorts', () => {
    expect(
      () =>
        new CecFramework({
          declarations: [
            { name: 'Agent', kind: 'sort', args: [] },
            { name: 'Agent', kind: 'sort', args: [] },
          ],
        }),
    ).toThrow('Duplicate CEC declaration');

    expect(
      () =>
        new CecFramework({
          declarations: [
            { name: 'needsNotice', kind: 'predicate', args: ['Tenant'], result: 'Formula' },
          ],
        }),
    ).toThrow("Unknown CEC sort 'Tenant'");
  });

  it('validates expression arity and nested malformed symbols fail closed', () => {
    const framework = createDefaultCecFramework();

    expect(
      framework.validateExpression({
        symbol: 'Happens',
        args: [
          { symbol: 'Appeal', sort: 'Action' },
          { symbol: 't', sort: 'Moment' },
        ],
      }),
    ).toEqual({ ok: true, errors: [] });

    const invalid = framework.validateExpression({
      symbol: 'B',
      args: [{ symbol: 'alice', sort: 'Agent' }],
    });

    expect(invalid.ok).toBe(false);
    expect(invalid.errors).toContain('expression B expects 2 argument(s), received 1');
    expect(framework.validateExpression({ symbol: 'tenant', sort: 'Person' }).errors).toEqual([
      'expression has unknown sort Person',
    ]);
  });
});

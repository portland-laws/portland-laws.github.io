import { DeonticAnalyzer } from './analyzer';

describe('DeonticAnalyzer', () => {
  it('extracts deontic statements from document corpora', () => {
    const analyzer = new DeonticAnalyzer();
    const statements = analyzer.extractDeonticStatements({
      documents: [
        {
          content: 'Tenant must pay rent. Tenant may inspect records. Tenant shall not block access.',
          source: 'code-a',
          date: '2026-01-01',
        },
      ],
    });

    expect(statements.map((statement) => statement.modality)).toEqual([
      'obligation',
      'permission',
      'prohibition',
    ]);
    expect(statements[0]).toMatchObject({
      entity: 'Tenant',
      action: 'pay rent',
      confidence: expect.any(Number),
      context: 'Tenant must pay rent.',
    });
  });

  it('filters by entity and groups statements', () => {
    const analyzer = new DeonticAnalyzer();
    const statements = analyzer.extractDeonticStatements(
      {
        documents: [{ content: 'Tenant must pay rent. Landlord must maintain records.' }],
      },
      ['tenant'],
    );

    expect(statements).toHaveLength(1);
    expect(Object.keys(analyzer.organizeByEntities(statements))).toEqual(['Tenant']);
  });

  it('detects direct, jurisdictional, and temporal conflicts', () => {
    const analyzer = new DeonticAnalyzer();
    const statements = analyzer.extractDeonticStatements({
      documents: [
        { content: 'Tenant must pay rent.', source: 'code-a', date: '2026-01-01' },
        { content: 'Tenant shall not pay rent.', source: 'code-b', date: '2026-02-01' },
      ],
    });

    const conflicts = analyzer.detectDeonticConflicts(statements, ['direct', 'jurisdictional', 'temporal']);
    expect(conflicts[0]).toMatchObject({
      type: 'direct',
      severity: 'high',
      entities: ['Tenant'],
    });
    expect(analyzer.calculateStatistics(statements, conflicts)).toMatchObject({
      total_statements: 2,
      obligations: 1,
      prohibitions: 1,
      conflicts: 1,
    });
  });

  it('checks action similarity and nearby condition extraction', () => {
    const analyzer = new DeonticAnalyzer();

    expect(analyzer.actionsAreSimilar('pay rent monthly', 'pay rent monthly')).toBe(true);
    expect(analyzer.extractConditions('Tenant must pay rent if the lease is active.', 0, 20)).toEqual([
      'the lease is active',
    ]);
    expect(analyzer.extractExceptions('Tenant must pay rent unless waived.', 0, 20)).toEqual(['waived']);
  });
});

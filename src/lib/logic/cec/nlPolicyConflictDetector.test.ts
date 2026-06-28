import { detectNlPolicyConflicts, NlPolicyConflictDetector } from './nlPolicyConflictDetector';

describe('NlPolicyConflictDetector', () => {
  it('detects direct natural-language policy conflicts without runtime services', () => {
    const result = detectNlPolicyConflicts([
      { id: 'housing-code', text: 'Tenant must pay rent.', date: '2026-01-01' },
      { id: 'emergency-order', text: 'Tenant shall not pay rent.', date: '2026-02-01' },
    ]);

    expect(result.conflicts).toEqual([
      expect.objectContaining({
        type: 'direct',
        severity: 'high',
        policy_ids: ['housing-code', 'emergency-order'],
        entity: 'Tenant',
        modalities: ['obligation', 'prohibition'],
        actions: ['pay rent', 'pay rent'],
      }),
    ]);
    expect(result.statistics).toMatchObject({
      total_policies: 2,
      total_statements: 2,
      conflicts: 1,
    });
  });

  it('supports class-based detection with filters and confidence thresholds', () => {
    const detector = new NlPolicyConflictDetector();
    const result = detector.detect(
      [
        { source: 'tenant-manual', content: 'Tenant may inspect records.' },
        { source: 'landlord-rule', content: 'Tenant must not inspect records.' },
        { source: 'unrelated', content: 'Landlord must maintain records.' },
      ],
      { entityFilter: ['tenant'], minimumConfidence: 0.8 },
    );

    expect(result.statements.map((statement) => statement.entity)).toEqual(['Tenant', 'Tenant']);
    expect(result.conflicts).toHaveLength(1);
    expect(result.conflicts[0]).toMatchObject({
      type: 'direct',
      modalities: ['permission', 'prohibition'],
      confidence: expect.any(Number),
    });
  });

  it('fails closed for empty or non-deontic policy text', () => {
    expect(detectNlPolicyConflicts([])).toMatchObject({
      conflicts: [],
      statements: [],
      statistics: {
        total_policies: 0,
        total_statements: 0,
        conflicts: 0,
        average_confidence: 0,
      },
    });
    expect(
      detectNlPolicyConflicts([{ text: 'This policy contains background only.' }]).conflicts,
    ).toEqual([]);
  });
});

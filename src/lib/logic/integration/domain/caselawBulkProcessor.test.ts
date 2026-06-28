import { processCaselawBulk } from './caselawBulkProcessor';

describe('caselaw bulk processor browser-native parity', () => {
  it('extracts deterministic case metadata across a local batch', () => {
    const result = processCaselawBulk([
      {
        id: 'brown',
        title: 'Brown v. Board of Education',
        text: 'Brown v. Board of Education, 347 U.S. 483 (1954), held that equal protection must apply.',
      },
      {
        id: 'oregon',
        title: 'State v. Smith',
        jurisdiction: 'OR',
        text: 'State v. Smith, 299 Or. 534 (1985), reversed and remanded. The court may review the record.',
      },
    ]);

    expect(result).toMatchObject({
      accepted: true,
      runtime: 'browser-native',
      wasmCompatible: true,
      serverCallsAllowed: false,
      pythonServiceAllowed: false,
      summary: { total: 2, accepted: 2, rejected: 0, citations: 2 },
    });
    expect(result.documents[0]).toMatchObject({
      id: 'brown',
      accepted: true,
      caseName: 'Brown v. Board of Education',
      citations: ['347 U.S. 483'],
      year: 1954,
      jurisdiction: 'US',
      concepts: ['holding', 'duty'],
      issues: [],
    });
    expect(result.documents[1].concepts).toEqual(['reversal', 'permission']);
  });

  it('fails closed locally for invalid or under-specified case records', () => {
    const result = processCaselawBulk([
      { id: '', text: 'No citation or party caption here.' },
      { id: 'blank', text: '   ' },
    ]);

    expect(result.accepted).toBe(false);
    expect(result.rejected).toHaveLength(2);
    expect(result.rejected[0].issues).toEqual([
      'id is required',
      'citation not found',
      'case name not found',
    ]);
    expect(result.rejected[1].issues).toEqual([
      'text is required',
      'citation not found',
      'case name not found',
    ]);
  });
});

import {
  DOCUMENT_CONSISTENCY_CHECKER_METADATA,
  BrowserNativeDocumentConsistencyChecker,
  checkDocumentConsistency,
} from './documentConsistencyChecker';

describe('browser-native document consistency checker', () => {
  it('accepts supported fields and citations without Python or server runtime', () => {
    const result = checkDocumentConsistency({
      id: 'pcc-1.01.010',
      text: 'Portland City Code 1.01.010 states the Code is known as the City Code. The auditor shall maintain the code.',
      citations: ['Portland City Code 1.01.010'],
      extractedFields: [
        {
          name: 'short_title',
          value: 'City Code',
          evidence: 'known as the City Code',
          required: true,
        },
        { name: 'custodian', value: 'auditor shall maintain the code', required: true },
      ],
    });

    expect(result).toMatchObject({
      accepted: true,
      runtime: 'browser-native',
      wasmCompatible: true,
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
      summary: { checkedFields: 2, matchedFields: 2, checkedCitations: 1, matchedCitations: 1 },
    });
    expect(result.metadata).toBe(DOCUMENT_CONSISTENCY_CHECKER_METADATA);
  });

  it('fails closed on missing evidence, missing citations, and contradictory terms', () => {
    const result = new BrowserNativeDocumentConsistencyChecker().check({
      id: 'permit-rule',
      text: 'The application is approved. The same application is denied. No permit required.',
      citations: ['Portland City Code 3.04.010'],
      extractedFields: [
        { name: 'permit_status', value: 'planning director approval', required: true },
      ],
    });

    expect(result.accepted).toBe(false);
    expect(result.issues).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          code: 'field_evidence_missing',
          severity: 'error',
          field: 'permit_status',
        }),
        expect.objectContaining({
          code: 'citation_not_in_text',
          severity: 'error',
          citation: 'Portland City Code 3.04.010',
        }),
        expect.objectContaining({ code: 'contradictory_terms', severity: 'error' }),
      ]),
    );
    expect(result.summary).toMatchObject({
      checkedFields: 1,
      matchedFields: 0,
      checkedCitations: 1,
      matchedCitations: 0,
    });
  });
});

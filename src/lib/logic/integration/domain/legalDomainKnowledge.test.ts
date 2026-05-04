import {
  BrowserNativeLegalDomainKnowledge,
  classify_legal_domain_knowledge,
  create_legal_domain_knowledge,
} from './legalDomainKnowledge';

describe('legal domain knowledge browser-native parity', () => {
  it('classifies legal domain concepts with deterministic local rules', () => {
    const result = new BrowserNativeLegalDomainKnowledge().classify(
      'The agency permit hearing concerns zoning for a tenant lease on the parcel.',
    );

    expect(result).toMatchObject({
      accepted: true,
      runtime: 'browser-native',
      wasmCompatible: true,
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
      primaryDomain: 'property',
      errors: [],
      metadata: {
        sourcePythonModule: 'logic/integration/domain/legal_domain_knowledge.py',
        runtimeDependencies: [],
      },
    });
    expect(result.matches[0]).toMatchObject({
      domain: 'property',
      matchedKeywords: ['tenant', 'lease', 'parcel', 'zoning'],
      concepts: ['possession', 'land use', 'ownership'],
    });
    expect(result.matches.map((match) => match.domain)).toContain('administrative');
  });

  it('supports Python-style aliases and fails closed without remote fallback', () => {
    const empty = create_legal_domain_knowledge().classify('');
    const evidence = classify_legal_domain_knowledge(
      'Hearsay testimony from a witness may be inadmissible without an exception.',
    );

    expect(empty).toMatchObject({
      accepted: false,
      matches: [],
      errors: ['source text is required'],
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
    });
    expect(evidence).toMatchObject({ accepted: true, primaryDomain: 'evidence' });
    expect(evidence.matches[0].matchedKeywords).toEqual(['hearsay', 'testimony', 'witness']);
  });
});

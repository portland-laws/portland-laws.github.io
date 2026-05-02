import {
  createLogicOutputMetadata,
  getLogicOutputLanguage,
  getLogicOutputLanguageCatalog,
  isLogicOutputKind,
  validateLogicOutputMetadata,
} from './outputClassification';

describe('logic output classification', () => {
  it('exposes strict UI and API language for each output kind', () => {
    expect(getLogicOutputLanguageCatalog()).toEqual([
      expect.objectContaining({
        kind: 'simulated',
        uiLabel: 'Simulated output',
        apiQualifier: 'simulated',
        cryptographic: false,
      }),
      expect.objectContaining({
        kind: 'heuristic',
        uiLabel: 'Heuristic output',
        apiQualifier: 'heuristic',
        cryptographic: false,
      }),
      expect.objectContaining({
        kind: 'proof-checking',
        uiLabel: 'Proof-checking output',
        apiQualifier: 'proof-checking',
        cryptographic: false,
      }),
      expect.objectContaining({
        kind: 'cryptographic',
        uiLabel: 'Cryptographic output',
        apiQualifier: 'cryptographic',
        cryptographic: true,
      }),
    ]);
  });

  it('distinguishes proof-checking from cryptographic output', () => {
    expect(getLogicOutputLanguage('proof-checking').cryptographic).toBe(false);
    expect(getLogicOutputLanguage('cryptographic').cryptographic).toBe(true);

    expect(createLogicOutputMetadata('proof-checking').warnings).toContain(
      'Proof-checking output must not be described as cryptographic unless a cryptographic verifier produced it.',
    );
  });

  it('validates supported metadata and normalizes the strict language fields', () => {
    const validation = validateLogicOutputMetadata({
      kind: 'heuristic',
      uiLabel: 'Heuristic output',
      apiQualifier: 'heuristic',
      cryptographic: false,
    });

    expect(validation).toEqual({
      ok: true,
      metadata: expect.objectContaining({
        kind: 'heuristic',
        uiLabel: 'Heuristic output',
        apiQualifier: 'heuristic',
        cryptographic: false,
      }),
    });
  });

  it('fails closed for unsupported or ambiguous output language', () => {
    expect(isLogicOutputKind('verified')).toBe(false);

    expect(validateLogicOutputMetadata({ kind: 'verified' })).toEqual({
      ok: false,
      reason: 'metadata.kind must be one of simulated, heuristic, proof-checking, or cryptographic',
      warnings: ['Unrecognized output language is not promoted to a stronger guarantee.'],
    });
  });

  it('rejects metadata that implies a stronger guarantee than its declared kind', () => {
    expect(
      validateLogicOutputMetadata({
        kind: 'proof-checking',
        uiLabel: 'Cryptographic output',
        apiQualifier: 'cryptographic',
        cryptographic: true,
      }),
    ).toEqual({
      ok: false,
      reason: 'metadata language does not match the declared output kind',
      warnings: [
        'apiQualifier must be proof-checking',
        'uiLabel must be Proof-checking output',
        'cryptographic must be false',
      ],
    });
  });
});

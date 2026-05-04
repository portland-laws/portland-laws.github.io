import {
  BrowserNativeMedicalTheoremFramework,
  analyze_medical_theorems,
  create_medical_theorem_framework,
} from './medicalTheoremFramework';

describe('medical theorem framework browser-native parity', () => {
  it('derives deterministic local medical care theorems from clinical evidence', () => {
    const result = new BrowserNativeMedicalTheoremFramework().analyze(
      'The patient is diagnosed with asthma symptoms. Medication treatment should reduce symptoms after informed consent.',
    );

    expect(result).toMatchObject({
      accepted: true,
      runtime: 'browser-native',
      wasmCompatible: true,
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
      issues: [],
    });
    expect(result.metadata).toMatchObject({
      sourcePythonModule: 'logic/integration/domain/medical_theorem_framework.py',
      runtimeDependencies: [],
    });
    expect(result.theorems).toHaveLength(1);
    expect(result.theorems[0]).toMatchObject({
      kind: 'treatment_permission',
      formula: expect.stringMatching(/^P\(clinician, /),
      confidence: 0.82,
    });
    expect(result.theorems[0].evidence.map((item) => item.kind)).toEqual(
      expect.arrayContaining(['diagnosis', 'intervention', 'outcome', 'consent']),
    );
  });

  it('fails closed for contraindication or incomplete evidence without remote fallback', () => {
    const contraindicated = analyze_medical_theorems(
      'The patient has diabetes. Surgery is contraindicated because bleeding risk is high.',
    );
    const incomplete = create_medical_theorem_framework().analyze('Recovery improved.');

    expect(contraindicated).toMatchObject({
      accepted: false,
      theorems: [],
      issues: ['contraindication requires local review', 'no medical theorem derived locally'],
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
    });
    expect(incomplete).toMatchObject({
      accepted: false,
      theorems: [],
      issues: [
        'diagnosis evidence is required',
        'intervention evidence is required',
        'no medical theorem derived locally',
      ],
    });
  });
});

import { jest } from '@jest/globals';

import {
  __resetPortlandLogicCacheForTests,
  buildLogicProofIndexes,
  buildLogicEvidenceForSearchResults,
  buildLogicEvidenceItem,
  filterLogicProofSummaries,
  explainLogicProofSummary,
  getLogicProofForIdentifier,
  getLogicProofForSection,
  getSimulatedCertificateWarning,
  loadLogicProofSummaries,
  normalizeLogicProofSummary,
  parseLogicProofTdfol,
  validateLogicProofSummary,
  type LogicProofSummary,
} from './portlandLogic';

const proofRows = [
  {
    ipfs_cid: 'bafk-permission',
    identifier: 'Portland City Code 1.01.010',
    title: '1.01.010 Title - Citation - Reference.',
    formalization_scope: 'machine_generated_candidate',
    fol_status: 'success',
    deontic_status: 'success',
    deontic_temporal_fol: 'forall a. SubjectTo(a, section) -> P(always(ComplyWith(a, section)))',
    deontic_cognitive_event_calculus: '(forall agent (P (always comply)))',
    frame_logic_ergo: 'section[identifier -> "Portland City Code 1.01.010"] : PortlandCityCodeSection.',
    norm_operator: 'P',
    norm_type: 'permission',
    zkp_backend: 'simulated',
    zkp_security_note: 'simulated educational certificate; not cryptographically secure',
    zkp_verified: true,
  },
  {
    ipfs_cid: 'bafk-obligation',
    identifier: 'Portland City Code 1.01.020',
    title: '1.01.020 Reference Applies to Amendments.',
    formalization_scope: 'machine_generated_candidate',
    fol_status: 'success',
    deontic_status: 'success',
    deontic_temporal_fol: 'forall a. SubjectTo(a, section) -> O(always(ComplyWith(a, section)))',
    deontic_cognitive_event_calculus: '(forall agent (O (always comply)))',
    frame_logic_ergo: 'section[identifier -> "Portland City Code 1.01.020"] : PortlandCityCodeSection.',
    norm_operator: 'O',
    norm_type: 'obligation',
    zkp_backend: 'simulated',
    zkp_security_note: 'simulated educational certificate; not cryptographically secure',
    zkp_verified: true,
  },
  {
    ipfs_cid: 'bafk-prohibition',
    identifier: 'Portland City Code 1.01.090',
    title: '1.01.090 Effect of Code on Past Actions and Obligations.',
    formalization_scope: 'machine_generated_candidate',
    fol_status: 'success',
    deontic_status: 'success',
    deontic_temporal_fol: 'forall a. SubjectTo(a, section) -> F(always(ComplyWith(a, section)))',
    deontic_cognitive_event_calculus: '(forall agent (F (always comply)))',
    frame_logic_ergo: 'section[identifier -> "Portland City Code 1.01.090"] : PortlandCityCodeSection.',
    norm_operator: 'F',
    norm_type: 'prohibition',
    zkp_backend: 'simulated',
    zkp_security_note: 'simulated educational certificate; not cryptographically secure',
    zkp_verified: true,
  },
];

function mockFetchJson(rows: unknown[]) {
  const manifest = {
    schemaVersion: 1,
    generatedAt: '2026-04-27T19:57:04.679Z',
    datasetId: 'justicedao/american_municipal_law',
    datasetPath: 'municipal_laws_portland_or_current_code',
    corpus: {
      jurisdiction: 'Portland, Oregon',
      name: 'Portland City Code',
      source: 'https://huggingface.co/datasets/justicedao/american_municipal_law',
    },
    artifacts: [],
    generatedFiles: [],
  };
  const fetchMock = jest.fn(async (url: RequestInfo | URL) => ({
    ok: true,
    json: async () => (String(url).includes('artifacts.manifest.json') ? manifest : rows),
  }) as Response);
  global.fetch = fetchMock as unknown as typeof fetch;
  return fetchMock;
}

describe('portlandLogic', () => {
  beforeEach(() => {
    __resetPortlandLogicCacheForTests();
    jest.restoreAllMocks();
  });

  it('loads and normalizes proof summaries', async () => {
    const fetchMock = mockFetchJson(proofRows);

    const summaries = await loadLogicProofSummaries();

    expect(summaries).toHaveLength(3);
    expect(summaries[0]).toMatchObject({
      identifier: 'Portland City Code 1.01.010',
      norm_operator: 'P',
      norm_type: 'permission',
    });
    expect(fetchMock).toHaveBeenCalledWith('/corpus/portland-or/current/artifacts.manifest.json', {
      cache: 'no-store',
    });
    expect(fetchMock).toHaveBeenCalledWith(
      '/corpus/portland-or/current/generated/logic-proof-summaries.json?v=2026-04-27T19%3A57%3A04.679Z',
    );
  });

  it('indexes summaries by CID, identifier, norm operator, and norm type', () => {
    const summaries = proofRows.map(normalizeLogicProofSummary);

    const indexes = buildLogicProofIndexes(summaries);

    expect(indexes.proofByCid.get('bafk-obligation')?.identifier).toBe('Portland City Code 1.01.020');
    expect(indexes.proofByIdentifier.get('Portland City Code 1.01.090')?.norm_type).toBe('prohibition');
    expect(indexes.normByOperator.get('O')).toHaveLength(1);
    expect(indexes.normByType.get('permission')).toHaveLength(1);
    expect(indexes.formalizationStatusCounts.success).toBe(3);
    expect(indexes.simulatedCertificateCount).toBe(3);
  });

  it('looks up loaded summaries by section CID and identifier', async () => {
    mockFetchJson(proofRows);

    await expect(getLogicProofForSection('bafk-permission')).resolves.toMatchObject({
      identifier: 'Portland City Code 1.01.010',
    });
    await expect(getLogicProofForIdentifier('Portland City Code 1.01.020')).resolves.toMatchObject({
      norm_operator: 'O',
    });
    await expect(getLogicProofForSection('missing-cid')).resolves.toBeNull();
  });

  it('filters summaries by logic metadata', () => {
    const summaries = proofRows.map(normalizeLogicProofSummary);

    const prohibitions = filterLogicProofSummaries(summaries, {
      normTypes: ['prohibition'],
      requireVerifiedCertificate: true,
    });

    expect(prohibitions.map((summary) => summary.identifier)).toEqual(['Portland City Code 1.01.090']);
  });

  it('parses TDFOL summaries and can filter to parseable formulas', () => {
    const summaries = [
      normalizeLogicProofSummary(proofRows[0]),
      normalizeLogicProofSummary({
        ...proofRows[1],
        deontic_temporal_fol: 'forall x. Broken(',
      }),
    ];

    expect(parseLogicProofTdfol(summaries[0])).toMatchObject({ ok: true });
    expect(parseLogicProofTdfol(summaries[1])).toMatchObject({ ok: false });
    expect(filterLogicProofSummaries(summaries, { requireParseableTdfol: true })).toEqual([summaries[0]]);
  });

  it('warns that simulated certificates are not cryptographic verification', () => {
    const summary = normalizeLogicProofSummary(proofRows[0]);

    expect(getSimulatedCertificateWarning(summary)).toContain('not cryptographic verification');
  });

  it('explains proof summaries in plain language with temporal scope', () => {
    const summary = normalizeLogicProofSummary(proofRows[1]);

    const explanation = explainLogicProofSummary(summary);

    expect(explanation).toMatchObject({
      normLabel: 'obligation',
      temporalScope: 'Always/continuing condition',
      parseStatus: 'valid',
      certificateStatus: 'Simulated certificate metadata only',
    });
    expect(explanation.plainLanguage).toContain('Portland City Code 1.01.020');
    expect(explanation.caveats.join(' ')).toContain('Machine-generated');
  });

  it('builds GraphRAG-ready logic evidence items', async () => {
    mockFetchJson(proofRows);
    const summary = normalizeLogicProofSummary(proofRows[0]);

    expect(buildLogicEvidenceItem(summary)).toMatchObject({
      identifier: 'Portland City Code 1.01.010',
      normType: 'permission',
      normOperator: 'P',
      temporalScope: 'Always/continuing condition',
      parseStatus: 'valid',
      certificateStatus: 'simulated_certificate_present',
      fLogicClass: 'PortlandCityCodeSection',
    });

    const evidence = await buildLogicEvidenceForSearchResults([
      {
        ipfs_cid: 'bafk-permission',
        citation: 'Portland City Code 1.01.010',
      } as never,
    ]);

    expect(evidence).toHaveLength(1);
    expect(evidence[0].fLogicAttributes).toContainEqual({
      name: 'identifier',
      value: 'Portland City Code 1.01.010',
    });
  });

  it('normalizes unsupported enum values to unknown with warnings', () => {
    const validation = validateLogicProofSummary({
      ...proofRows[0],
      fol_status: 'weird',
      norm_operator: 'M',
      norm_type: 'mandate',
      zkp_backend: 'demo',
    });
    const summary = normalizeLogicProofSummary({
      ...proofRows[0],
      fol_status: 'weird',
      norm_operator: 'M',
      norm_type: 'mandate',
      zkp_backend: 'demo',
    });

    expect(validation.valid).toBe(true);
    expect(validation.issues.some((issue) => issue.severity === 'warning')).toBe(true);
    expect(summary.fol_status).toBe('unknown');
    expect(summary.norm_operator).toBe('unknown');
    expect(summary.norm_type).toBe('unknown');
    expect(summary.zkp_backend).toBe('unknown');
  });

  it('rejects non-object or missing required fields', () => {
    const validation = validateLogicProofSummary({ ...proofRows[0], zkp_verified: 'yes' });

    expect(validateLogicProofSummary(null).valid).toBe(false);
    expect(validation.valid).toBe(false);
    expect(() => normalizeLogicProofSummary({ ipfs_cid: 'only-one-field' })).toThrow(
      'Invalid logic proof summary',
    );
  });
});

const _typeCheck: LogicProofSummary = normalizeLogicProofSummary(proofRows[0]);
void _typeCheck;

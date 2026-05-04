import {
  BrowserNativeTemporalDeonticRagStore,
  TEMPORAL_DEONTIC_RAG_STORE_METADATA,
  create_temporal_deontic_rag_store,
} from './temporalDeonticRagStore';

describe('BrowserNativeTemporalDeonticRagStore', () => {
  it('ports temporal_deontic_rag_store.py as a deterministic browser-native store', () => {
    const store = new BrowserNativeTemporalDeonticRagStore([
      {
        id: 'inspection',
        title: 'Inspection Rule',
        citation: 'PCC 1.01',
        text: 'The landlord shall inspect the unit within 10 days. The tenant may attend.',
      },
      {
        id: 'records',
        title: 'Sealed Records',
        text: 'The clerk must not disclose sealed records unless the court orders disclosure.',
      },
    ]);
    const result = store.query({
      text: 'What duties apply within 10 days?',
      normType: 'obligation',
      temporalOnly: true,
    });
    expect(TEMPORAL_DEONTIC_RAG_STORE_METADATA).toMatchObject({
      sourcePythonModule: 'logic/integration/domain/temporal_deontic_rag_store.py',
      browserNative: true,
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
    });
    expect(result).toMatchObject({
      status: 'success',
      success: true,
      metadata: { document_count: 2, evidence_count: 1, serverCallsAllowed: false },
    });
    expect(result.evidence[0]).toMatchObject({
      documentId: 'inspection',
      citation: 'PCC 1.01',
      normCount: 2,
      temporalCount: 1,
    });
    expect(result.evidence[0].norms[0].norm_type).toBe('obligation');
    expect(result.evidence[0].formulas[0]).toContain('O(');
  });

  it('fails closed without server, Python, filesystem, or RPC fallback', () => {
    expect(create_temporal_deontic_rag_store().query('notice')).toMatchObject({
      status: 'validation_failed',
      success: false,
      errors: ['at least one local document is required'],
      metadata: { serverCallsAllowed: false, pythonRuntimeAllowed: false },
    });
  });
});

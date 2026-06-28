import {
  BrowserNativeTemporalDeonticRagDemo,
  DEMO_TEMPORAL_DEONTIC_RAG_METADATA,
  run_temporal_deontic_rag_demo,
} from './demoTemporalDeonticRag';

describe('BrowserNativeTemporalDeonticRagDemo', () => {
  it('ports demo_temporal_deontic_rag.py as deterministic local RAG evidence', () => {
    const result = new BrowserNativeTemporalDeonticRagDemo([
      {
        id: 'inspection',
        title: 'Inspection Rule',
        text: 'The landlord shall inspect the unit within 10 days. The tenant may attend.',
      },
      {
        id: 'sealed',
        title: 'Sealed Records',
        text: 'The clerk must not disclose sealed records unless the court orders disclosure.',
      },
    ]).run('What duties apply within 10 days?');

    expect(DEMO_TEMPORAL_DEONTIC_RAG_METADATA).toMatchObject({
      sourcePythonModule: 'logic/integration/demos/demo_temporal_deontic_rag.py',
      browserNative: true,
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
    });
    expect(result).toMatchObject({
      status: 'success',
      success: true,
      metadata: {
        sourcePythonModule: 'logic/integration/demos/demo_temporal_deontic_rag.py',
        serverCallsAllowed: false,
        pythonRuntimeAllowed: false,
        evidence_count: 2,
      },
    });
    expect(result.evidence[0]).toMatchObject({
      documentId: 'inspection',
      normCount: 2,
      temporalCount: 1,
    });
    expect(result.evidence[0].formulas[0]).toContain('O(');
    expect(result.answer).toContain('temporal constraint');
  });

  it('fails closed without server, Python, filesystem, or RPC fallback', () => {
    expect(new BrowserNativeTemporalDeonticRagDemo([]).run('notice')).toMatchObject({
      status: 'validation_failed',
      success: false,
      metadata: { serverCallsAllowed: false, pythonRuntimeAllowed: false },
    });
    expect(run_temporal_deontic_rag_demo('sealed records').evidence[0].documentId).toBe('records');
  });
});

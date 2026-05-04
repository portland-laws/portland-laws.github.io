import {
  PHASE7_COMPLETE_INTEGRATION_METADATA,
  createBrowserNativePhase7CompleteIntegration,
  phase7_complete_integration,
} from './phase7CompleteIntegration';

describe('BrowserNativePhase7CompleteIntegration', () => {
  it('orchestrates phase7_complete_integration.py locally without server or Python runtime', () => {
    const result = createBrowserNativePhase7CompleteIntegration().integrate({
      text: 'Tenants must maintain exits. Owners may inspect after notice.',
      tdfolFormula: 'forall x. O(MaintainExit(x))',
      cecExpression: '(O (MaintainExit tenant))',
    });

    expect(result).toMatchObject({
      status: 'success',
      runtime: 'browser-native',
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
      metadata: PHASE7_COMPLETE_INTEGRATION_METADATA,
    });
    expect(result.stages.map((stage) => stage.name)).toEqual([
      'deontic',
      'fol',
      'tdfol_cec',
      'cec_json',
      'zkp_route',
    ]);
    expect(result.stages.find((stage) => stage.name === 'deontic')?.output).toContain('O(');
    expect(result.stages.find((stage) => stage.name === 'tdfol_cec')?.output).toBe(
      '(forall x (O (MaintainExit x)))',
    );
    expect(result.stages.find((stage) => stage.name === 'zkp_route')).toMatchObject({
      status: 'success',
      coreId: 'browser-native-typescript-logic-core',
    });
  });

  it('fails closed for invalid input and unavailable required WASM ZKP routing', () => {
    expect(phase7_complete_integration('')).toMatchObject({
      status: 'validation_failed',
      success: false,
    });
    const result = phase7_complete_integration({
      text: 'The agency shall publish the rule.',
      requireWasmZkp: true,
      wasmZkpAvailable: false,
    });

    expect(result.status).toBe('partial');
    expect(result.stages.find((stage) => stage.name === 'zkp_route')).toMatchObject({
      status: 'failed',
      warnings: ['requested WASM logic core is unavailable in this browser runtime'],
    });
    expect(result.issues).toContain(
      'requested WASM ZKP verification failed closed without TypeScript or external fallback',
    );
  });
});

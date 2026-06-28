import { TalosWrapper, mapTalosWrapperStatus, proveCecWithTalosWrapper } from './talosWrapper';

describe('Talos wrapper browser-native port', () => {
  it('advertises a browser-native contract without Python, server, or subprocess runtimes', () => {
    const capabilities = new TalosWrapper().getCapabilities();

    expect(capabilities).toEqual({
      browserNative: true,
      pythonRuntime: false,
      serverRuntime: false,
      filesystem: false,
      subprocess: false,
      rpc: false,
      wasmRequired: false,
      implementation: 'deterministic-typescript',
      pythonModule: 'logic/CEC/talos_wrapper.py',
    });
  });

  it('proves through the local TypeScript CEC engine and attaches Talos metadata', () => {
    const result = proveCecWithTalosWrapper(
      '(can_access ada dataset)',
      ['(can_access ada dataset)'],
      {
        problemName: 'talos_policy_case',
      },
    );

    expect(result.status).toBe('proved');
    expect(result.method).toContain('talos-compatible:');
    expect(result.talos).toEqual({
      adapter: 'browser-native-cec-talos-wrapper',
      sourcePythonModule: 'logic/CEC/talos_wrapper.py',
      runtime: 'typescript-wasm-browser',
      externalBinaryAllowed: false,
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
      command: null,
      problemName: 'talos_policy_case',
      normalizedTheorem: '(can_access ada dataset)',
      normalizedAxioms: ['(can_access ada dataset)'],
      statusMapping: 'valid',
      warnings: [
        'External Talos/Python execution is unavailable in the browser; proof search used the local TypeScript CEC engine.',
      ],
    });
  });

  it('maps CEC proof statuses into Talos-compatible wrapper statuses', () => {
    expect(mapTalosWrapperStatus('proved')).toBe('valid');
    expect(mapTalosWrapperStatus('disproved')).toBe('invalid');
    expect(mapTalosWrapperStatus('unknown')).toBe('unknown');
    expect(mapTalosWrapperStatus('timeout')).toBe('timeout');
    expect(mapTalosWrapperStatus('error')).toBe('error');
  });
});

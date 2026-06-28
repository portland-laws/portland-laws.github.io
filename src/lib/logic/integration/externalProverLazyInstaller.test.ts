import {
  BrowserNativeExternalProverLazyInstaller,
  EXTERNAL_PROVER_LAZY_INSTALLER_METADATA,
  ensure_external_prover_lazy_installed,
} from './externalProverLazyInstaller';
import { createBrowserNativeExternalProversBridge } from './externalProversBridge';

describe('BrowserNativeExternalProverLazyInstaller', () => {
  it('ports lazy_installer.py as a browser-native fail-closed validation gate', () => {
    expect(EXTERNAL_PROVER_LAZY_INSTALLER_METADATA).toMatchObject({
      sourcePythonModule: 'logic/external_provers/lazy_installer.py',
      runtime: 'typescript-wasm-browser',
      browserNative: true,
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
      subprocessAllowed: false,
      filesystemAllowed: false,
      rpcAllowed: false,
      failClosed: true,
    });

    const bridge = createBrowserNativeExternalProversBridge();
    const installer = new BrowserNativeExternalProverLazyInstaller(bridge);
    const cvc5Info = bridge.getProverInfo('cvc5');

    expect(cvc5Info.available).toBe(true);
    expect(cvc5Info.supportedLogics.length).toBeGreaterThan(0);

    const supportedLogic = cvc5Info.supportedLogics[0];
    expect(supportedLogic).toBeDefined();
    if (!supportedLogic) {
      throw new Error('Expected cvc5 to report at least one supported logic.');
    }

    const ready = installer.ensureInstalled({ prover: 'cvc5', logic: supportedLogic });
    expect(ready).toMatchObject({
      prover: 'cvc5',
      logic: supportedLogic,
      state: 'ready',
      available: true,
      metadata: {
        sourcePythonModule: 'logic/external_provers/lazy_installer.py',
        serverCallsAllowed: false,
        pythonRuntimeAllowed: false,
      },
    });

    expect(
      ensure_external_prover_lazy_installed(
        { prover: 'vampire', logic: supportedLogic },
        installer,
      ),
    ).toMatchObject({ state: 'unsupported', available: false });

    expect(installer.install({ prover: 'auto', logic: supportedLogic })).toMatchObject({
      state: 'validation_failed',
      available: false,
    });
  });
});

import {
  BrowserNativeExternalProversBridge,
  createBrowserNativeExternalProversBridge,
  type ExternalProverBridgeName,
} from './externalProversBridge';
import type { BrowserNativeProofLogic } from './proverAdapters';

export interface ExternalProverLazyInstallerMetadata {
  sourcePythonModule: 'logic/external_provers/lazy_installer.py';
  runtime: 'typescript-wasm-browser';
  browserNative: true;
  serverCallsAllowed: false;
  pythonRuntimeAllowed: false;
  subprocessAllowed: false;
  filesystemAllowed: false;
  rpcAllowed: false;
  failClosed: true;
  parity: Array<unknown>;
}

export const EXTERNAL_PROVER_LAZY_INSTALLER_METADATA: ExternalProverLazyInstallerMetadata = {
  sourcePythonModule: 'logic/external_provers/lazy_installer.py',
  runtime: 'typescript-wasm-browser',
  browserNative: true,
  serverCallsAllowed: false,
  pythonRuntimeAllowed: false,
  subprocessAllowed: false,
  filesystemAllowed: false,
  rpcAllowed: false,
  failClosed: true,
  parity: ['validation_only_no_runtime_install', 'browser_native_adapter_gate', 'fail_closed'],
};

export type ExternalProverLazyInstallState = 'ready' | 'unsupported' | 'validation_failed';

export interface ExternalProverLazyInstallRequest {
  prover: ExternalProverBridgeName;
  logic: BrowserNativeProofLogic;
}

export interface ExternalProverLazyInstallStatus {
  prover: ExternalProverBridgeName;
  logic: BrowserNativeProofLogic;
  state: ExternalProverLazyInstallState;
  available: boolean;
  message: string;
  metadata: ExternalProverLazyInstallerMetadata;
}

export class BrowserNativeExternalProverLazyInstaller {
  readonly metadata: ExternalProverLazyInstallerMetadata = EXTERNAL_PROVER_LAZY_INSTALLER_METADATA;

  private readonly bridge: BrowserNativeExternalProversBridge;

  constructor(
    bridge: BrowserNativeExternalProversBridge = createBrowserNativeExternalProversBridge(),
  ) {
    this.bridge = bridge;
  }

  ensureInstalled(request: ExternalProverLazyInstallRequest): ExternalProverLazyInstallStatus {
    if (request.prover === 'auto') {
      return this.createStatus(
        request,
        'validation_failed',
        false,
        'Auto prover cannot be lazily installed; choose an explicit browser-native prover.',
      );
    }

    const proverInfo = this.bridge.getProverInfo(request.prover);
    if (!proverInfo.available) {
      return this.createStatus(
        request,
        'unsupported',
        false,
        proverInfo.failClosedReason ??
          `${request.prover} has no browser-native TypeScript/WASM adapter in this build.`,
      );
    }

    if (!this.bridge.supports(request.prover, request.logic)) {
      return this.createStatus(
        request,
        'unsupported',
        false,
        `${request.prover} is available but does not support ${request.logic}.`,
      );
    }

    return this.createStatus(
      request,
      'ready',
      true,
      `${request.prover} is available through a browser-native adapter.`,
    );
  }

  install(request: ExternalProverLazyInstallRequest): ExternalProverLazyInstallStatus {
    return this.ensureInstalled(request);
  }

  private createStatus(
    request: ExternalProverLazyInstallRequest,
    state: ExternalProverLazyInstallState,
    available: boolean,
    message: string,
  ): ExternalProverLazyInstallStatus {
    return {
      prover: request.prover,
      logic: request.logic,
      state,
      available,
      message,
      metadata: this.metadata,
    };
  }
}

export function createBrowserNativeExternalProverLazyInstaller(): BrowserNativeExternalProverLazyInstaller {
  return new BrowserNativeExternalProverLazyInstaller();
}

export const create_browser_native_external_prover_lazy_installer =
  createBrowserNativeExternalProverLazyInstaller;

export function ensure_external_prover_lazy_installed(
  request: ExternalProverLazyInstallRequest,
  installer: BrowserNativeExternalProverLazyInstaller = createBrowserNativeExternalProverLazyInstaller(),
): ExternalProverLazyInstallStatus {
  return installer.ensureInstalled(request);
}

export const install_external_prover_lazy = ensure_external_prover_lazy_installed;

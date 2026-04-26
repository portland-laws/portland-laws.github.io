import { getLogicRuntimeCapabilities } from './runtimeCapabilities';

export interface BrowserLogicFeatureSet {
  webAssembly: boolean;
  webCrypto: boolean;
  indexedDb: boolean;
  webGpu: boolean;
  transformersJsDependency: boolean;
  onnxRuntimeWebDependency: boolean;
  serverCallsAllowed: false;
  fullPythonParityTarget: true;
}

export function truthy(value: string | null | undefined): boolean {
  return ['1', 'true', 'yes', 'on'].includes(String(value ?? '').trim().toLowerCase());
}

export function warnOptionalImportsEnabled(env: Record<string, string | undefined> = getProcessEnv()): boolean {
  return truthy(env.IPFS_DATASETS_PY_WARN_OPTIONAL_IMPORTS);
}

export function minimalImportsEnabled(env: Record<string, string | undefined> = getProcessEnv()): boolean {
  return truthy(env.IPFS_DATASETS_PY_MINIMAL_IMPORTS) || truthy(env.IPFS_DATASETS_PY_BENCHMARK);
}

export function optionalImportNotice(message: string, env?: Record<string, string | undefined>): void {
  if (warnOptionalImportsEnabled(env)) {
    console.warn(message);
  }
}

export function detectBrowserLogicFeatures(scope: Partial<typeof globalThis> = globalThis): BrowserLogicFeatureSet {
  return {
    webAssembly: typeof scope.WebAssembly === 'object',
    webCrypto: Boolean(scope.crypto?.subtle),
    indexedDb: Boolean(scope.indexedDB),
    webGpu: Boolean((scope.navigator as Navigator & { gpu?: unknown } | undefined)?.gpu),
    transformersJsDependency: true,
    onnxRuntimeWebDependency: true,
    serverCallsAllowed: getLogicRuntimeCapabilities().serverCallsAllowed,
    fullPythonParityTarget: true,
  };
}

export class FeatureDetector {
  static hasSymbolicAi(): boolean {
    return false;
  }

  static hasZ3(): boolean {
    return false;
  }

  static hasSpacy(): boolean {
    return false;
  }

  static hasSpacyModel(): boolean {
    return false;
  }

  static hasXgboost(): boolean {
    return false;
  }

  static hasLightgbm(): boolean {
    return false;
  }

  static hasMlModels(): boolean {
    return detectBrowserLogicFeatures().transformersJsDependency || detectBrowserLogicFeatures().onnxRuntimeWebDependency;
  }

  static hasIpfs(): boolean {
    return false;
  }

  static hasBrowserWasm(): boolean {
    return detectBrowserLogicFeatures().webAssembly;
  }

  static hasBrowserCrypto(): boolean {
    return detectBrowserLogicFeatures().webCrypto;
  }
}

export function clearFeatureDetectionCache(): void {
  // Browser feature probing is side-effect free and currently has no internal cache.
}

function getProcessEnv(): Record<string, string | undefined> {
  return typeof process !== 'undefined' ? process.env : {};
}

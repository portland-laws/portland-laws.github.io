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

export type LogicFeatureName =
  | 'symbolicAi'
  | 'z3'
  | 'spacy'
  | 'spacyModel'
  | 'xgboost'
  | 'lightgbm'
  | 'mlModels'
  | 'ipfs'
  | 'browserWasm'
  | 'browserCrypto';

export type LogicFeatureStatus = 'available' | 'unavailable' | 'adapter';

export interface LogicFeatureAvailability {
  name: LogicFeatureName;
  available: boolean;
  status: LogicFeatureStatus;
  browserNative: boolean;
}

export interface FeatureDetectionOptions {
  scope?: Partial<typeof globalThis>;
  localAdapters?: Partial<Record<LogicFeatureName, boolean>>;
}

const LOGIC_FEATURE_NAMES: Array<LogicFeatureName> = [
  'symbolicAi',
  'z3',
  'spacy',
  'spacyModel',
  'xgboost',
  'lightgbm',
  'mlModels',
  'ipfs',
  'browserWasm',
  'browserCrypto',
];

const PYTHON_ONLY_FEATURES = new Set<LogicFeatureName>(LOGIC_FEATURE_NAMES.slice(0, 6));

export function truthy(value: string | null | undefined): boolean {
  return ['1', 'true', 'yes', 'on'].includes(
    String(value ?? '')
      .trim()
      .toLowerCase(),
  );
}

export function warnOptionalImportsEnabled(
  env: Record<string, string | undefined> = getProcessEnv(),
): boolean {
  return truthy(env.IPFS_DATASETS_PY_WARN_OPTIONAL_IMPORTS);
}

export function minimalImportsEnabled(
  env: Record<string, string | undefined> = getProcessEnv(),
): boolean {
  return truthy(env.IPFS_DATASETS_PY_MINIMAL_IMPORTS) || truthy(env.IPFS_DATASETS_PY_BENCHMARK);
}

export function optionalImportNotice(
  message: string,
  env?: Record<string, string | undefined>,
): void {
  if (warnOptionalImportsEnabled(env)) {
    console.warn(message);
  }
}

export function detectBrowserLogicFeatures(
  scope: Partial<typeof globalThis> = globalThis,
  options: Pick<FeatureDetectionOptions, 'localAdapters'> = {},
): BrowserLogicFeatureSet {
  return {
    webAssembly: typeof scope.WebAssembly === 'object',
    webCrypto: Boolean(scope.crypto?.subtle),
    indexedDb: Boolean(scope.indexedDB),
    webGpu: Boolean((scope.navigator as (Navigator & { gpu?: unknown }) | undefined)?.gpu),
    transformersJsDependency: options.localAdapters?.mlModels !== false,
    onnxRuntimeWebDependency: options.localAdapters?.mlModels !== false,
    serverCallsAllowed: getLogicRuntimeCapabilities().serverCallsAllowed,
    fullPythonParityTarget: true,
  };
}

export function getFeatureAvailability(
  name: LogicFeatureName,
  options: FeatureDetectionOptions = {},
): LogicFeatureAvailability {
  const scope = options.scope ?? globalThis;
  const adapterAvailable = options.localAdapters?.[name] === true;
  const browserFeatures = detectBrowserLogicFeatures(scope, options);

  if (PYTHON_ONLY_FEATURES.has(name)) {
    return {
      name,
      available: adapterAvailable,
      status: adapterAvailable ? 'adapter' : 'unavailable',
      browserNative: adapterAvailable,
    };
  }

  if (name === 'mlModels') {
    const available =
      adapterAvailable ||
      browserFeatures.transformersJsDependency ||
      browserFeatures.onnxRuntimeWebDependency;
    return {
      name,
      available,
      status: adapterAvailable ? 'adapter' : available ? 'available' : 'unavailable',
      browserNative: available,
    };
  }

  if (name === 'ipfs') {
    return {
      name,
      available: adapterAvailable,
      status: adapterAvailable ? 'adapter' : 'unavailable',
      browserNative: adapterAvailable,
    };
  }

  const available =
    name === 'browserWasm' ? browserFeatures.webAssembly : browserFeatures.webCrypto;
  return {
    name,
    available,
    status: available ? 'available' : 'unavailable',
    browserNative: available,
  };
}

export function listFeatureAvailability(
  options: FeatureDetectionOptions = {},
): Array<LogicFeatureAvailability> {
  return LOGIC_FEATURE_NAMES.map((name) => getFeatureAvailability(name, options));
}

export class FeatureDetector {
  static hasSymbolicAi(options?: FeatureDetectionOptions): boolean {
    return getFeatureAvailability('symbolicAi', options).available;
  }

  static hasZ3(options?: FeatureDetectionOptions): boolean {
    return getFeatureAvailability('z3', options).available;
  }

  static hasSpacy(options?: FeatureDetectionOptions): boolean {
    return getFeatureAvailability('spacy', options).available;
  }

  static hasSpacyModel(options?: FeatureDetectionOptions): boolean {
    return getFeatureAvailability('spacyModel', options).available;
  }

  static hasXgboost(options?: FeatureDetectionOptions): boolean {
    return getFeatureAvailability('xgboost', options).available;
  }

  static hasLightgbm(options?: FeatureDetectionOptions): boolean {
    return getFeatureAvailability('lightgbm', options).available;
  }

  static hasMlModels(options?: FeatureDetectionOptions): boolean {
    return getFeatureAvailability('mlModels', options).available;
  }

  static hasIpfs(options?: FeatureDetectionOptions): boolean {
    return getFeatureAvailability('ipfs', options).available;
  }

  static hasBrowserWasm(options?: FeatureDetectionOptions): boolean {
    return getFeatureAvailability('browserWasm', options).available;
  }

  static hasBrowserCrypto(options?: FeatureDetectionOptions): boolean {
    return getFeatureAvailability('browserCrypto', options).available;
  }
}

export function clearFeatureDetectionCache(): void {
  // Browser feature probing is side-effect free and currently has no internal cache.
}

function getProcessEnv(): Record<string, string | undefined> {
  return typeof process !== 'undefined' ? process.env : {};
}

import {
  FeatureDetector,
  detectBrowserLogicFeatures,
  getFeatureAvailability,
  listFeatureAvailability,
  minimalImportsEnabled,
  truthy,
  warnOptionalImportsEnabled,
} from './featureDetection';

describe('featureDetection', () => {
  it('matches Python truthy environment parsing', () => {
    expect(truthy('1')).toBe(true);
    expect(truthy('true')).toBe(true);
    expect(truthy('yes')).toBe(true);
    expect(truthy('on')).toBe(true);
    expect(truthy('0')).toBe(false);
    expect(truthy(undefined)).toBe(false);
  });

  it('checks warning and minimal-import flags without importing optional modules', () => {
    expect(warnOptionalImportsEnabled({ IPFS_DATASETS_PY_WARN_OPTIONAL_IMPORTS: 'yes' })).toBe(
      true,
    );
    expect(minimalImportsEnabled({ IPFS_DATASETS_PY_MINIMAL_IMPORTS: 'true' })).toBe(true);
    expect(minimalImportsEnabled({ IPFS_DATASETS_PY_BENCHMARK: '1' })).toBe(true);
  });

  it('detects browser-native feature availability from an injected scope', () => {
    expect(
      detectBrowserLogicFeatures({
        WebAssembly: {} as typeof WebAssembly,
        crypto: { subtle: {} as SubtleCrypto } as Crypto,
        indexedDB: {} as IDBFactory,
        navigator: { gpu: {} } as unknown as Navigator,
      }),
    ).toEqual({
      webAssembly: true,
      webCrypto: true,
      indexedDb: true,
      webGpu: true,
      transformersJsDependency: true,
      onnxRuntimeWebDependency: true,
      serverCallsAllowed: false,
      fullPythonParityTarget: true,
    });
  });

  it('keeps Python-only optional dependencies unavailable in the browser detector', () => {
    expect(FeatureDetector.hasSpacy()).toBe(false);
    expect(FeatureDetector.hasZ3()).toBe(false);
    expect(FeatureDetector.hasMlModels()).toBe(true);
  });

  it('reports fail-closed Python optional dependency status without imports', () => {
    expect(getFeatureAvailability('spacy')).toMatchObject({
      available: false,
      status: 'unavailable',
    });
  });

  it('accepts explicit browser-native local adapters for Python parity surfaces', () => {
    const options = {
      scope: {
        WebAssembly: {} as typeof WebAssembly,
        crypto: { subtle: {} as SubtleCrypto } as Crypto,
      },
      localAdapters: { spacy: true, ipfs: true },
    };

    expect(FeatureDetector.hasSpacy(options)).toBe(true);
    expect(getFeatureAvailability('ipfs', options)).toMatchObject({
      available: true,
      status: 'adapter',
      browserNative: true,
    });
  });

  it('lists deterministic feature availability for validation surfaces', () => {
    const features = listFeatureAvailability({
      scope: {
        WebAssembly: {} as typeof WebAssembly,
        crypto: { subtle: {} as SubtleCrypto } as Crypto,
      },
      localAdapters: { mlModels: false },
    });

    expect(features).toHaveLength(10);
    expect(features.map((feature) => feature.name)).toContain('spacy');
    expect(features.map((feature) => feature.name)).toContain('browserWasm');
    expect(features.find((feature) => feature.name === 'mlModels')).toMatchObject({
      available: false,
      status: 'unavailable',
    });
  });
});

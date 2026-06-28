import {
  CecGrammarArtifact,
  CecGrammarData,
  CecGrammarEngine,
  CecGrammarLoader,
  CecGrammarValidationResult,
  createDefaultCecGrammarLoader,
} from './grammarEngine';

type CecGrammarLoaderMetadata = {
  readonly sourcePythonModule: 'logic/CEC/native/grammar_loader.py';
  readonly runtime: 'browser-native-typescript';
  readonly implementation: 'deterministic-in-memory-grammar-loader';
  readonly externalResourcePolicy: 'none';
};

export interface CecNativeGrammarLoaderCapabilities {
  readonly browserNative: true;
  readonly pythonRuntime: false;
  readonly serverRuntime: false;
  readonly filesystem: false;
  readonly subprocess: false;
  readonly rpc: false;
  readonly wasmCompatible: true;
  readonly wasmRequired: false;
  readonly implementation: 'deterministic-typescript';
  readonly pythonModule: 'logic/CEC/native/grammar_loader.py';
  readonly artifactSources: readonly ['in-memory'];
  readonly externalResourcePolicy: 'none';
}

export interface CecNativeGrammarLoadResult {
  readonly ok: boolean;
  readonly name: string;
  readonly loader?: CecGrammarLoader;
  readonly engine?: CecGrammarEngine;
  readonly artifact?: CecGrammarArtifact;
  readonly validation: CecGrammarValidationResult;
  readonly errors: readonly string[];
  readonly metadata: CecGrammarLoaderMetadata;
}

const DEFAULT_ARTIFACT_NAME = 'default-cec-grammar';
const METADATA: CecGrammarLoaderMetadata = {
  sourcePythonModule: 'logic/CEC/native/grammar_loader.py',
  runtime: 'browser-native-typescript',
  implementation: 'deterministic-in-memory-grammar-loader',
  externalResourcePolicy: 'none',
};
const CAPABILITIES: CecNativeGrammarLoaderCapabilities = {
  browserNative: true,
  pythonRuntime: false,
  serverRuntime: false,
  filesystem: false,
  subprocess: false,
  rpc: false,
  wasmCompatible: true,
  wasmRequired: false,
  implementation: 'deterministic-typescript',
  pythonModule: 'logic/CEC/native/grammar_loader.py',
  artifactSources: ['in-memory'],
  externalResourcePolicy: 'none',
};

export class CecNativeGrammarLoader {
  private readonly registry = new Map<string, CecGrammarData>();

  constructor(initialArtifacts: Record<string, CecGrammarData> = {}) {
    Object.entries(initialArtifacts).forEach(([name, artifact]) =>
      this.registerArtifact(name, artifact),
    );
  }

  getCapabilities(): CecNativeGrammarLoaderCapabilities {
    return CAPABILITIES;
  }

  registerArtifact(name: string, artifact: CecGrammarData): void {
    const normalized = normalizeArtifactName(name);
    if (normalized.length === 0)
      throw new Error('CEC grammar artifacts require a non-empty registry name.');
    this.registry.set(normalized, artifact);
  }

  listRegisteredArtifacts(): string[] {
    return [...this.registry.keys()].sort();
  }

  loadDefaultGrammar(): CecNativeGrammarLoadResult {
    return this.loadFromLoader(DEFAULT_ARTIFACT_NAME, createDefaultCecGrammarLoader());
  }

  loadRegisteredGrammar(name: string): CecNativeGrammarLoadResult {
    const normalized = normalizeArtifactName(name);
    const artifact = this.registry.get(normalized);
    return artifact
      ? this.loadStaticGrammar(normalized, artifact)
      : failClosed(normalized, `No in-memory CEC grammar artifact is registered as ${name}.`);
  }

  loadStaticGrammar(name: string, artifact: CecGrammarData): CecNativeGrammarLoadResult {
    return this.loadFromLoader(normalizeArtifactName(name), new CecGrammarLoader(artifact));
  }

  private loadFromLoader(name: string, loader: CecGrammarLoader): CecNativeGrammarLoadResult {
    const validation = loader.validateDetailed();
    if (!validation.valid) {
      return {
        ok: false,
        name,
        validation,
        errors: validation.issues.map((issue) => issue.message),
        metadata: METADATA,
      };
    }
    const engine = new CecGrammarEngine({ caseSensitive: loader.getConfig().caseSensitive });
    engine.setupFromLoader(loader);
    return {
      ok: true,
      name,
      loader,
      engine,
      artifact: loader.getArtifact(),
      validation,
      errors: [],
      metadata: METADATA,
    };
  }
}

export function createCecNativeGrammarLoader(
  initialArtifacts: Record<string, CecGrammarData> = {},
): CecNativeGrammarLoader {
  return new CecNativeGrammarLoader(initialArtifacts);
}

export function getCecNativeGrammarLoaderCapabilities(): CecNativeGrammarLoaderCapabilities {
  return CAPABILITIES;
}

function failClosed(name: string, error: string): CecNativeGrammarLoadResult {
  return {
    ok: false,
    name,
    validation: { valid: false, issues: [{ code: 'artifact-not-found', message: error }] },
    errors: [error],
    metadata: METADATA,
  };
}

function normalizeArtifactName(name: string): string {
  return String(name).trim().toLowerCase();
}

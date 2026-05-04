import {
  BrowserNativeInteractiveFolConstructor,
  type FolConstructorSession,
  type InteractiveFolConstructionOptions,
  type InteractiveFolConstructionResult,
  createBrowserNativeInteractiveFolConstructor,
} from './interactive/folConstructorIo';

export interface IntegrationInteractiveFolConstructorMetadata {
  sourcePythonModule: 'logic/integration/interactive_fol_constructor.py';
  browserNative: true;
  serverCallsAllowed: false;
  pythonRuntime: false;
  runtimeDependencies: Array<string>;
  implementation: 'browser-native-typescript';
  delegatesTo: 'logic/integration/interactive/interactive_fol_constructor.py';
}

export interface IntegrationInteractiveFolConstructionResult {
  ok: boolean;
  session: FolConstructorSession;
  formula: string;
  questions: InteractiveFolConstructionResult['questions'];
  symbols: InteractiveFolConstructionResult['symbols'];
  errors: Array<string>;
  metadata: IntegrationInteractiveFolConstructorMetadata;
}

export const INTEGRATION_INTERACTIVE_FOL_CONSTRUCTOR_METADATA: IntegrationInteractiveFolConstructorMetadata =
  {
    sourcePythonModule: 'logic/integration/interactive_fol_constructor.py',
    browserNative: true,
    serverCallsAllowed: false,
    pythonRuntime: false,
    runtimeDependencies: [],
    implementation: 'browser-native-typescript',
    delegatesTo: 'logic/integration/interactive/interactive_fol_constructor.py',
  };

export class BrowserNativeIntegrationInteractiveFolConstructor {
  readonly metadata = INTEGRATION_INTERACTIVE_FOL_CONSTRUCTOR_METADATA;
  private readonly constructorCore: BrowserNativeInteractiveFolConstructor;

  constructor(constructorCore = createBrowserNativeInteractiveFolConstructor()) {
    this.constructorCore = constructorCore;
  }

  construct(
    text: string,
    options: InteractiveFolConstructionOptions = {},
  ): IntegrationInteractiveFolConstructionResult {
    return this.withRootMetadata(this.constructorCore.construct(text, options));
  }

  continueSession(
    session: FolConstructorSession,
    text: string,
    options: InteractiveFolConstructionOptions = {},
  ): IntegrationInteractiveFolConstructionResult {
    return this.withRootMetadata(this.constructorCore.continueSession(session, text, options));
  }

  constructBatch(
    inputs: Array<string>,
    options: InteractiveFolConstructionOptions = {},
  ): Array<IntegrationInteractiveFolConstructionResult> {
    let session: FolConstructorSession | undefined;
    const results: Array<IntegrationInteractiveFolConstructionResult> = [];
    for (const input of inputs) {
      const result =
        session === undefined
          ? this.construct(input, options)
          : this.continueSession(session, input, options);
      session = result.session;
      results.push(result);
    }
    return results;
  }

  private withRootMetadata(
    result: InteractiveFolConstructionResult,
  ): IntegrationInteractiveFolConstructionResult {
    return {
      ok: result.ok,
      session: result.session,
      formula: result.formula,
      questions: result.questions,
      symbols: result.symbols,
      errors: result.errors,
      metadata: this.metadata,
    };
  }
}

export function createBrowserNativeIntegrationInteractiveFolConstructor(): BrowserNativeIntegrationInteractiveFolConstructor {
  return new BrowserNativeIntegrationInteractiveFolConstructor();
}

export const create_browser_native_integration_interactive_fol_constructor =
  createBrowserNativeIntegrationInteractiveFolConstructor;
export const integration_interactive_fol_constructor_metadata =
  INTEGRATION_INTERACTIVE_FOL_CONSTRUCTOR_METADATA;

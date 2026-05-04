import { runComprehensiveBenchmarks } from './benchmarks';
import {
  DeonticConverter,
  type DeonticConverterOptions,
  type DeonticFormula,
} from './deontic/converter';
import { FOLConverter, type FolConverterOptions, type FolFormula } from './fol/converter';
import {
  BrowserNativeLogicBridge,
  type BridgeProofRequest,
  type LogicBridgeFormat,
} from './integration/bridge';
import { LogicBridgeError } from './errors';
import { getGlobalMonitor, type LogicMonitor } from './monitoring';
import { compileDcecNlToPolicy } from './cec/nlConverter';
import type { ConversionResult } from './converters';
import type { LogicBridgeConversionResult, ProofResult } from './types';

export interface LogicApiOptions {
  fol?: FolConverterOptions;
  deontic?: DeonticConverterOptions;
  bridge?: BrowserNativeLogicBridge;
  monitor?: LogicMonitor;
}

export interface NlPolicyCompileResult {
  success: boolean;
  sourceText: string;
  policyFormula: string;
  warnings: string[];
  metadata: Record<string, unknown>;
  capabilities: {
    serverCallsAllowed: false;
    ucanSigningAvailable: false;
  };
}

export interface NlPolicyEvaluationResult extends NlPolicyCompileResult {
  tool: string;
  actor?: string;
  allowed: boolean;
  reason: string;
}

export interface SignedDelegationResult {
  success: false;
  status: 'unsupported';
  nlText: string;
  audienceDid: string;
  error: string;
  capabilities: {
    serverCallsAllowed: false;
    ucanSigningAvailable: false;
  };
}

export class BrowserNativeLogicApi {
  readonly folConverter: FOLConverter;
  readonly deonticConverter: DeonticConverter;
  readonly bridge: BrowserNativeLogicBridge;
  readonly monitor: LogicMonitor;

  constructor(options: LogicApiOptions = {}) {
    this.folConverter = new FOLConverter(options.fol);
    this.deonticConverter = new DeonticConverter(options.deontic);
    this.bridge =
      options.bridge ??
      new BrowserNativeLogicBridge({
        fol: options.fol,
        deontic: options.deontic,
      });
    this.monitor = options.monitor ?? getGlobalMonitor();
  }

  convertTextToFol(text: string): ConversionResult<FolFormula> {
    const startedAt = nowSeconds();
    const result = this.folConverter.convert(text);
    this.monitor.recordOperation(
      'api.convert_text_to_fol',
      result.success,
      nowSeconds() - startedAt,
    );
    return result;
  }

  convertLegalTextToDeontic(text: string): ConversionResult<DeonticFormula> {
    const startedAt = nowSeconds();
    const result = this.deonticConverter.convert(text);
    this.monitor.recordOperation(
      'api.convert_legal_text_to_deontic',
      result.success,
      nowSeconds() - startedAt,
    );
    return result;
  }

  convertLogic(
    source: string,
    sourceFormat: LogicBridgeFormat,
    targetFormat: LogicBridgeFormat,
  ): LogicBridgeConversionResult {
    const startedAt = nowSeconds();
    const result = this.bridge.convert(source, sourceFormat, targetFormat);
    this.monitor.recordOperation(
      'api.convert_logic',
      result.isSuccessful(),
      nowSeconds() - startedAt,
    );
    return result;
  }

  prove(request: BridgeProofRequest): ProofResult {
    const startedAt = nowSeconds();
    const result = this.bridge.prove(request);
    this.monitor.recordOperation('api.prove', result.status === 'proved', nowSeconds() - startedAt);
    return result;
  }

  compileNlToPolicy(text: string): NlPolicyCompileResult {
    const compiled = compileDcecNlToPolicy(text);
    return {
      success: compiled.success,
      sourceText: text,
      policyFormula: compiled.policy_formula,
      warnings: compiled.errors,
      metadata: {
        ...compiled.metadata,
        policy_rule_count: compiled.policy_rules.length,
        parse_method: compiled.parse_method,
        browser_native_policy_compiler: true,
      },
      capabilities: {
        serverCallsAllowed: false,
        ucanSigningAvailable: false,
      },
    };
  }

  evaluateNlPolicy(
    nlText: string,
    options: { tool: string; actor?: string },
  ): NlPolicyEvaluationResult {
    const compiled = this.compileNlToPolicy(nlText);
    const normalizedFormula = compiled.policyFormula.toLowerCase();
    const normalizedTool = options.tool.toLowerCase().replace(/[_-]+/g, ' ');
    const allowed =
      compiled.success &&
      normalizedFormula.includes(normalizedTool.split(/\s+/)[0] ?? normalizedTool);
    return {
      ...compiled,
      tool: options.tool,
      actor: options.actor,
      allowed,
      reason: allowed
        ? 'Policy formula references the requested tool/action through the local deontic compiler.'
        : 'No local policy grant matched the requested tool/action.',
    };
  }

  async buildSignedDelegation(
    nlText: string,
    options: { audienceDid: string },
  ): Promise<SignedDelegationResult> {
    return {
      success: false,
      status: 'unsupported',
      nlText,
      audienceDid: options.audienceDid,
      error: 'UCAN signing is not yet ported to browser-native crypto/WASM.',
      capabilities: {
        serverCallsAllowed: false,
        ucanSigningAvailable: false,
      },
    };
  }

  async runBenchmarks(): Promise<Record<string, unknown>> {
    return runComprehensiveBenchmarks();
  }
}

let globalApi: BrowserNativeLogicApi | undefined;

export function createLogicApi(options: LogicApiOptions = {}): BrowserNativeLogicApi {
  return new BrowserNativeLogicApi(options);
}

export function getGlobalLogicApi(): BrowserNativeLogicApi {
  globalApi ??= new BrowserNativeLogicApi();
  return globalApi;
}

export function resetGlobalLogicApi(): void {
  globalApi = undefined;
}

export function convertTextToFol(
  text: string,
  options: FolConverterOptions = {},
): ConversionResult<FolFormula> {
  return new BrowserNativeLogicApi({ fol: options }).convertTextToFol(text);
}

export function convertLegalTextToDeontic(
  text: string,
  options: DeonticConverterOptions = {},
): ConversionResult<DeonticFormula> {
  return new BrowserNativeLogicApi({ deontic: options }).convertLegalTextToDeontic(text);
}

export function convertLogic(
  source: string,
  sourceFormat: LogicBridgeFormat,
  targetFormat: LogicBridgeFormat,
): LogicBridgeConversionResult {
  return getGlobalLogicApi().convertLogic(source, sourceFormat, targetFormat);
}

export function proveLogic(request: BridgeProofRequest): ProofResult {
  return getGlobalLogicApi().prove(request);
}

export function compileNlToPolicy(text: string): NlPolicyCompileResult {
  return getGlobalLogicApi().compileNlToPolicy(text);
}

export function evaluateNlPolicy(
  nlText: string,
  options: { tool: string; actor?: string },
): NlPolicyEvaluationResult {
  return getGlobalLogicApi().evaluateNlPolicy(nlText, options);
}

export function buildSignedDelegation(
  nlText: string,
  options: { audienceDid: string },
): Promise<SignedDelegationResult> {
  return getGlobalLogicApi().buildSignedDelegation(nlText, options);
}

export const convert_text_to_fol = convertTextToFol;
export const convert_legal_text_to_deontic = convertLegalTextToDeontic;
export const compile_nl_to_policy = compileNlToPolicy;
export const evaluate_nl_policy = evaluateNlPolicy;
export const build_signed_delegation = buildSignedDelegation;

export function requireBrowserNativeSignedDelegation(): never {
  throw new LogicBridgeError('UCAN signing requires a future browser-native crypto/WASM port.');
}

function nowSeconds(): number {
  return (globalThis.performance?.now?.() ?? Date.now()) / 1000;
}

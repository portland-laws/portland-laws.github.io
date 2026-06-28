import {
  BrowserNativeNlUcanPolicyCompiler,
  type NlUcanPolicyCapability,
  type NlUcanPolicyCompilationResult,
  type NlUcanPolicyCompilerOptions,
  type NlUcanPolicyDelegation,
} from './nlUcanPolicyCompiler';

export interface UcanPolicyBridgeOptions extends NlUcanPolicyCompilerOptions {
  readonly issuer: string;
  readonly audience: string;
}

export interface UcanPolicyBridgeResult {
  readonly ok: boolean;
  readonly success: boolean;
  readonly input: string;
  readonly capabilities: readonly NlUcanPolicyCapability[];
  readonly delegation?: NlUcanPolicyDelegation;
  readonly token?: string;
  readonly errors: readonly string[];
  readonly fail_closed_reason?: string;
  readonly metadata: typeof UCAN_POLICY_BRIDGE_METADATA;
}

export const UCAN_POLICY_BRIDGE_METADATA = {
  sourcePythonModule: 'logic/integration/ucan_policy_bridge.py',
  runtime: 'browser-native-typescript',
  browserNative: true,
  serverCallsAllowed: false,
  pythonRuntimeAllowed: false,
  filesystemAllowed: false,
  subprocessAllowed: false,
  rpcAllowed: false,
  signing: 'unsigned-local-policy-payload',
} as const;

export class BrowserNativeUcanPolicyBridge {
  readonly metadata = UCAN_POLICY_BRIDGE_METADATA;
  constructor(readonly compiler = new BrowserNativeNlUcanPolicyCompiler()) {}
  compile(text: string, options: UcanPolicyBridgeOptions): UcanPolicyBridgeResult {
    const errors = validateOptions(options);
    return errors.length > 0
      ? closed(text, errors, 'ucan_policy_bridge_invalid_options')
      : this.fromCompilation(this.compiler.compile(text, options));
  }
  fromCompilation(compiled: NlUcanPolicyCompilationResult): UcanPolicyBridgeResult {
    if (!compiled.ok || compiled.capabilities.length === 0) {
      return closed(
        compiled.input,
        compiled.errors.length > 0
          ? compiled.errors
          : ['No UCAN policy capabilities were compiled.'],
        compiled.fail_closed_reason ?? 'ucan_policy_bridge_compile_failed',
      );
    }
    const errors = validateDelegation(compiled.delegation);
    return errors.length > 0
      ? closed(compiled.input, errors, 'ucan_policy_bridge_invalid_delegation')
      : {
          ok: true,
          success: true,
          input: compiled.input,
          capabilities: compiled.capabilities,
          delegation: compiled.delegation,
          token: encodeUnsignedUcan(compiled.delegation),
          errors: [],
          metadata: this.metadata,
        };
  }
}

export const compileUcanPolicyBridge = (
  text: string,
  options: UcanPolicyBridgeOptions,
): UcanPolicyBridgeResult => new BrowserNativeUcanPolicyBridge().compile(text, options);
export const createUnsignedUcanPolicyToken = (
  delegation: NlUcanPolicyDelegation,
): {
  readonly ok: boolean;
  readonly token?: string;
  readonly errors: readonly string[];
  readonly metadata: typeof UCAN_POLICY_BRIDGE_METADATA;
} => {
  const errors = validateDelegation(delegation);
  return errors.length > 0
    ? { ok: false, errors, metadata: UCAN_POLICY_BRIDGE_METADATA }
    : {
        ok: true,
        token: encodeUnsignedUcan(delegation),
        errors: [],
        metadata: UCAN_POLICY_BRIDGE_METADATA,
      };
};
export const compile_ucan_policy_bridge = compileUcanPolicyBridge;
export const create_unsigned_ucan_policy_token = createUnsignedUcanPolicyToken;
export const create_ucan_policy_bridge = () => new BrowserNativeUcanPolicyBridge();

function validateOptions(options: UcanPolicyBridgeOptions): string[] {
  return [
    ...(!isDid(options.issuer) ? ['issuer must be a local DID string.'] : []),
    ...(!isDid(options.audience) ? ['audience must be a local DID string.'] : []),
    ...(options.expiration !== undefined && !positive(options.expiration)
      ? ['expiration must be a positive integer timestamp.']
      : []),
    ...(options.notBefore !== undefined && !positive(options.notBefore)
      ? ['notBefore must be a positive integer timestamp.']
      : []),
  ];
}

function validateDelegation(delegation: NlUcanPolicyDelegation): string[] {
  return [
    ...(!isDid(delegation.iss) ? ['delegation issuer is required and must be a DID.'] : []),
    ...(!isDid(delegation.aud) ? ['delegation audience is required and must be a DID.'] : []),
    ...(delegation.att.length === 0 ? ['delegation must include at least one capability.'] : []),
    ...(delegation.signed !== false
      ? ['browser-native bridge only emits unsigned local payloads.']
      : []),
  ];
}

function closed(input: string, errors: readonly string[], reason: string): UcanPolicyBridgeResult {
  return {
    ok: false,
    success: false,
    input,
    capabilities: [],
    errors,
    fail_closed_reason: reason,
    metadata: UCAN_POLICY_BRIDGE_METADATA,
  };
}

function isDid(value: string | undefined): value is string {
  return typeof value === 'string' && /^did:[a-z0-9]+:.+/iu.test(value.trim());
}

const positive = (value: number): boolean => Number.isInteger(value) && value > 0;
const encodeUnsignedUcan = (delegation: NlUcanPolicyDelegation): string =>
  `${base64UrlJson({ alg: 'none', typ: 'JWT', ucan: '0.9.1' })}.${base64UrlJson(delegation)}.`;
const base64UrlJson = (value: unknown): string =>
  btoa(unescape(encodeURIComponent(JSON.stringify(value))))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/g, '');

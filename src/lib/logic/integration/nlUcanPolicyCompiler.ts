import { compileDcecNlToPolicy, type DcecNlToPolicyCompilerResult } from '../cec/nlConverter';

export type NlUcanDeonticOperator = 'O' | 'P' | 'F';
export type NlUcanEffect = 'can' | 'deny' | 'must';

export interface NlUcanPolicyCompilerOptions {
  readonly issuer?: string;
  readonly audience?: string;
  readonly expiration?: number;
  readonly notBefore?: number;
  readonly proofs?: readonly string[];
}

export interface NlUcanPolicyCapability {
  readonly with: string;
  readonly can: string;
  readonly nb: Record<string, unknown>;
  readonly deonticOperator: NlUcanDeonticOperator;
  readonly effect: NlUcanEffect;
  readonly sourceRuleIndex: number;
}

export interface NlUcanPolicyDelegation {
  readonly iss?: string;
  readonly aud?: string;
  readonly exp?: number;
  readonly nbf?: number;
  readonly att: readonly NlUcanPolicyCapability[];
  readonly prf?: readonly string[];
  readonly signed: false;
}

export interface NlUcanPolicyCompilationResult {
  readonly ok: boolean;
  readonly success: boolean;
  readonly input: string;
  readonly policy: DcecNlToPolicyCompilerResult;
  readonly capabilities: readonly NlUcanPolicyCapability[];
  readonly delegation: NlUcanPolicyDelegation;
  readonly errors: readonly string[];
  readonly fail_closed_reason?: string;
  readonly metadata: typeof NL_UCAN_POLICY_COMPILER_METADATA;
}

export const NL_UCAN_POLICY_COMPILER_METADATA = {
  sourcePythonModule: 'logic/integration/nl_ucan_policy_compiler.py',
  runtime: 'browser-native-typescript',
  browserNative: true,
  serverCallsAllowed: false,
  pythonRuntimeAllowed: false,
  filesystemAllowed: false,
  subprocessAllowed: false,
  rpcAllowed: false,
  signing: 'unsigned-local-policy-payload',
} as const;

const OPERATOR_EFFECTS: Record<NlUcanDeonticOperator, NlUcanEffect> = {
  O: 'must',
  P: 'can',
  F: 'deny',
};

export class BrowserNativeNlUcanPolicyCompiler {
  readonly metadata = NL_UCAN_POLICY_COMPILER_METADATA;

  compile(text: string, options: NlUcanPolicyCompilerOptions = {}): NlUcanPolicyCompilationResult {
    const policy = compileDcecNlToPolicy(text);
    const capabilities = policy.policy_rules
      .map((rule) =>
        policyFormulaToCapability(rule.index, rule.normalized_text, rule.policy_formula),
      )
      .filter((capability): capability is NlUcanPolicyCapability => capability !== undefined);
    const errors = [...policy.errors];
    if (policy.ok && capabilities.length !== policy.policy_rules.length) {
      errors.push('One or more policy rules could not be projected to a UCAN capability.');
    }
    const ok =
      policy.ok && capabilities.length > 0 && capabilities.length === policy.policy_rules.length;
    return {
      ok,
      success: ok,
      input: text,
      policy,
      capabilities: ok ? capabilities : [],
      delegation: createDelegation(ok ? capabilities : [], options),
      errors: ok ? [] : errors.length > 0 ? errors : ['No UCAN policy capabilities were compiled.'],
      fail_closed_reason: ok
        ? undefined
        : (policy.fail_closed_reason ?? 'ucan_capability_compile_failed'),
      metadata: this.metadata,
    };
  }
}

export function compileNlUcanPolicy(
  text: string,
  options: NlUcanPolicyCompilerOptions = {},
): NlUcanPolicyCompilationResult {
  return new BrowserNativeNlUcanPolicyCompiler().compile(text, options);
}

export const compile_nl_ucan_policy = compileNlUcanPolicy;
export const create_nl_ucan_policy_compiler = () => new BrowserNativeNlUcanPolicyCompiler();

function createDelegation(
  capabilities: readonly NlUcanPolicyCapability[],
  options: NlUcanPolicyCompilerOptions,
): NlUcanPolicyDelegation {
  return {
    ...(options.issuer === undefined ? {} : { iss: options.issuer }),
    ...(options.audience === undefined ? {} : { aud: options.audience }),
    ...(options.expiration === undefined ? {} : { exp: options.expiration }),
    ...(options.notBefore === undefined ? {} : { nbf: options.notBefore }),
    att: capabilities,
    ...(options.proofs === undefined ? {} : { prf: options.proofs }),
    signed: false,
  };
}

function policyFormulaToCapability(
  sourceRuleIndex: number,
  normalizedText: string,
  policyFormula: string,
): NlUcanPolicyCapability | undefined {
  const match = /^([OPF])\[([^\]]+)\]\(([\w-]+)\(([^)]*)\)\)$/.exec(policyFormula.trim());
  if (!match) return undefined;
  const operator = match[1] as NlUcanDeonticOperator;
  const subject = cleanEntity(match[2]);
  const predicate = match[3];
  const args = match[4].split(',').map(cleanEntity).filter(Boolean);
  const resource = args.length > 1 ? args[args.length - 1] : subject;
  return {
    with: `urn:policy:${resource}`,
    can: `policy/${predicate}`,
    nb: {
      subject,
      arguments: args,
      predicate,
      source_text: normalizedText,
      requirement: operatorName(operator),
    },
    deonticOperator: operator,
    effect: OPERATOR_EFFECTS[operator],
    sourceRuleIndex,
  };
}

function cleanEntity(value: string): string {
  return value
    .trim()
    .replace(/:Agent$/u, '')
    .replace(/\s+/gu, '_');
}

function operatorName(operator: NlUcanDeonticOperator): string {
  const names: Record<NlUcanDeonticOperator, string> = {
    O: 'OBLIGATION',
    P: 'PERMISSION',
    F: 'PROHIBITION',
  };
  return names[operator];
}

import type { CecApplication, CecExpression, CecUnaryExpression } from './ast';
import { parseCecExpression } from './parser';

export interface DcecUcanCapability {
  readonly with: string;
  readonly can: string;
  readonly nb: Record<string, unknown>;
  readonly deonticOperator: 'O' | 'P' | 'F';
  readonly effect: 'can' | 'deny';
}
export interface DcecUcanDelegationPayload {
  readonly iss: string;
  readonly aud: string;
  readonly exp?: number;
  readonly nbf?: number;
  readonly att: readonly DcecUcanCapability[];
  readonly prf?: readonly string[];
}
export interface DcecToUcanResult {
  readonly ok: boolean;
  readonly capabilities: readonly DcecUcanCapability[];
  readonly errors: readonly string[];
  readonly metadata: typeof METADATA;
}

const METADATA = {
  sourcePythonModule: 'logic/CEC/nl/dcec_to_ucan_bridge.py',
  runtime: 'browser-native-typescript',
  browserNative: true,
  pythonRuntime: false,
  serverRuntime: false,
} as const;

export function dcecToUcan(source: string | CecExpression): DcecToUcanResult {
  const expression = typeof source === 'string' ? parseCecExpression(source) : source;
  const capabilities = collectCapabilities(expression);
  return capabilities.length > 0
    ? { ok: true, capabilities, errors: [], metadata: METADATA }
    : {
        ok: false,
        capabilities: [],
        errors: ['No deontic O, P, or F capability formula was found.'],
        metadata: METADATA,
      };
}

export function dcecToUcanCapabilities(
  source: string | CecExpression,
): readonly DcecUcanCapability[] {
  return dcecToUcan(source).capabilities;
}

export function createUnsignedDcecUcanDelegation(
  source: string | CecExpression,
  issuer: string,
  audience: string,
  options: {
    readonly expiration?: number;
    readonly notBefore?: number;
    readonly proofs?: readonly string[];
  } = {},
): {
  readonly ok: boolean;
  readonly token?: string;
  readonly payload?: DcecUcanDelegationPayload;
  readonly errors: readonly string[];
} {
  const converted = dcecToUcan(source);
  if (!converted.ok) return { ok: false, errors: converted.errors };
  const payload: DcecUcanDelegationPayload = {
    iss: issuer,
    aud: audience,
    ...(options.expiration === undefined ? {} : { exp: options.expiration }),
    ...(options.notBefore === undefined ? {} : { nbf: options.notBefore }),
    att: converted.capabilities,
    ...(options.proofs === undefined ? {} : { prf: options.proofs }),
  };
  return {
    ok: true,
    token: `${base64UrlJson({ alg: 'none', typ: 'JWT', ucan: '0.9.1' })}.${base64UrlJson(payload)}.`,
    payload,
    errors: [],
  };
}

export const dcec_to_ucan = dcecToUcan;
export const dcec_to_ucan_capabilities = dcecToUcanCapabilities;
export const create_unsigned_dcec_ucan_delegation = createUnsignedDcecUcanDelegation;

function collectCapabilities(expression: CecExpression): DcecUcanCapability[] {
  if (expression.kind === 'unary') {
    const capability = unaryToCapability(expression);
    return capability ? [capability] : collectCapabilities(expression.expression);
  }
  if (expression.kind === 'binary')
    return [...collectCapabilities(expression.left), ...collectCapabilities(expression.right)];
  if (expression.kind === 'quantified') return collectCapabilities(expression.expression);
  if (expression.kind === 'application')
    return expression.args.flatMap((arg) => collectCapabilities(arg));
  return [];
}

function unaryToCapability(expression: CecUnaryExpression): DcecUcanCapability | undefined {
  if (expression.operator !== 'O' && expression.operator !== 'P' && expression.operator !== 'F')
    return undefined;
  const application = unwrapApplication(expression.expression);
  if (!application) return undefined;
  const args = application.args.map(formatTerm);
  const resource = args.length > 1 ? args[args.length - 1] : (args[0] ?? application.name);
  return {
    with: `urn:dcec:${resource}`,
    can: `dcec/${application.name}`,
    nb: {
      arguments: args,
      predicate: application.name,
      requirement: operatorName(expression.operator),
    },
    deonticOperator: expression.operator,
    effect: expression.operator === 'F' ? 'deny' : 'can',
  };
}

function unwrapApplication(expression: CecExpression): CecApplication | undefined {
  if (expression.kind === 'application') return expression;
  if (expression.kind === 'unary' && ['always', 'eventually', 'next'].includes(expression.operator))
    return unwrapApplication(expression.expression);
  return undefined;
}

function operatorName(operator: 'O' | 'P' | 'F'): string {
  const names: Record<'O' | 'P' | 'F', string> = {
    O: 'OBLIGATION',
    P: 'PERMISSION',
    F: 'PROHIBITION',
  };
  return names[operator];
}

function formatTerm(expression: CecExpression): string {
  if (expression.kind === 'atom') return expression.name;
  if (expression.kind === 'application')
    return `${expression.name}(${expression.args.map(formatTerm).join(',')})`;
  if (expression.kind === 'unary')
    return `${expression.operator}(${formatTerm(expression.expression)})`;
  if (expression.kind === 'binary')
    return `${expression.operator}(${formatTerm(expression.left)},${formatTerm(expression.right)})`;
  return `${expression.quantifier}(${expression.variable},${formatTerm(expression.expression)})`;
}

function base64UrlJson(value: unknown): string {
  const binary = unescape(encodeURIComponent(JSON.stringify(value)));
  return base64Encode(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
}

function base64Encode(binary: string): string {
  const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';
  let output = '';
  for (let index = 0; index < binary.length; index += 3) {
    const a = binary.charCodeAt(index);
    const b = index + 1 < binary.length ? binary.charCodeAt(index + 1) : 0;
    const c = index + 2 < binary.length ? binary.charCodeAt(index + 2) : 0;
    const triplet = (a << 16) | (b << 8) | c;
    output += alphabet[(triplet >> 18) & 63] + alphabet[(triplet >> 12) & 63];
    output += index + 1 < binary.length ? alphabet[(triplet >> 6) & 63] : '=';
    output += index + 2 < binary.length ? alphabet[triplet & 63] : '=';
  }
  return output;
}

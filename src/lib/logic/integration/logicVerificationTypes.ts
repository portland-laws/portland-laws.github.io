import type {
  LogicVerificationFormat,
  LogicVerificationResult,
  LogicVerificationStatus,
} from './logicVerification';

export interface LogicVerificationTypesMetadata {
  sourcePythonModule: 'logic/integration/logic_verification_types.py';
  browserNative: true;
  serverCallsAllowed: false;
  pythonRuntimeAllowed: false;
  runtimeDependencies: Array<string>;
}

export type LogicVerificationTypeName = 'options' | 'result' | 'issue' | 'metadata';

export interface LogicVerificationTypeIssue {
  path: string;
  message: string;
}

export interface LogicVerificationTypeCheckResult {
  ok: boolean;
  typeName: LogicVerificationTypeName;
  issues: Array<LogicVerificationTypeIssue>;
  metadata: LogicVerificationTypesMetadata;
}

export const LOGIC_VERIFICATION_TYPES_METADATA: LogicVerificationTypesMetadata = {
  sourcePythonModule: 'logic/integration/logic_verification_types.py',
  browserNative: true,
  serverCallsAllowed: false,
  pythonRuntimeAllowed: false,
  runtimeDependencies: [],
};

const REQUIRED_FIELDS: Record<LogicVerificationTypeName, Array<string>> = {
  options: [],
  issue: ['severity', 'message'],
  metadata: ['browserNative', 'serverCallsAllowed', 'pythonRuntimeAllowed', 'runtimeDependencies'],
  result: [
    'status',
    'success',
    'formula',
    'format',
    'normalizedFormula',
    'checks',
    'issues',
    'metadata',
  ],
};

export function checkLogicVerificationType(
  typeName: LogicVerificationTypeName,
  value: unknown,
): LogicVerificationTypeCheckResult {
  const object = asRecord(value);
  const issues: Array<LogicVerificationTypeIssue> = [];
  if (!object) return checked(typeName, [{ path: '$', message: 'expected_object' }]);
  for (const field of REQUIRED_FIELDS[typeName]) {
    if (!(field in object)) issues.push({ path: `$.${field}`, message: 'missing_required_field' });
  }
  if (typeName === 'options') {
    if ('format' in object && !isFormat(object.format))
      issues.push({ path: '$.format', message: 'expected_logic_verification_format' });
    if ('requirePredicate' in object && typeof object.requirePredicate !== 'boolean')
      issues.push({ path: '$.requirePredicate', message: 'expected_boolean' });
  } else if (typeName === 'issue') validateIssue(value, '$', issues);
  else if (typeName === 'metadata') validateMetadata(object, '$', issues);
  else validateResult(object, issues);
  return checked(typeName, issues);
}

export function isLogicVerificationType(
  typeName: LogicVerificationTypeName,
  value: unknown,
): boolean {
  return checkLogicVerificationType(typeName, value).ok;
}

export function assertLogicVerificationResult(value: unknown): LogicVerificationResult {
  const result = checkLogicVerificationType('result', value);
  if (!result.ok)
    throw new TypeError(
      `Invalid logic verification result: ${result.issues.map((issue) => `${issue.path}:${issue.message}`).join(', ')}`,
    );
  return value as LogicVerificationResult;
}

export const logic_verification_types_metadata = LOGIC_VERIFICATION_TYPES_METADATA;
export const check_logic_verification_type = checkLogicVerificationType;
export const is_logic_verification_type = isLogicVerificationType;
export const assert_logic_verification_result = assertLogicVerificationResult;

function validateResult(
  object: Record<string, unknown>,
  issues: Array<LogicVerificationTypeIssue>,
): void {
  if (!isStatus(object.status)) issues.push({ path: '$.status', message: 'expected_status' });
  requireKind(object, 'success', 'boolean', issues);
  requireKind(object, 'formula', 'string', issues);
  requireKind(object, 'normalizedFormula', 'string', issues);
  if (!isFormat(object.format)) issues.push({ path: '$.format', message: 'expected_format' });
  requireStringArray(object.checks, '$.checks', issues);
  if (!Array.isArray(object.issues)) issues.push({ path: '$.issues', message: 'expected_array' });
  else object.issues.forEach((issue, index) => validateIssue(issue, `$.issues[${index}]`, issues));
  const metadata = asRecord(object.metadata);
  if (!metadata) issues.push({ path: '$.metadata', message: 'expected_object' });
  else validateMetadata(metadata, '$.metadata', issues);
}

function validateIssue(
  value: unknown,
  path: string,
  issues: Array<LogicVerificationTypeIssue>,
): void {
  const object = asRecord(value);
  if (!object) {
    issues.push({ path, message: 'expected_object' });
    return;
  }
  if (object.severity !== 'error' && object.severity !== 'warning')
    issues.push({ path: `${path}.severity`, message: 'expected_issue_severity' });
  if (typeof object.message !== 'string' || object.message.length === 0)
    issues.push({ path: `${path}.message`, message: 'expected_non_empty_string' });
  if ('field' in object && typeof object.field !== 'string')
    issues.push({ path: `${path}.field`, message: 'expected_string' });
}

function validateMetadata(
  object: Record<string, unknown>,
  path: string,
  issues: Array<LogicVerificationTypeIssue>,
): void {
  if (object.browserNative !== true)
    issues.push({ path: `${path}.browserNative`, message: 'expected_true' });
  if (object.serverCallsAllowed !== false)
    issues.push({ path: `${path}.serverCallsAllowed`, message: 'expected_false' });
  if (object.pythonRuntimeAllowed !== false)
    issues.push({ path: `${path}.pythonRuntimeAllowed`, message: 'expected_false' });
  requireStringArray(object.runtimeDependencies, `${path}.runtimeDependencies`, issues);
  if (Array.isArray(object.runtimeDependencies) && object.runtimeDependencies.length > 0)
    issues.push({
      path: `${path}.runtimeDependencies`,
      message: 'expected_empty_browser_runtime_dependencies',
    });
}

function requireKind(
  object: Record<string, unknown>,
  field: string,
  kind: 'string' | 'boolean',
  issues: Array<LogicVerificationTypeIssue>,
): void {
  if (typeof object[field] !== kind)
    issues.push({ path: `$.${field}`, message: `expected_${kind}` });
}

function requireStringArray(
  value: unknown,
  path: string,
  issues: Array<LogicVerificationTypeIssue>,
): void {
  if (!Array.isArray(value) || value.some((item) => typeof item !== 'string'))
    issues.push({ path, message: 'expected_string_array' });
}

function isFormat(value: unknown): value is LogicVerificationFormat {
  return (
    value === 'auto' || value === 'fol' || value === 'tdfol' || value === 'cec' || value === 'dcec'
  );
}

function isStatus(value: unknown): value is LogicVerificationStatus {
  return value === 'verified' || value === 'invalid' || value === 'unsupported';
}

function checked(
  typeName: LogicVerificationTypeName,
  issues: Array<LogicVerificationTypeIssue>,
): LogicVerificationTypeCheckResult {
  return { ok: issues.length === 0, typeName, issues, metadata: LOGIC_VERIFICATION_TYPES_METADATA };
}

function asRecord(value: unknown): Record<string, unknown> | undefined {
  return value && typeof value === 'object' && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : undefined;
}

import type { DeontologicalReasoningResult } from './normConflicts';

export interface DeontologicalReasoningTypesMetadata {
  sourcePythonModule: 'logic/integration/reasoning/deontological_reasoning_types.py';
  browserNative: true;
  serverCallsAllowed: false;
  pythonRuntimeAllowed: false;
  runtimeDependencies: Array<string>;
}

export type DeontologicalReasoningTypeName =
  | 'norm'
  | 'query'
  | 'violation'
  | 'conflict'
  | 'result'
  | 'metadata';
export interface DeontologicalReasoningTypeIssue {
  path: string;
  message: string;
}
export interface DeontologicalReasoningTypeCheckResult {
  ok: boolean;
  typeName: DeontologicalReasoningTypeName;
  issues: Array<DeontologicalReasoningTypeIssue>;
  metadata: DeontologicalReasoningTypesMetadata;
}

export const DEONTOLOGICAL_REASONING_TYPES_METADATA: DeontologicalReasoningTypesMetadata = {
  sourcePythonModule: 'logic/integration/reasoning/deontological_reasoning_types.py',
  browserNative: true,
  serverCallsAllowed: false,
  pythonRuntimeAllowed: false,
  runtimeDependencies: [],
};

type IssueSink = Array<DeontologicalReasoningTypeIssue>;
type Validator = (object: Record<string, unknown>, path: string, issues: IssueSink) => void;
const validators: Record<DeontologicalReasoningTypeName, Validator> = {
  norm: validateNorm,
  query: validateQuery,
  violation: validateViolation,
  conflict: validateConflict,
  result: validateResult,
  metadata: validateMetadata,
};

export function checkDeontologicalReasoningType(
  typeName: DeontologicalReasoningTypeName,
  value: unknown,
): DeontologicalReasoningTypeCheckResult {
  const issues: IssueSink = [];
  const object = asRecord(value);
  if (!object) issues.push({ path: '$', message: 'expected_object' });
  else validators[typeName](object, '$', issues);
  return {
    ok: issues.length === 0,
    typeName,
    issues,
    metadata: DEONTOLOGICAL_REASONING_TYPES_METADATA,
  };
}

export function isDeontologicalReasoningType(
  typeName: DeontologicalReasoningTypeName,
  value: unknown,
): boolean {
  return checkDeontologicalReasoningType(typeName, value).ok;
}

export function assertDeontologicalReasoningResult(value: unknown): DeontologicalReasoningResult {
  const result = checkDeontologicalReasoningType('result', value);
  if (!result.ok) {
    const details = result.issues.map((issue) => `${issue.path}:${issue.message}`).join(', ');
    throw new TypeError(`Invalid deontological reasoning result: ${details}`);
  }
  return value as DeontologicalReasoningResult;
}

export const deontological_reasoning_types_metadata = DEONTOLOGICAL_REASONING_TYPES_METADATA;
export const check_deontological_reasoning_type = checkDeontologicalReasoningType;
export const is_deontological_reasoning_type = isDeontologicalReasoningType;
export const assert_deontological_reasoning_result = assertDeontologicalReasoningResult;

function validateResult(object: Record<string, unknown>, path: string, issues: IssueSink): void {
  oneOf(
    object.verdict,
    `${path}.verdict`,
    ['compliant', 'violation', 'conflict', 'permitted', 'unknown'],
    issues,
    'expected_verdict',
  );
  arrayOf(object.applicableNorms, `${path}.applicableNorms`, issues, validateNorm);
  arrayOf(object.violations, `${path}.violations`, issues, validateViolation);
  arrayOf(object.conflicts, `${path}.conflicts`, issues, validateConflict);
  strings(object.trace, `${path}.trace`, issues);
}

function validateNorm(object: Record<string, unknown>, path: string, issues: IssueSink): void {
  string(object.action, `${path}.action`, issues);
  optionalString(object, 'actor', path, issues);
  optionalString(object, 'subject', path, issues);
  optionalString(object, 'condition', path, issues);
  if ('exceptions' in object) strings(object.exceptions, `${path}.exceptions`, issues);
  if ('normOperator' in object)
    oneOf(
      object.normOperator,
      `${path}.normOperator`,
      ['O', 'P', 'F'],
      issues,
      'expected_deontic_operator',
    );
  if ('modality' in object)
    oneOf(
      object.modality,
      `${path}.modality`,
      ['obligation', 'permission', 'prohibition'],
      issues,
      'expected_deontic_modality',
    );
  optionalDateLike(object, 'validFrom', path, issues);
  optionalDateLike(object, 'validUntil', path, issues);
}

function validateQuery(object: Record<string, unknown>, path: string, issues: IssueSink): void {
  optionalString(object, 'actor', path, issues);
  optionalString(object, 'action', path, issues);
  if ('performedActions' in object)
    strings(object.performedActions, `${path}.performedActions`, issues);
  optionalDateLike(object, 'atTime', path, issues);
  const facts = asRecord(object.facts);
  if ('facts' in object && !facts)
    issues.push({ path: `${path}.facts`, message: 'expected_object' });
  for (const [key, value] of Object.entries(facts ?? {}))
    if (typeof value !== 'boolean')
      issues.push({ path: `${path}.facts.${key}`, message: 'expected_boolean' });
}

function validateViolation(object: Record<string, unknown>, path: string, issues: IssueSink): void {
  string(object.normId, `${path}.normId`, issues);
  oneOf(
    object.violationType,
    `${path}.violationType`,
    ['missing_obligation', 'forbidden_action'],
    issues,
    'expected_violation_type',
  );
  string(object.actor, `${path}.actor`, issues);
  string(object.action, `${path}.action`, issues);
  string(object.message, `${path}.message`, issues);
}

function validateConflict(object: Record<string, unknown>, path: string, issues: IssueSink): void {
  string(object.id, `${path}.id`, issues);
  string(object.key, `${path}.key`, issues);
  oneOf(
    object.conflictType,
    `${path}.conflictType`,
    ['obligation_prohibition', 'permission_prohibition'],
    issues,
    'expected_conflict_type',
  );
  oneOf(object.severity, `${path}.severity`, ['medium', 'high'], issues, 'expected_severity');
  oneOf(
    object.conditionRelationship,
    `${path}.conditionRelationship`,
    ['same', 'overlap', 'unconditional'],
    issues,
    'expected_condition_relationship',
  );
  strings(object.sourceIds, `${path}.sourceIds`, issues);
}

function validateMetadata(object: Record<string, unknown>, path: string, issues: IssueSink): void {
  if (object.browserNative !== true)
    issues.push({ path: `${path}.browserNative`, message: 'expected_true' });
  if (object.serverCallsAllowed !== false)
    issues.push({ path: `${path}.serverCallsAllowed`, message: 'expected_false' });
  if (object.pythonRuntimeAllowed !== false)
    issues.push({ path: `${path}.pythonRuntimeAllowed`, message: 'expected_false' });
  strings(object.runtimeDependencies, `${path}.runtimeDependencies`, issues);
}

function arrayOf(value: unknown, path: string, issues: IssueSink, validate: Validator): void {
  if (!Array.isArray(value)) {
    issues.push({ path, message: 'expected_array' });
    return;
  }
  value.forEach((item, index) => {
    const object = asRecord(item);
    if (!object) issues.push({ path: `${path}[${index}]`, message: 'expected_object' });
    else validate(object, `${path}[${index}]`, issues);
  });
}

function strings(value: unknown, path: string, issues: IssueSink): void {
  if (!Array.isArray(value)) {
    issues.push({ path, message: 'expected_array' });
    return;
  }
  value.forEach((item, index) => {
    if (typeof item !== 'string')
      issues.push({ path: `${path}[${index}]`, message: 'expected_string' });
  });
}

function string(value: unknown, path: string, issues: IssueSink): void {
  if (typeof value !== 'string' || value.length === 0)
    issues.push({ path, message: 'expected_non_empty_string' });
}

function optionalString(
  object: Record<string, unknown>,
  key: string,
  path: string,
  issues: IssueSink,
): void {
  if (key in object && typeof object[key] !== 'string')
    issues.push({ path: `${path}.${key}`, message: 'expected_string' });
}

function optionalDateLike(
  object: Record<string, unknown>,
  key: string,
  path: string,
  issues: IssueSink,
): void {
  if (key in object && typeof object[key] !== 'string' && !(object[key] instanceof Date))
    issues.push({ path: `${path}.${key}`, message: 'expected_date_or_string' });
}

function oneOf(
  value: unknown,
  path: string,
  allowed: Array<string>,
  issues: IssueSink,
  message: string,
): void {
  if (typeof value !== 'string' || !allowed.includes(value)) issues.push({ path, message });
}

function asRecord(value: unknown): Record<string, unknown> | null {
  return value !== null && typeof value === 'object' ? (value as Record<string, unknown>) : null;
}

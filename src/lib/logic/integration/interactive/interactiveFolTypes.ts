export interface InteractiveFolTypesMetadata {
  sourcePythonModule: 'logic/integration/interactive/interactive_fol_types.py';
  browserNative: true;
  serverCallsAllowed: false;
  pythonRuntime: false;
  runtimeDependencies: Array<string>;
}

export type InteractiveFolTypeName = 'prompt' | 'turn' | 'session' | 'question' | 'symbol';

export interface InteractiveFolTypeIssue {
  path: string;
  message: string;
}

export interface InteractiveFolTypeCheckResult {
  ok: boolean;
  typeName: InteractiveFolTypeName;
  issues: Array<InteractiveFolTypeIssue>;
  metadata: InteractiveFolTypesMetadata;
}

export const INTERACTIVE_FOL_TYPES_METADATA: InteractiveFolTypesMetadata = {
  sourcePythonModule: 'logic/integration/interactive/interactive_fol_types.py',
  browserNative: true,
  serverCallsAllowed: false,
  pythonRuntime: false,
  runtimeDependencies: [],
};

export const INTERACTIVE_FOL_TYPE_DESCRIPTORS: Record<
  InteractiveFolTypeName,
  { name: InteractiveFolTypeName; requiredFields: Array<string>; optionalFields: Array<string> }
> = {
  prompt: { name: 'prompt', requiredFields: ['id', 'role', 'content'], optionalFields: [] },
  turn: {
    name: 'turn',
    requiredFields: ['prompt', 'formula', 'valid', 'warnings'],
    optionalFields: [],
  },
  session: {
    name: 'session',
    requiredFields: ['id', 'prompts', 'turns'],
    optionalFields: ['metadata'],
  },
  question: { name: 'question', requiredFields: ['id', 'reason'], optionalFields: [] },
  symbol: { name: 'symbol', requiredFields: ['name', 'kind'], optionalFields: [] },
};

export function checkInteractiveFolType(
  typeName: InteractiveFolTypeName,
  value: unknown,
): InteractiveFolTypeCheckResult {
  const object = asRecord(value);
  if (!object) return makeResult(typeName, [{ path: '$', message: 'expected_object' }]);
  const issues = INTERACTIVE_FOL_TYPE_DESCRIPTORS[typeName].requiredFields
    .filter((field) => !(field in object))
    .map((field) => ({ path: `$.${field}`, message: 'missing_required_field' }));

  if (typeName === 'prompt') {
    requireKind(object, 'id', 'string', issues);
    requireRole(object.role, issues);
    requireKind(object, 'content', 'string', issues);
  } else if (typeName === 'turn') {
    if (!checkInteractiveFolType('prompt', object.prompt).ok) {
      issues.push({ path: '$.prompt', message: 'invalid_prompt' });
    }
    requireKind(object, 'formula', 'string', issues);
    requireKind(object, 'valid', 'boolean', issues);
    requireStringArray(object.warnings, issues);
  } else if (typeName === 'session') {
    requireKind(object, 'id', 'string', issues);
    requireArray(object, 'prompts', issues);
    requireArray(object, 'turns', issues);
  } else if (typeName === 'symbol') {
    requireKind(object, 'name', 'string', issues);
    if (object.kind !== 'predicate' && object.kind !== 'variable') {
      issues.push({ path: '$.kind', message: 'expected_symbol_kind' });
    }
  } else {
    requireKind(object, 'id', 'string', issues);
    requireKind(object, 'reason', 'string', issues);
  }
  return makeResult(typeName, issues);
}

export function isInteractiveFolType(typeName: InteractiveFolTypeName, value: unknown): boolean {
  return checkInteractiveFolType(typeName, value).ok;
}

export const interactive_fol_types_metadata = INTERACTIVE_FOL_TYPES_METADATA;
export const interactive_fol_type_descriptors = INTERACTIVE_FOL_TYPE_DESCRIPTORS;
export const check_interactive_fol_type = checkInteractiveFolType;
export const is_interactive_fol_type = isInteractiveFolType;

function makeResult(
  typeName: InteractiveFolTypeName,
  issues: Array<InteractiveFolTypeIssue>,
): InteractiveFolTypeCheckResult {
  return { ok: issues.length === 0, typeName, issues, metadata: INTERACTIVE_FOL_TYPES_METADATA };
}

function asRecord(value: unknown): Record<string, unknown> | undefined {
  return value && typeof value === 'object' && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : undefined;
}

function requireKind(
  object: Record<string, unknown>,
  field: string,
  kind: 'string' | 'boolean',
  issues: Array<InteractiveFolTypeIssue>,
): void {
  if (field in object && typeof object[field] !== kind) {
    issues.push({ path: `$.${field}`, message: `expected_${kind}` });
  }
}

function requireArray(
  object: Record<string, unknown>,
  field: string,
  issues: Array<InteractiveFolTypeIssue>,
): void {
  if (field in object && !Array.isArray(object[field]))
    issues.push({ path: `$.${field}`, message: 'expected_array' });
}

function requireStringArray(value: unknown, issues: Array<InteractiveFolTypeIssue>): void {
  if (
    value !== undefined &&
    (!Array.isArray(value) || value.some((item) => typeof item !== 'string'))
  ) {
    issues.push({ path: '$.warnings', message: 'expected_string_array' });
  }
}

function requireRole(value: unknown, issues: Array<InteractiveFolTypeIssue>): void {
  if (value !== 'system' && value !== 'user' && value !== 'assistant') {
    issues.push({ path: '$.role', message: 'expected_prompt_role' });
  }
}

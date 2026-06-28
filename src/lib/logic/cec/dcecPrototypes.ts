import { stripDcecWhitespace } from './dcecCleaning';

export type DcecFunctionPrototype = [returnType: string, argumentTypes: string[]];

export const DCEC_PROTOTYPES_METADATA = {
  sourcePythonModule: 'logic/CEC/native/dcec_prototypes.py',
  runtime: 'browser-native-typescript',
  implementation: 'deterministic-dcec-prototype-namespace',
  browserNative: true,
  pythonRuntime: false,
  serverRuntime: false,
  filesystem: false,
  subprocess: false,
  rpc: false,
  supportedOperations: [
    'addSort',
    'addFunction',
    'addAtomic',
    'validateAtomic',
    'validateFunction',
    'statistics',
    'snapshot',
  ],
} as const;

export interface DcecPrototypeStatistics {
  sorts: number;
  functions: number;
  atomics: number;
  function_overloads: number;
}

export interface DcecPrototypeValidationResult {
  ok: boolean;
  issue?:
    | 'unknown_sort'
    | 'unknown_symbol'
    | 'arity_mismatch'
    | 'type_conflict'
    | 'ambiguous_overload';
  returnType?: string;
  overload?: DcecFunctionPrototype;
  distance?: number;
}

export type DcecPrototypeOperation =
  | 'addSort'
  | 'addFunction'
  | 'addAtomic'
  | 'validateAtomic'
  | 'validateFunction'
  | 'statistics'
  | 'snapshot'
  | (string & {});

export interface DcecPrototypeRequest {
  readonly operation: DcecPrototypeOperation;
  readonly name?: string;
  readonly expression?: string;
  readonly inheritance?: Array<string>;
  readonly returnType?: string;
  readonly typeName?: string;
  readonly argumentTypes?: Array<string>;
  readonly expectedType?: string;
  readonly expectedReturnType?: string;
}

export interface DcecPrototypeOperationResult {
  readonly ok: boolean;
  readonly errors: Array<string>;
  readonly validation?: DcecPrototypeValidationResult;
  readonly statistics?: DcecPrototypeStatistics;
  readonly snapshot?: string;
  readonly metadata: typeof DCEC_PROTOTYPES_METADATA;
}

export class DcecPrototypeNamespace {
  readonly functions: Record<string, DcecFunctionPrototype[]> = {};
  readonly atomics: Record<string, string> = {};
  readonly sorts: Record<string, string[]> = {};
  readonly quantMap: Record<string, number> = { TEMP: 0 };
  readonly metadata: typeof DCEC_PROTOTYPES_METADATA = DCEC_PROTOTYPES_METADATA;

  addCodeSort(name: string, inheritance: string[] = []): boolean {
    if (typeof name !== 'string' || !Array.isArray(inheritance)) return false;
    if (inheritance.some((parent) => this.sorts[parent] === undefined)) return false;
    if (this.sorts[name] !== undefined) return true;
    this.sorts[name] = [...inheritance];
    return true;
  }

  addTextSort(expression: string): boolean {
    const args = parsePrototypeExpression(expression);
    if (args.length === 2) return this.addCodeSort(args[1]);
    if (args.length > 2) return this.addCodeSort(args[1], args.slice(2));
    return false;
  }

  findAtomicType(name: string): string | undefined {
    return this.atomics[name];
  }

  addCodeFunction(name: string, returnType: string, argumentTypes: string[]): boolean {
    if (!this.hasSort(returnType) || argumentTypes.some((typeName) => !this.hasSort(typeName)))
      return false;
    const item: DcecFunctionPrototype = [returnType, [...argumentTypes]];
    const overloads = this.functions[name] ?? [];
    if (
      overloads.some(
        (overload) => prototypesOverlap(this, overload, item) && overload[0] !== item[0],
      )
    ) {
      return false;
    }
    if (
      !overloads.some(
        ([existingReturn, existingArgs]) =>
          existingReturn === item[0] && existingArgs.join('\u0000') === item[1].join('\u0000'),
      )
    ) {
      overloads.push(item);
    }
    this.functions[name] = overloads;
    return true;
  }

  addTextFunction(expression: string): boolean {
    const args = parsePrototypeExpression(expression);
    if (args[0]?.toLowerCase() === 'typedef') return this.addTextSort(expression);
    if (args.length === 2) return this.addTextAtomic(expression);

    let remaining = [...args];
    let returnType = '';
    let functionName = '';
    const argumentTypes: string[] = [];

    if (this.sorts[remaining[0]] !== undefined) {
      returnType = remaining[0];
      remaining = remaining.slice(1);
    }

    const functionIndex = remaining.findIndex((arg) => this.sorts[arg] === undefined);
    if (functionIndex !== -1) {
      functionName = remaining[functionIndex];
      remaining = [...remaining.slice(0, functionIndex), ...remaining.slice(functionIndex + 1)];
    }

    for (const arg of remaining) {
      if (this.sorts[arg] !== undefined) argumentTypes.push(arg);
    }

    if (!returnType || !functionName || argumentTypes.length === 0) return false;
    return this.addCodeFunction(functionName, returnType, argumentTypes);
  }

  addCodeAtomic(name: string, typeName: string): boolean {
    if (!this.hasSort(typeName)) return false;
    if (this.atomics[name] !== undefined) return this.atomics[name] === typeName;
    this.atomics[name] = typeName;
    return true;
  }

  addTextAtomic(expression: string): boolean {
    const args = parsePrototypeExpression(expression);
    const typeIndex = args.findIndex((arg) => this.sorts[arg] !== undefined);
    if (typeIndex === -1) return false;
    const returnType = args[typeIndex];
    const name = args.find((arg, index) => index !== typeIndex && this.sorts[arg] === undefined);
    return name === undefined ? false : this.addCodeAtomic(name, returnType);
  }

  addBasicDcec(): void {
    this.addCodeSort('Object');
    this.addCodeSort('Agent', ['Object']);
    this.addCodeSort('Self', ['Object', 'Agent']);
    this.addCodeSort('ActionType', ['Object']);
    this.addCodeSort('Event', ['Object']);
    this.addCodeSort('Action', ['Object', 'Event']);
    this.addCodeSort('Moment', ['Object']);
    this.addCodeSort('Boolean', ['Object']);
    this.addCodeSort('Fluent', ['Object']);
    this.addCodeSort('Numeric', ['Object']);
    this.addCodeSort('Set', ['Object']);

    this.addCodeFunction('C', 'Boolean', ['Moment', 'Boolean']);
    this.addCodeFunction('B', 'Boolean', ['Agent', 'Moment', 'Boolean']);
    this.addCodeFunction('K', 'Boolean', ['Agent', 'Moment', 'Boolean']);
    this.addCodeFunction('P', 'Boolean', ['Agent', 'Moment', 'Boolean']);
    this.addCodeFunction('I', 'Boolean', ['Agent', 'Moment', 'Boolean']);
    this.addCodeFunction('D', 'Boolean', ['Agent', 'Moment', 'Boolean']);
    this.addCodeFunction('S', 'Boolean', ['Agent', 'Agent', 'Moment', 'Boolean']);
    this.addCodeFunction('O', 'Boolean', ['Agent', 'Moment', 'Boolean', 'Boolean']);

    this.addCodeFunction('action', 'Action', ['Agent', 'ActionType']);
    this.addCodeFunction('initially', 'Boolean', ['Fluent']);
    this.addCodeFunction('holds', 'Boolean', ['Fluent', 'Moment']);
    this.addCodeFunction('happens', 'Boolean', ['Event', 'Moment']);
    this.addCodeFunction('clipped', 'Boolean', ['Moment', 'Fluent', 'Moment']);
    this.addCodeFunction('initiates', 'Boolean', ['Event', 'Fluent', 'Moment']);
    this.addCodeFunction('terminates', 'Boolean', ['Event', 'Fluent', 'Moment']);
    this.addCodeFunction('prior', 'Boolean', ['Moment', 'Moment']);
    this.addCodeFunction('interval', 'Fluent', ['Moment', 'Boolean']);
    this.addCodeFunction('self', 'Self', ['Agent']);
    this.addCodeFunction('payoff', 'Numeric', ['Agent', 'ActionType', 'Moment']);

    this.addCodeFunction('implies', 'Boolean', ['Boolean', 'Boolean']);
    this.addCodeFunction('iff', 'Boolean', ['Boolean', 'Boolean']);
    this.addCodeFunction('not', 'Boolean', ['Boolean']);
    this.addCodeFunction('and', 'Boolean', ['Boolean', 'Boolean']);
    this.addCodeFunction('lessOrEqual', 'Boolean', ['Moment', 'Moment']);
  }

  addBasicLogic(): void {
    this.addCodeFunction('or', 'Boolean', ['Boolean', 'Boolean']);
    this.addCodeFunction('xor', 'Boolean', ['Boolean', 'Boolean']);
  }

  addBasicNumerics(): void {
    this.addCodeFunction('negate', 'Numeric', ['Numeric']);
    this.addCodeFunction('add', 'Numeric', ['Numeric', 'Numeric']);
    this.addCodeFunction('sub', 'Numeric', ['Numeric', 'Numeric']);
    this.addCodeFunction('multiply', 'Numeric', ['Numeric', 'Numeric']);
    this.addCodeFunction('divide', 'Numeric', ['Numeric', 'Numeric']);
    this.addCodeFunction('exponent', 'Numeric', ['Numeric', 'Numeric']);

    this.addCodeFunction('greater', 'Boolean', ['Numeric', 'Numeric']);
    this.addCodeFunction('greaterOrEqual', 'Boolean', ['Numeric', 'Numeric']);
    this.addCodeFunction('less', 'Boolean', ['Numeric', 'Numeric']);
    this.addCodeFunction('lessOrEqual', 'Boolean', ['Numeric', 'Numeric']);
    this.addCodeFunction('equals', 'Boolean', ['Numeric', 'Numeric']);
  }

  noConflict(type1: string, type2: string, level = 0): [boolean, number] {
    if (type1 === '?') return [true, level];
    if (type1 === type2) return [true, level];
    if (this.sorts[type1]?.includes(type2)) return [true, level + 1];

    const parents = this.sorts[type1];
    if (parents !== undefined) {
      const distances = parents
        .map((parent) => this.noConflict(parent, type2, level + 1))
        .filter(([compatible]) => compatible)
        .map(([, distance]) => distance);
      if (distances.length > 0) return [true, Math.min(...distances)];
    }
    return [false, level];
  }

  validateAtomic(name: string, expectedType: string): DcecPrototypeValidationResult {
    const actualType = this.atomics[name];
    if (actualType === undefined) return { ok: false, issue: 'unknown_symbol' };
    if (!this.hasSort(expectedType))
      return { ok: false, issue: 'unknown_sort', returnType: actualType };
    const [compatible, distance] = this.noConflict(actualType, expectedType);
    return compatible
      ? { ok: true, returnType: actualType, distance }
      : { ok: false, issue: 'type_conflict', returnType: actualType };
  }

  validateFunctionCall(
    name: string,
    argumentTypes: string[],
    expectedReturnType?: string,
  ): DcecPrototypeValidationResult {
    if (argumentTypes.some((typeName) => !this.hasSort(typeName)))
      return { ok: false, issue: 'unknown_sort' };
    if (expectedReturnType !== undefined && !this.hasSort(expectedReturnType)) {
      return { ok: false, issue: 'unknown_sort' };
    }

    const overloads = this.functions[name];
    if (overloads === undefined) return { ok: false, issue: 'unknown_symbol' };
    if (!overloads.some(([, expectedArgs]) => expectedArgs.length === argumentTypes.length)) {
      return { ok: false, issue: 'arity_mismatch' };
    }

    const matches = overloads
      .filter(([, expectedArgs]) => expectedArgs.length === argumentTypes.length)
      .map((overload) => {
        const distances: number[] = [];
        for (let index = 0; index < argumentTypes.length; index += 1) {
          const [compatible, distance] = this.noConflict(argumentTypes[index], overload[1][index]);
          if (!compatible) return undefined;
          distances.push(distance);
        }
        return {
          overload,
          distance: distances.reduce((sum, distance) => sum + distance, 0),
        };
      })
      .filter(
        (match): match is { overload: DcecFunctionPrototype; distance: number } =>
          match !== undefined,
      )
      .filter(
        (match) =>
          expectedReturnType === undefined ||
          this.noConflict(match.overload[0], expectedReturnType)[0],
      )
      .sort((left, right) => left.distance - right.distance);

    if (matches.length === 0) return { ok: false, issue: 'type_conflict' };

    const bestDistance = matches[0].distance;
    const bestMatches = matches.filter((match) => match.distance === bestDistance);
    const bestReturnTypes = new Set(bestMatches.map((match) => match.overload[0]));
    if (bestReturnTypes.size > 1) return { ok: false, issue: 'ambiguous_overload' };

    return {
      ok: true,
      returnType: matches[0].overload[0],
      overload: [matches[0].overload[0], [...matches[0].overload[1]]],
      distance: matches[0].distance,
    };
  }

  private hasSort(typeName: string): boolean {
    return typeName === '?' || this.sorts[typeName] !== undefined;
  }

  getStatistics(): DcecPrototypeStatistics {
    return {
      sorts: Object.keys(this.sorts).length,
      functions: Object.keys(this.functions).length,
      atomics: Object.keys(this.atomics).length,
      function_overloads: Object.values(this.functions).reduce(
        (sum, overloads) => sum + overloads.length,
        0,
      ),
    };
  }

  snapshot(): string {
    return [
      '=== Sorts ===',
      ...Object.entries(this.sorts).map(([name, parents]) => `${name}: ${parents.join(',')}`),
      '',
      '=== Functions ===',
      ...Object.entries(this.functions).map(
        ([name, overloads]) => `${name}: ${JSON.stringify(overloads)}`,
      ),
      '',
      '=== Atomics ===',
      ...Object.entries(this.atomics).map(([name, type]) => `${name}: ${type}`),
    ].join('\n');
  }
}

export function invokeDcecPrototypeOperation(
  namespace: DcecPrototypeNamespace,
  request: DcecPrototypeRequest,
): DcecPrototypeOperationResult {
  const success = (extras: Omit<DcecPrototypeOperationResult, 'ok' | 'errors' | 'metadata'> = {}) =>
    prototypeResult(true, [], extras);
  const mutation = (ok: boolean) =>
    prototypeResult(ok, ok ? [] : [`DCEC prototype ${request.operation} operation failed.`]);

  if (request.operation === 'addSort') {
    if (request.expression !== undefined)
      return mutation(namespace.addTextSort(request.expression));
    return request.name === undefined
      ? prototypeFailure('DCEC prototype addSort operation requires a name.')
      : mutation(namespace.addCodeSort(request.name, request.inheritance ?? []));
  }

  if (request.operation === 'addFunction') {
    if (request.expression !== undefined)
      return mutation(namespace.addTextFunction(request.expression));
    if (
      request.name === undefined ||
      request.returnType === undefined ||
      request.argumentTypes === undefined
    ) {
      return prototypeFailure(
        'DCEC prototype addFunction operation requires name, returnType, and argumentTypes.',
      );
    }
    return mutation(
      namespace.addCodeFunction(request.name, request.returnType, request.argumentTypes),
    );
  }

  if (request.operation === 'addAtomic') {
    if (request.expression !== undefined)
      return mutation(namespace.addTextAtomic(request.expression));
    return request.name === undefined || request.typeName === undefined
      ? prototypeFailure('DCEC prototype addAtomic operation requires name and typeName.')
      : mutation(namespace.addCodeAtomic(request.name, request.typeName));
  }

  if (request.operation === 'validateAtomic') {
    if (request.name === undefined || request.expectedType === undefined) {
      return prototypeFailure(
        'DCEC prototype validateAtomic operation requires name and expectedType.',
      );
    }
    const validation = namespace.validateAtomic(request.name, request.expectedType);
    return prototypeResult(
      validation.ok,
      validation.ok ? [] : [`DCEC prototype ${request.operation} operation failed.`],
      { validation },
    );
  }

  if (request.operation === 'validateFunction') {
    if (request.name === undefined || request.argumentTypes === undefined) {
      return prototypeFailure(
        'DCEC prototype validateFunction operation requires name and argumentTypes.',
      );
    }
    const validation = namespace.validateFunctionCall(
      request.name,
      request.argumentTypes,
      request.expectedReturnType,
    );
    return prototypeResult(
      validation.ok,
      validation.ok ? [] : [`DCEC prototype ${request.operation} operation failed.`],
      { validation },
    );
  }

  if (request.operation === 'statistics') return success({ statistics: namespace.getStatistics() });
  if (request.operation === 'snapshot') return success({ snapshot: namespace.snapshot() });

  return prototypeFailure(
    `Unsupported browser-native DCEC prototype operation: ${request.operation}`,
  );
}

function prototypeFailure(error: string): DcecPrototypeOperationResult {
  return prototypeResult(false, [error]);
}

function prototypeResult(
  ok: boolean,
  errors: Array<string>,
  extras: Omit<DcecPrototypeOperationResult, 'ok' | 'errors' | 'metadata'> = {},
): DcecPrototypeOperationResult {
  return {
    ok,
    errors,
    metadata: DCEC_PROTOTYPES_METADATA,
    ...extras,
  };
}

function prototypesOverlap(
  namespace: DcecPrototypeNamespace,
  left: DcecFunctionPrototype,
  right: DcecFunctionPrototype,
): boolean {
  if (left[1].length !== right[1].length) return false;
  return left[1].every((leftType, index) => {
    const rightType = right[1][index];
    return (
      namespace.noConflict(leftType, rightType)[0] || namespace.noConflict(rightType, leftType)[0]
    );
  });
}

function parsePrototypeExpression(expression: string): string[] {
  const text = stripDcecWhitespace(expression.replaceAll('(', ' ').replaceAll(')', ' ')).replaceAll(
    '`',
    '',
  );
  return text
    .split(',')
    .map((arg) => arg.trim())
    .filter(Boolean);
}

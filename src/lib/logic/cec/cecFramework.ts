export type CecSymbolKind = 'sort' | 'predicate' | 'function' | 'modality';

export interface CecSymbolDeclaration {
  readonly name: string;
  readonly kind: CecSymbolKind;
  readonly args: readonly string[];
  readonly result?: string;
  readonly description?: string;
}

export interface CecFrameworkSpec {
  readonly name?: string;
  readonly description?: string;
  readonly declarations?: readonly CecSymbolDeclaration[];
}

export interface CecExpression {
  readonly symbol: string;
  readonly args?: readonly CecExpression[];
  readonly sort?: string;
}

export interface CecValidationResult {
  readonly ok: boolean;
  readonly errors: readonly string[];
}

const DEFAULT_DECLARATIONS: readonly CecSymbolDeclaration[] = [
  { name: 'Entity', kind: 'sort', args: [], description: 'Top-level entity sort' },
  { name: 'Agent', kind: 'sort', args: [], description: 'Acting subject sort' },
  { name: 'Action', kind: 'sort', args: [], description: 'Action/event sort' },
  { name: 'Moment', kind: 'sort', args: [], description: 'Temporal instant sort' },
  { name: 'Happens', kind: 'predicate', args: ['Action', 'Moment'], result: 'Formula' },
  { name: 'HoldsAt', kind: 'predicate', args: ['Entity', 'Moment'], result: 'Formula' },
  {
    name: 'O',
    kind: 'modality',
    args: ['Formula'],
    result: 'Formula',
    description: 'Obligation modality',
  },
  {
    name: 'P',
    kind: 'modality',
    args: ['Formula'],
    result: 'Formula',
    description: 'Permission modality',
  },
  {
    name: 'F',
    kind: 'modality',
    args: ['Formula'],
    result: 'Formula',
    description: 'Forbidden modality',
  },
  {
    name: 'B',
    kind: 'modality',
    args: ['Agent', 'Formula'],
    result: 'Formula',
    description: 'Belief modality',
  },
  {
    name: 'K',
    kind: 'modality',
    args: ['Agent', 'Formula'],
    result: 'Formula',
    description: 'Knowledge modality',
  },
];

function isObject(value: unknown): value is { readonly [key: string]: unknown } {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function asStringArray(value: unknown): readonly string[] {
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === 'string')
    : [];
}

function normalizeDeclaration(value: unknown): CecSymbolDeclaration {
  if (!isObject(value) || typeof value.name !== 'string' || typeof value.kind !== 'string') {
    throw new Error('CEC framework declarations require string name and kind fields');
  }
  if (!['sort', 'predicate', 'function', 'modality'].includes(value.kind)) {
    throw new Error(`Unsupported CEC declaration kind: ${value.kind}`);
  }
  return {
    name: value.name,
    kind: value.kind as CecSymbolKind,
    args: asStringArray(value.args),
    result: typeof value.result === 'string' ? value.result : undefined,
    description: typeof value.description === 'string' ? value.description : undefined,
  };
}

export class CecFramework {
  readonly name: string;
  readonly description: string;
  private readonly declarations = new Map();

  constructor(spec: CecFrameworkSpec = {}) {
    this.name = spec.name ?? 'Common Event Calculus';
    this.description = spec.description ?? 'Browser-native CEC framework declaration registry';
    for (const declaration of spec.declarations ?? DEFAULT_DECLARATIONS) {
      this.register(declaration);
    }
  }

  static fromPythonDict(value: unknown): CecFramework {
    if (!isObject(value)) {
      throw new Error('CEC framework spec must be an object');
    }
    const rawDeclarations = value.declarations ?? value.symbols ?? [];
    return new CecFramework({
      name: typeof value.name === 'string' ? value.name : undefined,
      description: typeof value.description === 'string' ? value.description : undefined,
      declarations: Array.isArray(rawDeclarations) ? rawDeclarations.map(normalizeDeclaration) : [],
    });
  }

  register(declaration: CecSymbolDeclaration): void {
    const normalized = normalizeDeclaration(declaration);
    const key = `${normalized.kind}:${normalized.name}`;
    if (this.declarations.has(key)) {
      throw new Error(`Duplicate CEC declaration: ${normalized.kind} ${normalized.name}`);
    }
    if (normalized.kind !== 'sort') {
      for (const sort of normalized.args) {
        if (sort !== 'Formula' && !this.hasSort(sort)) {
          throw new Error(`Unknown CEC sort '${sort}' for ${normalized.name}`);
        }
      }
    }
    this.declarations.set(key, normalized);
  }

  get(name: string, kind?: CecSymbolKind): CecSymbolDeclaration | undefined {
    if (kind) {
      return this.declarations.get(`${kind}:${name}`);
    }
    return this.list().find((declaration) => declaration.name === name);
  }

  hasSort(name: string): boolean {
    return this.declarations.has(`sort:${name}`);
  }

  list(kind?: CecSymbolKind): readonly CecSymbolDeclaration[] {
    const values = Array.from(this.declarations.values());
    return kind ? values.filter((declaration) => declaration.kind === kind) : values;
  }

  validateExpression(expression: CecExpression): CecValidationResult {
    const errors: string[] = [];
    this.validateNode(expression, errors, 'expression');
    return { ok: errors.length === 0, errors };
  }

  toPythonDict(): {
    readonly name: string;
    readonly description: string;
    readonly declarations: readonly CecSymbolDeclaration[];
  } {
    return { name: this.name, description: this.description, declarations: this.list() };
  }

  private validateNode(expression: CecExpression, errors: string[], path: string): void {
    if (!expression || typeof expression.symbol !== 'string' || expression.symbol.length === 0) {
      errors.push(`${path} must name a CEC symbol`);
      return;
    }
    const args = expression.args ?? [];
    const declaration = this.get(expression.symbol);
    if (!declaration) {
      if (expression.sort && !this.hasSort(expression.sort)) {
        errors.push(`${path} has unknown sort ${expression.sort}`);
      }
      return;
    }
    if (declaration.kind === 'sort') {
      return;
    }
    if (args.length !== declaration.args.length) {
      errors.push(
        `${path} ${expression.symbol} expects ${declaration.args.length} argument(s), received ${args.length}`,
      );
    }
    args.forEach((arg, index) =>
      this.validateNode(arg, errors, `${path}.${expression.symbol}[${index}]`),
    );
  }
}

export function createDefaultCecFramework(): CecFramework {
  return new CecFramework();
}

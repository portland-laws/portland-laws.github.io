import { stripDcecWhitespace } from './dcecCleaning';

export type DcecFunctionPrototype = [returnType: string, argumentTypes: string[]];

export interface DcecPrototypeStatistics {
  sorts: number;
  functions: number;
  atomics: number;
  function_overloads: number;
}

export class DcecPrototypeNamespace {
  readonly functions: Record<string, DcecFunctionPrototype[]> = {};
  readonly atomics: Record<string, string> = {};
  readonly sorts: Record<string, string[]> = {};
  readonly quantMap: Record<string, number> = { TEMP: 0 };

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
    const item: DcecFunctionPrototype = [returnType, [...argumentTypes]];
    const overloads = this.functions[name] ?? [];
    if (!overloads.some(([existingReturn, existingArgs]) => (
      existingReturn === item[0] && existingArgs.join('\u0000') === item[1].join('\u0000')
    ))) {
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

  getStatistics(): DcecPrototypeStatistics {
    return {
      sorts: Object.keys(this.sorts).length,
      functions: Object.keys(this.functions).length,
      atomics: Object.keys(this.atomics).length,
      function_overloads: Object.values(this.functions).reduce((sum, overloads) => sum + overloads.length, 0),
    };
  }

  snapshot(): string {
    return [
      '=== Sorts ===',
      ...Object.entries(this.sorts).map(([name, parents]) => `${name}: ${parents.join(',')}`),
      '',
      '=== Functions ===',
      ...Object.entries(this.functions).map(([name, overloads]) => `${name}: ${JSON.stringify(overloads)}`),
      '',
      '=== Atomics ===',
      ...Object.entries(this.atomics).map(([name, type]) => `${name}: ${type}`),
    ].join('\n');
  }
}

function parsePrototypeExpression(expression: string): string[] {
  const text = stripDcecWhitespace(expression.replaceAll('(', ' ').replaceAll(')', ' ')).replaceAll('`', '');
  return text.split(',').map((arg) => arg.trim()).filter(Boolean);
}

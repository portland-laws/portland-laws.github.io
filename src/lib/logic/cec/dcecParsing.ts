export type DcecParseArg = string | DcecParseToken;

export class DcecParseToken {
  readonly funcName: string;
  readonly args: DcecParseArg[];

  private depth?: number;
  private width?: number;
  private sExpression?: string;
  private fExpression?: string;

  constructor(funcName: string, args: DcecParseArg[]) {
    this.funcName = funcName;
    this.args = args;
  }

  depthOf(): number {
    if (this.depth !== undefined) return this.depth;
    const childDepths = this.args
      .filter(isDcecParseToken)
      .map((arg) => arg.depthOf());
    this.depth = childDepths.length === 0 ? 1 : 1 + Math.max(...childDepths);
    return this.depth;
  }

  widthOf(): number {
    if (this.width !== undefined) return this.width;
    this.width = this.args.reduce((sum, arg) => sum + (isDcecParseToken(arg) ? arg.widthOf() : 1), 0);
    return this.width;
  }

  createSExpression(): string {
    if (this.sExpression !== undefined) return this.sExpression;
    const args = this.args.map((arg) => (isDcecParseToken(arg) ? arg.createSExpression() : arg));
    this.sExpression = `(${[this.funcName, ...args].join(' ')})`;
    return this.sExpression;
  }

  createFExpression(): string {
    if (this.fExpression !== undefined) return this.fExpression;
    const args = this.args.map((arg) => (isDcecParseToken(arg) ? arg.createFExpression() : arg));
    this.fExpression = `${this.funcName}(${args.join(',')})`;
    return this.fExpression;
  }

  toString(): string {
    return this.createFExpression();
  }
}

export interface DcecPrefixOptions {
  atomics?: Record<string, string[]>;
}

const DCEC_SYNONYMS: Record<string, string> = {
  ifAndOnlyIf: 'iff',
  if: 'implies',
  Time: 'Moment',
  forall: 'forAll',
  Forall: 'forAll',
  ForAll: 'forAll',
  Exists: 'exists',
};

const LOGICAL_KEYWORDS = ['not', 'and', 'or', 'xor', 'implies', 'iff'];
const ARITHMETIC_KEYWORDS = ['negate', 'exponent', 'multiply', 'divide', 'add', 'sub'];

export function isDcecParseToken(arg: DcecParseArg): arg is DcecParseToken {
  return arg instanceof DcecParseToken;
}

export function replaceDcecSynonyms(args: DcecParseArg[]): DcecParseArg[] {
  return args.map((arg) => {
    if (typeof arg === 'string') {
      return DCEC_SYNONYMS[arg] ?? arg;
    }
    return new DcecParseToken(arg.funcName, replaceDcecSynonyms(arg.args));
  });
}

export function prefixDcecLogicalFunctions(
  args: DcecParseArg[],
  options: DcecPrefixOptions = {},
): DcecParseArg[] {
  return prefixDcecFunctions(args, LOGICAL_KEYWORDS, 'Boolean', options.atomics);
}

export function prefixDcecEmdas(
  args: DcecParseArg[],
  options: DcecPrefixOptions = {},
): DcecParseArg[] {
  return prefixDcecFunctions(args, ARITHMETIC_KEYWORDS, 'Numeric', options.atomics);
}

function prefixDcecFunctions(
  inputArgs: DcecParseArg[],
  keywords: string[],
  atomicSort: string,
  atomics: Record<string, string[]> = {},
): DcecParseArg[] {
  let args = [...inputArgs];
  const [unaryKeyword] = keywords;

  if (args.length === 2 && args[0] === unaryKeyword) {
    const operand = args[1];
    if (typeof operand === 'string' && !keywords.includes(operand)) {
      addAtomicSort(atomics, operand, atomicSort);
      return [new DcecParseToken(unaryKeyword, [operand])];
    }
  }

  if (args.length < 3) return args;
  if (typeof args.at(-2) !== 'string' || !keywords.includes(args.at(-2) as string)) return args;

  for (const keyword of keywords) {
    while (args.includes(keyword)) {
      const index = args.indexOf(keyword);

      if (keyword === unaryKeyword) {
        const operand = args[index + 1];
        const token = new DcecParseToken(keyword, [operand]);
        if (typeof operand === 'string') {
          addAtomicSort(atomics, operand, atomicSort);
        }
        args = [...args.slice(0, index + 1), ...args.slice(index + 2)];
        args[index] = token;
        break;
      }

      const leftIndex = index - 1;
      const rightIndex = index + 1;
      if (leftIndex < 0) break;

      const left = args[leftIndex];
      const right = args[rightIndex];
      const token = new DcecParseToken(keyword, [left, right]);
      if (typeof left === 'string') addAtomicSort(atomics, left, atomicSort);
      if (typeof right === 'string') addAtomicSort(atomics, right, atomicSort);

      args = [...args.slice(0, leftIndex), ...args.slice(rightIndex)];
      args[leftIndex] = token;
    }
  }

  return args;
}

function addAtomicSort(atomics: Record<string, string[]>, name: string, sort: string) {
  if (atomics[name]) {
    atomics[name].push(sort);
  } else {
    atomics[name] = [sort];
  }
}

export const DcecDeonticOperator = {
  OBLIGATION: 'O',
  OBLIGATORY: 'O',
  PERMISSION: 'P',
  PROHIBITION: 'F',
  SUPEREROGATION: 'S',
  RIGHT: 'R',
  LIBERTY: 'L',
  POWER: 'POW',
  IMMUNITY: 'IMM',
} as const;

export const DcecCognitiveOperator = {
  BELIEF: 'B',
  BELIEVES: 'B',
  KNOWLEDGE: 'K',
  KNOWS: 'K',
  INTENTION: 'I',
  DESIRE: 'D',
  GOAL: 'G',
  PERCEPTION: 'P',
} as const;

export const DcecLogicalConnective = {
  AND: 'and',
  OR: 'or',
  NOT: 'not',
  IMPLIES: 'implies',
  BICONDITIONAL: 'iff',
  IFF: 'iff',
  EXISTS: 'exists',
  FORALL: 'forAll',
} as const;

export const DcecTemporalOperator = {
  ALWAYS: 'always',
  EVENTUALLY: 'eventually',
  NEXT: 'next',
  UNTIL: 'until',
  SINCE: 'since',
} as const;

export type DcecDeonticOperatorValue = typeof DcecDeonticOperator[keyof typeof DcecDeonticOperator];
export type DcecCognitiveOperatorValue = typeof DcecCognitiveOperator[keyof typeof DcecCognitiveOperator];
export type DcecLogicalConnectiveValue = typeof DcecLogicalConnective[keyof typeof DcecLogicalConnective];
export type DcecTemporalOperatorValue = typeof DcecTemporalOperator[keyof typeof DcecTemporalOperator];

export class DcecSort {
  readonly name: string;
  readonly parent?: DcecSort;

  constructor(name: string, parent?: DcecSort) {
    this.name = name;
    this.parent = parent;
  }

  isSubtypeOf(other: DcecSort): boolean {
    if (this.name === other.name) return true;
    return this.parent?.isSubtypeOf(other) ?? false;
  }

  toString(): string {
    return this.name;
  }
}

export class DcecVariable {
  readonly name: string;
  readonly sort: DcecSort;

  constructor(name: string, sort: DcecSort) {
    this.name = name;
    this.sort = sort;
  }

  toString(): string {
    return `${this.name}:${this.sort.name}`;
  }
}

export class DcecFunctionSymbol {
  readonly name: string;
  readonly argumentSorts: DcecSort[];
  readonly returnSort: DcecSort;

  constructor(name: string, argumentSorts: DcecSort[], returnSort: DcecSort) {
    this.name = name;
    this.argumentSorts = [...argumentSorts];
    this.returnSort = returnSort;
  }

  arity(): number {
    return this.argumentSorts.length;
  }

  toString(): string {
    return `${this.name}(${this.argumentSorts.map((sort) => sort.name).join(', ')}) -> ${this.returnSort.name}`;
  }
}

export class DcecPredicateSymbol {
  readonly name: string;
  readonly argumentSorts: DcecSort[];

  constructor(name: string, argumentSorts: DcecSort[]) {
    this.name = name;
    this.argumentSorts = [...argumentSorts];
  }

  arity(): number {
    return this.argumentSorts.length;
  }

  toString(): string {
    return `${this.name}(${this.argumentSorts.map((sort) => sort.name).join(', ')})`;
  }
}

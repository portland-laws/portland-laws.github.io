export const DcecGrammarCategory = {
  S: 'S',
  NP: 'NP',
  VP: 'VP',
  DEONTIC: 'Deontic',
  COGNITIVE: 'Cognitive',
  TEMPORAL: 'Temporal',
  AGENT: 'Agent',
  ACTION: 'Action',
  FLUENT: 'Fluent',
  N: 'N',
  V: 'V',
  ADJ: 'ADJ',
  ADV: 'ADV',
  DET: 'DET',
  MODAL: 'MODAL',
} as const;

export type DcecGrammarCategoryValue = typeof DcecGrammarCategory[keyof typeof DcecGrammarCategory];

export class DcecGrammarTerminal {
  readonly word: string;
  readonly category: DcecGrammarCategoryValue;

  constructor(word: string, category: DcecGrammarCategoryValue) {
    this.word = word;
    this.category = category;
  }

  toString(): string {
    return `${this.word}:${this.category}`;
  }

  key(): string {
    return `${this.word}:${this.category}`;
  }
}

export class DcecGrammarRule {
  readonly lhs: DcecGrammarCategoryValue;
  readonly rhs: DcecGrammarCategoryValue[];
  readonly semanticFn?: (...args: unknown[]) => unknown;

  constructor(lhs: DcecGrammarCategoryValue, rhs: DcecGrammarCategoryValue[], semanticFn?: (...args: unknown[]) => unknown) {
    this.lhs = lhs;
    this.rhs = [...rhs];
    this.semanticFn = semanticFn;
  }

  toString(): string {
    return `${this.lhs} -> ${this.rhs.join(' ')}`;
  }

  key(): string {
    return `${this.lhs}->${this.rhs.join(',')}`;
  }
}

export class DcecParseTree {
  readonly category: DcecGrammarCategoryValue;
  readonly children: DcecParseTree[];
  readonly terminal?: DcecGrammarTerminal;
  readonly semantics?: unknown;

  constructor(
    category: DcecGrammarCategoryValue,
    options: { children?: DcecParseTree[]; terminal?: DcecGrammarTerminal; semantics?: unknown } = {},
  ) {
    this.category = category;
    this.children = [...(options.children ?? [])];
    this.terminal = options.terminal;
    this.semantics = options.semantics;
  }

  isTerminal(): boolean {
    return this.terminal !== undefined;
  }

  toString(indent = 0): string {
    const prefix = '  '.repeat(indent);
    if (this.isTerminal()) return `${prefix}${this.category}: ${this.terminal!.word}`;
    const lines = [`${prefix}${this.category}`];
    for (const child of this.children) lines.push(child.toString(indent + 1));
    return lines.join('\n');
  }

  leaves(): string[] {
    if (this.isTerminal()) return [this.terminal!.word];
    return this.children.flatMap((child) => child.leaves());
  }
}

export class DcecEarleyState {
  readonly rule: DcecGrammarRule;
  readonly dotPos: number;
  readonly origin: number;
  readonly current: number;
  readonly tree?: DcecParseTree;

  constructor(rule: DcecGrammarRule, dotPos: number, origin: number, current: number, tree?: DcecParseTree) {
    this.rule = rule;
    this.dotPos = dotPos;
    this.origin = origin;
    this.current = current;
    this.tree = tree;
  }

  nextCategory(): DcecGrammarCategoryValue | undefined {
    return this.isComplete() ? undefined : this.rule.rhs[this.dotPos];
  }

  isComplete(): boolean {
    return this.dotPos >= this.rule.rhs.length;
  }

  advance(tree = this.tree, current = this.current): DcecEarleyState {
    return new DcecEarleyState(this.rule, this.dotPos + 1, this.origin, current, tree);
  }

  toString(): string {
    const before = this.rule.rhs.slice(0, this.dotPos).join(' ');
    const after = this.rule.rhs.slice(this.dotPos).join(' ');
    return `${this.rule.lhs} -> ${before} • ${after} (${this.origin}, ${this.current})`;
  }

  key(): string {
    return `${this.rule.key()}|${this.dotPos}|${this.origin}|${this.current}`;
  }
}

export class DcecEnhancedGrammarParser {
  readonly rules: DcecGrammarRule[] = [];
  readonly lexicon = new Map<string, DcecGrammarTerminal[]>();
  startSymbol: DcecGrammarCategoryValue = DcecGrammarCategory.S;

  constructor() {
    this.initGrammar();
    this.initLexicon();
  }

  addRule(rule: DcecGrammarRule): void {
    this.rules.push(rule);
  }

  addLexicalEntry(word: string, category: DcecGrammarCategoryValue): void {
    this.addWords([word], category);
  }

  parse(sentence: string): DcecParseTree[] {
    const words = sentence.toLowerCase().trim().split(/\s+/).filter(Boolean);
    const chart = Array.from({ length: words.length + 1 }, () => new Map<string, DcecEarleyState>());

    for (const rule of this.rules.filter((candidate) => candidate.lhs === this.startSymbol)) {
      this.addState(chart[0], new DcecEarleyState(rule, 0, 0, 0));
    }

    for (let position = 0; position <= words.length; position += 1) {
      let changed = true;
      while (changed) {
        changed = false;
        for (const state of [...chart[position].values()]) {
          const beforeSize = chart[position].size + (chart[position + 1]?.size ?? 0);
          if (state.isComplete()) this.completer(chart, state, position);
          else if (this.isTerminalCategory(state.nextCategory())) {
            if (position < words.length) this.scanner(chart, state, words[position], position);
          } else {
            this.predictor(chart, state, position);
          }
          const afterSize = chart[position].size + (chart[position + 1]?.size ?? 0);
          if (afterSize > beforeSize) changed = true;
        }
      }
    }

    return [...chart[words.length].values()]
      .filter((state) => state.rule.lhs === this.startSymbol && state.isComplete() && state.origin === 0)
      .map((state) => this.buildTree(state))
      .filter((tree): tree is DcecParseTree => tree !== undefined);
  }

  validateGrammar(): [boolean, string[]] {
    const issues: string[] = [];
    if (!this.rules.some((rule) => rule.lhs === this.startSymbol)) {
      issues.push(`No rules for start symbol ${this.startSymbol}`);
    }

    const reachable = new Set<DcecGrammarCategoryValue>([this.startSymbol]);
    let changed = true;
    while (changed) {
      changed = false;
      for (const rule of this.rules) {
        if (!reachable.has(rule.lhs)) continue;
        for (const category of rule.rhs) {
          if (!reachable.has(category)) {
            reachable.add(category);
            changed = true;
          }
        }
      }
    }

    const allRuleCategories = new Set(this.rules.map((rule) => rule.lhs));
    const unreachable = [...allRuleCategories].filter((category) => !reachable.has(category));
    if (unreachable.length > 0) issues.push(`Unreachable categories: ${unreachable.join(',')}`);

    const productive = new Set<DcecGrammarCategoryValue>();
    for (const terminals of this.lexicon.values()) {
      for (const terminal of terminals) productive.add(terminal.category);
    }
    changed = true;
    while (changed) {
      changed = false;
      for (const rule of this.rules) {
        if (rule.rhs.every((category) => productive.has(category)) && !productive.has(rule.lhs)) {
          productive.add(rule.lhs);
          changed = true;
        }
      }
    }
    const unproductive = [...allRuleCategories].filter((category) => !productive.has(category));
    if (unproductive.length > 0) issues.push(`Unproductive categories: ${unproductive.join(',')}`);

    return [issues.length === 0, issues];
  }

  private predictor(chart: Array<Map<string, DcecEarleyState>>, state: DcecEarleyState, position: number): void {
    const next = state.nextCategory();
    if (!next) return;
    for (const rule of this.rules) {
      if (rule.lhs === next) this.addState(chart[position], new DcecEarleyState(rule, 0, position, position));
    }
  }

  private scanner(chart: Array<Map<string, DcecEarleyState>>, state: DcecEarleyState, word: string, position: number): void {
    const next = state.nextCategory();
    if (!next) return;
    for (const terminal of this.lexicon.get(word) ?? []) {
      if (terminal.category === next) {
        const tree = new DcecParseTree(next, { terminal });
        this.addState(chart[position + 1], state.advance(tree, position + 1));
      }
    }
  }

  private completer(chart: Array<Map<string, DcecEarleyState>>, completed: DcecEarleyState, position: number): void {
    for (const state of [...chart[completed.origin].values()]) {
      if (state.nextCategory() === completed.rule.lhs) {
        this.addState(chart[position], state.advance(undefined, position));
      }
    }
  }

  private buildTree(state: DcecEarleyState): DcecParseTree | undefined {
    return state.tree ?? new DcecParseTree(state.rule.lhs);
  }

  private isTerminalCategory(category?: DcecGrammarCategoryValue): boolean {
    if (!category) return false;
    return [...this.lexicon.values()].some((terminals) => terminals.some((terminal) => terminal.category === category));
  }

  private addState(chartCell: Map<string, DcecEarleyState>, state: DcecEarleyState): void {
    if (!chartCell.has(state.key())) chartCell.set(state.key(), state);
  }

  private initGrammar(): void {
    this.rules.push(
      new DcecGrammarRule(DcecGrammarCategory.S, [DcecGrammarCategory.NP, DcecGrammarCategory.VP]),
      new DcecGrammarRule(DcecGrammarCategory.S, [DcecGrammarCategory.DEONTIC]),
      new DcecGrammarRule(DcecGrammarCategory.S, [DcecGrammarCategory.COGNITIVE]),
      new DcecGrammarRule(DcecGrammarCategory.S, [DcecGrammarCategory.TEMPORAL]),
      new DcecGrammarRule(DcecGrammarCategory.NP, [DcecGrammarCategory.DET, DcecGrammarCategory.N]),
      new DcecGrammarRule(DcecGrammarCategory.NP, [DcecGrammarCategory.N]),
      new DcecGrammarRule(DcecGrammarCategory.NP, [DcecGrammarCategory.AGENT]),
      new DcecGrammarRule(DcecGrammarCategory.VP, [DcecGrammarCategory.V]),
      new DcecGrammarRule(DcecGrammarCategory.VP, [DcecGrammarCategory.V, DcecGrammarCategory.NP]),
      new DcecGrammarRule(DcecGrammarCategory.VP, [DcecGrammarCategory.MODAL, DcecGrammarCategory.V]),
      new DcecGrammarRule(DcecGrammarCategory.VP, [DcecGrammarCategory.ACTION]),
      new DcecGrammarRule(DcecGrammarCategory.DEONTIC, [DcecGrammarCategory.AGENT, DcecGrammarCategory.MODAL, DcecGrammarCategory.ACTION]),
      new DcecGrammarRule(DcecGrammarCategory.DEONTIC, [DcecGrammarCategory.MODAL, DcecGrammarCategory.ACTION]),
      new DcecGrammarRule(DcecGrammarCategory.COGNITIVE, [DcecGrammarCategory.AGENT, DcecGrammarCategory.V, DcecGrammarCategory.S]),
      new DcecGrammarRule(DcecGrammarCategory.COGNITIVE, [DcecGrammarCategory.AGENT, DcecGrammarCategory.V, DcecGrammarCategory.FLUENT]),
      new DcecGrammarRule(DcecGrammarCategory.TEMPORAL, [DcecGrammarCategory.ADV, DcecGrammarCategory.S]),
      new DcecGrammarRule(DcecGrammarCategory.TEMPORAL, [DcecGrammarCategory.ADV, DcecGrammarCategory.FLUENT]),
    );
  }

  private initLexicon(): void {
    this.addWords(['the', 'a', 'an'], DcecGrammarCategory.DET);
    this.addWords(['agent', 'person', 'robot', 'system'], DcecGrammarCategory.N);
    this.addWords(['alice', 'bob', 'charlie'], DcecGrammarCategory.AGENT);
    this.addWords(['run', 'walk', 'think', 'believe', 'know'], DcecGrammarCategory.V);
    this.addWords(['open', 'close', 'move', 'stop'], DcecGrammarCategory.ACTION);
    this.addWords(['must', 'should', 'may', 'can', 'must_not'], DcecGrammarCategory.MODAL);
    this.addWords(['always', 'eventually', 'never', 'sometimes'], DcecGrammarCategory.ADV);
    this.addWords(['door_open', 'light_on', 'running'], DcecGrammarCategory.FLUENT);
  }

  private addWords(words: string[], category: DcecGrammarCategoryValue): void {
    for (const word of words) {
      const terminals = this.lexicon.get(word) ?? [];
      terminals.push(new DcecGrammarTerminal(word, category));
      this.lexicon.set(word, terminals);
    }
  }
}

export function createDcecEnhancedGrammarParser(): DcecEnhancedGrammarParser {
  return new DcecEnhancedGrammarParser();
}

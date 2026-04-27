export type CecGrammarCategory =
  | 'Utterance'
  | 'Sentence'
  | 'Boolean'
  | 'Cl'
  | 'Agent'
  | 'ActionType'
  | 'Event'
  | 'Moment'
  | 'Fluent'
  | 'Class'
  | 'Dom'
  | 'Entity'
  | 'Object'
  | 'Query'
  | 'NP'
  | 'VP'
  | 'N'
  | 'V'
  | 'A'
  | 'Adv'
  | 'Prep'
  | 'Det'
  | 'Conj';

export interface CecGrammarConfig {
  version: string;
  language: string;
  caseSensitive: boolean;
  allowContractions: boolean;
  defaultTense: string;
}

export interface CecGrammarOperatorData {
  word?: string;
  words?: string[];
  category?: string;
  pattern?: string;
  patterns?: string[];
  semantics?: Record<string, unknown>;
  examples?: string[];
}

export interface CecGrammarData {
  config?: Partial<CecGrammarConfig> & {
    case_sensitive?: boolean;
    allow_contractions?: boolean;
    default_tense?: string;
  };
  connectives?: Record<string, CecGrammarOperatorData>;
  deontic?: Record<string, CecGrammarOperatorData>;
  cognitive?: Record<string, CecGrammarOperatorData>;
  temporal?: Record<string, CecGrammarOperatorData>;
  quantifiers?: Record<string, CecGrammarOperatorData>;
  production_rules?: Record<string, Array<{ pattern: string; example?: string }>>;
}

export type CecSemanticFunction = (semanticValues: unknown[]) => unknown;
export type CecLinearizeFunction = (semanticValue: unknown) => string;

export interface CecGrammarRuleOptions {
  name: string;
  category: CecGrammarCategory;
  constituents: CecGrammarCategory[];
  semanticFn: CecSemanticFunction;
  linearizeFn?: CecLinearizeFunction;
}

export class CecGrammarRule {
  readonly name: string;
  readonly category: CecGrammarCategory;
  readonly constituents: CecGrammarCategory[];
  readonly semanticFn: CecSemanticFunction;
  readonly linearizeFn?: CecLinearizeFunction;

  constructor(options: CecGrammarRuleOptions) {
    this.name = options.name;
    this.category = options.category;
    this.constituents = [...options.constituents];
    this.semanticFn = options.semanticFn;
    this.linearizeFn = options.linearizeFn;
  }

  canApply(categories: CecGrammarCategory[]): boolean {
    return categories.length === this.constituents.length &&
      categories.every((category, index) => category === this.constituents[index]);
  }

  applySemantics(semanticValues: unknown[]): unknown {
    return this.semanticFn(semanticValues);
  }

  linearize(semanticValue: unknown): string {
    return this.linearizeFn ? this.linearizeFn(semanticValue) : String(semanticValue);
  }
}

export interface CecLexicalEntryOptions {
  word: string;
  category: CecGrammarCategory;
  semantics: unknown;
  features?: Record<string, unknown>;
}

export class CecLexicalEntry {
  readonly word: string;
  readonly category: CecGrammarCategory;
  readonly semantics: unknown;
  readonly features: Record<string, unknown>;

  constructor(options: CecLexicalEntryOptions) {
    this.word = options.word;
    this.category = options.category;
    this.semantics = options.semantics;
    this.features = options.features ? { ...options.features } : {};
  }
}

export class CecParseNode {
  constructor(
    readonly category: CecGrammarCategory,
    readonly rule: CecGrammarRule | undefined,
    readonly children: CecParseNode[],
    readonly semantics: unknown,
    readonly span: [number, number],
  ) {}

  isLexical(): boolean {
    return this.rule === undefined && this.children.length === 0;
  }

  linearize(): string {
    if (this.isLexical()) return String(this.semantics);
    if (this.rule?.linearizeFn) return this.rule.linearize(this.semantics);
    return this.children.map((child) => child.linearize()).join(' ');
  }
}

export class CecGrammarLoader {
  private readonly grammarData: CecGrammarData;
  private readonly config: CecGrammarConfig;

  constructor(grammarData: CecGrammarData = DEFAULT_CEC_GRAMMAR) {
    this.grammarData = grammarData;
    const rawConfig = grammarData.config ?? {};
    this.config = {
      version: rawConfig.version ?? '1.0',
      language: rawConfig.language ?? 'en',
      caseSensitive: rawConfig.caseSensitive ?? rawConfig.case_sensitive ?? false,
      allowContractions: rawConfig.allowContractions ?? rawConfig.allow_contractions ?? true,
      defaultTense: rawConfig.defaultTense ?? rawConfig.default_tense ?? 'present',
    };
  }

  getConfig(): CecGrammarConfig {
    return { ...this.config };
  }

  getConnectives(): Record<string, CecGrammarOperatorData> {
    return this.grammarData.connectives ?? {};
  }

  getDeonticRules(): Record<string, CecGrammarOperatorData> {
    return this.grammarData.deontic ?? {};
  }

  getCognitiveRules(): Record<string, CecGrammarOperatorData> {
    return this.grammarData.cognitive ?? {};
  }

  getTemporalRules(): Record<string, CecGrammarOperatorData> {
    return this.grammarData.temporal ?? {};
  }

  getQuantifiers(): Record<string, CecGrammarOperatorData> {
    return this.grammarData.quantifiers ?? {};
  }

  getProductionRules(): Record<string, Array<{ pattern: string; example?: string }>> {
    return this.grammarData.production_rules ?? {};
  }

  getWordsForOperator(operatorType: keyof Pick<CecGrammarData, 'deontic' | 'cognitive' | 'temporal' | 'quantifiers' | 'connectives'>, operatorName: string): string[] {
    const operatorData = this.grammarData[operatorType]?.[operatorName];
    if (!operatorData) return [];
    if (operatorData.words) return [...operatorData.words];
    if (operatorData.word) return [operatorData.word];
    return [];
  }

  getSemantics(operatorType: keyof CecGrammarData, operatorName: string): Record<string, unknown> {
    const section = this.grammarData[operatorType];
    if (!section || Array.isArray(section)) return {};
    return (section as Record<string, CecGrammarOperatorData>)[operatorName]?.semantics ?? {};
  }

  getExamples(operatorType: keyof CecGrammarData, operatorName: string): string[] {
    const section = this.grammarData[operatorType];
    if (!section || Array.isArray(section)) return [];
    return (section as Record<string, CecGrammarOperatorData>)[operatorName]?.examples ?? [];
  }

  validate(): boolean {
    return ['connectives', 'deontic', 'cognitive', 'temporal', 'quantifiers']
      .every((section) => section in this.grammarData);
  }

  getAllWords(): string[] {
    const words: string[] = [];
    for (const connective of Object.values(this.getConnectives())) {
      if (connective.word) words.push(connective.word);
    }
    for (const section of [this.getDeonticRules(), this.getCognitiveRules(), this.getTemporalRules(), this.getQuantifiers()]) {
      for (const operator of Object.values(section)) {
        if (operator.words) words.push(...operator.words);
        else if (operator.word) words.push(operator.word);
      }
    }
    return words;
  }
}

export class CecGrammarEngine {
  readonly rules: CecGrammarRule[] = [];
  readonly lexicon = new Map<string, CecLexicalEntry[]>();
  startCategory: CecGrammarCategory = 'Utterance';

  addRule(rule: CecGrammarRule): void {
    this.rules.push(rule);
  }

  addLexicalEntry(entry: CecLexicalEntry): void {
    const key = entry.word.toLowerCase();
    const entries = this.lexicon.get(key) ?? [];
    entries.push(entry);
    this.lexicon.set(key, entries);
  }

  parse(text: string): CecParseNode[] {
    const tokens = this.tokenize(text);
    const count = tokens.length;
    if (count === 0) return [];
    const chart: CecParseNode[][][] = Array.from({ length: count + 1 }, () =>
      Array.from({ length: count + 1 }, () => []),
    );

    tokens.forEach((token, index) => {
      for (const entry of this.lexicon.get(token) ?? []) {
        chart[index][index + 1].push(new CecParseNode(entry.category, undefined, [], entry.semantics, [index, index + 1]));
      }
    });

    for (let length = 1; length <= count; length += 1) {
      for (let start = 0; start <= count - length; start += 1) {
        const end = start + length;
        let changed = true;
        while (changed) {
          changed = false;
          for (const rule of this.rules.filter((candidate) => candidate.constituents.length === 1)) {
            for (const child of [...chart[start][end]]) {
              if (!rule.canApply([child.category])) continue;
              const semantics = rule.applySemantics([child.semantics]);
              const node = new CecParseNode(rule.category, rule, [child], semantics, [start, end]);
              if (!hasEquivalentParse(chart[start][end], node)) {
                chart[start][end].push(node);
                changed = true;
              }
            }
          }
        }
      }
      for (let start = 0; start <= count - length; start += 1) {
        const end = start + length;
        for (let split = start + 1; split < end; split += 1) {
          for (const rule of this.rules.filter((candidate) => candidate.constituents.length === 2)) {
            for (const left of chart[start][split]) {
              for (const right of chart[split][end]) {
                if (!rule.canApply([left.category, right.category])) continue;
                chart[start][end].push(new CecParseNode(
                  rule.category,
                  rule,
                  [left, right],
                  rule.applySemantics([left.semantics, right.semantics]),
                  [start, end],
                ));
              }
            }
          }
        }
      }
    }

    return chart[0][count].filter((node) => node.category === this.startCategory);
  }

  linearize(semanticValue: unknown, category: CecGrammarCategory): string {
    for (const rule of this.rules) {
      if (rule.category !== category || !rule.linearizeFn) continue;
      try {
        return rule.linearizeFn(semanticValue);
      } catch {
        // Try the next rule, mirroring the Python engine's fallback behavior.
      }
    }
    return String(semanticValue);
  }

  resolveAmbiguity(parses: CecParseNode[], strategy: 'first' | 'shortest' | 'most_specific' = 'first'): CecParseNode | undefined {
    if (parses.length === 0) return undefined;
    if (strategy === 'shortest') return minBy(parses, countParseNodes);
    if (strategy === 'most_specific') return maxBy(parses, specificityScore);
    return parses[0];
  }

  protected tokenize(text: string): string[] {
    return text.toLowerCase().trim().split(/\s+/).filter(Boolean);
  }
}

export function createDefaultCecGrammarLoader(): CecGrammarLoader {
  return new CecGrammarLoader(DEFAULT_CEC_GRAMMAR);
}

function hasEquivalentParse(nodes: CecParseNode[], candidate: CecParseNode): boolean {
  return nodes.some((node) =>
    node.category === candidate.category &&
    node.span[0] === candidate.span[0] &&
    node.span[1] === candidate.span[1] &&
    JSON.stringify(node.semantics) === JSON.stringify(candidate.semantics),
  );
}

function countParseNodes(node: CecParseNode): number {
  return 1 + node.children.reduce((total, child) => total + countParseNodes(child), 0);
}

function specificityScore(node: CecParseNode): number {
  if (node.isLexical()) {
    const scores: Partial<Record<CecGrammarCategory, number>> = {
      Agent: 5,
      ActionType: 4,
      Fluent: 3,
      N: 2,
      V: 2,
    };
    return scores[node.category] ?? 1;
  }
  return node.children.reduce((total, child) => total + specificityScore(child), 0);
}

function minBy<T>(items: T[], scorer: (item: T) => number): T {
  return items.reduce((best, item) => scorer(item) < scorer(best) ? item : best);
}

function maxBy<T>(items: T[], scorer: (item: T) => number): T {
  return items.reduce((best, item) => scorer(item) > scorer(best) ? item : best);
}

export const DEFAULT_CEC_GRAMMAR: CecGrammarData = {
  connectives: {
    and: { word: 'and', category: 'CONJUNCTION', semantics: { type: 'and', connective: 'AND' }, examples: ['Alice loves Bob and Carol'] },
    or: { word: 'or', category: 'CONJUNCTION', semantics: { type: 'or', connective: 'OR' }, examples: ['Alice or Bob will go'] },
    not: { word: 'not', category: 'ADVERB', semantics: { type: 'not', connective: 'NOT' }, examples: ['It is not raining'] },
    if_then: { patterns: ['if {P} then {Q}', '{P} implies {Q}'], semantics: { type: 'implies', connective: 'IMPLIES' } },
  },
  deontic: {
    obligation: { words: ['must', 'obligated', 'should', 'required'], category: 'VERB', semantics: { type: 'deontic', operator: 'obligated' } },
    permission: { words: ['may', 'permitted', 'allowed', 'can'], category: 'VERB', semantics: { type: 'deontic', operator: 'permitted' } },
    prohibition: { words: ['forbidden', 'prohibited', 'must not'], category: 'VERB', semantics: { type: 'deontic', operator: 'forbidden' } },
  },
  cognitive: {
    belief: { words: ['believes', 'think', 'assume'], category: 'VERB', semantics: { type: 'cognitive', operator: 'belief' } },
    knowledge: { words: ['knows', 'aware'], category: 'VERB', semantics: { type: 'cognitive', operator: 'knowledge' } },
    intention: { words: ['intends', 'plans', 'wants'], category: 'VERB', semantics: { type: 'cognitive', operator: 'intention' } },
    desire: { words: ['desires', 'wishes', 'hopes'], category: 'VERB', semantics: { type: 'cognitive', operator: 'desire' } },
  },
  temporal: {
    always: { words: ['always', 'necessarily', 'invariably'], category: 'ADVERB', semantics: { type: 'temporal', operator: 'always' } },
    eventually: { words: ['eventually', 'sometime', 'ultimately'], category: 'ADVERB', semantics: { type: 'temporal', operator: 'eventually' } },
    next: { words: ['next', 'immediately'], category: 'ADVERB', semantics: { type: 'temporal', operator: 'next' } },
    until: { words: ['until'], category: 'PREPOSITION', semantics: { type: 'temporal', operator: 'until' } },
  },
  quantifiers: {
    universal: { words: ['all', 'every', 'each'], category: 'DETERMINER', semantics: { type: 'quantifier', operator: 'forall' } },
    existential: { words: ['some', 'a', 'an', 'exists'], category: 'DETERMINER', semantics: { type: 'quantifier', operator: 'exists' } },
  },
  production_rules: {
    sentence: [
      { pattern: '{subject} {verb} {object}', example: 'Alice loves Bob' },
      { pattern: '{agent} {modal} {verb} {object}', example: 'Alice must go home' },
    ],
    compound: [
      { pattern: '{sentence} {connective} {sentence}', example: 'Alice goes and Bob stays' },
      { pattern: 'if {condition} then {consequence}', example: 'if it rains then the ground is wet' },
    ],
  },
  config: {
    version: '1.0',
    language: 'en',
    caseSensitive: false,
    allowContractions: true,
    defaultTense: 'present',
  },
};

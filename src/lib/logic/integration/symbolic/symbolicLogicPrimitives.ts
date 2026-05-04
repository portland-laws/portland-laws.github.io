export type LogicPrimitiveOutputFormat = 'symbolic' | 'prolog' | 'tptp';
export type LogicStructureType =
  | 'simple_statement'
  | 'universal'
  | 'existential'
  | 'conditional'
  | 'compound';
export interface LogicStructureAnalysis {
  readonly type: LogicStructureType;
  readonly hasQuantifiers: boolean;
  readonly hasConnectives: boolean;
  readonly wordCount: number;
  readonly complexity: 'low' | 'medium';
}

export const SYMBOLIC_LOGIC_PRIMITIVES_METADATA = {
  sourcePythonModule: 'logic/integration/symbolic/symbolic_logic_primitives.py',
  browserNative: true,
  wasmCompatible: true,
  serverCallsAllowed: false,
  pythonRuntimeAllowed: false,
  runtimeDependencies: [],
  symbolicAiAvailable: false,
  parity: [
    'create_logic_symbol',
    'fallback_to_fol',
    'fallback_quantifier_extraction',
    'fallback_predicate_extraction',
    'logical_operator_primitives',
    'local_fail_closed_no_symai',
  ],
} as const;

const QUANTIFIERS: readonly [string, RegExp][] = [
  ['universal', /\b(all|every|each|always|never)\b/gi],
  ['existential', /\b(some|exists?|there\s+(?:is|are)|at\s+least\s+one)\b/gi],
  ['numerical', /\b(many|few|most|several|majority)\b/gi],
];
const PREDICATES: readonly RegExp[] = [
  /\b(is|are|was|were|being|been)\b/gi,
  /\b(has|have|had|having)\b/gi,
  /\b(can|could|cannot|must|should|will|would)\b/gi,
  /\b(loves?|hates?|likes?|enjoys?)\b/gi,
  /\b(studies?|works?|plays?|runs?|flies?|swims?)\b/gi,
  /\b(belongs?|owns?|contains?|includes?)\b/gi,
];

export class BrowserNativeLogicSymbol {
  readonly metadata = SYMBOLIC_LOGIC_PRIMITIVES_METADATA;
  readonly value: string;
  readonly semantic: boolean;
  constructor(value: string, semantic = true) {
    this.value = typeof value === 'string' ? value : String(value);
    this.semantic = semantic;
  }
  toFol(outputFormat: LogicPrimitiveOutputFormat = 'symbolic'): BrowserNativeLogicSymbol {
    return this.toType(formatFormula(toFolFormula(this.value.toLowerCase()), outputFormat));
  }
  to_fol(outputFormat: LogicPrimitiveOutputFormat = 'symbolic'): BrowserNativeLogicSymbol {
    return this.toFol(outputFormat);
  }
  extractQuantifiers(): BrowserNativeLogicSymbol {
    const found = QUANTIFIERS.flatMap(([kind, pattern]) =>
      matches(this.value, pattern).map((match) => `${kind}:${match}`),
    );
    return this.toType(found.length > 0 ? found.join(', ') : 'none');
  }
  extract_quantifiers(): BrowserNativeLogicSymbol {
    return this.extractQuantifiers();
  }
  extractPredicates(): BrowserNativeLogicSymbol {
    const found = unique(PREDICATES.flatMap((pattern) => matches(this.value, pattern)));
    return this.toType(found.length > 0 ? found.join(', ') : 'none');
  }
  extract_predicates(): BrowserNativeLogicSymbol {
    return this.extractPredicates();
  }
  logicalAnd(other: BrowserNativeLogicSymbol): BrowserNativeLogicSymbol {
    return this.toType(`(${this.value}) ∧ (${other.value})`);
  }
  logical_and(other: BrowserNativeLogicSymbol): BrowserNativeLogicSymbol {
    return this.logicalAnd(other);
  }
  logicalOr(other: BrowserNativeLogicSymbol): BrowserNativeLogicSymbol {
    return this.toType(`(${this.value}) ∨ (${other.value})`);
  }
  logical_or(other: BrowserNativeLogicSymbol): BrowserNativeLogicSymbol {
    return this.logicalOr(other);
  }
  implies(other: BrowserNativeLogicSymbol): BrowserNativeLogicSymbol {
    return this.toType(`(${this.value}) → (${other.value})`);
  }
  negate(): BrowserNativeLogicSymbol {
    return this.toType(`¬(${this.value})`);
  }
  analyzeLogicalStructure(): BrowserNativeLogicSymbol {
    const wordCount = this.value
      .trim()
      .split(/\s+/)
      .filter((word) => word.length > 0).length;
    const hasQuantifiers =
      /\b(all|every|each|always|never|some|exists?|there\s+(?:is|are))\b/i.test(this.value);
    const hasConnectives = /\b(and|or|if|then|not)\b/i.test(this.value);
    return this.toType(
      JSON.stringify({
        type: detectType(this.value, hasQuantifiers, hasConnectives),
        hasQuantifiers,
        hasConnectives,
        wordCount,
        complexity: wordCount < 10 ? 'low' : 'medium',
      } satisfies LogicStructureAnalysis),
    );
  }
  analyze_logical_structure(): BrowserNativeLogicSymbol {
    return this.analyzeLogicalStructure();
  }
  simplifyLogic(): BrowserNativeLogicSymbol {
    return this.toType(
      this.value
        .trim()
        .replace(/\s+/g, ' ')
        .replace(/\(\s*([^)]+?)\s*\)/g, '($1)'),
    );
  }
  simplify_logic(): BrowserNativeLogicSymbol {
    return this.simplifyLogic();
  }
  private toType(value: string): BrowserNativeLogicSymbol {
    return new BrowserNativeLogicSymbol(value, this.semantic);
  }
}

export const LogicSymbol = BrowserNativeLogicSymbol;
export const LogicPrimitives = BrowserNativeLogicSymbol;
export const createLogicSymbol = (text: string, semantic = true): BrowserNativeLogicSymbol =>
  new BrowserNativeLogicSymbol(text, semantic);
export const create_logic_symbol = createLogicSymbol;
export const getAvailablePrimitives = (): Array<string> => [
  'to_fol',
  'extract_quantifiers',
  'extract_predicates',
  'logical_and',
  'logical_or',
  'implies',
  'negate',
  'analyze_logical_structure',
  'simplify_logic',
];
export const get_available_primitives = getAvailablePrimitives;

function toFolFormula(text: string): string {
  const areParts = text.split(' are ');
  if (/\b(all|every)\b/.test(text))
    return areParts.length === 2
      ? `∀x (${cap(areParts[0].replace(/\b(all|every)\b/g, ''))}(x) → ${cap(areParts[1])}(x))`
      : '∀x Statement(x)';
  if (/\b(some|exists?)\b/.test(text)) {
    const canParts = text.split(' can ');
    if (areParts.length === 2)
      return `∃x (${cap(areParts[0].replace(/\b(some|exists?)\b/g, ''))}(x) ∧ ${cap(areParts[1])}(x))`;
    return canParts.length === 2
      ? `∃x (${cap(canParts[0].replace(/\bsome\b/g, ''))}(x) ∧ ${cap(canParts[1])}(x))`
      : '∃x Statement(x)';
  }
  if (text.includes(' if ') || text.startsWith('if ')) {
    const parts = text.split(' then ');
    return parts.length === 2
      ? `${atom(parts[0].replace(/^if\s+/, ''))} → ${atom(parts[1])}`
      : 'If_condition → Consequence';
  }
  if (text.includes(' or ')) {
    const parts = text.split(' or ');
    return `${atom(parts[0])} ∨ ${atom(parts.slice(1).join(' or '))}`;
  }
  return `Statement(${snake(text)})`;
}

function formatFormula(formula: string, outputFormat: LogicPrimitiveOutputFormat): string {
  if (outputFormat === 'prolog') {
    const converted = formula
      .replace(/∀x/g, 'forall(X,')
      .replace(/∃x/g, 'exists(X,')
      .replace(/∧/g, ',')
      .replace(/∨/g, ';')
      .replace(/→/g, ':-');
    return converted.endsWith(')') ? converted : `${converted})`;
  }
  return outputFormat === 'tptp'
    ? formula
        .replace(/∀x/g, '! [X]:')
        .replace(/∃x/g, '? [X]:')
        .replace(/∧/g, ' & ')
        .replace(/∨/g, ' | ')
        .replace(/→/g, ' => ')
    : formula;
}

function detectType(
  text: string,
  hasQuantifiers: boolean,
  hasConnectives: boolean,
): LogicStructureType {
  if (/^\s*if\b|\bthen\b/i.test(text)) return 'conditional';
  if (/\b(all|every|each|always|never)\b/i.test(text)) return 'universal';
  if (/\b(some|exists?|there\s+(?:is|are)|at\s+least\s+one)\b/i.test(text)) return 'existential';
  return hasQuantifiers || hasConnectives ? 'compound' : 'simple_statement';
}

function matches(text: string, pattern: RegExp): Array<string> {
  pattern.lastIndex = 0;
  return Array.from(text.matchAll(pattern), (match) => match[0]);
}
const unique = (items: Array<string>): Array<string> =>
  Array.from(new Set(items.map((item) => item.toLowerCase())));
const cap = (value: string): string =>
  value.trim().replace(/^./, (letter) => letter.toUpperCase()) || 'Statement';
const snake = (value: string): string =>
  value
    .trim()
    .replace(/[^a-z0-9]+/gi, '_')
    .replace(/^_+|_+$/g, '') || 'statement';
const atom = (value: string): string => cap(snake(value));

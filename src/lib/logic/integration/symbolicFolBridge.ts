import { convertToPrologFormat, convertToTptpFormat } from '../fol/formatter';

export interface BrowserNativeSemanticSymbol {
  value: string;
  semantic: boolean;
}
export interface LogicalComponents {
  quantifiers: string[];
  predicates: string[];
  entities: string[];
  logicalConnectives: string[];
  connectives: string[];
  confidence: number;
  rawText: string;
}
export interface FOLConversionResult {
  folFormula: string;
  fol_formula: string;
  components: LogicalComponents;
  confidence: number;
  reasoningSteps: string[];
  reasoning_steps: string[];
  fallbackUsed: boolean;
  fallback_used: boolean;
  errors: string[];
}

export interface SymbolicFOLBridgeOptions {
  confidenceThreshold?: number;
  fallbackEnabled?: boolean;
  enableCaching?: boolean;
  sourcePythonModule?: string;
}

const STOP_WORDS = new Set([
  'all',
  'every',
  'each',
  'some',
  'exists',
  'exist',
  'there',
  'is',
  'are',
  'has',
  'have',
  'can',
  'cannot',
  'and',
  'or',
  'not',
  'if',
  'then',
  'that',
  'the',
  'for',
  'with',
]);

export class SymbolicFOLBridge {
  readonly confidenceThreshold: number;
  readonly fallbackEnabled: boolean;
  readonly enableCaching: boolean;
  readonly sourcePythonModule: string;
  private readonly cache = new Map<string, FOLConversionResult>();

  constructor(options: SymbolicFOLBridgeOptions = {}) {
    this.confidenceThreshold = options.confidenceThreshold ?? 0.7;
    this.fallbackEnabled = options.fallbackEnabled ?? true;
    this.enableCaching = options.enableCaching ?? true;
    this.sourcePythonModule =
      options.sourcePythonModule ?? 'logic/integration/bridges/symbolic_fol_bridge.py';
  }

  createSemanticSymbol(text: string): BrowserNativeSemanticSymbol {
    const value = text.trim();
    if (!value || /^\d+$/.test(value) || (/^[a-z]$/.test(value) && value.length === 1))
      throw new Error('Text cannot be empty');
    return { value, semantic: true };
  }
  create_semantic_symbol(text: string): BrowserNativeSemanticSymbol {
    return this.createSemanticSymbol(text);
  }

  extractLogicalComponents(symbol: BrowserNativeSemanticSymbol): LogicalComponents {
    const connectives = matches(symbol.value, /\b(and|or|not|if|then|implies?|but|however)\b/gi);
    const predicates = matches(
      symbol.value,
      /\b(is|are|has|have|can|cannot|loves?|studies?|flies?|runs?|requires?|uses?|knows?|works?|exists?)\b/gi,
    ).map(lower);
    const entities = matches(symbol.value, /\b[a-zA-Z]{2,}\b/g).filter(
      (word) => !STOP_WORDS.has(lower(word)) && !predicates.includes(lower(word)),
    );
    return {
      quantifiers: matches(
        symbol.value,
        /\b(all|every|each|some|exists?|for\s+all|there\s+(?:is|are))\b/gi,
      ).map(lower),
      predicates,
      entities,
      logicalConnectives: connectives,
      connectives,
      confidence: 0.6,
      rawText: symbol.value,
    };
  }
  extract_logical_components(symbol: BrowserNativeSemanticSymbol): LogicalComponents {
    return this.extractLogicalComponents(symbol);
  }

  convertToFol(text: string, outputFormat = 'symbolic'): FOLConversionResult {
    if (!text.trim())
      return makeResult('', emptyComponents(text), 0, [], true, ['Input text is empty']);
    const cacheKey = `${outputFormat}|${text.trim()}|${this.confidenceThreshold}|${this.fallbackEnabled}`;
    const cached = this.enableCaching ? this.cache.get(cacheKey) : undefined;
    if (cached) return cached;
    const reasoningSteps = [`Processing: '${text}'`];
    let folFormula = this.patternBasedConversion(text);
    let confidence = 0.8;
    let fallbackUsed = false;
    if (folFormula) reasoningSteps.push('Pattern-based conversion succeeded');
    else {
      reasoningSteps.push('Using semantic/fallback conversion');
      folFormula = `Statement(${text.trim().replace(/\s+/g, '_')})`;
      confidence = 0.5;
      fallbackUsed = true;
    }
    const converted = makeResult(
      formatFormula(folFormula, outputFormat),
      this.extractLogicalComponents({ value: text.trim(), semantic: true }),
      confidence,
      reasoningSteps,
      fallbackUsed,
      [],
    );
    if (this.enableCaching) this.cache.set(cacheKey, converted);
    return converted;
  }
  convert_to_fol(text: string, output_format = 'symbolic'): FOLConversionResult {
    return this.convertToFol(text, output_format);
  }
  semanticToFol(
    symbol: BrowserNativeSemanticSymbol,
    outputFormat = 'symbolic',
  ): FOLConversionResult {
    return this.convertToFol(symbol.value, outputFormat);
  }
  semantic_to_fol(
    symbol: BrowserNativeSemanticSymbol,
    output_format = 'symbolic',
  ): FOLConversionResult {
    return this.semanticToFol(symbol, output_format);
  }

  validateFolFormula(formula: string): Record<string, unknown> {
    const predicates = [...formula.matchAll(/[A-Z][a-zA-Z]*\([^)]+\)/g)].map((match) => match[0]);
    const errors: string[] = [];
    if (!formula.trim()) errors.push('Formula is empty');
    if ((formula.match(/\(/g) ?? []).length !== (formula.match(/\)/g) ?? []).length)
      errors.push('Unbalanced parentheses');
    return {
      valid: errors.length === 0,
      errors,
      warnings: predicates.length === 0 ? ['No predicates found'] : [],
      structure: {
        has_quantifiers: /[∀∃!?]|\b(?:forall|exists)\b/.test(formula),
        predicates,
        predicate_count: predicates.length,
        connectives: ['∧', '∨', '→', '¬', '&', '|', '=>', ':-', ',', ';'].filter((item) =>
          formula.includes(item),
        ),
      },
    };
  }
  validate_fol_formula(formula: string): Record<string, unknown> {
    return this.validateFolFormula(formula);
  }

  getStatistics(): Record<string, unknown> {
    const totalConversions = this.enableCaching ? this.cache.size : 'N/A';
    return {
      sourcePythonModule: this.sourcePythonModule,
      source_python_module: this.sourcePythonModule,
      runtime: 'typescript-wasm-browser',
      symbolicAiAvailable: false,
      symbolic_ai_available: false,
      fallbackAvailable: true,
      fallback_available: true,
      serverCallsAllowed: false,
      pythonRuntime: false,
      cacheSize: this.cache.size,
      cache_size: this.cache.size,
      confidenceThreshold: this.confidenceThreshold,
      confidence_threshold: this.confidenceThreshold,
      totalConversions,
      total_conversions: totalConversions,
    };
  }
  get_statistics(): Record<string, unknown> {
    return this.getStatistics();
  }
  get_stats(): Record<string, unknown> {
    return this.getStatistics();
  }
  clearCache(): void {
    this.cache.clear();
  }
  clear_cache(): void {
    this.clearCache();
  }

  private patternBasedConversion(text: string): string | undefined {
    const normalized = lower(text.trim());
    const implication = normalized.match(/^if\s+(.+?)\s+then\s+(.+)$/);
    if (implication) {
      const antecedent = this.patternBasedConversion(implication[1]);
      const consequent = this.patternBasedConversion(implication[2]);
      if (antecedent && consequent) return `(${antecedent} → ${consequent})`;
    }
    const all = normalized.match(/^(?:all|every)\s+(\w+)\s+are\s+(\w+)/);
    if (all) return `∀x (${cap(all[1])}(x) → ${cap(all[2])}(x))`;
    const some = normalized.match(/^some\s+(\w+)\s+are\s+(\w+)/);
    if (some) return `∃x (${cap(some[1])}(x) ∧ ${cap(some[2])}(x))`;
    const relation = text
      .trim()
      .match(/^([A-Z][a-zA-Z]*)\s+(loves?|knows?|requires?)\s+([A-Z][a-zA-Z]*)$/);
    return relation
      ? `${cap(lower(relation[2]).replace(/s$/, ''))}(${relation[1]}, ${relation[3]})`
      : undefined;
  }
}

export const BrowserNativeSymbolicFOLBridge = SymbolicFOLBridge;

function makeResult(
  folFormula: string,
  components: LogicalComponents,
  confidence: number,
  reasoningSteps: string[],
  fallbackUsed: boolean,
  errors: string[],
): FOLConversionResult {
  return {
    folFormula,
    fol_formula: folFormula,
    components,
    confidence,
    reasoningSteps,
    reasoning_steps: reasoningSteps,
    fallbackUsed,
    fallback_used: fallbackUsed,
    errors,
  };
}
function emptyComponents(rawText: string): LogicalComponents {
  return {
    quantifiers: [],
    predicates: [],
    entities: [],
    logicalConnectives: [],
    connectives: [],
    confidence: 0,
    rawText,
  };
}
function matches(text: string, pattern: RegExp): string[] {
  return Array.from(new Set([...text.matchAll(pattern)].map((match) => match[0])));
}
function formatFormula(formula: string, outputFormat: string): string {
  if (outputFormat === 'prolog') return convertToPrologFormat(formula);
  if (outputFormat === 'tptp') return convertToTptpFormat(formula).replace('formula', 'statement');
  return formula;
}
function lower(value: string): string {
  return value.toLowerCase();
}
function cap(value: string): string {
  return `${value.charAt(0).toUpperCase()}${value.slice(1)}`;
}

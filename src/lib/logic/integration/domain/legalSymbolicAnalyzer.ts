import { classifyLegalDomainKnowledge, type LegalDomainId } from './legalDomainKnowledge';

export type LegalSymbolicOperator = 'obligation' | 'permission' | 'prohibition' | 'condition';
export type LegalSymbolicSymbol = 'O' | 'P' | 'F' | 'IF';
export interface LegalSymbolicStatement {
  readonly operator: LegalSymbolicOperator;
  readonly symbol: LegalSymbolicSymbol;
  readonly text: string;
  readonly formula: string;
  readonly confidence: number;
}
export interface LegalSymbolicReference {
  readonly kind: 'citation' | 'section' | 'case';
  readonly value: string;
}
export interface LegalSymbolicAnalysisResult {
  readonly accepted: boolean;
  readonly runtime: 'browser-native';
  readonly wasmCompatible: true;
  readonly serverCallsAllowed: false;
  readonly pythonRuntimeAllowed: false;
  readonly sourceText: string;
  readonly domains: readonly LegalDomainId[];
  readonly statements: readonly LegalSymbolicStatement[];
  readonly references: readonly LegalSymbolicReference[];
  readonly issues: readonly string[];
  readonly metadata: typeof LEGAL_SYMBOLIC_ANALYZER_METADATA;
}

export const LEGAL_SYMBOLIC_ANALYZER_METADATA = {
  sourcePythonModule: 'logic/integration/domain/legal_symbolic_analyzer.py',
  browserNative: true,
  wasmCompatible: true,
  serverCallsAllowed: false,
  pythonRuntimeAllowed: false,
  runtimeDependencies: [],
  parity: ['deterministic_symbol_extraction', 'reference_detection', 'local_fail_closed'],
} as const;

const OPERATORS: readonly [LegalSymbolicOperator, LegalSymbolicSymbol, RegExp][] = [
  ['obligation', 'O', /\b(shall(?!\s+not)|must(?!\s+not)|required to|has a duty to)\b/i],
  ['permission', 'P', /\b(may|authorized to|permitted to|allowed to)\b/i],
  ['prohibition', 'F', /\b(shall not|must not|may not|prohibited from|forbidden to)\b/i],
  ['condition', 'IF', /\b(if|unless|provided that|when|where)\b/i],
];

const REFERENCE_PATTERNS: readonly [LegalSymbolicReference['kind'], RegExp][] = [
  [
    'citation',
    /\b\d{1,4}\s+(?:U\.S\.|S\. Ct\.|F\.\d+d|F\. Supp\. \d+d|P\.\d+d|Or\.|Or\. App\.)\s+\d{1,5}\b/g,
  ],
  ['section', /\b(?:PCC|ORS|USC|U\.S\.C\.|§)\s*[\w.-]+(?:\([\w-]+\))*/gi],
  [
    'case',
    /\b[A-Z][\w.'&-]*(?:\s+[A-Z][\w.'&-]*){0,4}\s+v\.\s+[A-Z][\w.'&-]*(?:\s+[A-Z][\w.'&-]*){0,4}\b/g,
  ],
];

export class BrowserNativeLegalSymbolicAnalyzer {
  readonly metadata = LEGAL_SYMBOLIC_ANALYZER_METADATA;

  analyze(text: string): LegalSymbolicAnalysisResult {
    const sourceText = typeof text === 'string' ? text : '';
    const normalized = sourceText.replace(/\s+/g, ' ').trim();
    if (normalized.length < 3) return closed(sourceText, ['source text is required']);

    const statements = splitSentences(normalized).flatMap(extractStatements);
    const references = extractReferences(normalized);
    const issues = [
      ...(statements.length === 0 ? ['no legal symbolic operators matched locally'] : []),
      ...(references.length === 0 ? ['no legal references detected locally'] : []),
    ];
    return {
      accepted: statements.length > 0,
      runtime: 'browser-native',
      wasmCompatible: true,
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
      sourceText,
      domains: classifyLegalDomainKnowledge(normalized).matches.map((match) => match.domain),
      statements,
      references,
      issues,
      metadata: this.metadata,
    };
  }
}

export function analyzeLegalSymbolicText(text: string): LegalSymbolicAnalysisResult {
  return new BrowserNativeLegalSymbolicAnalyzer().analyze(text);
}

export const create_legal_symbolic_analyzer = (): BrowserNativeLegalSymbolicAnalyzer =>
  new BrowserNativeLegalSymbolicAnalyzer();
export const analyze_legal_symbolic_text = analyzeLegalSymbolicText;
export const analyze_legal_symbols = analyzeLegalSymbolicText;

function extractStatements(sentence: string): readonly LegalSymbolicStatement[] {
  return OPERATORS.filter(([, , pattern]) => pattern.test(sentence)).map(([operator, symbol]) => ({
    operator,
    symbol,
    text: sentence,
    formula: `${symbol}(${toPredicate(sentence)})`,
    confidence: Number(
      Math.min(0.95, 0.72 + (extractReferences(sentence).length > 0 ? 0.1 : 0)).toFixed(2),
    ),
  }));
}

function extractReferences(text: string): readonly LegalSymbolicReference[] {
  return REFERENCE_PATTERNS.flatMap(([kind, pattern]) => {
    pattern.lastIndex = 0;
    return [...new Set([...text.matchAll(pattern)].map((match) => match[0].trim()))].map(
      (value) => ({ kind, value }),
    );
  });
}

function splitSentences(text: string): readonly string[] {
  return text
    .split(/(?<=[.!?])\s+/)
    .map((item) => item.trim())
    .filter((item) => item.length > 0);
}

function toPredicate(sentence: string): string {
  const value = sentence
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .slice(0, 96);
  return value.length > 0 ? value : 'legal_statement';
}

function closed(sourceText: string, issues: readonly string[]): LegalSymbolicAnalysisResult {
  return {
    accepted: false,
    runtime: 'browser-native',
    wasmCompatible: true,
    serverCallsAllowed: false,
    pythonRuntimeAllowed: false,
    sourceText,
    domains: [],
    statements: [],
    references: [],
    issues,
    metadata: LEGAL_SYMBOLIC_ANALYZER_METADATA,
  };
}

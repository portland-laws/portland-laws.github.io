import {
  DcecAtomicFormula,
  DcecCognitiveFormula,
  DcecConnectiveFormula,
  DcecDeonticFormula,
  DcecFormula,
  DcecTemporalFormula,
  DcecVariableTerm,
} from './dcecCore';
import { DcecNamespace } from './dcecNamespace';
import {
  DcecCognitiveOperator,
  DcecCognitiveOperatorValue,
  DcecDeonticOperator,
  DcecDeonticOperatorValue,
  DcecLogicalConnective,
  DcecLogicalConnectiveValue,
  DcecPredicateSymbol,
  DcecTemporalOperator,
  DcecTemporalOperatorValue,
} from './dcecTypes';

export interface DcecNlConversionResult {
  english_text: string;
  dcec_formula?: DcecFormula;
  success: boolean;
  error_message?: string;
  confidence: number;
  parse_method: string;
}

export interface DcecConversionStatistics {
  [metric: string]: number;
}

export type DcecScoredPolicyLanguage = 'en' | 'es' | 'fr' | 'de';
export type DcecPolicyLanguage = DcecScoredPolicyLanguage | 'unknown';

export interface DcecPolicyLanguageScores {
  en: number;
  es: number;
  fr: number;
  de: number;
}

export interface DcecPolicyLanguageDetection {
  language: DcecPolicyLanguage;
  confidence: number;
  scores: DcecPolicyLanguageScores;
  matched_terms: string[];
  method: 'browser_native_keyword_profile';
  browser_native: true;
}

export interface DcecPolicyCompilationResult extends DcecNlConversionResult {
  normalized_policy_text: string;
  language_detection: DcecPolicyLanguageDetection;
  policy_formula_text?: string;
  fail_closed_reason?: string;
  browser_native: true;
}

export interface DcecGrammarAdapter {
  parse_to_dcec(text: string): DcecFormula | undefined;
  formula_to_english(formula: DcecFormula): string | undefined;
  browser_native: true;
}

export type DcecProofStrategy =
  | 'direct'
  | 'advanced_inference'
  | 'deontic_consistency'
  | 'temporal_lift';
export type DcecProofStatus = 'proved' | 'unknown' | 'invalid';

export interface DcecProofRequest {
  goal: DcecFormula;
  assumptions?: DcecFormula[];
  strategy?: DcecProofStrategy;
  cache?: DcecProofCache;
}

export interface DcecProofResult {
  status: DcecProofStatus;
  proved: boolean;
  strategy: DcecProofStrategy;
  goal: string;
  proof_steps: string[];
  cache_hit: boolean;
  browser_native: true;
  error_message?: string;
}

export class DcecProofCache {
  private readonly entries = new Map<string, DcecProofResult>();

  get(key: string): DcecProofResult | undefined {
    const cached = this.entries.get(key);
    return cached
      ? { ...cached, proof_steps: [...cached.proof_steps], cache_hit: true }
      : undefined;
  }

  set(key: string, result: DcecProofResult): void {
    this.entries.set(key, { ...result, proof_steps: [...result.proof_steps], cache_hit: false });
  }

  clear(): void {
    this.entries.clear();
  }

  get size(): number {
    return this.entries.size;
  }
}

type DeonticPattern = [RegExp, DcecDeonticOperatorValue];
type CognitivePattern = [RegExp, DcecCognitiveOperatorValue];
type TemporalPattern = [RegExp, DcecTemporalOperatorValue];
type ConnectivePattern = [RegExp, DcecLogicalConnectiveValue];

interface DcecLanguageProfile {
  language: DcecScoredPolicyLanguage;
  terms: string[];
  policyTerms: string[];
}

const POLICY_LANGUAGE_PROFILES: DcecLanguageProfile[] = [
  {
    language: 'en',
    terms: [
      'the',
      'tenant',
      'landlord',
      'person',
      'must',
      'shall',
      'may',
      'required',
      'prohibited',
      'policy',
    ],
    policyTerms: ['must', 'shall', 'may', 'required to', 'prohibited from', 'permitted to'],
  },
  {
    language: 'es',
    terms: ['el', 'la', 'inquilino', 'arrendador', 'debe', 'puede', 'prohibido', 'politica'],
    policyTerms: ['debe', 'puede', 'prohibido'],
  },
  {
    language: 'fr',
    terms: ['le', 'la', 'locataire', 'bailleur', 'doit', 'peut', 'interdit', 'politique'],
    policyTerms: ['doit', 'peut', 'interdit'],
  },
  {
    language: 'de',
    terms: ['der', 'die', 'mieter', 'vermieter', 'muss', 'darf', 'verboten', 'richtlinie'],
    policyTerms: ['muss', 'darf', 'verboten'],
  },
];

export class DcecPatternMatcher {
  readonly namespace: DcecNamespace;
  readonly deonticPatterns: DeonticPattern[];
  readonly cognitivePatterns: CognitivePattern[];
  readonly temporalPatterns: TemporalPattern[];
  readonly connectivePatterns: ConnectivePattern[];

  constructor(namespace: DcecNamespace) {
    this.namespace = namespace;
    this.deonticPatterns = [
      [
        /(?:must not|should not|(?:is|are) forbidden to|(?:is|are) prohibited from|forbidden to|prohibited from) ([\w ]+)/,
        DcecDeonticOperator.PROHIBITION,
      ],
      [
        /(?:must|shall|should|ought to|(?:is|are) required to|(?:is|are) obligated to|required to|obligated to) ([\w ]+)/,
        DcecDeonticOperator.OBLIGATION,
      ],
      [
        /(?:may|can|(?:is|are) allowed to|(?:is|are) permitted to|allowed to|permitted to) ([\w ]+)/,
        DcecDeonticOperator.PERMISSION,
      ],
    ];
    this.cognitivePatterns = [
      [/(?:believes that|thinks that) (.+)/, DcecCognitiveOperator.BELIEF],
      [/(?:knows that) (.+)/, DcecCognitiveOperator.KNOWLEDGE],
      [/(?:intends to|plans to) ([\w ]+)/, DcecCognitiveOperator.INTENTION],
      [/(?:desires to|wants to) ([\w ]+)/, DcecCognitiveOperator.DESIRE],
      [/(?:has goal to|aims to) ([\w ]+)/, DcecCognitiveOperator.GOAL],
    ];
    this.temporalPatterns = [
      [/always (.+)/, DcecTemporalOperator.ALWAYS],
      [/eventually (.+)/, DcecTemporalOperator.EVENTUALLY],
      [/next (.+)/, DcecTemporalOperator.NEXT],
    ];
    this.connectivePatterns = [
      [/(.+) and (.+)/, DcecLogicalConnective.AND],
      [/(.+) or (.+)/, DcecLogicalConnective.OR],
      [/if (.+) then (.+)/, DcecLogicalConnective.IMPLIES],
      [/not (.+)/, DcecLogicalConnective.NOT],
    ];
  }

  convert(text: string): DcecFormula {
    const normalized = normalizeEnglish(text);
    const agentName = this.extractAgent(normalized);

    for (const [pattern, operator] of this.cognitivePatterns) {
      const match = normalized.match(pattern);
      if (!match) continue;
      const content = match[1];
      const agent = this.createAgentTerm(agentName);
      const inner = this.convertOrAtomic(content, agentName);
      return new DcecCognitiveFormula(operator, agent, inner);
    }

    for (const [pattern, operator] of this.temporalPatterns) {
      const match = normalized.match(pattern);
      if (!match) continue;
      return new DcecTemporalFormula(operator, this.convert(match[1]));
    }

    for (const [pattern, connective] of this.connectivePatterns) {
      if (connective === DcecLogicalConnective.NOT) continue;
      const match = normalized.match(pattern);
      if (!match) continue;
      return new DcecConnectiveFormula(connective, [
        this.convert(match[1]),
        this.convert(match[2]),
      ]);
    }

    if (normalized.startsWith('not ')) {
      return new DcecConnectiveFormula(DcecLogicalConnective.NOT, [
        this.convert(normalized.slice(4)),
      ]);
    }

    for (const [pattern, operator] of this.deonticPatterns) {
      const match = normalized.match(pattern);
      if (!match) continue;
      const action = match[1];
      const predicate = this.createSimplePredicate(action);
      const agent = this.createAgentTerm(agentName);
      return new DcecDeonticFormula(operator, new DcecAtomicFormula(predicate, [agent]));
    }

    const predicate = this.createSimplePredicate(normalized);
    return new DcecAtomicFormula(predicate, [this.createAgentTerm(agentName)]);
  }

  extractAgent(text: string): string | undefined {
    const match = text.match(/^(?:the )?(\w+)/);
    return match?.[1];
  }

  createSimplePredicate(action: string): DcecPredicateSymbol {
    const name = action.trim().replace(/\s+/g, '_');
    return this.namespace.getPredicate(name) ?? this.namespace.addPredicate(name, ['Agent']);
  }

  createAgentTerm(agentName?: string): DcecVariableTerm {
    const name = agentName?.trim() || 'agent';
    const variable = this.namespace.getVariable(name) ?? this.namespace.addVariable(name, 'Agent');
    return new DcecVariableTerm(variable);
  }

  private convertOrAtomic(content: string, agentName?: string): DcecFormula {
    try {
      return this.convert(content);
    } catch {
      const agent = this.createAgentTerm(agentName);
      return new DcecAtomicFormula(this.createSimplePredicate(content), [agent]);
    }
  }
}

export class DcecNaturalLanguageConverter {
  readonly namespace: DcecNamespace;
  readonly matcher: DcecPatternMatcher;
  readonly conversionHistory: DcecNlConversionResult[] = [];
  readonly proofCache = new DcecProofCache();
  private initialized = true;
  useGrammar = false;
  grammar: DcecGrammarAdapter | undefined = undefined;

  constructor(namespace = new DcecNamespace()) {
    this.namespace = namespace;
    this.matcher = new DcecPatternMatcher(this.namespace);
  }

  initialize(): boolean {
    this.initialized = true;
    return this.initialized;
  }

  get conversion_history(): DcecNlConversionResult[] {
    return this.conversionHistory;
  }

  convertToDcec(text: string): DcecNlConversionResult {
    try {
      const formula = this.matcher.convert(text);
      const result: DcecNlConversionResult = {
        english_text: text,
        dcec_formula: formula,
        success: true,
        confidence: 0.7,
        parse_method: 'pattern_matching',
      };
      this.conversionHistory.push(result);
      return result;
    } catch (error) {
      const result: DcecNlConversionResult = {
        english_text: text,
        success: false,
        error_message: error instanceof Error ? error.message : String(error),
        confidence: 0,
        parse_method: 'pattern_matching',
      };
      this.conversionHistory.push(result);
      return result;
    }
  }

  convert_to_dcec(text: string): DcecNlConversionResult {
    return this.convertToDcec(text);
  }

  compilePolicyText(text: string): DcecPolicyCompilationResult {
    return compileDcecPolicyText(text, this);
  }

  proveFormula(
    goal: DcecFormula,
    assumptions: DcecFormula[] = [],
    strategy: DcecProofStrategy = 'advanced_inference',
  ): DcecProofResult {
    return proveDcecFormula({ goal, assumptions, strategy, cache: this.proofCache });
  }

  convertFromDcec(formula: DcecFormula): string {
    if (formula instanceof DcecDeonticFormula) {
      const inner = this.convertFromDcec(formula.formula);
      if (formula.operator === DcecDeonticOperator.OBLIGATION) return `must ${inner}`;
      if (formula.operator === DcecDeonticOperator.PERMISSION) return `may ${inner}`;
      if (formula.operator === DcecDeonticOperator.PROHIBITION) return `must not ${inner}`;
      return `${formula.operator}(${inner})`;
    }
    if (formula instanceof DcecCognitiveFormula) {
      const inner = this.convertFromDcec(formula.formula);
      if (formula.operator === DcecCognitiveOperator.BELIEF)
        return `${formula.agent} believes that ${inner}`;
      if (formula.operator === DcecCognitiveOperator.KNOWLEDGE)
        return `${formula.agent} knows that ${inner}`;
      if (formula.operator === DcecCognitiveOperator.INTENTION)
        return `${formula.agent} intends to ${inner}`;
      return `${formula.operator}(${formula.agent}, ${inner})`;
    }
    if (formula instanceof DcecTemporalFormula) {
      const inner = this.convertFromDcec(formula.formula);
      if (formula.operator === DcecTemporalOperator.ALWAYS) return `always ${inner}`;
      if (formula.operator === DcecTemporalOperator.EVENTUALLY) return `eventually ${inner}`;
      if (formula.operator === DcecTemporalOperator.NEXT) return `next ${inner}`;
      return `${formula.operator}(${inner})`;
    }
    if (formula instanceof DcecConnectiveFormula) {
      if (formula.connective === DcecLogicalConnective.NOT)
        return `not ${this.convertFromDcec(formula.formulas[0])}`;
      if (formula.connective === DcecLogicalConnective.AND)
        return formula.formulas.map((part) => this.convertFromDcec(part)).join(' and ');
      if (formula.connective === DcecLogicalConnective.OR)
        return formula.formulas.map((part) => this.convertFromDcec(part)).join(' or ');
      if (formula.connective === DcecLogicalConnective.IMPLIES) {
        return `if ${this.convertFromDcec(formula.formulas[0])} then ${this.convertFromDcec(formula.formulas[1])}`;
      }
      return formula.toString();
    }
    if (formula instanceof DcecAtomicFormula) {
      return formula.predicate.name.replace(/_/g, ' ');
    }
    return formula.toString();
  }

  convert_from_dcec(formula: DcecFormula): string {
    return this.convertFromDcec(formula);
  }

  getConversionStatistics(): DcecConversionStatistics {
    if (this.conversionHistory.length === 0) return { total_conversions: 0 };
    const successful = this.conversionHistory.filter((result) => result.success).length;
    return {
      total_conversions: this.conversionHistory.length,
      successful,
      failed: this.conversionHistory.length - successful,
      success_rate: successful / this.conversionHistory.length,
      average_confidence:
        this.conversionHistory.reduce((sum, result) => sum + result.confidence, 0) /
        this.conversionHistory.length,
    };
  }

  get_conversion_statistics(): DcecConversionStatistics {
    return this.getConversionStatistics();
  }

  toString(): string {
    return `NaturalLanguageConverter(conversions=${this.conversionHistory.length})`;
  }
}

export function detectDcecPolicyLanguage(text: string): DcecPolicyLanguageDetection {
  const normalized = normalizePolicyText(text);
  const scores: DcecPolicyLanguageScores = { en: 0, es: 0, fr: 0, de: 0 };
  const matchedTerms: string[] = [];

  for (const profile of POLICY_LANGUAGE_PROFILES) {
    for (const term of profile.terms) {
      if (containsLanguageTerm(normalized, term)) {
        scores[profile.language] += 1;
        matchedTerms.push(`${profile.language}:${term}`);
      }
    }
    for (const term of profile.policyTerms) {
      if (containsLanguageTerm(normalized, term)) {
        scores[profile.language] += 1;
      }
    }
  }

  let language: DcecPolicyLanguage = 'unknown';
  let bestScore = 0;
  let totalScore = 0;
  for (const profile of POLICY_LANGUAGE_PROFILES) {
    const score = scores[profile.language];
    totalScore += score;
    if (score > bestScore) {
      bestScore = score;
      language = profile.language;
    }
  }

  return {
    language: bestScore === 0 ? 'unknown' : language,
    confidence: totalScore === 0 ? 0 : bestScore / totalScore,
    scores,
    matched_terms: matchedTerms,
    method: 'browser_native_keyword_profile',
    browser_native: true,
  };
}

export function compileDcecPolicyText(
  text: string,
  converter = new DcecNaturalLanguageConverter(),
): DcecPolicyCompilationResult {
  const normalizedPolicyText = normalizePolicyText(text);
  const languageDetection = detectDcecPolicyLanguage(text);
  const baseResult = {
    english_text: text,
    normalized_policy_text: normalizedPolicyText,
    language_detection: languageDetection,
    parse_method: 'browser_native_policy_compiler',
    browser_native: true as const,
  };

  if (!normalizedPolicyText) {
    return {
      ...baseResult,
      success: false,
      confidence: 0,
      error_message: 'Policy text is empty.',
      fail_closed_reason: 'empty_policy_text',
    };
  }

  if (languageDetection.language !== 'en') {
    return {
      ...baseResult,
      success: false,
      confidence: languageDetection.confidence,
      error_message: `Policy compiler only accepts English policy text; detected ${languageDetection.language}.`,
      fail_closed_reason: 'unsupported_policy_language',
    };
  }

  const conversion = converter.convertToDcec(normalizedPolicyText);
  return {
    ...baseResult,
    dcec_formula: conversion.dcec_formula,
    success: conversion.success,
    error_message: conversion.error_message,
    confidence: Math.min(1, (conversion.confidence + languageDetection.confidence) / 2),
    policy_formula_text: conversion.dcec_formula?.toString(),
    fail_closed_reason: conversion.success ? undefined : 'policy_parse_failed',
  };
}

export function proveDcecFormula(request: DcecProofRequest): DcecProofResult {
  const strategy = request.strategy ?? 'advanced_inference';
  const assumptions = request.assumptions ?? [];
  const key = proofCacheKey(request.goal, assumptions, strategy);
  const cached = request.cache?.get(key);
  if (cached) return cached;

  const result = runDcecProofStrategy(strategy, request.goal, assumptions);
  request.cache?.set(key, result);
  return result;
}

function runDcecProofStrategy(
  strategy: DcecProofStrategy,
  goal: DcecFormula,
  assumptions: DcecFormula[],
): DcecProofResult {
  if (strategy === 'direct') return directProof(goal, assumptions, strategy);
  if (strategy === 'deontic_consistency') return deonticConsistencyProof(goal, assumptions);
  if (strategy === 'temporal_lift') return temporalLiftProof(goal, assumptions);
  if (strategy === 'advanced_inference') return advancedInferenceProof(goal, assumptions);
  return proofResult(
    'invalid',
    strategy,
    goal,
    [`Unsupported DCEC proof strategy: ${strategy}`],
    false,
  );
}

function advancedInferenceProof(goal: DcecFormula, assumptions: DcecFormula[]): DcecProofResult {
  const direct = directProof(goal, assumptions, 'advanced_inference');
  if (direct.proved) return direct;

  const contradiction = findContradiction(assumptions);
  if (contradiction) {
    return proofResult('invalid', 'advanced_inference', goal, [contradiction], false);
  }

  const goalText = goal.toString();
  for (const assumption of assumptions) {
    if (
      assumption instanceof DcecConnectiveFormula &&
      assumption.connective === DcecLogicalConnective.IMPLIES
    ) {
      const [antecedent, consequent] = assumption.formulas;
      if (
        consequent.toString() === goalText &&
        assumptions.some((candidate) => candidate.toString() === antecedent.toString())
      ) {
        return proofResult(
          'proved',
          'advanced_inference',
          goal,
          [
            `Matched implication ${assumption.toString()}`,
            `Matched antecedent ${antecedent.toString()}`,
            'Applied modus ponens.',
          ],
          false,
        );
      }
    }
  }

  const temporal = temporalLiftProof(goal, assumptions, 'advanced_inference');
  if (temporal.proved) return temporal;

  return proofResult(
    'unknown',
    'advanced_inference',
    goal,
    ['No browser-native proof rule matched.'],
    false,
  );
}

function directProof(
  goal: DcecFormula,
  assumptions: DcecFormula[],
  strategy: DcecProofStrategy,
): DcecProofResult {
  const goalText = goal.toString();
  const matched = assumptions.some((assumption) => assumption.toString() === goalText);
  return proofResult(
    matched ? 'proved' : 'unknown',
    strategy,
    goal,
    matched ? [`Matched assumption ${goalText}.`] : ['Goal is not present in assumptions.'],
    false,
  );
}

function deonticConsistencyProof(goal: DcecFormula, assumptions: DcecFormula[]): DcecProofResult {
  const contradiction = findContradiction([...assumptions, goal]);
  if (contradiction)
    return proofResult('invalid', 'deontic_consistency', goal, [contradiction], false);
  return proofResult(
    'proved',
    'deontic_consistency',
    goal,
    ['No obligation/prohibition contradiction found.'],
    false,
  );
}

function temporalLiftProof(
  goal: DcecFormula,
  assumptions: DcecFormula[],
  strategy: DcecProofStrategy = 'temporal_lift',
): DcecProofResult {
  const goalText = goal.toString();
  const matched = assumptions.some(
    (assumption) =>
      assumption instanceof DcecTemporalFormula &&
      assumption.operator === DcecTemporalOperator.ALWAYS &&
      assumption.formula.toString() === goalText,
  );
  return proofResult(
    matched ? 'proved' : 'unknown',
    strategy,
    goal,
    matched
      ? [`Eliminated always premise for ${goalText}.`]
      : ['No always premise matched the goal.'],
    false,
  );
}

function findContradiction(formulas: DcecFormula[]): string | undefined {
  const obligations = new Set<string>();
  const prohibitions = new Set<string>();
  for (const formula of formulas) {
    if (!(formula instanceof DcecDeonticFormula)) continue;
    const inner = formula.formula.toString();
    if (formula.operator === DcecDeonticOperator.OBLIGATION) obligations.add(inner);
    if (formula.operator === DcecDeonticOperator.PROHIBITION) prohibitions.add(inner);
  }
  for (const obligation of obligations) {
    if (prohibitions.has(obligation))
      return `Contradictory obligation and prohibition for ${obligation}.`;
  }
  return undefined;
}

function proofResult(
  status: DcecProofStatus,
  strategy: DcecProofStrategy,
  goal: DcecFormula,
  proofSteps: string[],
  cacheHit: boolean,
): DcecProofResult {
  return {
    status,
    proved: status === 'proved',
    strategy,
    goal: goal.toString(),
    proof_steps: proofSteps,
    cache_hit: cacheHit,
    browser_native: true,
    error_message: status === 'invalid' ? proofSteps[0] : undefined,
  };
}

function proofCacheKey(
  goal: DcecFormula,
  assumptions: DcecFormula[],
  strategy: DcecProofStrategy,
): string {
  return JSON.stringify({
    strategy,
    goal: goal.toString(),
    assumptions: assumptions.map(String).sort(),
  });
}

export function createEnhancedDcecNlConverter(useGrammar = true): DcecNaturalLanguageConverter {
  const converter = new DcecNaturalLanguageConverter();
  if (useGrammar) {
    converter.grammar = createBrowserNativeDcecGrammar(converter);
    converter.useGrammar = true;
  } else {
    converter.grammar = undefined;
    converter.useGrammar = false;
  }
  return converter;
}

export function parseDcecWithGrammar(text: string): DcecFormula | undefined {
  return createBrowserNativeDcecGrammar().parse_to_dcec(text);
}

export function linearizeDcecWithGrammar(formula: DcecFormula): string | undefined {
  return createBrowserNativeDcecGrammar().formula_to_english(formula);
}

export function createBrowserNativeDcecGrammar(
  converter = new DcecNaturalLanguageConverter(),
): DcecGrammarAdapter {
  return {
    browser_native: true,
    parse_to_dcec(text: string): DcecFormula | undefined {
      const result = converter.convertToDcec(text);
      return result.success ? result.dcec_formula : undefined;
    },
    formula_to_english(formula: DcecFormula): string | undefined {
      return converter.convertFromDcec(formula);
    },
  };
}

function normalizeEnglish(text: string): string {
  return normalizePolicyText(text);
}

function normalizePolicyText(text: string): string {
  return text
    .trim()
    .toLowerCase()
    .replace(/[^\p{L}\p{N}\s]/gu, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function containsLanguageTerm(text: string, term: string): boolean {
  if (term.includes(' ')) return text.includes(term);
  return new RegExp(`\\b${escapeRegExp(term)}\\b`, 'u').test(text);
}

function escapeRegExp(text: string): string {
  return text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

export const NaturalLanguageConverter = DcecNaturalLanguageConverter;
export const PatternMatcher = DcecPatternMatcher;
export const create_enhanced_nl_converter = createEnhancedDcecNlConverter;
export const parse_with_grammar = parseDcecWithGrammar;
export const linearize_with_grammar = linearizeDcecWithGrammar;

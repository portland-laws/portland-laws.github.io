import type { CecExpression } from './ast';

export type CecFormulaString = string;
export type CecSymbolName = string;
export type CecSortName = string;
export type CecNamespaceDict = Record<string, unknown>;
export type CecSymbolTable = Record<CecSymbolName, unknown>;
export type CecProofStepId = number;
export type CecRuleName = string;
export type CecNativeProofCache = Record<string, unknown>;
export type CecNativeGrammarRule = string;
export type CecNativeLexicalEntry = string;
export type CecPatternString = string;
export type CecConfigValue = string | number | boolean | null | unknown[] | Record<string, unknown>;
export type CecConfigDict = Record<string, CecConfigValue>;

export interface CecFormulaDict {
  type?: string;
  operator?: string;
  arguments?: unknown[];
  variables?: string[];
  bound_variables?: string[];
  body?: unknown;
  metadata?: Record<string, unknown>;
}

export interface CecProofResultDict {
  is_valid?: boolean;
  proof_tree?: unknown;
  steps?: Array<Record<string, unknown>>;
  time_taken?: number;
  rules_used?: string[];
  cached?: boolean;
  error?: string;
}

export interface CecConversionResultDict {
  formula?: unknown;
  confidence?: number;
  patterns_matched?: string[];
  text?: string;
  language?: string;
  metadata?: Record<string, unknown>;
}

export interface CecNamespaceExport {
  sorts?: Record<string, unknown>;
  variables?: Record<string, unknown>;
  functions?: Record<string, unknown>;
  predicates?: Record<string, unknown>;
  constants?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
}

export interface CecNativeGrammarConfig {
  language?: string;
  lexicon_file?: string;
  rules_file?: string;
  enable_caching?: boolean;
  max_cache_size?: number;
  strict_mode?: boolean;
}

export interface CecProverConfig {
  max_depth?: number;
  timeout?: number;
  enable_caching?: boolean;
  strategy?: string;
  verbose?: boolean;
  parallel?: boolean;
}

export interface CecFormulaProtocol {
  toString(): string;
  freeVariables?(): Set<string>;
  getFreeVariables?(): Set<unknown>;
}

export interface CecTermProtocol {
  toString(): string;
}

export interface CecProverProtocol<TFormula = unknown, TResult = unknown> {
  prove(formula: TFormula, premises?: TFormula[]): TResult;
  isProvable?(formula: TFormula, premises?: TFormula[]): boolean;
}

export interface CecConverterProtocol<TResult = unknown> {
  convert(text: string, language?: string): TResult;
  addPattern?(pattern: string, template: string): void;
}

export interface CecKnowledgeBaseProtocol<TFormula = unknown> {
  add(formula: TFormula): string;
  query(pattern: unknown): TFormula[];
  remove(formulaId: string): boolean;
}

export type CecValidator<T = unknown> = (value: T) => boolean;
export type CecValidatorWithContext<T = unknown> = (value: T, context: Record<string, unknown>) => boolean;
export type CecTransformer<T> = (value: T) => T;
export type CecParser<TResult = unknown> = (source: string) => TResult;
export type CecFormatter<T = unknown> = (value: T) => string;
export type CecCacheKeyGenerator<T = unknown> = (value: T) => string;
export type CecErrorHandler<TResult = unknown> = (error: Error) => TResult;
export type CecErrorRecovery<TInput = unknown, TResult = unknown> = (error: Error, input: TInput) => TResult;

export type CecFormulaList<TFormula = CecFormulaProtocol> = TFormula[];
export type CecTermList<TTerm = CecTermProtocol> = TTerm[];
export type CecStringList = string[];
export type CecFormulaMap<TFormula = CecFormulaProtocol> = Record<string, TFormula>;
export type CecProofDict = Record<string, unknown>;
export type CecFormulaOrString<TFormula = CecFormulaProtocol> = TFormula | string;
export type CecTermOrString<TTerm = CecTermProtocol> = TTerm | string;
export type CecConfigValueType = string | number | boolean | null;
export type CecVariableBinding = [string, unknown];
export type CecProofStepTuple<TFormula = CecFormulaProtocol> = [CecProofStepId, CecRuleName, TFormula];
export type CecPatternMatch = [CecPatternString, number];

export interface CecResult<T = unknown> {
  success: boolean;
  value?: T;
  error?: string;
  metadata?: Record<string, unknown>;
}

export interface CecCacheEntry<T = unknown> {
  value: T;
  timestamp: number;
  hits: number;
  size: number;
}

export interface CecStatistics {
  total_operations?: number;
  successful?: number;
  failed?: number;
  average_time?: number;
  cache_hits?: number;
  cache_misses?: number;
}

export interface CecProofStatisticsDict {
  total_attempts: number;
  succeeded: number;
  failed: number;
  steps_taken: number;
  average_time: number;
  cache_hits: number;
  rules_applied: Record<string, number>;
  success_rate: number;
}

export class CecProofStatistics {
  attempts = 0;
  succeeded = 0;
  failed = 0;
  stepsTaken = 0;
  avgTime = 0;
  cacheHits = 0;
  readonly rulesApplied = new Map<string, number>();

  recordSuccess(steps: number, time: number): void {
    this.attempts += 1;
    this.succeeded += 1;
    this.stepsTaken += steps;
    this.updateAverageTime(time);
  }

  recordFailure(time: number): void {
    this.attempts += 1;
    this.failed += 1;
    this.updateAverageTime(time);
  }

  recordRule(ruleName: string): void {
    this.rulesApplied.set(ruleName, (this.rulesApplied.get(ruleName) ?? 0) + 1);
  }

  recordCacheHit(): void {
    this.cacheHits += 1;
  }

  getSuccessRate(): number {
    return this.attempts === 0 ? 0 : (this.succeeded / this.attempts) * 100;
  }

  getStatsDict(): CecProofStatisticsDict {
    return {
      total_attempts: this.attempts,
      succeeded: this.succeeded,
      failed: this.failed,
      steps_taken: this.stepsTaken,
      average_time: this.avgTime,
      cache_hits: this.cacheHits,
      rules_applied: Object.fromEntries(this.rulesApplied),
      success_rate: this.getSuccessRate(),
    };
  }

  reset(): void {
    this.attempts = 0;
    this.succeeded = 0;
    this.failed = 0;
    this.stepsTaken = 0;
    this.avgTime = 0;
    this.cacheHits = 0;
    this.rulesApplied.clear();
  }

  private updateAverageTime(time: number): void {
    this.avgTime = this.attempts === 1
      ? time
      : (this.avgTime * (this.attempts - 1) + time) / this.attempts;
  }
}

export function isCecFormulaProtocol(value: unknown): value is CecFormulaProtocol {
  return typeof value === 'object'
    && value !== null
    && typeof (value as { toString?: unknown }).toString === 'function';
}

export function isCecExpression(value: unknown): value is CecExpression {
  return typeof value === 'object'
    && value !== null
    && typeof (value as { kind?: unknown }).kind === 'string';
}

export function isCecProverProtocol(value: unknown): value is CecProverProtocol {
  return typeof value === 'object'
    && value !== null
    && typeof (value as { prove?: unknown }).prove === 'function';
}

export function isCecConverterProtocol(value: unknown): value is CecConverterProtocol {
  return typeof value === 'object'
    && value !== null
    && typeof (value as { convert?: unknown }).convert === 'function';
}

export function isCecKnowledgeBaseProtocol(value: unknown): value is CecKnowledgeBaseProtocol {
  return typeof value === 'object'
    && value !== null
    && typeof (value as { add?: unknown }).add === 'function'
    && typeof (value as { query?: unknown }).query === 'function'
    && typeof (value as { remove?: unknown }).remove === 'function';
}

export function createCecResult<T>(value: T, metadata: Record<string, unknown> = {}): CecResult<T> {
  return { success: true, value, metadata };
}

export function createCecErrorResult(error: string, metadata: Record<string, unknown> = {}): CecResult<never> {
  return { success: false, error, metadata };
}

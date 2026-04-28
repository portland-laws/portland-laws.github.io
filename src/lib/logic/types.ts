export type ConfidenceScore = number;
export type ComplexityScore = number;

export type LogicOperator = 'AND' | 'OR' | 'NOT' | 'IMPLIES' | 'IFF' | 'XOR';
export type Quantifier = 'FORALL' | 'EXISTS';
export type FormulaType =
  | 'first_order_logic'
  | 'modal_logic'
  | 'temporal_logic'
  | 'deontic_logic'
  | 'mixed_logic'
  | 'arithmetic'
  | 'quantified'
  | 'propositional';

export const LOGIC_OPERATOR_SYMBOLS: Record<LogicOperator, string> = {
  AND: '∧',
  OR: '∨',
  NOT: '¬',
  IMPLIES: '→',
  IFF: '↔',
  XOR: '⊕',
};

export const QUANTIFIER_SYMBOLS: Record<Quantifier, string> = {
  FORALL: '∀',
  EXISTS: '∃',
};

export interface ComplexityMetrics {
  quantifierDepth: number;
  nestingLevel: number;
  operatorCount: number;
  variableCount: number;
  predicateCount: number;
  complexityScore: ComplexityScore;
}

export interface PythonComplexityMetrics {
  quantifier_depth: number;
  nesting_level: number;
  operator_count: number;
  variable_count: number;
  predicate_count: number;
  complexity_score: ComplexityScore;
}

export const EMPTY_COMPLEXITY_METRICS: ComplexityMetrics = {
  quantifierDepth: 0,
  nestingLevel: 0,
  operatorCount: 0,
  variableCount: 0,
  predicateCount: 0,
  complexityScore: 0,
};

export function createComplexityMetrics(input: Partial<ComplexityMetrics> = {}): ComplexityMetrics {
  return {
    quantifierDepth: input.quantifierDepth ?? 0,
    nestingLevel: input.nestingLevel ?? 0,
    operatorCount: input.operatorCount ?? 0,
    variableCount: input.variableCount ?? 0,
    predicateCount: input.predicateCount ?? 0,
    complexityScore: input.complexityScore ?? 0,
  };
}

export function complexityMetricsToDict(metrics: ComplexityMetrics): PythonComplexityMetrics {
  return {
    quantifier_depth: metrics.quantifierDepth,
    nesting_level: metrics.nestingLevel,
    operator_count: metrics.operatorCount,
    variable_count: metrics.variableCount,
    predicate_count: metrics.predicateCount,
    complexity_score: Math.trunc(metrics.complexityScore),
  };
}

export interface FormulaLike {
  toString(): string;
  getComplexity?(): ComplexityMetrics;
}

export interface FormulaProtocol {
  toString(): string;
  getComplexity(): ComplexityMetrics;
}

export interface ProverProtocol {
  prove(formula: string, timeout?: number): ProofResult;
  getName(): string;
}

export interface ConverterProtocol {
  convert(formula: string, sourceFormat: string, targetFormat: string): string;
}

export type ProofStatus = 'proved' | 'disproved' | 'unknown' | 'timeout' | 'error';

export interface ProofStep {
  id: string;
  rule: string;
  premises: string[];
  conclusion: string;
  explanation?: string;
}

export interface ProofResult {
  status: ProofStatus;
  theorem: string;
  steps: ProofStep[];
  method?: string;
  timeMs?: number;
  error?: string;
}

export interface LogicValidationIssue {
  severity: 'error' | 'warning';
  field?: string;
  message: string;
}

export interface LogicValidationResult {
  valid: boolean;
  issues: LogicValidationIssue[];
}

export interface ParsePosition {
  offset: number;
  line: number;
  column: number;
}

export type BridgeCapability = 'bidirectional' | 'incremental' | 'rule_extraction' | 'optimization' | 'parallel';
export type BridgeConversionStatus = 'success' | 'partial' | 'failed' | 'unsupported';

export const BRIDGE_CAPABILITIES = {
  BIDIRECTIONAL_CONVERSION: 'bidirectional',
  INCREMENTAL_PROVING: 'incremental',
  RULE_EXTRACTION: 'rule_extraction',
  OPTIMIZATION: 'optimization',
  PARALLEL_PROVING: 'parallel',
} as const satisfies Record<string, BridgeCapability>;

export const BRIDGE_CONVERSION_STATUSES = {
  SUCCESS: 'success',
  PARTIAL: 'partial',
  FAILED: 'failed',
  UNSUPPORTED: 'unsupported',
} as const satisfies Record<string, BridgeConversionStatus>;

export class BridgeMetadata {
  constructor(
    readonly name: string,
    readonly version: string,
    readonly targetSystem: string,
    readonly capabilities: BridgeCapability[],
    readonly requiresExternalProver: boolean,
    readonly description: string,
  ) {}

  supportsCapability(capability: BridgeCapability): boolean {
    return this.capabilities.includes(capability);
  }

  toDict(): Record<string, unknown> {
    return {
      name: this.name,
      version: this.version,
      target_system: this.targetSystem,
      capabilities: [...this.capabilities],
      requires_external_prover: this.requiresExternalProver,
      description: this.description,
    };
  }
}

export class LogicBridgeConversionResult {
  constructor(
    readonly status: BridgeConversionStatus,
    readonly sourceFormula: string,
    readonly targetFormula: string,
    readonly sourceFormat: string,
    readonly targetFormat: string,
    readonly confidence = 1.0,
    readonly warnings: string[] = [],
    readonly metadata: Record<string, unknown> = {},
  ) {}

  isSuccessful(): boolean {
    return this.status === 'success';
  }

  hasWarnings(): boolean {
    return this.warnings.length > 0;
  }

  toDict(): Record<string, unknown> {
    return {
      status: this.status,
      source_formula: this.sourceFormula,
      target_formula: this.targetFormula,
      source_format: this.sourceFormat,
      target_format: this.targetFormat,
      confidence: this.confidence,
      warnings: [...this.warnings],
      metadata: { ...this.metadata },
    };
  }
}

export class BridgeConfig {
  constructor(
    readonly name: string,
    readonly targetSystem: string,
    readonly timeout = 30,
    readonly maxRetries = 3,
    readonly enableCaching = true,
    readonly cacheTtl = 3600,
    readonly customSettings: Record<string, unknown> = {},
  ) {}

  getSetting<T = unknown>(key: string, defaultValue?: T): T | undefined {
    return (key in this.customSettings ? this.customSettings[key] : defaultValue) as T | undefined;
  }

  toDict(): Record<string, unknown> {
    return {
      name: this.name,
      target_system: this.targetSystem,
      timeout: this.timeout,
      max_retries: this.maxRetries,
      enable_caching: this.enableCaching,
      cache_ttl: this.cacheTtl,
      custom_settings: { ...this.customSettings },
    };
  }
}

export class ProverRecommendation {
  constructor(
    readonly proverName: string,
    readonly confidence: number,
    readonly reasons: string[],
    readonly estimatedTime?: number,
  ) {}

  compare(other: ProverRecommendation): number {
    return other.confidence - this.confidence;
  }

  toDict(): Record<string, unknown> {
    return {
      prover_name: this.proverName,
      confidence: this.confidence,
      reasons: [...this.reasons],
      estimated_time: this.estimatedTime,
    };
  }
}

export type FolOutputFormatType = 'prolog' | 'tptp' | 'json' | 'defeasible' | 'smtlib' | 'natural_language';
export type PredicateCategoryType = 'entity' | 'action' | 'relation' | 'property' | 'temporal' | 'modal' | 'unknown';

export class PredicateType {
  constructor(
    readonly name: string,
    readonly arity: number,
    readonly category: PredicateCategoryType = 'unknown',
    readonly definition?: string,
  ) {}

  toString(): string {
    if (this.arity === 0) return this.name;
    return `${this.name}(${Array.from({ length: this.arity }, (_, index) => `x${index}`).join(', ')})`;
  }
}

export class FOLFormulaType {
  constructor(
    readonly formulaString: string,
    readonly predicates: PredicateType[] = [],
    readonly quantifiers: Quantifier[] = [],
    readonly operators: LogicOperator[] = [],
    readonly variables: string[] = [],
    readonly complexity: ComplexityMetrics | undefined = undefined,
    readonly confidence: ConfidenceScore = 1.0,
    readonly metadata: Record<string, unknown> = {},
  ) {}

  getPredicateNames(): string[] {
    return this.predicates.map((predicate) => predicate.name);
  }

  hasQuantifiers(): boolean {
    return this.quantifiers.length > 0;
  }
}

export class FOLConversionResultType {
  constructor(
    readonly sourceText: string,
    readonly folFormula: FOLFormulaType,
    readonly outputFormat: FolOutputFormatType,
    readonly formattedOutput: string,
    readonly confidence: ConfidenceScore,
    readonly warnings: string[] = [],
    readonly metadata: Record<string, unknown> = {},
  ) {}

  isHighConfidence(threshold = 0.7): boolean {
    return this.confidence >= threshold;
  }
}

export class PredicateExtractionType {
  constructor(
    readonly text: string,
    readonly predicatesByCategory: Partial<Record<PredicateCategoryType, PredicateType[]>>,
    readonly totalPredicates: number,
    readonly confidence: ConfidenceScore,
  ) {}

  getAllPredicates(): PredicateType[] {
    return Object.values(this.predicatesByCategory).flatMap((predicates) => predicates ?? []);
  }
}

export type LogicTranslationTarget =
  | 'lean'
  | 'coq'
  | 'isabelle'
  | 'smt-lib'
  | 'tptp'
  | 'z3'
  | 'vampire'
  | 'eprover'
  | 'agda'
  | 'hol'
  | 'pvs';

export class TranslationResultType {
  constructor(
    readonly target: LogicTranslationTarget,
    readonly translatedFormula: string,
    readonly success: boolean,
    readonly confidence = 1.0,
    readonly errors: string[] = [],
    readonly warnings: string[] = [],
    readonly metadata: Record<string, unknown> = {},
    readonly dependencies: string[] = [],
  ) {}

  toDict(): Record<string, unknown> {
    return {
      target: this.target,
      translated_formula: this.translatedFormula,
      success: this.success,
      confidence: this.confidence,
      errors: [...this.errors],
      warnings: [...this.warnings],
      metadata: { ...this.metadata },
      dependencies: [...this.dependencies],
    };
  }
}

export class AbstractLogicFormulaType {
  constructor(
    readonly formulaType: string,
    readonly operators: string[],
    readonly variables: Array<[string, string]>,
    readonly quantifiers: Array<[string, string, string]>,
    readonly propositions: string[],
    readonly logicalStructure: Record<string, unknown>,
    readonly sourceFormulaId?: string,
  ) {}

  toDict(): Record<string, unknown> {
    return {
      formula_type: this.formulaType,
      operators: [...this.operators],
      variables: this.variables.map((variable) => [...variable]),
      quantifiers: this.quantifiers.map((quantifier) => [...quantifier]),
      propositions: [...this.propositions],
      logical_structure: { ...this.logicalStructure },
      source_formula_id: this.sourceFormulaId,
    };
  }
}

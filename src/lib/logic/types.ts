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

export const EMPTY_COMPLEXITY_METRICS: ComplexityMetrics = {
  quantifierDepth: 0,
  nestingLevel: 0,
  operatorCount: 0,
  variableCount: 0,
  predicateCount: 0,
  complexityScore: 0,
};

export interface FormulaLike {
  toString(): string;
  getComplexity?(): ComplexityMetrics;
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


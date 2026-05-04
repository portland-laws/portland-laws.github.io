import type { ProofResult, ProofStatus, ProofStep } from '../types';
import type { TdfolFormula } from './ast';
import { formatTdfolFormula } from './formatter';
import {
  applyTdfolRules,
  formulaEquals,
  formulaKey,
  getAllTdfolRules,
  type TdfolInferenceRule,
} from './inferenceRules';
import { proveTdfolWithStrategySelection, type TdfolProverStrategy } from './strategies';

export const TDFOL_PROVER_METADATA = {
  sourcePythonModule: 'logic/TDFOL/tdfol_prover.py',
  browserNative: true,
  runtimeDependencies: [] as Array<string>,
  serverCallsAllowed: false,
  pythonRuntimeRequired: false,
  parity: [
    'direct_axiom_lookup',
    'bounded_forward_chaining',
    'derived_formula_budget',
    'strategy_selection',
    'direct_contradiction_disproof',
    'python_style_proof_report',
  ] as Array<string>,
} as const;

export interface TdfolProverOptions {
  maxSteps?: number;
  maxDerivedFormulas?: number;
  rules?: TdfolInferenceRule[];
  useStrategySelection?: boolean;
  strategies?: TdfolProverStrategy[];
  preferLowCostStrategy?: boolean;
  timeoutMs?: number;
}

export interface TdfolKnowledgeBase {
  axioms: TdfolFormula[];
  theorems?: TdfolFormula[];
}

export interface TdfolPythonProofReport {
  success: boolean;
  status: ProofStatus;
  theorem: string;
  assumptions: string[];
  method: string;
  steps: ProofStep[];
  stepCount: number;
  metadata: typeof TDFOL_PROVER_METADATA;
  error?: string;
}

export class TdfolProver {
  private readonly maxSteps: number;
  private readonly maxDerivedFormulas: number;
  private readonly rules: TdfolInferenceRule[];
  private readonly useStrategySelection: boolean;
  private readonly strategies?: TdfolProverStrategy[];
  private readonly preferLowCostStrategy: boolean;
  private readonly timeoutMs?: number;

  constructor(options: TdfolProverOptions = {}) {
    this.maxSteps = options.maxSteps ?? 50;
    this.maxDerivedFormulas = options.maxDerivedFormulas ?? 250;
    this.rules = options.rules ?? getAllTdfolRules();
    this.useStrategySelection = options.useStrategySelection ?? false;
    this.strategies = options.strategies;
    this.preferLowCostStrategy = options.preferLowCostStrategy ?? false;
    this.timeoutMs = options.timeoutMs;
  }

  prove(theorem: TdfolFormula, kb: TdfolKnowledgeBase): ProofResult {
    const contradiction = findDirectContradiction(theorem, kb);
    if (contradiction) {
      return {
        status: 'disproved',
        theorem: formatTdfolFormula(theorem),
        steps: [
          {
            id: 'tdfol-contradiction-1',
            rule: 'DirectContradiction',
            premises: [formatTdfolFormula(contradiction)],
            conclusion: formatTdfolFormula(theorem),
            explanation: 'Knowledge base contains the direct negation of the requested theorem',
          },
        ],
        method: 'tdfol-direct-contradiction',
        error: 'Theorem is contradicted by the local knowledge base',
      };
    }

    if (this.useStrategySelection) {
      return proveTdfolWithStrategySelection(theorem, kb, {
        strategies: this.strategies,
        preferLowCost: this.preferLowCostStrategy,
        timeoutMs: this.timeoutMs,
      });
    }

    const known = new Map<string, TdfolFormula>();
    const steps: ProofStep[] = [];
    for (const formula of [...kb.axioms, ...(kb.theorems ?? [])]) {
      known.set(formulaKey(formula), formula);
    }
    if (known.has(formulaKey(theorem))) {
      return {
        status: 'proved',
        theorem: formatTdfolFormula(theorem),
        steps: [],
        method: 'tdfol-forward-chaining',
      };
    }

    for (let iteration = 0; iteration < this.maxSteps; iteration += 1) {
      const formulas = [...known.values()];
      const applications = applyTdfolRules(formulas, this.rules);
      let progressed = false;

      for (const application of applications) {
        const key = formulaKey(application.conclusion);
        if (known.has(key)) {
          continue;
        }
        known.set(key, application.conclusion);
        const step: ProofStep = {
          id: `tdfol-step-${steps.length + 1}`,
          rule: application.rule,
          premises: application.premises.map(formatTdfolFormula),
          conclusion: formatTdfolFormula(application.conclusion),
        };
        steps.push(step);
        progressed = true;

        if (formulaEquals(application.conclusion, theorem)) {
          return {
            status: 'proved',
            theorem: formatTdfolFormula(theorem),
            steps,
            method: 'tdfol-forward-chaining',
          };
        }
        if (known.size >= this.maxDerivedFormulas) {
          return this.finish('timeout', theorem, steps, 'Derived formula budget exceeded');
        }
      }

      if (!progressed) {
        return this.finish('unknown', theorem, steps);
      }
    }

    return this.finish('timeout', theorem, steps, 'Step budget exceeded');
  }

  private finish(
    status: ProofStatus,
    theorem: TdfolFormula,
    steps: ProofStep[],
    error?: string,
  ): ProofResult {
    return {
      status,
      theorem: formatTdfolFormula(theorem),
      steps,
      method: 'tdfol-forward-chaining',
      error,
    };
  }
}

export function proveTdfol(
  theorem: TdfolFormula,
  kb: TdfolKnowledgeBase,
  options: TdfolProverOptions = {},
): ProofResult {
  return new TdfolProver(options).prove(theorem, kb);
}

export function proveTdfolPythonStyle(
  theorem: TdfolFormula,
  kb: TdfolKnowledgeBase,
  options: TdfolProverOptions = {},
): TdfolPythonProofReport {
  const result = proveTdfol(theorem, kb, options);
  return {
    success: result.status === 'proved',
    status: result.status,
    theorem: result.theorem,
    assumptions: [...kb.axioms, ...(kb.theorems ?? [])].map(formatTdfolFormula),
    method: result.method ?? 'tdfol-forward-chaining',
    steps: result.steps,
    stepCount: result.steps.length,
    metadata: TDFOL_PROVER_METADATA,
    error: result.error,
  };
}

function findDirectContradiction(
  theorem: TdfolFormula,
  kb: TdfolKnowledgeBase,
): TdfolFormula | undefined {
  return [...kb.axioms, ...(kb.theorems ?? [])].find((formula) =>
    areDirectNegations(formula, theorem),
  );
}

function areDirectNegations(left: TdfolFormula, right: TdfolFormula): boolean {
  if (left.kind === 'unary' && left.operator === 'NOT' && formulaEquals(left.formula, right)) {
    return true;
  }
  return right.kind === 'unary' && right.operator === 'NOT' && formulaEquals(right.formula, left);
}

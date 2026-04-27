import type { ProofResult, ProofStatus, ProofStep } from '../types';
import type { TdfolFormula } from './ast';
import { formatTdfolFormula } from './formatter';
import { applyTdfolRules, formulaEquals, formulaKey, getAllTdfolRules, type TdfolInferenceRule } from './inferenceRules';

export interface TdfolProverOptions {
  maxSteps?: number;
  maxDerivedFormulas?: number;
  rules?: TdfolInferenceRule[];
}

export interface TdfolKnowledgeBase {
  axioms: TdfolFormula[];
  theorems?: TdfolFormula[];
}

export class TdfolProver {
  private readonly maxSteps: number;
  private readonly maxDerivedFormulas: number;
  private readonly rules: TdfolInferenceRule[];

  constructor(options: TdfolProverOptions = {}) {
    this.maxSteps = options.maxSteps ?? 50;
    this.maxDerivedFormulas = options.maxDerivedFormulas ?? 250;
    this.rules = options.rules ?? getAllTdfolRules();
  }

  prove(theorem: TdfolFormula, kb: TdfolKnowledgeBase): ProofResult {
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

  private finish(status: ProofStatus, theorem: TdfolFormula, steps: ProofStep[], error?: string): ProofResult {
    return {
      status,
      theorem: formatTdfolFormula(theorem),
      steps,
      method: 'tdfol-forward-chaining',
      error,
    };
  }
}

export function proveTdfol(theorem: TdfolFormula, kb: TdfolKnowledgeBase, options: TdfolProverOptions = {}): ProofResult {
  return new TdfolProver(options).prove(theorem, kb);
}

import type { ProofResult, ProofStatus, ProofStep } from '../types';
import type { CecExpression } from './ast';
import { formatCecExpression } from './formatter';
import {
  applyCecRules,
  cecExpressionEquals,
  cecExpressionKey,
  getAllCecRules,
  type CecInferenceRule,
} from './inferenceRules';

export interface CecKnowledgeBase {
  axioms: CecExpression[];
  theorems?: CecExpression[];
}

export interface CecProverOptions {
  maxSteps?: number;
  maxDerivedExpressions?: number;
  rules?: CecInferenceRule[];
}

export class CecProver {
  private readonly maxSteps: number;
  private readonly maxDerivedExpressions: number;
  private readonly rules: CecInferenceRule[];

  constructor(options: CecProverOptions = {}) {
    this.maxSteps = options.maxSteps ?? 50;
    this.maxDerivedExpressions = options.maxDerivedExpressions ?? 250;
    this.rules = options.rules ?? getAllCecRules();
  }

  prove(theorem: CecExpression, kb: CecKnowledgeBase): ProofResult {
    const known = new Map<string, CecExpression>();
    const steps: ProofStep[] = [];
    for (const expression of [...kb.axioms, ...(kb.theorems ?? [])]) {
      known.set(cecExpressionKey(expression), expression);
    }

    if (known.has(cecExpressionKey(theorem))) {
      return {
        status: 'proved',
        theorem: formatCecExpression(theorem),
        steps,
        method: 'cec-forward-chaining',
      };
    }

    for (let iteration = 0; iteration < this.maxSteps; iteration += 1) {
      const applications = applyCecRules([...known.values()], this.rules);
      let progressed = false;

      for (const application of applications) {
        const key = cecExpressionKey(application.conclusion);
        if (known.has(key)) continue;

        known.set(key, application.conclusion);
        const step: ProofStep = {
          id: `cec-step-${steps.length + 1}`,
          rule: application.rule,
          premises: application.premises.map(formatCecExpression),
          conclusion: formatCecExpression(application.conclusion),
          explanation: `Applied ${application.rule}`,
        };
        steps.push(step);
        progressed = true;

        if (cecExpressionEquals(application.conclusion, theorem)) {
          return {
            status: 'proved',
            theorem: formatCecExpression(theorem),
            steps,
            method: 'cec-forward-chaining',
          };
        }
        if (known.size >= this.maxDerivedExpressions) {
          return this.finish('timeout', theorem, steps, 'Derived expression budget exceeded');
        }
      }

      if (!progressed) {
        return this.finish('unknown', theorem, steps);
      }
    }

    return this.finish('timeout', theorem, steps, 'Step budget exceeded');
  }

  private finish(status: ProofStatus, theorem: CecExpression, steps: ProofStep[], error?: string): ProofResult {
    return {
      status,
      theorem: formatCecExpression(theorem),
      steps,
      method: 'cec-forward-chaining',
      error,
    };
  }
}

export function proveCec(theorem: CecExpression, kb: CecKnowledgeBase, options: CecProverOptions = {}): ProofResult {
  return new CecProver(options).prove(theorem, kb);
}

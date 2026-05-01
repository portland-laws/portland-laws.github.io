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
import {
  getCecNativeRuleGroups,
  getCecNativeRulesByGroup,
  type CecNativeRuleGroupName,
} from './nativeRuleGroups';

export interface CecKnowledgeBase {
  axioms: CecExpression[];
  theorems?: CecExpression[];
}

export interface CecProofTraceStep extends ProofStep {
  ruleGroup?: CecNativeRuleGroupName;
  ruleDescription?: string;
  derivedExpressionCount: number;
}

export interface CecProofResult extends ProofResult {
  ruleGroups: CecNativeRuleGroupName[];
  trace: CecProofTraceStep[];
}

export interface CecProverOptions {
  maxSteps?: number;
  maxDerivedExpressions?: number;
  rules?: CecInferenceRule[];
  ruleGroups?: CecNativeRuleGroupName[];
}

export class CecProver {
  private readonly maxSteps: number;
  private readonly maxDerivedExpressions: number;
  private readonly rules: CecInferenceRule[];
  private readonly ruleGroups: CecNativeRuleGroupName[];
  private readonly ruleGroupByRuleName: Map<string, CecNativeRuleGroupName>;

  constructor(options: CecProverOptions = {}) {
    this.maxSteps = options.maxSteps ?? 50;
    this.maxDerivedExpressions = options.maxDerivedExpressions ?? 250;
    this.ruleGroups = options.ruleGroups ? [...options.ruleGroups] : [];
    this.rules = options.rules ?? resolveCecProverRules(this.ruleGroups);
    this.ruleGroupByRuleName = buildRuleGroupIndex(this.ruleGroups);
  }

  prove(theorem: CecExpression, kb: CecKnowledgeBase): CecProofResult {
    const known = new Map<string, CecExpression>();
    const steps: CecProofTraceStep[] = [];
    for (const expression of [...kb.axioms, ...(kb.theorems ?? [])]) {
      known.set(cecExpressionKey(expression), expression);
    }

    if (known.has(cecExpressionKey(theorem))) {
      return {
        status: 'proved',
        theorem: formatCecExpression(theorem),
        steps,
        method: 'cec-forward-chaining',
        ruleGroups: [...this.ruleGroups],
        trace: steps,
      };
    }

    for (let iteration = 0; iteration < this.maxSteps; iteration += 1) {
      const applications = applyCecRules([...known.values()], this.rules);
      let progressed = false;

      for (const application of applications) {
        const key = cecExpressionKey(application.conclusion);
        if (known.has(key)) continue;

        known.set(key, application.conclusion);
        const rule = this.rules.find((candidate) => candidate.name === application.rule);
        const step: CecProofTraceStep = {
          id: `cec-step-${steps.length + 1}`,
          rule: application.rule,
          ruleGroup: this.ruleGroupByRuleName.get(application.rule),
          ruleDescription: rule?.description,
          premises: application.premises.map(formatCecExpression),
          conclusion: formatCecExpression(application.conclusion),
          explanation: `Applied ${application.rule}`,
          derivedExpressionCount: known.size,
        };
        steps.push(step);
        progressed = true;

        if (cecExpressionEquals(application.conclusion, theorem)) {
          return {
            status: 'proved',
            theorem: formatCecExpression(theorem),
            steps,
            method: 'cec-forward-chaining',
            ruleGroups: [...this.ruleGroups],
            trace: steps,
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

  private finish(status: ProofStatus, theorem: CecExpression, steps: CecProofTraceStep[], error?: string): CecProofResult {
    return {
      status,
      theorem: formatCecExpression(theorem),
      steps,
      method: 'cec-forward-chaining',
      error,
      ruleGroups: [...this.ruleGroups],
      trace: steps,
    };
  }
}

export function proveCec(theorem: CecExpression, kb: CecKnowledgeBase, options: CecProverOptions = {}): CecProofResult {
  return new CecProver(options).prove(theorem, kb);
}

function resolveCecProverRules(ruleGroups: CecNativeRuleGroupName[]): CecInferenceRule[] {
  if (ruleGroups.length === 0) return getAllCecRules();
  const rules = ruleGroups.flatMap((group) => [...getCecNativeRulesByGroup(group)]);
  return dedupeRules(rules);
}

function buildRuleGroupIndex(selectedGroups: CecNativeRuleGroupName[]): Map<string, CecNativeRuleGroupName> {
  const names =
    selectedGroups.length > 0
      ? selectedGroups
      : getCecNativeRuleGroups().map((group) => group.name);
  const index = new Map<string, CecNativeRuleGroupName>();
  for (const groupName of names) {
    for (const rule of getCecNativeRulesByGroup(groupName)) {
      if (!index.has(rule.name)) {
        index.set(rule.name, groupName);
      }
    }
  }
  return index;
}

function dedupeRules(rules: CecInferenceRule[]): CecInferenceRule[] {
  const seen = new Set<string>();
  const unique: CecInferenceRule[] = [];
  for (const rule of rules) {
    if (seen.has(rule.name)) continue;
    seen.add(rule.name);
    unique.push(rule);
  }
  return unique;
}

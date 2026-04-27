import type { ProofResult, ProofStep } from '../types';

export type TdfolProofType = 'forward_chaining' | 'backward_chaining' | 'modal_tableaux' | 'zkp' | 'hybrid';
export type TdfolExplanationLevel = 'brief' | 'normal' | 'detailed' | 'verbose';

export interface TdfolExplainedStep {
  stepNumber: number;
  action: string;
  ruleName?: string;
  premises: string[];
  conclusion?: string;
  justification: string;
  naturalLanguage: string;
}

export interface TdfolProofExplanation {
  formula: string;
  isProved: boolean;
  proofType: TdfolProofType;
  steps: TdfolExplainedStep[];
  summary: string;
  inferenceChain: string[];
  statistics: Record<string, unknown>;
  text: string;
}

const RULE_DESCRIPTIONS: Record<string, string> = {
  ModusPonens: 'Given phi -> psi and phi, conclude psi.',
  ModusTollens: 'Given phi -> psi and not psi, conclude not phi.',
  HypotheticalSyllogism: 'Compose two implications into a longer implication.',
  ConjunctionIntroduction: 'Combine two formulas into a conjunction.',
  ConjunctionEliminationLeft: 'Take the left side of a conjunction.',
  ConjunctionEliminationRight: 'Take the right side of a conjunction.',
  DoubleNegationElimination: 'Remove a pair of negations.',
  TemporalKAxiom: 'Distribute always over implication.',
  TemporalTAxiom: 'Use always(phi) to conclude phi.',
  DeonticKAxiom: 'Distribute obligation over implication.',
  DeonticDAxiom: 'An obligation implies a permission.',
  ProhibitionEquivalence: 'A prohibition is an obligation not to perform the action.',
  ProhibitionFromObligation: 'An obligation not to do something is a prohibition.',
  ObligationWeakening: 'A conjunctive obligation implies an obligation for one conjunct.',
};

export class TdfolProofExplainer {
  constructor(private readonly level: TdfolExplanationLevel = 'normal') {}

  explainProof(result: ProofResult, proofType: TdfolProofType = 'forward_chaining'): TdfolProofExplanation {
    const steps = result.steps.map((step, index) => this.explainStep(step, index + 1));
    const explanation: Omit<TdfolProofExplanation, 'text'> = {
      formula: result.theorem,
      isProved: result.status === 'proved',
      proofType,
      steps,
      summary: this.generateSummary(result, steps, proofType),
      inferenceChain: steps.map((step) => step.naturalLanguage),
      statistics: this.computeStatistics(result, steps),
    };
    return { ...explanation, text: renderProofExplanation(explanation) };
  }

  explainRule(ruleName?: string): string {
    if (!ruleName) return 'Applied an inference rule.';
    if (RULE_DESCRIPTIONS[ruleName]) return RULE_DESCRIPTIONS[ruleName];
    if (ruleName.includes('Weakening')) return 'Derived a weaker conclusion from a stronger premise.';
    if (ruleName.includes('Distribution') || ruleName.includes('KAxiom')) return 'Distributed an operator across a logical implication.';
    if (ruleName.includes('Induction')) return 'Used an induction-style inference step.';
    return `Applied ${ruleName} inference rule.`;
  }

  private explainStep(step: ProofStep, stepNumber: number): TdfolExplainedStep {
    const justification = step.explanation || this.explainRule(step.rule);
    const action = `Forward chaining applied ${step.rule}`;
    const naturalLanguage =
      this.level === 'brief'
        ? `Step ${stepNumber}: derived ${step.conclusion}.`
        : `Step ${stepNumber}: applied ${step.rule} to derive ${step.conclusion}.`;
    return {
      stepNumber,
      action,
      ruleName: step.rule,
      premises: step.premises,
      conclusion: step.conclusion,
      justification,
      naturalLanguage,
    };
  }

  private generateSummary(result: ProofResult, steps: TdfolExplainedStep[], proofType: TdfolProofType): string {
    if (result.status === 'proved') {
      return `Proved ${result.theorem} using ${proofType} in ${steps.length} step${steps.length === 1 ? '' : 's'}.`;
    }
    if (result.status === 'timeout') {
      return `Could not prove ${result.theorem} before the proof budget was exhausted.`;
    }
    return `No proof for ${result.theorem} was found with the selected local rules.`;
  }

  private computeStatistics(result: ProofResult, steps: TdfolExplainedStep[]): Record<string, unknown> {
    return {
      status: result.status,
      step_count: steps.length,
      method: result.method ?? 'unknown',
      rules_used: [...new Set(steps.map((step) => step.ruleName).filter(Boolean))],
      proof_depth: steps.length,
    };
  }
}

export function explainTdfolProof(
  result: ProofResult,
  proofType: TdfolProofType = 'forward_chaining',
  level: TdfolExplanationLevel = 'normal',
): TdfolProofExplanation {
  return new TdfolProofExplainer(level).explainProof(result, proofType);
}

export function renderProofExplanation(explanation: Omit<TdfolProofExplanation, 'text'>): string {
  const lines = [
    `Proof of: ${explanation.formula}`,
    `Result: ${explanation.isProved ? 'PROVED' : 'NOT PROVED'}`,
    `Method: ${explanation.proofType}`,
    '',
    'Summary:',
    `  ${explanation.summary}`,
  ];
  if (explanation.steps.length > 0) {
    lines.push('', `Proof Steps (${explanation.steps.length}):`);
    for (const step of explanation.steps) {
      lines.push(`  ${step.naturalLanguage}`);
      if (step.justification) {
        lines.push(`    ${step.justification}`);
      }
    }
  }
  if (explanation.inferenceChain.length > 0) {
    lines.push('', 'Reasoning Chain:');
    explanation.inferenceChain.forEach((item, index) => lines.push(`  ${index + 1}. ${item}`));
  }
  return lines.join('\n');
}

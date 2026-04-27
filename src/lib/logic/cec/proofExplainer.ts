import type { ProofResult, ProofStep } from '../types';

export type CecProofType = 'forward_chaining' | 'cached_forward' | 'strategy_selection' | 'hybrid';
export type CecExplanationLevel = 'brief' | 'normal' | 'detailed';

export interface CecExplainedStep {
  stepNumber: number;
  ruleName?: string;
  premises: string[];
  conclusion?: string;
  justification: string;
  naturalLanguage: string;
}

export interface CecProofExplanation {
  expression: string;
  isProved: boolean;
  proofType: CecProofType;
  steps: CecExplainedStep[];
  summary: string;
  inferenceChain: string[];
  statistics: Record<string, unknown>;
  text: string;
}

const CEC_RULE_DESCRIPTIONS: Record<string, string> = {
  CecModusPonens: 'Given an implication and its antecedent, conclude the consequent.',
  CecConjunctionEliminationLeft: 'Take the left expression from a CEC conjunction.',
  CecConjunctionEliminationRight: 'Take the right expression from a CEC conjunction.',
  CecDoubleNegationElimination: 'Remove two nested CEC negations.',
  CecTemporalT: 'Use always(phi) to conclude phi in the local temporal fragment.',
  CecDeonticD: 'Use an obligation to infer the corresponding permission.',
  CecProhibitionEquivalence: 'A prohibition is represented as an obligation of negation.',
};

export class CecProofExplainer {
  constructor(private readonly level: CecExplanationLevel = 'normal') {}

  explainProof(result: ProofResult, proofType: CecProofType = 'forward_chaining'): CecProofExplanation {
    const steps = result.steps.map((step, index) => this.explainStep(step, index + 1));
    const explanation: Omit<CecProofExplanation, 'text'> = {
      expression: result.theorem,
      isProved: result.status === 'proved',
      proofType,
      steps,
      summary: this.generateSummary(result, steps, proofType),
      inferenceChain: steps.map((step) => step.naturalLanguage),
      statistics: this.computeStatistics(result, steps),
    };
    return { ...explanation, text: renderCecProofExplanation(explanation) };
  }

  explainRule(ruleName?: string): string {
    if (!ruleName) return 'Applied a CEC inference rule.';
    if (CEC_RULE_DESCRIPTIONS[ruleName]) return CEC_RULE_DESCRIPTIONS[ruleName];
    if (ruleName.includes('Temporal')) return 'Applied a temporal CEC inference rule.';
    if (ruleName.includes('Deontic')) return 'Applied a deontic CEC inference rule.';
    if (ruleName.includes('Modal')) return 'Applied a modal CEC inference rule.';
    return `Applied ${ruleName} CEC inference rule.`;
  }

  private explainStep(step: ProofStep, stepNumber: number): CecExplainedStep {
    const naturalLanguage = this.level === 'brief'
      ? `Step ${stepNumber}: derived ${step.conclusion}.`
      : `Step ${stepNumber}: applied ${step.rule} to derive ${step.conclusion}.`;
    return {
      stepNumber,
      ruleName: step.rule,
      premises: step.premises,
      conclusion: step.conclusion,
      justification: step.explanation || this.explainRule(step.rule),
      naturalLanguage,
    };
  }

  private generateSummary(result: ProofResult, steps: CecExplainedStep[], proofType: CecProofType): string {
    if (result.status === 'proved') {
      return `Proved ${result.theorem} using ${proofType} in ${steps.length} step${steps.length === 1 ? '' : 's'}.`;
    }
    if (result.status === 'timeout') {
      return `Could not prove ${result.theorem} before the CEC proof budget was exhausted.`;
    }
    return `No CEC proof for ${result.theorem} was found with the selected local rules.`;
  }

  private computeStatistics(result: ProofResult, steps: CecExplainedStep[]): Record<string, unknown> {
    return {
      status: result.status,
      method: result.method ?? 'unknown',
      step_count: steps.length,
      rules_used: [...new Set(steps.map((step) => step.ruleName).filter(Boolean))],
      proof_depth: steps.length,
    };
  }
}

export function explainCecProof(
  result: ProofResult,
  proofType: CecProofType = 'forward_chaining',
  level: CecExplanationLevel = 'normal',
): CecProofExplanation {
  return new CecProofExplainer(level).explainProof(result, proofType);
}

export function renderCecProofExplanation(explanation: Omit<CecProofExplanation, 'text'>): string {
  const lines = [
    `CEC proof of: ${explanation.expression}`,
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
      if (step.justification) lines.push(`    ${step.justification}`);
    }
  }
  if (explanation.inferenceChain.length > 0) {
    lines.push('', 'Reasoning Chain:');
    explanation.inferenceChain.forEach((item, index) => lines.push(`  ${index + 1}. ${item}`));
  }
  return lines.join('\n');
}

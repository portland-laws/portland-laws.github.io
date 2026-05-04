import type { ProofResult, ProofStep } from '../types';

export type TdfolProofType =
  | 'forward_chaining'
  | 'backward_chaining'
  | 'modal_tableaux'
  | 'zkp'
  | 'hybrid';
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

export type TdfolRawProofStep = {
  rule?: string;
  premises?: string[];
  conclusion?: string;
  action?: string;
  explanation?: string;
};
export type TdfolZkpExplanationOptions = {
  backend?: string;
  securityLevel?: number;
  proofSize?: string;
  verificationTime?: string;
};

const RULE_DESCRIPTIONS: Record<string, string> = {
  ModusPonens: 'Given p -> q and p, we conclude q.',
  ModusTollens: 'Given p -> q and not q, we conclude not p.',
  HypotheticalSyllogism: 'Given p -> q and q -> r, we conclude p -> r.',
  TemporalInduction: 'Given always(P -> next P) and P, prove always(P) by induction.',
  DeonticDetachment: 'Given obligation(P -> Q) and P, conclude obligation(Q).',
  ObligationWeakening: 'A conjunctive obligation implies an obligation for one conjunct.',
};

export class TdfolProofExplainer {
  constructor(private readonly level: TdfolExplanationLevel = 'normal') {}

  explainProof(
    result: ProofResult,
    proofType: TdfolProofType = 'forward_chaining',
  ): TdfolProofExplanation {
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

  explainProofSteps(
    formula: string,
    proofSteps: Array<TdfolRawProofStep | string>,
    proofType: TdfolProofType = 'forward_chaining',
    isProved = true,
  ): TdfolProofExplanation {
    const steps =
      proofSteps.length > 0
        ? proofSteps
        : proofType === 'zkp'
          ? ['Verified zero-knowledge proof']
          : [];
    const proofResult: ProofResult = {
      status: isProved ? 'proved' : 'unknown',
      theorem: formula,
      steps: steps.map((step, index) => this.normalizeProofStep(step, index + 1, proofType)),
      method: `tdfol-${proofType}`,
    };
    return this.explainProof(proofResult, proofType);
  }

  explainRule(ruleName?: string): string {
    if (!ruleName) return 'Applied an inference rule.';
    if (RULE_DESCRIPTIONS[ruleName]) return RULE_DESCRIPTIONS[ruleName];
    if (ruleName.includes('Weakening'))
      return 'Derived a weaker conclusion from a stronger premise.';
    if (ruleName.includes('Strengthening')) return 'Strengthened the conclusion.';
    if (ruleName.includes('Distribution') || ruleName.includes('KAxiom'))
      return 'Distributed an operator across a logical implication.';
    if (ruleName.includes('Induction')) return 'Used an induction-style inference step.';
    return `Applied ${ruleName} inference rule.`;
  }

  explainInferenceRule(ruleName: string, premises: string[], conclusion: string): string {
    const baseExplanation = this.explainRule(ruleName);
    if (this.level === 'brief') {
      return `${ruleName}: ${premises.join(', ')} |- ${conclusion}`;
    }
    if (this.level === 'detailed' || this.level === 'verbose') {
      return [
        `Inference Rule: ${ruleName}`,
        `Premises: ${premises.join(', ')}`,
        `Conclusion: ${conclusion}`,
        `Explanation: ${baseExplanation}`,
      ].join('\n');
    }
    return `${ruleName}: ${baseExplanation}`;
  }

  explainZkpProof(
    formula: string,
    _zkpResult: unknown = {},
    options: TdfolZkpExplanationOptions = {},
  ): TdfolProofExplanation {
    const backend = options.backend ?? 'simulated';
    const securityLevel = options.securityLevel ?? 128;
    const proofSize = options.proofSize ?? '~160 bytes';
    const verificationTime = options.verificationTime ?? '<10ms';
    const summary = `Proved ${formula} using zero-knowledge proof (${backend} backend, ${securityLevel}-bit security). Axioms remain private. Proof is succinct (${proofSize}).`;
    const inferenceChain = [
      'Private axioms loaded (hidden from verifier)',
      'Zero-knowledge proof generated',
      'Proof verified cryptographically',
      'Formula proven without revealing axioms',
    ];
    const explanation = this.explainProofSteps(
      formula,
      [
        {
          action: 'Generated zero-knowledge proof',
          explanation: 'Cryptographic proof generation with private axioms',
        },
        {
          action: 'Verified proof cryptographically',
          explanation: `Fast verification (${verificationTime}) using ${backend} backend`,
        },
      ],
      'zkp',
      true,
    );
    return {
      ...explanation,
      summary,
      inferenceChain,
      statistics: {
        backend,
        security_level: `${securityLevel}-bit`,
        proof_size: proofSize,
        verification_time: verificationTime,
        privacy: 'Axioms hidden',
      },
      text: renderProofExplanation({ ...explanation, summary, inferenceChain, statistics: {} }),
    };
  }

  explainSecurityProperties(backend: string, securityLevel: number): string {
    const warning =
      backend === 'simulated'
        ? '\nWARNING: Simulated backend is not cryptographically secure.'
        : '';
    const groth16 =
      backend === 'groth16'
        ? '\nGroth16: constant-size proofs, fast verification, trusted setup required.'
        : '';
    return `ZKP Security Properties (${backend} backend)\nSecurity Level: ${securityLevel}-bit\nProperties:\n  - Completeness: honest proofs for true statements verify\n  - Soundness: false statements fail closed for dishonest proofs\n  - Zero-Knowledge: verifier learns only the statement truth${warning}${groth16}`;
  }

  compareProofs(
    standardExplanation: TdfolProofExplanation,
    zkpExplanation: TdfolProofExplanation,
  ): string {
    return `Proof Comparison: Standard vs ZKP\n\nStandard Proof:\n  Method: ${standardExplanation.proofType}\n  Steps: ${standardExplanation.steps.length}\n  Rules used: ${String(standardExplanation.statistics.rules_used ?? 0)}\n\nZKP Proof:\n  Method: ${zkpExplanation.proofType}\n  Steps: Cryptographic verification\n  Privacy: Axioms hidden\n\nTrade-offs:\n  Standard: Transparent reasoning, shows all steps\n  ZKP: Private axioms, fast verification, succinct proof`;
  }

  private explainStep(step: ProofStep, stepNumber: number): TdfolExplainedStep {
    const justification = step.explanation || this.explainRule(step.rule);
    const action =
      step.rule === 'ZkpVerification'
        ? 'Verified zero-knowledge proof'
        : `Forward chaining applied ${step.rule}`;
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

  private generateSummary(
    result: ProofResult,
    steps: TdfolExplainedStep[],
    proofType: TdfolProofType,
  ): string {
    if (result.status === 'proved') {
      return `Proved ${result.theorem} using ${proofType} in ${steps.length} step${steps.length === 1 ? '' : 's'}.`;
    }
    if (result.status === 'timeout') {
      return `Could not prove ${result.theorem} before the proof budget was exhausted.`;
    }
    return `No proof for ${result.theorem} was found with the selected local rules.`;
  }

  private computeStatistics(
    result: ProofResult,
    steps: TdfolExplainedStep[],
  ): Record<string, unknown> {
    return {
      status: result.status,
      step_count: steps.length,
      method: result.method ?? 'unknown',
      rules_used: [...new Set(steps.map((step) => step.ruleName).filter(Boolean))],
      proof_depth: steps.length,
    };
  }

  private normalizeProofStep(
    step: TdfolRawProofStep | string,
    stepNumber: number,
    proofType: TdfolProofType,
  ): ProofStep {
    if (typeof step === 'string') {
      return {
        id: `tdfol-explained-step-${stepNumber}`,
        rule:
          proofType === 'modal_tableaux'
            ? 'TableauxExpansion'
            : proofType === 'zkp'
              ? 'ZkpVerification'
              : proofType === 'backward_chaining'
                ? 'BackwardChaining'
                : 'NarratedStep',
        premises: [],
        conclusion: step,
        explanation:
          proofType === 'modal_tableaux'
            ? 'Tableaux expansion'
            : proofType === 'zkp'
              ? 'Cryptographic verification of proof without revealing axioms'
              : proofType === 'backward_chaining'
                ? 'Goal-directed search'
                : '',
      };
    }
    return {
      id: `tdfol-explained-step-${stepNumber}`,
      rule: step.rule ?? (proofType === 'backward_chaining' ? 'BackwardChaining' : 'NarratedStep'),
      premises: step.premises ?? [],
      conclusion: step.conclusion ?? step.action ?? '',
      explanation:
        step.explanation ??
        (proofType === 'backward_chaining' ? 'Goal-directed search' : undefined),
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

export function explainTdfolProofSteps(
  formula: string,
  proofSteps: Array<TdfolRawProofStep | string>,
  proofType: TdfolProofType = 'forward_chaining',
  isProved = true,
  level: TdfolExplanationLevel = 'normal',
): TdfolProofExplanation {
  return new TdfolProofExplainer(level).explainProofSteps(formula, proofSteps, proofType, isProved);
}

export function explainTdfolZkpProof(
  formula: string,
  zkpResult: unknown = {},
  options: TdfolZkpExplanationOptions = {},
  level: TdfolExplanationLevel = 'normal',
): TdfolProofExplanation {
  return new TdfolProofExplainer(level).explainZkpProof(formula, zkpResult, options);
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

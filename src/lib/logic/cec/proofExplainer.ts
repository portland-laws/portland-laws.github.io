import type { ProofResult, ProofStep } from '../types';
import { buildCecDependencyGraph } from './dependencyGraph';

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

export interface CecProofDependencyPath {
  premise: string;
  path: string[];
}

export interface CecProofDependencyMetadata {
  nodes: number;
  edges: number;
  topologicalOrder: string[];
  leafPremises: string[];
  criticalPath: string[];
  premisePaths: CecProofDependencyPath[];
}

interface CecProofExplanationBase {
  expression: string;
  isProved: boolean;
  proofType: CecProofType;
  steps: CecExplainedStep[];
  summary: string;
  inferenceChain: string[];
  statistics: { [key: string]: unknown };
  dependencyGraph: CecProofDependencyMetadata;
}

export interface CecProofExplanation extends CecProofExplanationBase {
  text: string;
}

const CEC_RULE_DESCRIPTIONS: { [ruleName: string]: string } = {
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

  explainProof(
    result: ProofResult,
    proofType: CecProofType = 'forward_chaining',
  ): CecProofExplanation {
    const steps = result.steps.map((step: ProofStep, index: number) =>
      this.explainStep(step, index + 1),
    );
    const dependencyGraph = buildDependencyMetadata(result);
    const explanation: CecProofExplanationBase = {
      expression: result.theorem,
      isProved: result.status === 'proved',
      proofType,
      steps,
      summary: this.generateSummary(result, steps, proofType),
      inferenceChain: steps.map((step: CecExplainedStep) => step.naturalLanguage),
      statistics: this.computeStatistics(result, steps, dependencyGraph),
      dependencyGraph,
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
    const naturalLanguage =
      this.level === 'brief'
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

  private generateSummary(
    result: ProofResult,
    steps: CecExplainedStep[],
    proofType: CecProofType,
  ): string {
    if (result.status === 'proved') {
      return `Proved ${result.theorem} using ${proofType} in ${steps.length} step${steps.length === 1 ? '' : 's'}.`;
    }
    if (result.status === 'timeout') {
      return `Could not prove ${result.theorem} before the CEC proof budget was exhausted.`;
    }
    return `No CEC proof for ${result.theorem} was found with the selected local rules.`;
  }

  private computeStatistics(
    result: ProofResult,
    steps: CecExplainedStep[],
    dependencyGraph: CecProofDependencyMetadata,
  ): { [key: string]: unknown } {
    return {
      status: result.status,
      method: result.method ?? 'unknown',
      step_count: steps.length,
      rules_used: [
        ...new Set(steps.map((step: CecExplainedStep) => step.ruleName).filter(Boolean)),
      ],
      proof_depth:
        dependencyGraph.criticalPath.length > 0
          ? dependencyGraph.criticalPath.length - 1
          : steps.length,
      dependency_nodes: dependencyGraph.nodes,
      dependency_edges: dependencyGraph.edges,
      leaf_premise_count: dependencyGraph.leafPremises.length,
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

export function renderCecProofExplanation(explanation: CecProofExplanationBase): string {
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
    explanation.inferenceChain.forEach((item: string, index: number) =>
      lines.push(`  ${index + 1}. ${item}`),
    );
  }
  if (explanation.dependencyGraph.criticalPath.length > 0) {
    lines.push('', 'Dependency Graph:');
    lines.push(
      `  Nodes: ${explanation.dependencyGraph.nodes}; edges: ${explanation.dependencyGraph.edges}`,
    );
    lines.push(`  Critical path: ${explanation.dependencyGraph.criticalPath.join(' -> ')}`);
  }
  return lines.join('\n');
}

function buildDependencyMetadata(result: ProofResult): CecProofDependencyMetadata {
  const graph = buildCecDependencyGraph(result);
  const graphJson = graph.toJson();
  const topologicalOrder = safeTopologicalOrder(graph);
  const theorem = result.theorem;
  const leafPremises = graphJson.nodes
    .filter(
      (node) =>
        (node.type === 'premise' || node.type === 'axiom') &&
        !graphJson.edges.some((edge) => edge.target === node.id),
    )
    .map((node) => node.formula)
    .sort();
  const premisePaths = leafPremises
    .map((premise: string) => ({ premise, path: graph.findPath(premise, theorem) }))
    .filter((item: CecProofDependencyPath) => item.path.length > 0);
  const criticalPath = premisePaths.reduce(
    (longest: string[], item: CecProofDependencyPath) =>
      item.path.length > longest.length ? item.path : longest,
    [] as string[],
  );
  return {
    nodes: graphJson.nodes.length,
    edges: graphJson.edges.length,
    topologicalOrder,
    leafPremises,
    criticalPath,
    premisePaths,
  };
}

function safeTopologicalOrder(graph: { topologicalOrder(): string[] }): string[] {
  try {
    return graph.topologicalOrder();
  } catch {
    return [];
  }
}

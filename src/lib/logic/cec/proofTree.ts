import type { ProofResult, ProofStep } from '../types';
import { buildCecDependencyGraph } from './dependencyGraph';

export type CecProofNodeType = 'axiom' | 'premise' | 'inferred' | 'theorem' | 'goal' | 'contradiction' | 'lemma';
export type CecTreeStyle = 'compact' | 'expanded' | 'detailed';
export type CecVerbosityLevel = 'minimal' | 'normal' | 'detailed';

export interface CecProofTreeNode {
  id: string;
  formula: string;
  nodeType: CecProofNodeType;
  ruleName?: string;
  justification?: string;
  stepNumber: number;
  premises: CecProofTreeNode[];
  metadata: Record<string, unknown>;
}

export class CecProofTreeVisualizer {
  readonly root: CecProofTreeNode;
  readonly allNodes: CecProofTreeNode[];

  constructor(
    private readonly proofResult: ProofResult,
    private readonly verbosity: CecVerbosityLevel = 'normal',
  ) {
    const built = buildTree(proofResult);
    this.root = built.root;
    this.allNodes = built.nodes;
  }

  renderAscii(style: CecTreeStyle = 'compact'): string {
    const lines = [this.nodeLabel(this.root)];
    this.root.premises.forEach((child, index) => {
      renderNode(child, '', index === this.root.premises.length - 1, lines, (node) => this.nodeLabel(node), style);
    });
    return lines.join('\n');
  }

  renderJson(): Record<string, unknown> {
    return {
      theorem: this.proofResult.theorem,
      status: this.proofResult.status,
      method: this.proofResult.method,
      root: serializeNode(this.root),
      nodes: this.allNodes.map(serializeNode),
    };
  }

  renderDot(): string {
    return buildCecDependencyGraph(this.proofResult).toDot();
  }

  renderHtml(): string {
    const escaped = escapeHtml(this.renderAscii('detailed'));
    return `<section class="cec-proof-tree"><pre>${escaped}</pre></section>`;
  }

  private nodeLabel(node: CecProofTreeNode): string {
    if (this.verbosity === 'minimal') return node.formula;
    const rule = node.ruleName ? ` [${node.ruleName}]` : '';
    if (this.verbosity === 'detailed') {
      return `${node.stepNumber ? `${node.stepNumber}. ` : ''}${node.formula}${rule} (${node.nodeType})`;
    }
    return `${node.formula}${rule}`;
  }
}

export function visualizeCecProofTree(result: ProofResult, verbosity: CecVerbosityLevel = 'normal'): CecProofTreeVisualizer {
  return new CecProofTreeVisualizer(result, verbosity);
}

function buildTree(proofResult: ProofResult): { root: CecProofTreeNode; nodes: CecProofTreeNode[] } {
  const nodesByFormula = new Map<string, CecProofTreeNode>();
  const nodes: CecProofTreeNode[] = [];

  const getNode = (formula: string, type: CecProofNodeType, step?: ProofStep, stepNumber = 0): CecProofTreeNode => {
    const existing = nodesByFormula.get(formula);
    if (existing) {
      if (existing.nodeType === 'premise' && type !== 'premise') existing.nodeType = type;
      return existing;
    }
    const node: CecProofTreeNode = {
      id: `cec-node-${nodes.length + 1}`,
      formula,
      nodeType: type,
      ruleName: step?.rule,
      justification: step?.explanation,
      stepNumber,
      premises: [],
      metadata: step ? { step_id: step.id } : {},
    };
    nodesByFormula.set(formula, node);
    nodes.push(node);
    return node;
  };

  proofResult.steps.forEach((step, index) => {
    const conclusion = getNode(step.conclusion, 'inferred', step, index + 1);
    conclusion.ruleName = step.rule;
    conclusion.justification = step.explanation;
    conclusion.stepNumber = index + 1;
    conclusion.premises = step.premises.map((premise) => getNode(premise, 'premise'));
  });

  const root = getNode(proofResult.theorem, proofResult.status === 'proved' ? 'theorem' : 'goal');
  root.nodeType = proofResult.status === 'proved' ? 'theorem' : 'goal';
  const finalStep = proofResult.steps.find((step) => step.conclusion === proofResult.theorem);
  if (finalStep) {
    root.ruleName = finalStep.rule;
    root.justification = finalStep.explanation;
    root.stepNumber = proofResult.steps.indexOf(finalStep) + 1;
    root.premises = finalStep.premises.map((premise) => getNode(premise, 'premise'));
  }
  return { root, nodes };
}

function renderNode(
  node: CecProofTreeNode,
  prefix: string,
  isLast: boolean,
  lines: string[],
  label: (node: CecProofTreeNode) => string,
  style: CecTreeStyle,
): void {
  const connector = isLast ? '`- ' : '|- ';
  lines.push(`${prefix}${connector}${label(node)}`);
  const nextPrefix = `${prefix}${isLast ? '   ' : '|  '}${style === 'expanded' ? ' ' : ''}`;
  node.premises.forEach((child, index) => renderNode(child, nextPrefix, index === node.premises.length - 1, lines, label, style));
}

function serializeNode(node: CecProofTreeNode): Record<string, unknown> {
  return {
    ...node,
    premises: node.premises.map(serializeNode),
  };
}

function escapeHtml(value: string): string {
  return value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

import type { ProofResult, ProofStep } from '../types';
import { buildTdfolDependencyGraph } from './dependencyGraph';

export type TdfolProofNodeType = 'axiom' | 'premise' | 'inferred' | 'theorem' | 'goal' | 'contradiction' | 'lemma';
export type TdfolTreeStyle = 'compact' | 'expanded' | 'detailed';
export type TdfolVerbosityLevel = 'minimal' | 'normal' | 'detailed';

export interface TdfolProofTreeNode {
  id: string;
  formula: string;
  nodeType: TdfolProofNodeType;
  ruleName?: string;
  justification?: string;
  stepNumber: number;
  premises: TdfolProofTreeNode[];
  metadata: Record<string, unknown>;
}

export class TdfolProofTreeVisualizer {
  readonly root: TdfolProofTreeNode;
  readonly allNodes: TdfolProofTreeNode[];

  constructor(
    private readonly proofResult: ProofResult,
    private readonly verbosity: TdfolVerbosityLevel = 'normal',
  ) {
    const built = buildTree(proofResult);
    this.root = built.root;
    this.allNodes = built.nodes;
  }

  renderAscii(style: TdfolTreeStyle = 'compact'): string {
    const lines = [`${this.nodeLabel(this.root)}`];
    this.root.premises.forEach((child, index) => {
      renderNode(child, '', index === this.root.premises.length - 1, lines, (node) => this.nodeLabel(node), style);
    });
    return lines.join('\n');
  }

  renderJson(): Record<string, unknown> {
    return {
      theorem: this.proofResult.theorem,
      status: this.proofResult.status,
      root: serializeNode(this.root),
      nodes: this.allNodes.map(serializeNode),
    };
  }

  renderDot(): string {
    return buildTdfolDependencyGraph(this.proofResult).toDot();
  }

  renderHtml(): string {
    const escaped = escapeHtml(this.renderAscii('detailed'));
    return `<section class="tdfol-proof-tree"><pre>${escaped}</pre></section>`;
  }

  private nodeLabel(node: TdfolProofTreeNode): string {
    if (this.verbosity === 'minimal') return node.formula;
    const rule = node.ruleName ? ` [${node.ruleName}]` : '';
    if (this.verbosity === 'detailed') {
      return `${node.stepNumber ? `${node.stepNumber}. ` : ''}${node.formula}${rule} (${node.nodeType})`;
    }
    return `${node.formula}${rule}`;
  }
}

export function visualizeTdfolProofTree(result: ProofResult, verbosity: TdfolVerbosityLevel = 'normal'): TdfolProofTreeVisualizer {
  return new TdfolProofTreeVisualizer(result, verbosity);
}

function buildTree(proofResult: ProofResult): { root: TdfolProofTreeNode; nodes: TdfolProofTreeNode[] } {
  const nodesByFormula = new Map<string, TdfolProofTreeNode>();
  const nodes: TdfolProofTreeNode[] = [];

  const getNode = (formula: string, type: TdfolProofNodeType, step?: ProofStep, stepNumber = 0): TdfolProofTreeNode => {
    const existing = nodesByFormula.get(formula);
    if (existing) {
      if (existing.nodeType === 'premise' && type !== 'premise') existing.nodeType = type;
      return existing;
    }
    const node: TdfolProofTreeNode = {
      id: `node_${nodes.length + 1}`,
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
    conclusion.stepNumber = index + 1;
    conclusion.premises = step.premises.map((premise) => getNode(premise, 'premise'));
  });

  const root = getNode(proofResult.theorem, proofResult.status === 'proved' ? 'theorem' : 'goal');
  root.nodeType = proofResult.status === 'proved' ? 'theorem' : 'goal';
  if (proofResult.steps.length > 0) {
    const finalStep = proofResult.steps.find((step) => step.conclusion === proofResult.theorem);
    if (finalStep) {
      root.ruleName = finalStep.rule;
      root.stepNumber = proofResult.steps.indexOf(finalStep) + 1;
      root.premises = finalStep.premises.map((premise) => getNode(premise, 'premise'));
    }
  }
  return { root, nodes };
}

function renderNode(
  node: TdfolProofTreeNode,
  prefix: string,
  isLast: boolean,
  lines: string[],
  label: (node: TdfolProofTreeNode) => string,
  style: TdfolTreeStyle,
): void {
  const connector = isLast ? '└─ ' : '├─ ';
  lines.push(`${prefix}${connector}${label(node)}`);
  const nextPrefix = `${prefix}${isLast ? '   ' : '│  '}${style === 'expanded' ? ' ' : ''}`;
  node.premises.forEach((child, index) => renderNode(child, nextPrefix, index === node.premises.length - 1, lines, label, style));
}

function serializeNode(node: TdfolProofTreeNode): Record<string, unknown> {
  return {
    ...node,
    premises: node.premises.map(serializeNode),
  };
}

function escapeHtml(value: string): string {
  return value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

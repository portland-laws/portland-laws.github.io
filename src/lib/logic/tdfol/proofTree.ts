import type { ProofResult, ProofStep } from '../types';
import { buildTdfolDependencyGraph } from './dependencyGraph';

export type TdfolProofNodeType =
  | 'axiom'
  | 'premise'
  | 'inferred'
  | 'theorem'
  | 'goal'
  | 'contradiction'
  | 'lemma';
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

export type TdfolProofTreeLayoutNode = {
  id: string;
  formula: string;
  x: number;
  y: number;
  depth: number;
  nodeType: TdfolProofNodeType;
};
export type TdfolProofTreeEdge = { source: string; target: string; rule?: string };
export type TdfolProofTreeGraphJson = {
  theorem: string;
  status: ProofResult['status'];
  method?: string;
  nodes: TdfolProofTreeLayoutNode[];
  edges: TdfolProofTreeEdge[];
};

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
      renderNode(
        child,
        '',
        index === this.root.premises.length - 1,
        lines,
        (node) => this.nodeLabel(node),
        style,
      );
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

  renderGraphJson(): TdfolProofTreeGraphJson {
    const nodes = this.getLayout();
    const edges: TdfolProofTreeEdge[] = [];
    const visit = (node: TdfolProofTreeNode): void => {
      for (const premise of node.premises) {
        edges.push({ source: premise.id, target: node.id, rule: node.ruleName });
        visit(premise);
      }
    };
    visit(this.root);
    return {
      theorem: this.proofResult.theorem,
      status: this.proofResult.status,
      method: this.proofResult.method,
      nodes,
      edges,
    };
  }

  renderDot(): string {
    return buildTdfolDependencyGraph(this.proofResult).toDot();
  }

  renderHtml(): string {
    const escaped = escapeHtml(this.renderAscii('detailed'));
    return `<section class="tdfol-proof-tree"><pre>${escaped}</pre></section>`;
  }

  renderSvg(): string {
    const graph = this.renderGraphJson();
    const width = Math.max(320, ...graph.nodes.map((node) => node.x + 220));
    const height = Math.max(160, ...graph.nodes.map((node) => node.y + 70));
    const byId = new Map<string, TdfolProofTreeLayoutNode>(
      graph.nodes.map((node) => [node.id, node]),
    );
    const lines = graph.edges
      .map((edge) => {
        const source = byId.get(edge.source);
        const target = byId.get(edge.target);
        if (!source || !target) return '';
        return `<line x1="${source.x + 160}" y1="${source.y}" x2="${target.x}" y2="${target.y}" stroke="#667085" stroke-width="1.5" />`;
      })
      .filter((line) => line.length > 0)
      .join('');
    const nodes = graph.nodes
      .map((node) => {
        const label = escapeHtml(
          this.nodeLabel(this.allNodes.find((candidate) => candidate.id === node.id) ?? this.root),
        );
        return `<g data-node-id="${escapeHtml(node.id)}"><rect x="${node.x}" y="${node.y - 18}" width="160" height="36" rx="4" fill="#f2f4f7" stroke="#344054" /><text x="${node.x + 8}" y="${node.y + 5}" font-family="monospace" font-size="11" fill="#101828">${label}</text></g>`;
      })
      .join('');
    return `<svg class="tdfol-proof-tree-svg" xmlns="http://www.w3.org/2000/svg" role="img" viewBox="0 0 ${width} ${height}">${lines}${nodes}</svg>`;
  }

  getLayout(): TdfolProofTreeLayoutNode[] {
    const rows = new Map<string, number>();
    let nextRow = 0;
    const assign = (node: TdfolProofTreeNode, depth: number): void => {
      if (!rows.has(node.id)) {
        rows.set(node.id, nextRow);
        nextRow += 1;
      }
      node.premises.forEach((premise) => assign(premise, depth + 1));
    };
    assign(this.root, 0);
    return this.allNodes.map((node) => {
      const depth = findDepth(this.root, node.id) ?? 0;
      return {
        id: node.id,
        formula: node.formula,
        x: 24 + depth * 220,
        y: 36 + (rows.get(node.id) ?? 0) * 72,
        depth,
        nodeType: node.nodeType,
      };
    });
  }

  findPath(targetFormulaOrId: string): string[] {
    return findPath(this.root, targetFormulaOrId) ?? [];
  }

  getSubtree(targetFormulaOrId: string): TdfolProofTreeNode | null {
    return findNode(this.root, targetFormulaOrId);
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

export function visualizeTdfolProofTree(
  result: ProofResult,
  verbosity: TdfolVerbosityLevel = 'normal',
): TdfolProofTreeVisualizer {
  return new TdfolProofTreeVisualizer(result, verbosity);
}

function buildTree(proofResult: ProofResult): {
  root: TdfolProofTreeNode;
  nodes: TdfolProofTreeNode[];
} {
  const nodesByFormula = new Map<string, TdfolProofTreeNode>();
  const nodes: TdfolProofTreeNode[] = [];

  const getNode = (
    formula: string,
    type: TdfolProofNodeType,
    step?: ProofStep,
    stepNumber = 0,
  ): TdfolProofTreeNode => {
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
  node.premises.forEach((child, index) =>
    renderNode(child, nextPrefix, index === node.premises.length - 1, lines, label, style),
  );
}

function serializeNode(node: TdfolProofTreeNode): Record<string, unknown> {
  return {
    ...node,
    premises: node.premises.map(serializeNode),
  };
}

function findDepth(node: TdfolProofTreeNode, targetId: string, depth = 0): number | null {
  if (node.id === targetId) return depth;
  for (const premise of node.premises) {
    const found = findDepth(premise, targetId, depth + 1);
    if (found !== null) return found;
  }
  return null;
}

function findNode(node: TdfolProofTreeNode, targetFormulaOrId: string): TdfolProofTreeNode | null {
  if (node.id === targetFormulaOrId || node.formula === targetFormulaOrId) return node;
  for (const premise of node.premises) {
    const found = findNode(premise, targetFormulaOrId);
    if (found) return found;
  }
  return null;
}

function findPath(node: TdfolProofTreeNode, targetFormulaOrId: string): string[] | null {
  if (node.id === targetFormulaOrId || node.formula === targetFormulaOrId) return [node.formula];
  for (const premise of node.premises) {
    const found = findPath(premise, targetFormulaOrId);
    if (found) return [node.formula, ...found];
  }
  return null;
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

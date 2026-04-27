import type { ProofResult, ProofStep } from '../types';

export type CecFormulaNodeType = 'axiom' | 'theorem' | 'derived' | 'premise' | 'goal' | 'lemma';
export type CecDependencyType = 'direct' | 'transitive' | 'support';

export interface CecDependencyNode {
  id: string;
  formula: string;
  type: CecFormulaNodeType;
  name?: string;
  metadata: Record<string, unknown>;
}

export interface CecDependencyEdge {
  source: string;
  target: string;
  rule?: string;
  justification?: string;
  type: CecDependencyType;
  metadata: Record<string, unknown>;
}

export interface CecDependencyGraphJson {
  nodes: CecDependencyNode[];
  edges: CecDependencyEdge[];
}

export class CecCircularDependencyError extends Error {
  constructor(readonly cycle: string[]) {
    super(`Circular CEC dependency detected: ${cycle.join(' -> ')}`);
    this.name = 'CecCircularDependencyError';
  }
}

export class CecFormulaDependencyGraph {
  private readonly nodes = new Map<string, CecDependencyNode>();
  private readonly edges = new Map<string, CecDependencyEdge>();
  private readonly adjacency = new Map<string, Set<string>>();
  private readonly reverseAdjacency = new Map<string, Set<string>>();

  constructor(proofResult?: ProofResult) {
    if (proofResult) {
      this.addProof(proofResult);
    }
  }

  addFormula(formula: string, type: CecFormulaNodeType = 'derived', metadata: Record<string, unknown> = {}): CecDependencyNode {
    const id = nodeId(formula);
    const existing = this.nodes.get(id);
    if (existing) {
      if (existing.type === 'derived' && type !== 'derived') {
        existing.type = type;
      }
      existing.metadata = { ...existing.metadata, ...metadata };
      return existing;
    }
    const node: CecDependencyNode = { id, formula, type, metadata };
    this.nodes.set(id, node);
    this.adjacency.set(id, this.adjacency.get(id) ?? new Set());
    this.reverseAdjacency.set(id, this.reverseAdjacency.get(id) ?? new Set());
    return node;
  }

  addDependency(sourceFormula: string, targetFormula: string, rule?: string, type: CecDependencyType = 'direct'): void {
    const source = this.addFormula(sourceFormula, 'premise');
    const target = this.addFormula(targetFormula, 'derived');
    const edgeKey = `${source.id}->${target.id}:${rule ?? ''}:${type}`;
    this.edges.set(edgeKey, {
      source: source.id,
      target: target.id,
      rule,
      type,
      metadata: {},
    });
    this.adjacency.get(source.id)?.add(target.id);
    this.reverseAdjacency.get(target.id)?.add(source.id);
    this.assertAcyclic();
  }

  addProof(proofResult: ProofResult): void {
    this.addFormula(proofResult.theorem, proofResult.status === 'proved' ? 'theorem' : 'goal', {
      status: proofResult.status,
      method: proofResult.method,
      error: proofResult.error,
    });
    for (const step of proofResult.steps) {
      this.addStep(step);
    }
  }

  addStep(step: ProofStep): void {
    this.addFormula(step.conclusion, 'derived', { step_id: step.id, rule: step.rule });
    for (const premise of step.premises) {
      this.addDependency(premise, step.conclusion, step.rule);
    }
  }

  findPath(sourceFormula: string, targetFormula: string): string[] {
    const source = nodeId(sourceFormula);
    const target = nodeId(targetFormula);
    const queue: Array<{ id: string; path: string[] }> = [{ id: source, path: [source] }];
    const seen = new Set<string>();
    while (queue.length > 0) {
      const current = queue.shift()!;
      if (current.id === target) {
        return current.path.map((id) => this.nodes.get(id)?.formula ?? id);
      }
      if (seen.has(current.id)) continue;
      seen.add(current.id);
      for (const next of this.adjacency.get(current.id) ?? []) {
        queue.push({ id: next, path: [...current.path, next] });
      }
    }
    return [];
  }

  findUnusedAxioms(): string[] {
    return [...this.nodes.values()]
      .filter((node) => node.type === 'axiom' && (this.adjacency.get(node.id)?.size ?? 0) === 0)
      .map((node) => node.formula);
  }

  topologicalOrder(): string[] {
    const indegree = new Map([...this.nodes.keys()].map((id) => [id, this.reverseAdjacency.get(id)?.size ?? 0]));
    const queue = [...indegree.entries()].filter(([, degree]) => degree === 0).map(([id]) => id);
    const ordered: string[] = [];
    while (queue.length > 0) {
      const id = queue.shift()!;
      ordered.push(id);
      for (const next of this.adjacency.get(id) ?? []) {
        const degree = (indegree.get(next) ?? 0) - 1;
        indegree.set(next, degree);
        if (degree === 0) queue.push(next);
      }
    }
    if (ordered.length !== this.nodes.size) {
      throw new CecCircularDependencyError(ordered);
    }
    return ordered.map((id) => this.nodes.get(id)?.formula ?? id);
  }

  toJson(): CecDependencyGraphJson {
    return {
      nodes: [...this.nodes.values()],
      edges: [...this.edges.values()],
    };
  }

  toDot(): string {
    const lines = ['digraph CECProof {', '  rankdir=LR;'];
    for (const node of this.nodes.values()) {
      lines.push(`  "${node.id}" [label="${escapeDot(node.formula)}", shape=${nodeShape(node.type)}];`);
    }
    for (const edge of this.edges.values()) {
      const label = edge.rule ? ` [label="${escapeDot(edge.rule)}"]` : '';
      lines.push(`  "${edge.source}" -> "${edge.target}"${label};`);
    }
    lines.push('}');
    return lines.join('\n');
  }

  private assertAcyclic(): void {
    this.topologicalOrder();
  }
}

export function buildCecDependencyGraph(proofResult: ProofResult): CecFormulaDependencyGraph {
  return new CecFormulaDependencyGraph(proofResult);
}

function nodeId(formula: string): string {
  let hash = 2166136261;
  for (let index = 0; index < formula.length; index += 1) {
    hash ^= formula.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return `cec_${(hash >>> 0).toString(16)}`;
}

function escapeDot(value: string): string {
  return value.replace(/\\/g, '\\\\').replace(/"/g, '\\"');
}

function nodeShape(type: CecFormulaNodeType): string {
  if (type === 'theorem' || type === 'goal') return 'doublecircle';
  if (type === 'axiom' || type === 'premise') return 'box';
  return 'ellipse';
}

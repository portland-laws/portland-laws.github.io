import type { ProofResult, ProofStep } from '../types';

export type TdfolFormulaNodeType = 'axiom' | 'theorem' | 'derived' | 'premise' | 'goal' | 'lemma';
export type TdfolDependencyType = 'direct' | 'transitive' | 'support';

export interface TdfolDependencyNode {
  id: string;
  formula: string;
  type: TdfolFormulaNodeType;
  name?: string;
  metadata: Record<string, unknown>;
}

export interface TdfolDependencyEdge {
  source: string;
  target: string;
  rule?: string;
  justification?: string;
  type: TdfolDependencyType;
  metadata: Record<string, unknown>;
}

export interface TdfolDependencyGraphJson {
  nodes: TdfolDependencyNode[];
  edges: TdfolDependencyEdge[];
  statistics?: TdfolDependencyGraphStatistics;
}

export interface TdfolDependencyGraphStatistics {
  num_nodes: number;
  num_edges: number;
  node_types: Record<TdfolFormulaNodeType, number>;
  edge_types: Record<TdfolDependencyType, number>;
  has_cycles: boolean;
  num_axioms: number;
  num_theorems: number;
  num_derived: number;
}

export interface TdfolAdjacencyMatrix {
  formulas: string[];
  matrix: Array<Array<number>>;
}

export interface TdfolExampleFormulaDependencyGraph {
  proofResult: ProofResult;
  graph: TdfolFormulaDependencyGraph;
  json: TdfolDependencyGraphJson;
  dot: string;
  topologicalOrder: string[];
  accessDecisionPath: string[];
  unusedAxioms: string[];
}

export const TDFOL_EXAMPLE_FORMULA_DEPENDENCY_PROOF: ProofResult = {
  status: 'proved',
  theorem: 'Permitted(Alice, DatasetAlpha)',
  method: 'tdfol-example-formula-dependency-graph',
  steps: [
    {
      id: 's1',
      rule: 'UniversalInstantiation',
      premises: [
        '∀a:Agent (RequestsAccess(a, DatasetAlpha) → OBLIGATION(ReviewAccess(a, DatasetAlpha)))',
        'RequestsAccess(Alice, DatasetAlpha)',
      ],
      conclusion: 'OBLIGATION(ReviewAccess(Alice, DatasetAlpha))',
      explanation: 'Instantiate the access-review policy for Alice.',
    },
    {
      id: 's2',
      rule: 'DeonticDischarge',
      premises: ['OBLIGATION(ReviewAccess(Alice, DatasetAlpha))', 'Approved(Alice, DatasetAlpha)'],
      conclusion: 'Permitted(Alice, DatasetAlpha)',
      explanation: 'A completed approval discharges the review obligation into permission.',
    },
  ],
};

export class TdfolCircularDependencyError extends Error {
  constructor(readonly cycle: string[]) {
    super(`Circular dependency detected: ${cycle.join(' -> ')}`);
    this.name = 'TdfolCircularDependencyError';
  }
}

export class TdfolFormulaDependencyGraph {
  private readonly nodes = new Map<string, TdfolDependencyNode>();
  private readonly edges = new Map<string, TdfolDependencyEdge>();
  private readonly adjacency = new Map<string, Set<string>>();
  private readonly reverseAdjacency = new Map<string, Set<string>>();

  constructor(proofResult?: ProofResult) {
    if (proofResult) {
      this.addProof(proofResult);
    }
  }

  addFormula(
    formula: string,
    type: TdfolFormulaNodeType = 'derived',
    metadata: Record<string, unknown> = {},
  ): TdfolDependencyNode {
    const id = nodeId(formula);
    const existing = this.nodes.get(id);
    if (existing) {
      if (existing.type === 'premise' && type !== 'premise') {
        existing.type = type;
      } else if (existing.type === 'derived' && type !== 'derived' && type !== 'premise') {
        existing.type = type;
      }
      existing.metadata = { ...existing.metadata, ...metadata };
      return existing;
    }
    const node: TdfolDependencyNode = { id, formula, type, metadata };
    this.nodes.set(id, node);
    this.adjacency.set(id, this.adjacency.get(id) ?? new Set());
    this.reverseAdjacency.set(id, this.reverseAdjacency.get(id) ?? new Set());
    return node;
  }

  addDependency(
    sourceFormula: string,
    targetFormula: string,
    rule?: string,
    type: TdfolDependencyType = 'direct',
    justification = '',
    metadata: Record<string, unknown> = {},
  ): void {
    const source = this.addFormula(sourceFormula, 'premise');
    const target = this.addFormula(targetFormula, 'derived');
    const edgeKey = `${source.id}->${target.id}:${rule ?? ''}:${type}`;
    this.edges.set(edgeKey, {
      source: source.id,
      target: target.id,
      rule,
      justification,
      type,
      metadata,
    });
    this.adjacency.get(source.id)?.add(target.id);
    this.reverseAdjacency.get(target.id)?.add(source.id);
    this.assertAcyclic();
  }

  addProof(proofResult: ProofResult): void {
    this.addFormula(proofResult.theorem, proofResult.status === 'proved' ? 'theorem' : 'goal', {
      status: proofResult.status,
      method: proofResult.method,
    });
    for (const step of proofResult.steps) {
      this.addStep(step);
    }
  }

  addStep(step: ProofStep): void {
    this.addFormula(step.conclusion, 'derived', { step_id: step.id, rule: step.rule });
    for (const premise of step.premises) {
      this.addDependency(premise, step.conclusion, step.rule, 'direct', step.explanation ?? '');
    }
  }

  addFormulaWithDependencies(
    formula: string,
    dependsOn: string[],
    rule: string,
    justification = '',
    nodeType: TdfolFormulaNodeType = 'derived',
    metadata: Record<string, unknown> = {},
  ): void {
    this.addFormula(formula, nodeType, metadata);
    for (const premise of dependsOn) {
      this.addDependency(premise, formula, rule, 'direct', justification);
    }
  }

  getDependencies(formula: string): string[] {
    return this.sortedFormulas(this.reverseAdjacency.get(nodeId(formula)) ?? new Set());
  }

  getDependents(formula: string): string[] {
    return this.sortedFormulas(this.adjacency.get(nodeId(formula)) ?? new Set());
  }

  getAllDependencies(formula: string): string[] {
    return this.walkFormulaClosure(formula, (current) => this.getDependencies(current));
  }

  getAllDependents(formula: string): string[] {
    return this.walkFormulaClosure(formula, (current) => this.getDependents(current));
  }

  detectCycles(): string[][] {
    const cycles: string[][] = [],
      path: string[] = [];
    const visited = new Set<string>(),
      active = new Set<string>();
    const visit = (id: string): void => {
      visited.add(id);
      active.add(id);
      path.push(id);
      for (const next of this.adjacency.get(id) ?? []) {
        if (!visited.has(next)) visit(next);
        else if (active.has(next)) {
          const cycleStart = path.indexOf(next);
          cycles.push(
            [...path.slice(cycleStart), next].map((cycleId) => this.nodeFormula(cycleId)),
          );
        }
      }
      path.pop();
      active.delete(id);
    };
    for (const id of this.nodes.keys()) {
      if (!visited.has(id)) visit(id);
    }
    return cycles;
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

  findCriticalPath(sourceFormula: string, targetFormula: string): string[] | null {
    const path = this.findPath(sourceFormula, targetFormula);
    return path.length > 0 ? path : null;
  }

  findUnusedAxioms(): string[] {
    return [...this.nodes.values()]
      .filter((node) => node.type === 'axiom' && (this.adjacency.get(node.id)?.size ?? 0) === 0)
      .map((node) => node.formula);
  }

  topologicalOrder(): string[] {
    const cycles = this.detectCycles();
    if (cycles.length > 0) {
      throw new TdfolCircularDependencyError(cycles[0]);
    }
    const indegree = new Map(
      [...this.nodes.keys()].map((id) => [id, this.reverseAdjacency.get(id)?.size ?? 0]),
    );
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
      throw new TdfolCircularDependencyError(ordered);
    }
    return ordered.map((id) => this.nodes.get(id)?.formula ?? id);
  }

  topologicalSort(): string[] {
    return this.topologicalOrder();
  }

  getStatistics(): TdfolDependencyGraphStatistics {
    const emptyNodeTypes: Record<TdfolFormulaNodeType, number> = {
      axiom: 0,
      theorem: 0,
      derived: 0,
      premise: 0,
      goal: 0,
      lemma: 0,
    };
    const emptyEdgeTypes: Record<TdfolDependencyType, number> = {
      direct: 0,
      transitive: 0,
      support: 0,
    };
    for (const node of this.nodes.values()) emptyNodeTypes[node.type] += 1;
    for (const edge of this.edges.values()) emptyEdgeTypes[edge.type] += 1;
    return {
      num_nodes: this.nodes.size,
      num_edges: this.edges.size,
      node_types: emptyNodeTypes,
      edge_types: emptyEdgeTypes,
      has_cycles: this.detectCycles().length > 0,
      num_axioms: emptyNodeTypes.axiom,
      num_theorems: emptyNodeTypes.theorem,
      num_derived: emptyNodeTypes.derived,
    };
  }

  toJson(): TdfolDependencyGraphJson {
    return {
      nodes: [...this.nodes.values()],
      edges: [...this.edges.values()],
      statistics: this.getStatistics(),
    };
  }

  toAdjacencyMatrix(): TdfolAdjacencyMatrix {
    const formulas = [...this.nodes.values()].map((node) => node.formula);
    const indexById = new Map([...this.nodes.keys()].map((id, index) => [id, index]));
    const matrix = formulas.map(() => formulas.map(() => 0));
    for (const edge of this.edges.values()) {
      const source = indexById.get(edge.source);
      const target = indexById.get(edge.target);
      if (source !== undefined && target !== undefined) matrix[source][target] = 1;
    }
    return { formulas, matrix };
  }

  toDot(): string {
    const lines = ['digraph TDFOLProof {', '  rankdir=LR;'];
    for (const node of this.nodes.values()) {
      lines.push(
        `  "${node.id}" [label="${escapeDot(node.formula)}", shape=${nodeShape(node.type)}];`,
      );
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

  private sortedFormulas(ids: Set<string>): string[] {
    return [...ids].map((id) => this.nodeFormula(id)).sort();
  }

  private nodeFormula(id: string): string {
    return this.nodes.get(id)?.formula ?? id;
  }

  private walkFormulaClosure(
    formula: string,
    nextFormulas: (current: string) => string[],
  ): string[] {
    const seen = new Set<string>();
    const queue = [formula];
    while (queue.length > 0) {
      const current = queue.shift()!;
      if (seen.has(current)) continue;
      seen.add(current);
      for (const next of nextFormulas(current)) {
        if (!seen.has(next)) queue.push(next);
      }
    }
    seen.delete(formula);
    return [...seen].sort();
  }
}

export function buildTdfolDependencyGraph(proofResult: ProofResult): TdfolFormulaDependencyGraph {
  return new TdfolFormulaDependencyGraph(proofResult);
}

export function analyzeTdfolProofDependencies(
  proofResult: ProofResult,
): TdfolFormulaDependencyGraph {
  return new TdfolFormulaDependencyGraph(proofResult);
}

export function findTdfolProofChain(
  startFormula: string,
  endFormula: string,
  proofResults: ProofResult[],
): string[] | null {
  const graph = new TdfolFormulaDependencyGraph();
  for (const proofResult of proofResults) graph.addProof(proofResult);
  return graph.findCriticalPath(startFormula, endFormula);
}

export function buildExampleTdfolFormulaDependencyGraph(): TdfolExampleFormulaDependencyGraph {
  const graph = buildTdfolDependencyGraph(TDFOL_EXAMPLE_FORMULA_DEPENDENCY_PROOF);
  graph.addFormula('RetentionOnly(ArchiveNotice)', 'axiom', {
    example: 'unused_axiom',
    reason: 'Included to mirror the Python example diagnostic path for unused axioms.',
  });

  return {
    proofResult: TDFOL_EXAMPLE_FORMULA_DEPENDENCY_PROOF,
    graph,
    json: graph.toJson(),
    dot: graph.toDot(),
    topologicalOrder: graph.topologicalOrder(),
    accessDecisionPath: graph.findPath(
      'RequestsAccess(Alice, DatasetAlpha)',
      'Permitted(Alice, DatasetAlpha)',
    ),
    unusedAxioms: graph.findUnusedAxioms(),
  };
}

function nodeId(formula: string): string {
  let hash = 2166136261;
  for (let index = 0; index < formula.length; index += 1) {
    hash ^= formula.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return `f_${(hash >>> 0).toString(16)}`;
}

function escapeDot(value: string): string {
  return value.replace(/\\/g, '\\\\').replace(/"/g, '\\"');
}

function nodeShape(type: TdfolFormulaNodeType): string {
  if (type === 'theorem' || type === 'goal') return 'doublecircle';
  if (type === 'axiom' || type === 'premise') return 'box';
  return 'ellipse';
}

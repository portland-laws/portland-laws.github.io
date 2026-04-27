import type { CecExpression } from './ast';
import { formatCecExpression } from './formatter';
import { measureCecDepth } from './analyzer';

export type CecDisambiguationStrategy =
  | 'minimal_attachment'
  | 'right_association'
  | 'recency_preference'
  | 'semantic_coherence'
  | 'statistical';

export interface CecSyntaxNodeLike {
  value: unknown;
  children?: CecSyntaxNodeLike[];
}

export interface CecParseLike {
  root: CecSyntaxNodeLike;
  label?: string;
  metadata?: Record<string, unknown>;
}

export interface CecParseScore<TParse = CecParseLike> {
  tree: TParse;
  totalScore: number;
  componentScores: Record<string, number>;
}

export type CecPreferenceRule<TParse = CecParseLike> = (tree: TParse) => number;

export class CecSyntaxNode implements CecSyntaxNodeLike {
  readonly value: unknown;
  readonly children: CecSyntaxNode[];

  constructor(value: unknown, children: CecSyntaxNodeLike[] = []) {
    this.value = value;
    this.children = children.map((child) => toSyntaxNode(child));
  }

  isLeaf(): boolean {
    return this.children.length === 0;
  }

  size(): number {
    return 1 + this.children.reduce((total, child) => total + child.size(), 0);
  }

  height(): number {
    if (this.children.length === 0) return 1;
    return 1 + Math.max(...this.children.map((child) => child.height()));
  }

  preorder(): CecSyntaxNode[] {
    return [this, ...this.children.flatMap((child) => child.preorder())];
  }

  leaves(): CecSyntaxNode[] {
    if (this.children.length === 0) return [this];
    return this.children.flatMap((child) => child.leaves());
  }
}

export class CecSyntaxTree implements CecParseLike {
  readonly root: CecSyntaxNode;
  readonly label?: string;
  readonly metadata: Record<string, unknown>;

  constructor(root: CecSyntaxNodeLike, options: { label?: string; metadata?: Record<string, unknown> } = {}) {
    this.root = toSyntaxNode(root);
    this.label = options.label;
    this.metadata = options.metadata ?? {};
  }

  size(): number {
    return this.root.size();
  }

  height(): number {
    return this.root.height();
  }

  preorder(): CecSyntaxNode[] {
    return this.root.preorder();
  }

  leaves(): CecSyntaxNode[] {
    return this.root.leaves();
  }
}

export class CecAmbiguityResolver<TParse extends CecParseLike = CecParseLike> {
  readonly strategies = new Map<CecDisambiguationStrategy, number>([
    ['minimal_attachment', 1],
    ['right_association', 0.8],
    ['semantic_coherence', 1.2],
  ]);
  readonly preferenceRules: Array<{ name: string; rule: CecPreferenceRule<TParse> }> = [];

  constructor() {
    this.addPreferenceRule('minimal_attachment_score', (tree) => this.minimalAttachmentScore(tree));
    this.addPreferenceRule('right_association_score', (tree) => this.rightAssociationScore(tree));
    this.addPreferenceRule('tree_balance_score', (tree) => this.treeBalanceScore(tree));
  }

  resolve(parses: TParse[]): Array<CecParseScore<TParse>> {
    if (parses.length === 0) return [];
    if (parses.length === 1) {
      return [{ tree: parses[0], totalScore: 1, componentScores: {} }];
    }

    return parses
      .map((tree) => this.scoreParse(tree))
      .sort((left, right) => right.totalScore - left.totalScore);
  }

  scoreParse(tree: TParse): CecParseScore<TParse> {
    const componentScores: Record<string, number> = {};
    let totalScore = 0;

    for (const { name, rule } of this.preferenceRules) {
      const ruleScore = clamp01(rule(tree));
      componentScores[name] = ruleScore;
      totalScore += ruleScore;
    }

    return { tree, totalScore, componentScores };
  }

  addPreferenceRule(name: string, rule: CecPreferenceRule<TParse>): void {
    if (!name.trim()) throw new Error('CEC ambiguity preference rule name cannot be empty');
    this.preferenceRules.push({ name, rule });
  }

  setStrategyWeight(strategy: CecDisambiguationStrategy, weight: number): void {
    if (!Number.isFinite(weight) || weight < 0) throw new Error('CEC ambiguity strategy weight must be non-negative');
    this.strategies.set(strategy, weight);
  }

  explainRanking(scores: Array<CecParseScore<TParse>>): string {
    if (scores.length === 0) return 'No parses to rank.';

    return scores
      .map((score, index) => {
        const lines = [
          `Rank ${index + 1}: Total Score = ${score.totalScore.toFixed(3)}`,
          '  Component Scores:',
          ...Object.entries(score.componentScores).map(([component, value]) => `    ${component}: ${value.toFixed(3)}`),
          `  Tree size: ${treeSize(score.tree)} nodes`,
          `  Tree height: ${treeHeight(score.tree)}`,
        ];
        return lines.join('\n');
      })
      .join('\n\n');
  }

  private minimalAttachmentScore(tree: TParse): number {
    const sizeScore = 1 / (1 + treeSize(tree) * 0.1);
    const heightScore = 1 / (1 + treeHeight(tree) * 0.2);
    return (sizeScore + heightScore) / 2;
  }

  private rightAssociationScore(tree: TParse): number {
    const nonLeafNodes = treePreorder(tree).filter((node) => node.children.length > 0);
    if (nonLeafNodes.length === 0) return 0.5;

    const ratios = nonLeafNodes.map((node) => {
      if (node.children.length < 2) return 0.5;
      const rightSize = syntaxNodeSize(node.children[node.children.length - 1]);
      const otherSize = node.children.slice(0, -1).reduce((total, child) => total + syntaxNodeSize(child), 0);
      const total = rightSize + otherSize;
      return total === 0 ? 0.5 : rightSize / total;
    });

    return ratios.reduce((total, ratio) => total + ratio, 0) / ratios.length;
  }

  private treeBalanceScore(tree: TParse): number {
    const nodes = treePreorder(tree);
    if (nodes.length === 0) return 0.5;

    const balances = nodes.map((node) => {
      if (node.children.length === 0) return 1;
      const childHeights = node.children.map(syntaxNodeHeight);
      const maxHeight = Math.max(...childHeights);
      const minHeight = Math.min(...childHeights);
      if (maxHeight === 0) return 1;
      return 1 - (maxHeight - minHeight) / (maxHeight + 1);
    });

    return balances.reduce((total, balance) => total + balance, 0) / balances.length;
  }
}

export class CecSemanticDisambiguator<TParse extends CecParseLike = CecParseLike> {
  readonly semanticScores = new Map<string, number>();

  addSemanticScore(pattern: string, score: number): void {
    if (!pattern.trim()) throw new Error('CEC semantic disambiguation pattern cannot be empty');
    this.semanticScores.set(pattern, clamp01(score));
  }

  scoreSemantics(tree: TParse): number {
    const values = treeLeaves(tree).map((node) => String(node.value).toLowerCase());
    const joined = values.join(' ');
    const scores = [...this.semanticScores.entries()]
      .filter(([pattern]) => joined.includes(pattern.toLowerCase()))
      .map(([, score]) => score);
    if (scores.length === 0) return 0.5;
    return scores.reduce((total, score) => total + score, 0) / scores.length;
  }
}

export class CecStatisticalDisambiguator<TParse extends CecParseLike = CecParseLike> {
  readonly ngramCounts = new Map<string, number>();
  totalCount = 0;

  addNgram(ngram: readonly string[], count = 1): void {
    if (ngram.length === 0) throw new Error('CEC statistical ngram cannot be empty');
    if (!Number.isInteger(count) || count < 1) throw new Error('CEC statistical ngram count must be a positive integer');
    const key = ngramKey(ngram);
    this.ngramCounts.set(key, (this.ngramCounts.get(key) ?? 0) + count);
    this.totalCount += count;
  }

  scoreProbability(tree: TParse): number {
    if (this.totalCount === 0) return 0.5;
    const leaves = treeLeaves(tree).map((node) => String(node.value));
    if (leaves.length < 2) return 0.5;

    let totalProbability = 1;
    for (let index = 0; index < leaves.length - 1; index += 1) {
      const count = this.ngramCounts.get(ngramKey([leaves[index], leaves[index + 1]])) ?? 0;
      totalProbability *= (count + 1) / (this.totalCount + this.ngramCounts.size);
    }

    return Math.min(1, totalProbability * 10);
  }
}

export function cecExpressionToSyntaxTree(expression: CecExpression): CecSyntaxTree {
  return new CecSyntaxTree(cecExpressionToNode(expression), {
    label: formatCecExpression(expression),
    metadata: { expressionDepth: measureCecDepth(expression) },
  });
}

function cecExpressionToNode(expression: CecExpression): CecSyntaxNode {
  switch (expression.kind) {
    case 'atom':
      return new CecSyntaxNode(expression.name);
    case 'application':
      return new CecSyntaxNode(expression.name, expression.args.map(cecExpressionToNode));
    case 'quantified':
      return new CecSyntaxNode(expression.quantifier, [new CecSyntaxNode(expression.variable), cecExpressionToNode(expression.expression)]);
    case 'unary':
      return new CecSyntaxNode(expression.operator, [cecExpressionToNode(expression.expression)]);
    case 'binary':
      return new CecSyntaxNode(expression.operator, [cecExpressionToNode(expression.left), cecExpressionToNode(expression.right)]);
  }
}

function toSyntaxNode(node: CecSyntaxNodeLike): CecSyntaxNode {
  if (node instanceof CecSyntaxNode) return node;
  return new CecSyntaxNode(node.value, node.children ?? []);
}

function treeSize(tree: CecParseLike): number {
  return syntaxNodeSize(toSyntaxNode(tree.root));
}

function treeHeight(tree: CecParseLike): number {
  return syntaxNodeHeight(toSyntaxNode(tree.root));
}

function treePreorder(tree: CecParseLike): CecSyntaxNode[] {
  return toSyntaxNode(tree.root).preorder();
}

function treeLeaves(tree: CecParseLike): CecSyntaxNode[] {
  return toSyntaxNode(tree.root).leaves();
}

function syntaxNodeSize(node: CecSyntaxNode): number {
  return node.size();
}

function syntaxNodeHeight(node: CecSyntaxNode): number {
  return node.height();
}

function ngramKey(ngram: readonly string[]): string {
  return ngram.join('\u0000');
}

function clamp01(value: number): number {
  if (!Number.isFinite(value)) return 0;
  return Math.max(0, Math.min(1, value));
}

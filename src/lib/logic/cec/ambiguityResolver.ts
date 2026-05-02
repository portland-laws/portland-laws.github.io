export type CecDisambiguationStrategy =
  | 'minimal_attachment'
  | 'right_association'
  | 'semantic'
  | 'statistical';

export interface CecScoreMap {
  [name: string]: number;
}

export interface CecPreferenceRuleEntry {
  name: string;
  strategy: CecDisambiguationStrategy;
  rule: CecPreferenceRule;
}

export interface CecParseScore {
  tree: CecSyntaxTree;
  totalScore: number;
  componentScores: CecScoreMap;
}

export interface CecAmbiguityValidationResult {
  valid: boolean;
  errors: string[];
}

export interface CecSyntaxTreeOptions {
  label?: string;
  metadata?: { [name: string]: string | number | boolean | null };
}

export type CecPreferenceRule = (tree: CecSyntaxTree) => number;

export class CecSyntaxNode {
  readonly type: string;
  readonly children: CecSyntaxNode[];
  readonly value?: string;

  constructor(type: string, children: CecSyntaxNode[] = [], value?: string) {
    this.type = type;
    this.children = children.slice();
    this.value = value;
  }
}

export class CecSyntaxTree {
  readonly root: CecSyntaxNode;
  readonly label?: string;
  readonly metadata: { [name: string]: string | number | boolean | null };

  constructor(root: CecSyntaxNode, options: CecSyntaxTreeOptions = {}) {
    this.root = root;
    this.label = options.label;
    this.metadata = options.metadata ? { ...options.metadata } : {};
  }
}

function clampScore(value: number): number {
  if (!Number.isFinite(value)) return 0;
  if (value < 0) return 0;
  if (value > 1) return 1;
  return value;
}

function countNodes(node: CecSyntaxNode): number {
  let total = 1;
  node.children.forEach((child) => {
    total += countNodes(child);
  });
  return total;
}

function maxDepth(node: CecSyntaxNode): number {
  if (node.children.length === 0) return 1;
  return 1 + Math.max(...node.children.map((child) => maxDepth(child)));
}

function leafValues(node: CecSyntaxNode): string[] {
  if (node.children.length === 0) return node.value ? [node.value] : [node.type];
  return node.children.flatMap((child) => leafValues(child));
}

function parseLabel(tree: CecSyntaxTree): string {
  return tree.label || leafValues(tree.root).join(' ') || tree.root.type;
}

function isSyntaxNode(value: unknown): value is CecSyntaxNode {
  if (!(value instanceof CecSyntaxNode)) return false;
  return value.children.every((child) => isSyntaxNode(child));
}

export class CecAmbiguityResolver {
  readonly preferenceRules: CecPreferenceRuleEntry[] = [];
  private readonly strategyWeights: { [name: string]: number } = {
    minimal_attachment: 1,
    right_association: 1,
    semantic: 1,
    statistical: 1,
  };

  constructor() {
    this.addPreferenceRule(
      'minimal_attachment_score',
      (tree) => this.minimalAttachmentScore(tree),
      'minimal_attachment',
    );
    this.addPreferenceRule(
      'right_association_score',
      (tree) => this.rightAssociationScore(tree),
      'right_association',
    );
    this.addPreferenceRule('tree_balance_score', (tree) => this.treeBalanceScore(tree), 'semantic');
  }

  resolve(parses: CecSyntaxTree[]): CecParseScore[] {
    const validation = this.validateParses(parses);
    if (!validation.valid) throw new Error(`Invalid CEC parses: ${validation.errors.join('; ')}`);
    if (parses.length === 0) return [];
    if (parses.length === 1) return [{ tree: parses[0], totalScore: 1, componentScores: {} }];
    return parses
      .map((tree) => this.scoreParse(tree))
      .sort(
        (left, right) =>
          right.totalScore - left.totalScore ||
          parseLabel(left.tree).localeCompare(parseLabel(right.tree)),
      );
  }

  validateParses(parses: CecSyntaxTree[]): CecAmbiguityValidationResult {
    const errors: string[] = [];
    if (!Array.isArray(parses)) errors.push('parses must be an array');
    parses.forEach((parse, index) => {
      if (!(parse instanceof CecSyntaxTree)) {
        errors.push(`parse ${index} must be a CecSyntaxTree`);
      } else if (!isSyntaxNode(parse.root)) {
        errors.push(`parse ${index} has an invalid root node`);
      }
    });
    return { valid: errors.length === 0, errors };
  }

  scoreParse(tree: CecSyntaxTree): CecParseScore {
    const validation = this.validateParses([tree]);
    if (!validation.valid) throw new Error(`Invalid CEC parse: ${validation.errors.join('; ')}`);
    const componentScores: CecScoreMap = {};
    let weightedTotal = 0;
    let totalWeight = 0;
    this.preferenceRules.forEach((entry) => {
      const weight = this.strategyWeights[entry.strategy];
      const score = clampScore(entry.rule(tree));
      componentScores[entry.name] = score;
      weightedTotal += score * weight;
      totalWeight += weight;
    });
    return {
      tree,
      totalScore: totalWeight === 0 ? 0 : clampScore(weightedTotal / totalWeight),
      componentScores,
    };
  }

  addPreferenceRule(
    name: string,
    rule: CecPreferenceRule,
    strategy: CecDisambiguationStrategy = 'statistical',
  ): void {
    if (name.trim().length === 0)
      throw new Error('CEC ambiguity preference rule name cannot be empty');
    this.preferenceRules.push({ name, rule, strategy });
  }

  setStrategyWeight(strategy: CecDisambiguationStrategy, weight: number): void {
    if (!Number.isFinite(weight) || weight < 0)
      throw new Error('CEC ambiguity strategy weight must be a non-negative finite number');
    this.strategyWeights[strategy] = weight;
  }

  explain(scores: CecParseScore[]): string {
    if (scores.length === 0) return 'No parses to rank.';
    return scores
      .map(
        (score, index) =>
          `${index + 1}. ${parseLabel(score.tree)} score=${score.totalScore.toFixed(3)}`,
      )
      .join('\n');
  }

  private minimalAttachmentScore(tree: CecSyntaxTree): number {
    return 1 / countNodes(tree.root);
  }

  private rightAssociationScore(tree: CecSyntaxTree): number {
    if (tree.root.children.length === 0) return 1;
    const lastDepth = maxDepth(tree.root.children[tree.root.children.length - 1]);
    return clampScore(lastDepth / maxDepth(tree.root));
  }

  private treeBalanceScore(tree: CecSyntaxTree): number {
    if (tree.root.children.length === 0) return 1;
    const depths = tree.root.children.map((child) => maxDepth(child));
    const spread = Math.max(...depths) - Math.min(...depths);
    return 1 / (1 + spread);
  }
}

export class CecSemanticDisambiguator {
  resolve(parses: CecSyntaxTree[]): CecParseScore[] {
    const resolver = new CecAmbiguityResolver();
    resolver.setStrategyWeight('minimal_attachment', 0.5);
    resolver.setStrategyWeight('right_association', 0.5);
    resolver.setStrategyWeight('semantic', 2);
    return resolver.resolve(parses);
  }
}

export class CecStatisticalDisambiguator {
  private readonly priors: { [label: string]: number };

  constructor(priors: { [label: string]: number } = {}) {
    this.priors = { ...priors };
  }

  resolve(parses: CecSyntaxTree[]): CecParseScore[] {
    const resolver = new CecAmbiguityResolver();
    resolver.addPreferenceRule(
      'statistical_prior_score',
      (tree) => this.priors[parseLabel(tree)] || 0,
      'statistical',
    );
    resolver.setStrategyWeight('statistical', 2);
    return resolver.resolve(parses);
  }
}

export function cecExpressionToSyntaxTree(expression: string): CecSyntaxTree {
  const trimmed = expression.trim();
  if (trimmed.length === 0) throw new Error('CEC expression cannot be empty');
  const tokens = trimmed.split(/\s+/).map((token) => new CecSyntaxNode('token', [], token));
  return new CecSyntaxTree(new CecSyntaxNode('expression', tokens), { label: trimmed });
}

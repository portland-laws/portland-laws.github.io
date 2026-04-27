import {
  CecAmbiguityResolver,
  CecSemanticDisambiguator,
  CecStatisticalDisambiguator,
  CecSyntaxNode,
  CecSyntaxTree,
  cecExpressionToSyntaxTree,
} from './ambiguityResolver';
import { parseCecExpression } from './parser';

describe('CEC ambiguity resolver', () => {
  it('ranks parse trees with Python-style attachment, right association, and balance scores', () => {
    const simple = new CecSyntaxTree(new CecSyntaxNode('S', [new CecSyntaxNode('NP'), new CecSyntaxNode('VP')]), {
      label: 'simple',
    });
    const deep = new CecSyntaxTree(
      new CecSyntaxNode('S', [new CecSyntaxNode('NP'), new CecSyntaxNode('VP', [new CecSyntaxNode('PP', [new CecSyntaxNode('NP')])])]),
      { label: 'deep' },
    );

    const scores = new CecAmbiguityResolver().resolve([deep, simple]);

    expect(scores).toHaveLength(2);
    expect(scores[0].tree.label).toBe('simple');
    expect(scores[0].totalScore).toBeGreaterThan(scores[1].totalScore);
    expect(Object.keys(scores[0].componentScores)).toEqual([
      'minimal_attachment_score',
      'right_association_score',
      'tree_balance_score',
    ]);
  });

  it('returns the Python-compatible single-parse neutral score', () => {
    const tree = new CecSyntaxTree(new CecSyntaxNode('atom'));

    expect(new CecAmbiguityResolver().resolve([tree])).toEqual([
      { tree, totalScore: 1, componentScores: {} },
    ]);
  });

  it('supports custom preference rules and strategy weights', () => {
    const left = new CecSyntaxTree(new CecSyntaxNode('left'));
    const right = new CecSyntaxTree(new CecSyntaxNode('right'));
    const resolver = new CecAmbiguityResolver();
    resolver.addPreferenceRule('prefer_right', (tree) => (tree.label === 'right' ? 1 : 0));
    resolver.setStrategyWeight('statistical', 0.4);

    const scores = resolver.resolve([
      new CecSyntaxTree(left.root, { label: 'left' }),
      new CecSyntaxTree(right.root, { label: 'right' }),
    ]);

    expect(resolver.strategies.get('statistical')).toBe(0.4);
    expect(scores[0].tree.label).toBe('right');
    expect(() => resolver.setStrategyWeight('statistical', -1)).toThrow('non-negative');
  });

  it('explains rankings with component scores and tree statistics', () => {
    const resolver = new CecAmbiguityResolver();
    const scores = resolver.resolve([
      new CecSyntaxTree(new CecSyntaxNode('A', [new CecSyntaxNode('B')])),
      new CecSyntaxTree(new CecSyntaxNode('A', [new CecSyntaxNode('B'), new CecSyntaxNode('C')])),
    ]);

    expect(resolver.explainRanking(scores)).toContain('Rank 1: Total Score');
    expect(resolver.explainRanking(scores)).toContain('Tree size:');
    expect(resolver.explainRanking([])).toBe('No parses to rank.');
  });

  it('scores semantic patterns and statistical bigram probabilities', () => {
    const tree = new CecSyntaxTree(new CecSyntaxNode('S', [new CecSyntaxNode('permit'), new CecSyntaxNode('approved')]));
    const semantic = new CecSemanticDisambiguator();
    semantic.addSemanticScore('permit approved', 0.9);

    const statistical = new CecStatisticalDisambiguator();
    statistical.addNgram(['permit', 'approved'], 3);

    expect(semantic.scoreSemantics(tree)).toBe(0.9);
    expect(new CecSemanticDisambiguator().scoreSemantics(tree)).toBe(0.5);
    expect(statistical.scoreProbability(tree)).toBe(1);
    expect(new CecStatisticalDisambiguator().scoreProbability(tree)).toBe(0.5);
    expect(() => statistical.addNgram([], 1)).toThrow('cannot be empty');
  });

  it('converts CEC expressions to syntax trees for parse ranking', () => {
    const expression = parseCecExpression('(implies (permit tenant) (O (pay tenant rent)))');
    const tree = cecExpressionToSyntaxTree(expression);
    const score = new CecAmbiguityResolver().scoreParse(tree);

    expect(tree.label).toBe('(implies (permit tenant) (O (pay tenant rent)))');
    expect(tree.size()).toBeGreaterThan(5);
    expect(tree.height()).toBeGreaterThan(2);
    expect(tree.metadata.expressionDepth).toBeGreaterThan(2);
    expect(score.totalScore).toBeGreaterThan(0);
  });
});

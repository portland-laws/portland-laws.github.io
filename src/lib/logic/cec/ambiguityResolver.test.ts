import {
  CecAmbiguityResolver,
  CecSemanticDisambiguator,
  CecStatisticalDisambiguator,
  CecSyntaxNode,
  CecSyntaxTree,
  cecExpressionToSyntaxTree,
} from './ambiguityResolver';

describe('CEC ambiguity resolver', () => {
  it('ranks parse trees with deterministic browser-native scores', () => {
    const simple = new CecSyntaxTree(
      new CecSyntaxNode('S', [new CecSyntaxNode('NP'), new CecSyntaxNode('VP')]),
      {
        label: 'simple',
      },
    );
    const deep = new CecSyntaxTree(
      new CecSyntaxNode('S', [
        new CecSyntaxNode('NP'),
        new CecSyntaxNode('VP', [new CecSyntaxNode('PP', [new CecSyntaxNode('NP')])]),
      ]),
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

  it('keeps the Python-compatible single-parse neutral score', () => {
    const tree = new CecSyntaxTree(new CecSyntaxNode('atom'));

    expect(new CecAmbiguityResolver().resolve([tree])).toEqual([
      { tree, totalScore: 1, componentScores: {} },
    ]);
  });

  it('supports custom preference rules, validation, and fail-closed input handling', () => {
    const resolver = new CecAmbiguityResolver();
    resolver.addPreferenceRule('prefer_right', (tree) => (tree.label === 'right' ? 1 : 0));
    resolver.setStrategyWeight('statistical', 2);

    const scores = resolver.resolve([
      new CecSyntaxTree(new CecSyntaxNode('choice'), { label: 'left' }),
      new CecSyntaxTree(new CecSyntaxNode('choice'), { label: 'right' }),
    ]);

    expect(scores[0].tree.label).toBe('right');
    expect(scores[0].componentScores.prefer_right).toBe(1);
    expect(() => resolver.resolve([{} as CecSyntaxTree])).toThrow('Invalid CEC parses');
  });

  it('provides semantic, statistical, and expression conversion adapters without runtime services', () => {
    const expressionTree = cecExpressionToSyntaxTree('happens open door');
    const otherTree = new CecSyntaxTree(
      new CecSyntaxNode('expression', [new CecSyntaxNode('token', [], 'other')]),
      { label: 'other' },
    );

    const semanticScores = new CecSemanticDisambiguator().resolve([expressionTree, otherTree]);
    const statisticalScores = new CecStatisticalDisambiguator({ 'happens open door': 1 }).resolve([
      otherTree,
      expressionTree,
    ]);

    expect(expressionTree.root.children.map((child) => child.value)).toEqual([
      'happens',
      'open',
      'door',
    ]);
    expect(semanticScores).toHaveLength(2);
    expect(statisticalScores[0].tree.label).toBe('happens open door');
  });
});

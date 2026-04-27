import { CecAstSyntaxNode, CecAstSyntaxTree } from './syntaxTree';

describe('CEC syntax tree', () => {
  function sampleTree() {
    const root = new CecAstSyntaxNode('Root');
    const sentence = root.addChild(new CecAstSyntaxNode('Sentence', 'permit'));
    const phrase = sentence.addChild(new CecAstSyntaxNode('Phrase', 'tenant may appeal', {
      metadata: { source: 'fixture' },
      semantics: '(P (appeal tenant))',
    }));
    phrase.addChildren([
      new CecAstSyntaxNode('Word', 'tenant'),
      new CecAstSyntaxNode('Operator', 'may'),
      new CecAstSyntaxNode('Predicate', 'appeal'),
    ]);
    return new CecAstSyntaxTree(root);
  }

  it('constructs parent-aware syntax nodes and measures shape', () => {
    const tree = sampleTree();
    const phrase = tree.find((node) => node.nodeType === 'Phrase');
    const word = tree.find((node) => node.value === 'tenant');

    expect(tree.size()).toBe(6);
    expect(tree.height()).toBe(3);
    expect(phrase?.depth()).toBe(2);
    expect(word?.isLeaf()).toBe(true);
    expect(tree.root.isRoot()).toBe(true);
    expect(tree.leaves().map((node) => node.value)).toEqual(['tenant', 'may', 'appeal']);
  });

  it('supports Python-style traversals and search helpers', () => {
    const tree = sampleTree();

    expect(tree.preorder().map((node) => node.value ?? node.nodeType)).toEqual([
      'Root',
      'permit',
      'tenant may appeal',
      'tenant',
      'may',
      'appeal',
    ]);
    expect(tree.inorder().map((node) => node.value ?? node.nodeType)).toEqual([
      'tenant',
      'tenant may appeal',
      'may',
      'appeal',
      'permit',
      'Root',
    ]);
    expect(tree.postorder().map((node) => node.value ?? node.nodeType)).toEqual([
      'tenant',
      'may',
      'appeal',
      'tenant may appeal',
      'permit',
      'Root',
    ]);
    expect(tree.levelorder().map((node) => node.value ?? node.nodeType)).toEqual([
      'Root',
      'permit',
      'tenant may appeal',
      'tenant',
      'may',
      'appeal',
    ]);
    expect(tree.findAll((node) => node.nodeType === 'Word' || node.nodeType === 'Operator')).toHaveLength(2);
  });

  it('removes children and clears parent links', () => {
    const parent = new CecAstSyntaxNode('Phrase', 'parent');
    const child = parent.addChild(new CecAstSyntaxNode('Word', 'child'));

    expect(parent.removeChild(child)).toBe(true);
    expect(parent.removeChild(child)).toBe(false);
    expect(child.parent).toBeUndefined();
    expect(parent.children).toHaveLength(0);
  });

  it('transforms, maps, and filters trees without mutating the original', () => {
    const tree = sampleTree();
    const transformed = tree.transform((node) => new CecAstSyntaxNode(node.nodeType, String(node.value ?? node.nodeType).toUpperCase()));
    const mapped = tree.map((value) => String(value).replace('appeal', 'object'));
    const filtered = tree.filter((node) => node.nodeType !== 'Operator');

    expect(transformed.find((node) => node.value === 'TENANT')).toBeDefined();
    expect(mapped.find((node) => node.value === 'tenant may object')).toBeDefined();
    expect(filtered.find((node) => node.value === 'may')).toBeUndefined();
    expect(tree.find((node) => node.value === 'may')).toBeDefined();
  });

  it('round-trips JSON and renders an ASCII tree', () => {
    const tree = sampleTree();
    const json = tree.toJson();
    const roundTrip = CecAstSyntaxTree.fromJson(json);

    expect(json).toMatchObject({
      type: 'Root',
      children: [
        {
          type: 'Sentence',
          value: 'permit',
          children: [
            {
              type: 'Phrase',
              value: 'tenant may appeal',
              semantics: '(P (appeal tenant))',
              metadata: { source: 'fixture' },
            },
          ],
        },
      ],
    });
    expect(roundTrip.toJson()).toEqual(json);
    expect(roundTrip.prettyPrint()).toContain('Root');
    expect(roundTrip.prettyPrint()).toContain('`- Predicate(appeal)');
  });
});

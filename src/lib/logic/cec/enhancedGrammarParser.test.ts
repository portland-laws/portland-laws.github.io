import {
  DcecEarleyState,
  DcecEnhancedGrammarParser,
  DcecGrammarCategory,
  DcecGrammarRule,
  DcecGrammarTerminal,
  DcecParseTree,
  createDcecEnhancedGrammarParser,
} from './enhancedGrammarParser';

describe('DCEC enhanced grammar parser parity helpers', () => {
  it('formats terminals, grammar rules, parse trees, and Earley states', () => {
    const terminal = new DcecGrammarTerminal('alice', DcecGrammarCategory.AGENT);
    const rule = new DcecGrammarRule(DcecGrammarCategory.S, [DcecGrammarCategory.NP, DcecGrammarCategory.VP]);
    const tree = new DcecParseTree(DcecGrammarCategory.S, {
      children: [new DcecParseTree(DcecGrammarCategory.AGENT, { terminal })],
    });
    const state = new DcecEarleyState(rule, 1, 0, 1);

    expect(terminal.toString()).toBe('alice:Agent');
    expect(rule.toString()).toBe('S -> NP VP');
    expect(tree.isTerminal()).toBe(false);
    expect(tree.leaves()).toEqual(['alice']);
    expect(tree.toString()).toBe('S\n  Agent: alice');
    expect(state.nextCategory()).toBe(DcecGrammarCategory.VP);
    expect(state.isComplete()).toBe(false);
    expect(state.advance().toString()).toBe('S -> NP VP •  (0, 1)');
  });

  it('parses built-in sentence forms with an Earley-style chart', () => {
    const parser = createDcecEnhancedGrammarParser();

    expect(parser.parse('alice must open').map((tree) => tree.category)).toContain(DcecGrammarCategory.S);
    expect(parser.parse('alice open').map((tree) => tree.category)).toContain(DcecGrammarCategory.S);
    expect(parser.parse('always running').map((tree) => tree.category)).toContain(DcecGrammarCategory.S);
    expect(parser.parse('unknown words')).toEqual([]);
  });

  it('supports adding lexicon entries and grammar rules', () => {
    const parser = new DcecEnhancedGrammarParser();

    parser.addLexicalEntry('tenant', DcecGrammarCategory.AGENT);
    parser.addLexicalEntry('repair', DcecGrammarCategory.ACTION);

    expect(parser.parse('tenant must repair')).toHaveLength(1);
    expect(parser.lexicon.get('tenant')?.[0].category).toBe(DcecGrammarCategory.AGENT);
  });

  it('validates productive and reachable grammar categories', () => {
    const parser = new DcecEnhancedGrammarParser();
    const [valid, issues] = parser.validateGrammar();

    expect(valid).toBe(true);
    expect(issues).toEqual([]);

    const broken = new DcecEnhancedGrammarParser();
    broken.startSymbol = DcecGrammarCategory.ADJ;
    const [brokenValid, brokenIssues] = broken.validateGrammar();

    expect(brokenValid).toBe(false);
    expect(brokenIssues.some((issue) => issue.includes('No rules for start symbol'))).toBe(true);
  });
});

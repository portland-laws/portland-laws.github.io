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
    const rule = new DcecGrammarRule(DcecGrammarCategory.S, [
      DcecGrammarCategory.NP,
      DcecGrammarCategory.VP,
    ]);
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

    expect(parser.parse('alice must open').map((tree) => tree.category)).toContain(
      DcecGrammarCategory.S,
    );
    expect(parser.parse('alice open').map((tree) => tree.category)).toContain(
      DcecGrammarCategory.S,
    );
    expect(parser.parse('always running').map((tree) => tree.category)).toContain(
      DcecGrammarCategory.S,
    );
    expect(parser.parse('unknown words')).toEqual([]);
  });

  it('returns chart-parser diagnostics for complete and failed parses', () => {
    const parser = createDcecEnhancedGrammarParser();
    const success = parser.parseWithDiagnostics('alice must open');

    expect(success.alternatives).toHaveLength(1);
    expect(success.alternatives[0].toString()).toContain('Deontic');
    expect(success.diagnostics.chartSizes).toHaveLength(4);
    expect(success.diagnostics.scans).toBeGreaterThan(0);
    expect(success.diagnostics.completions).toBeGreaterThan(0);
    expect(success.diagnostics.diagnostics.at(-1)?.code).toBe('parse-complete');

    const failure = parser.parseWithDiagnostics('alice must teleport');

    expect(failure.alternatives).toEqual([]);
    expect(
      failure.diagnostics.diagnostics.some(
        (entry) => entry.code === 'unknown-token' && entry.token === 'teleport',
      ),
    ).toBe(true);
    expect(failure.diagnostics.diagnostics.at(-1)?.code).toBe('incomplete-parse');
  });

  it('keeps grammar fixture alternatives for ambiguous lexical categories', () => {
    const parser = new DcecEnhancedGrammarParser();

    parser.addLexicalEntry('repair', DcecGrammarCategory.V);
    parser.addLexicalEntry('repair', DcecGrammarCategory.ACTION);
    const result = parser.parseWithDiagnostics('alice repair');

    expect(result.alternatives).toHaveLength(2);
    expect(result.alternatives.map((tree) => tree.leaves())).toEqual([
      ['alice', 'repair'],
      ['alice', 'repair'],
    ]);
    expect(result.alternatives.map((tree) => tree.toString()).join('\n---\n')).toContain(
      'VP\n    V: repair',
    );
    expect(result.alternatives.map((tree) => tree.toString()).join('\n---\n')).toContain(
      'VP\n    Action: repair',
    );
    expect(result.diagnostics.diagnostics.at(-1)?.message).toContain('2 parse alternatives');
  });

  it('supports adding lexicon entries and grammar rules', () => {
    const parser = new DcecEnhancedGrammarParser();

    parser.addLexicalEntry('tenant', DcecGrammarCategory.AGENT);
    parser.addLexicalEntry('repair', DcecGrammarCategory.ACTION);

    expect(parser.parse('tenant must repair')).toHaveLength(1);
    expect(parser.lexicon.get('tenant')?.[0].category).toBe(DcecGrammarCategory.AGENT);
  });

  it('round-trips browser-native grammar snapshots without external resources', () => {
    const parser = createDcecEnhancedGrammarParser();
    parser.addLexicalEntry('tenant', DcecGrammarCategory.AGENT);
    parser.addLexicalEntry('repair', DcecGrammarCategory.ACTION);

    const snapshot = parser.createSnapshot();
    const restored = new DcecEnhancedGrammarParser({ initializeDefaults: false });
    const validation = restored.loadSnapshot(snapshot);

    expect(snapshot).toMatchObject({
      sourcePythonModule: 'logic/CEC/native/enhanced_grammar_parser.py',
      runtime: 'browser-native',
      externalResourcePolicy: 'none',
      startSymbol: DcecGrammarCategory.S,
    });
    expect(validation).toEqual({ valid: true, issues: [] });
    expect(restored.parse('tenant must repair')).toHaveLength(1);
    expect(restored.createSnapshot().lexicon.tenant).toEqual([DcecGrammarCategory.AGENT]);
  });

  it('rejects malformed grammar snapshots before mutating parser state', () => {
    const parser = createDcecEnhancedGrammarParser();
    const before = parser.createSnapshot();
    const invalid = {
      ...before,
      rules: [{ lhs: DcecGrammarCategory.S, rhs: [] }],
      lexicon: { '': [], alice: ['UnknownCategory'] },
    } as unknown as ReturnType<DcecEnhancedGrammarParser['createSnapshot']>;

    const validation = parser.loadSnapshot(invalid);

    expect(validation.valid).toBe(false);
    expect(validation.issues.map((issue) => issue.code)).toEqual([
      'empty-rule-rhs',
      'empty-lexical-entry',
      'invalid-lexical-category',
    ]);
    expect(parser.createSnapshot()).toEqual(before);
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

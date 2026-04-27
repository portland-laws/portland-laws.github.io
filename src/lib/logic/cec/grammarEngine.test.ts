import {
  CecGrammarEngine,
  CecGrammarLoader,
  CecGrammarRule,
  CecLexicalEntry,
  createDefaultCecGrammarLoader,
} from './grammarEngine';

describe('CEC grammar loader and engine', () => {
  it('loads default grammar sections and operator metadata without filesystem access', () => {
    const loader = createDefaultCecGrammarLoader();

    expect(loader.getConfig()).toMatchObject({ version: '1.0', language: 'en', caseSensitive: false });
    expect(loader.validate()).toBe(true);
    expect(loader.getWordsForOperator('deontic', 'obligation')).toEqual(['must', 'obligated', 'should', 'required']);
    expect(loader.getWordsForOperator('connectives', 'and')).toEqual(['and']);
    expect(loader.getSemantics('temporal', 'always')).toEqual({ type: 'temporal', operator: 'always' });
    expect(loader.getExamples('connectives', 'and')).toEqual(['Alice loves Bob and Carol']);
    expect(loader.getProductionRules().compound[0].pattern).toBe('{sentence} {connective} {sentence}');
    expect(loader.getAllWords()).toEqual(expect.arrayContaining(['and', 'must', 'believes', 'always', 'every']));
  });

  it('accepts static browser-native grammar data and validates required sections', () => {
    const loader = new CecGrammarLoader({
      config: { version: '2.0', language: 'en-GB', case_sensitive: true },
      connectives: {},
      deontic: {},
      cognitive: {},
      temporal: {},
      quantifiers: {},
    });
    const invalid = new CecGrammarLoader({ connectives: {} });

    expect(loader.getConfig()).toMatchObject({ version: '2.0', language: 'en-GB', caseSensitive: true });
    expect(loader.validate()).toBe(true);
    expect(invalid.validate()).toBe(false);
  });

  it('applies grammar rules and parses with bottom-up chart parsing', () => {
    const engine = new CecGrammarEngine();
    engine.addLexicalEntry(new CecLexicalEntry({ word: 'alice', category: 'Agent', semantics: 'alice' }));
    engine.addLexicalEntry(new CecLexicalEntry({ word: 'appeal', category: 'ActionType', semantics: 'appeal' }));
    engine.addLexicalEntry(new CecLexicalEntry({ word: 'may', category: 'V', semantics: 'P' }));
    engine.addRule(new CecGrammarRule({
      name: 'AgentToSentence',
      category: 'Sentence',
      constituents: ['Agent'],
      semanticFn: ([agent]) => agent,
    }));
    engine.addRule(new CecGrammarRule({
      name: 'ModalAction',
      category: 'VP',
      constituents: ['V', 'ActionType'],
      semanticFn: ([modal, action]) => ({ modal, action }),
    }));
    engine.addRule(new CecGrammarRule({
      name: 'SentenceVP',
      category: 'Utterance',
      constituents: ['Sentence', 'VP'],
      semanticFn: ([agent, vp]) => ({ agent, ...(vp as Record<string, unknown>) }),
      linearizeFn: (value) => {
        const record = value as { agent: string; modal: string; action: string };
        return `${record.agent} ${record.modal === 'P' ? 'may' : record.modal} ${record.action}`;
      },
    }));

    const parses = engine.parse('Alice may appeal');

    expect(parses).toHaveLength(1);
    expect(parses[0].semantics).toEqual({ agent: 'alice', modal: 'P', action: 'appeal' });
    expect(parses[0].span).toEqual([0, 3]);
    expect(parses[0].linearize()).toBe('alice may appeal');
    expect(engine.linearize(parses[0].semantics, 'Utterance')).toBe('alice may appeal');
  });

  it('resolves ambiguity by first, shortest, and most specific strategies', () => {
    const engine = new CecGrammarEngine();
    const short = { category: 'Utterance' as const, children: [], semantics: 'short', span: [0, 1] as [number, number], isLexical: () => false, linearize: () => 'short' };
    const specific = {
      category: 'Utterance' as const,
      children: [
        { category: 'Agent' as const, children: [], semantics: 'alice', span: [0, 1] as [number, number], isLexical: () => true, linearize: () => 'alice' },
        { category: 'ActionType' as const, children: [], semantics: 'appeal', span: [1, 2] as [number, number], isLexical: () => true, linearize: () => 'appeal' },
      ],
      semantics: 'specific',
      span: [0, 2] as [number, number],
      isLexical: () => false,
      linearize: () => 'specific',
    };

    expect(engine.resolveAmbiguity([specific as never, short as never], 'first')).toBe(specific);
    expect(engine.resolveAmbiguity([specific as never, short as never], 'shortest')).toBe(short);
    expect(engine.resolveAmbiguity([short as never, specific as never], 'most_specific')).toBe(specific);
    expect(engine.resolveAmbiguity([])).toBeUndefined();
  });

  it('falls back to string linearization when no rule handles a category', () => {
    const engine = new CecGrammarEngine();
    expect(engine.parse('unknown tokens')).toEqual([]);
    expect(engine.linearize({ raw: true }, 'Sentence')).toBe('[object Object]');
  });
});

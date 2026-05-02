import {
  expandFormulaTree,
  renderInteractiveExpansion,
  type ExpansionFormula,
} from './expansionRules';

describe('FOL expansion rules', () => {
  it('expands alpha, beta, gamma, and delta rules with deterministic branch diagnostics', () => {
    const root: ExpansionFormula = {
      id: 'a1',
      text: 'P and (Q or R)',
      rule: 'alpha',
      children: [
        { id: 'p', text: 'P', rule: 'literal' },
        {
          id: 'b1',
          text: 'Q or not P',
          rule: 'beta',
          branches: [
            [
              { id: 'q', text: 'Q', rule: 'literal' },
              {
                id: 'g1',
                text: 'forall x S(x)',
                rule: 'gamma',
                children: [{ id: 's-a', text: 'S(a)', rule: 'literal' }],
              },
            ],
            [
              { id: 'np', text: 'not P', rule: 'literal' },
              {
                id: 'd1',
                text: 'exists x T(x)',
                rule: 'delta',
                witness: 'w1',
                children: [{ id: 't-w1', text: 'T(w1)', rule: 'literal', witness: 'w1' }],
              },
            ],
          ],
        },
      ],
    };

    const result = expandFormulaTree(root, 'breadth-first');

    expect(result.strategy).toBe('breadth-first');
    expect(result.branches).toHaveLength(2);
    expect(result.appliedRuleIds).toEqual(['a1', 'b1', 'g1', 'd1']);
    expect(result.branches.find((branch) => branch.id === 'b1.1')?.closed).toBe(false);
    expect(result.branches.find((branch) => branch.id === 'b1.2')?.closed).toBe(true);
    expect(result.diagnostics.map((diagnostic) => diagnostic.code)).toEqual(
      expect.arrayContaining(['open-branch', 'closed-branch']),
    );
  });

  it('reports fail-closed adapter diagnostics for malformed browser-native rule metadata', () => {
    const result = expandFormulaTree({
      id: 'd1',
      text: 'exists x P(x)',
      rule: 'delta',
      children: [{ id: 'p-w', text: 'P(w)', rule: 'literal' }],
    });

    expect(result.diagnostics).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ code: 'missing-witness', formulaId: 'd1' }),
      ]),
    );
  });

  it('renders interactive branch state without server or filesystem dependencies', () => {
    const result = expandFormulaTree({
      id: 'b1',
      text: 'P or not P',
      rule: 'beta',
      branches: [
        [{ id: 'p', text: 'P', rule: 'literal' }],
        [{ id: 'np', text: 'not P', rule: 'literal' }],
      ],
    });

    const rendered = renderInteractiveExpansion(result);

    expect(rendered.strategy).toBe('depth-first');
    expect(rendered.nodes.map((node) => node.label).sort()).toEqual(['P', 'not P']);
    expect(rendered.nodes.every((node) => node.status === 'open')).toBe(true);
    expect(rendered.edges).toEqual([]);
  });
});

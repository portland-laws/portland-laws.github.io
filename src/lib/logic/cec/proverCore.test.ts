import type { CecExpression } from './ast';
import type { CecKnowledgeBase, CecProofResult } from './prover';
import {
  BrowserNativeCecProverCore,
  CEC_PROVER_CORE_RUNTIME,
  normalizeCecProverCoreSearchLimits,
  prove_cec_core,
} from './proverCore';

describe('BrowserNativeCecProverCore', () => {
  it('ports prover_core.py with browser-native metadata and deterministic search-limit normalization', () => {
    expect(CEC_PROVER_CORE_RUNTIME).toEqual({
      module: 'logic/CEC/native/prover_core.py',
      runtime: 'browser-native-typescript',
      pythonRuntime: false,
      serverDelegation: false,
    });
    expect(
      normalizeCecProverCoreSearchLimits({ maxDepth: 0, maxNodes: -4, maxRuleApplications: 3.8 }),
    ).toEqual({ maxDepth: 12, maxNodes: 256, maxRuleApplications: 3 });
  });

  it('fails closed for invalid inputs and returns deterministic local proof summaries', () => {
    const proof = { proved: true } as unknown as CecProofResult;
    const theorem = { kind: 'atom' } as unknown as CecExpression;
    const kb = { axioms: [] } as unknown as CecKnowledgeBase;
    const core = new BrowserNativeCecProverCore(
      { searchLimits: { maxDepth: 5 } },
      {
        proverFactory: () => ({ prove: () => proof }),
        now: (() => {
          let tick = 10;
          return () => {
            tick += 2;
            return tick;
          };
        })(),
      },
    );

    expect(core.prove(theorem, kb)).toMatchObject({
      proof,
      summary: {
        outcome: 'proved',
        success: true,
        limits: { maxDepth: 5, maxNodes: 256, maxRuleApplications: 512 },
        metadata: { module: 'logic/CEC/native/prover_core.py', serverDelegation: false },
      },
    });
    expect(core.prove(undefined as unknown as CecExpression, kb)).toMatchObject({
      proof: null,
      summary: {
        outcome: 'invalid_input',
        success: false,
        diagnostics: ['Theorem must be provided as a CEC expression.'],
      },
    });
    expect(
      prove_cec_core(theorem, kb, {}, { proverFactory: () => ({ prove: () => proof }) }).summary
        .success,
    ).toBe(true);
  });
});

import { formatCecExpression } from './formatter';
import { parseCecExpression } from './parser';
import {
  applySpecializedAlwaysElimination,
  applySpecializedCecInferenceRules,
  applySpecializedHypotheticalSyllogism,
  applySpecializedModusPonens,
  applySpecializedObligationPermission,
} from './specializedInferenceRules';

describe('specialized CEC inference rules', () => {
  it('applies specialized modus ponens over a premise batch', () => {
    const premises = [
      parseCecExpression('(subject_to agent code)'),
      parseCecExpression('(implies (subject_to agent code) (comply_with agent code))'),
    ];

    const results = applySpecializedModusPonens(premises);

    expect(results).toHaveLength(1);
    expect(results[0].rule).toBe('specialized-modus-ponens');
    expect(results[0].metadata).toEqual({
      sourceModule: 'logic/CEC/native/inference_rules/specialized.py',
      browserNative: true,
    });
    expect(formatCecExpression(results[0].conclusion)).toBe('(comply_with agent code)');
  });

  it('chains implication premises with specialized hypothetical syllogism', () => {
    const results = applySpecializedHypotheticalSyllogism([
      parseCecExpression('(implies (a) (b))'),
      parseCecExpression('(implies (b) (c))'),
      parseCecExpression('(implies (x) (y))'),
    ]);

    expect(results.map((item) => formatCecExpression(item.conclusion))).toEqual([
      '(implies (a) (c))',
    ]);
    expect(results[0].rule).toBe('specialized-hypothetical-syllogism');
  });

  it('derives deontic and temporal specialized conclusions without runtime fallbacks', () => {
    const obligationResults = applySpecializedObligationPermission([
      parseCecExpression('(O (pay agent fee))'),
    ]);
    const temporalResults = applySpecializedAlwaysElimination([
      parseCecExpression('(always (active permit))'),
    ]);

    expect(formatCecExpression(obligationResults[0].conclusion)).toBe('(P (pay agent fee))');
    expect(formatCecExpression(temporalResults[0].conclusion)).toBe('(active permit)');
  });

  it('combines specialized rules through one browser-native adapter', () => {
    const results = applySpecializedCecInferenceRules([
      parseCecExpression('(p)'),
      parseCecExpression('(implies (p) (q))'),
      parseCecExpression('(implies (q) (r))'),
      parseCecExpression('(O (q))'),
      parseCecExpression('(always (r))'),
    ]);

    expect(results.map((item) => item.rule)).toEqual([
      'specialized-modus-ponens',
      'specialized-hypothetical-syllogism',
      'specialized-obligation-permission',
      'specialized-always-elimination',
    ]);
    expect(results.map((item) => formatCecExpression(item.conclusion))).toEqual([
      '(q)',
      '(implies (p) (r))',
      '(P (q))',
      '(r)',
    ]);
  });
});

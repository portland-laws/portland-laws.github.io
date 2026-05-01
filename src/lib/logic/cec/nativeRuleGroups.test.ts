import {
  CecNativeRuleGroups,
  getCecNativeRuleGroup,
  getCecNativeRuleGroups,
  getCecNativeRulesByGroup,
} from './nativeRuleGroups';

describe('CEC native inference rule groups', () => {
  it('enumerates the native rule families required by the TypeScript port plan', () => {
    expect(getCecNativeRuleGroups().map((group) => group.name)).toEqual([
      'propositional',
      'modal',
      'temporal',
      'deontic',
      'cognitive',
      'specialized',
      'resolution',
    ]);
  });

  it('maps representative Python-native inference rules into deterministic TypeScript groups', () => {
    expect(getCecNativeRulesByGroup('propositional').map((rule) => rule.name)).toEqual(
      expect.arrayContaining([
        'CecModusPonens',
        'CecHypotheticalSyllogism',
        'CecMaterialImplication',
        'CecBiconditionalElimination',
      ]),
    );

    expect(getCecNativeRulesByGroup('modal').map((rule) => rule.name)).toEqual(
      expect.arrayContaining([
        'CecNecessityElimination',
        'CecPossibilityIntroduction',
        'CecNecessityDistribution',
      ]),
    );

    expect(getCecNativeRulesByGroup('temporal').map((rule) => rule.name)).toEqual(
      expect.arrayContaining([
        'CecTemporalT',
        'CecEventuallyIntroduction',
        'CecTemporalUntilElimination',
      ]),
    );

    expect(getCecNativeRulesByGroup('deontic').map((rule) => rule.name)).toEqual(
      expect.arrayContaining([
        'CecDeonticD',
        'CecObligationDistribution',
        'CecObligationConsistency',
      ]),
    );

    expect(getCecNativeRulesByGroup('cognitive').map((rule) => rule.name)).toEqual(
      expect.arrayContaining([
        'CecBeliefDistribution',
        'CecKnowledgeImpliesBelief',
        'CecIntentionCommitment',
      ]),
    );

    expect(getCecNativeRulesByGroup('specialized').map((rule) => rule.name)).toEqual(
      expect.arrayContaining([
        'CecUniversalModusPonens',
        'CecExistentialInstantiation',
        'CecFixedPointInduction',
      ]),
    );

    expect(getCecNativeRulesByGroup('resolution').map((rule) => rule.name)).toEqual(
      expect.arrayContaining(['CecResolution', 'CecUnitResolution', 'CecProofByContradiction']),
    );
  });

  it('returns stable group objects without duplicate rule names inside a family', () => {
    expect(getCecNativeRuleGroup('resolution')).toBe(CecNativeRuleGroups[6]);

    for (const group of getCecNativeRuleGroups()) {
      const names = group.rules.map((rule) => rule.name);
      expect(names.length).toBeGreaterThan(0);
      expect(new Set(names).size).toBe(names.length);
    }
  });
});

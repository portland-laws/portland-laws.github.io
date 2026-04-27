import { parseCecExpression } from './parser';
import { CecModalTableaux, CecTableauxBranch, CecTableauxWorld, proveCecModalFormula } from './modalTableaux';

describe('CEC modal tableaux', () => {
  it('closes direct contradictions in negated validity checks', () => {
    const result = proveCecModalFormula(parseCecExpression('(implies (subject_to agent code) (subject_to agent code))'), 'K');

    expect(result.isValid).toBe(true);
    expect(result.closedBranches).toBe(result.totalBranches);
    expect(result.proofSteps).toContain('CEC negated IMPLIES expansion at world 0');
    expect(result.proofSteps.some((step) => step.includes('contradiction'))).toBe(true);
  });

  it('distinguishes K from reflexive T for always implies body', () => {
    const formula = parseCecExpression('(implies (always (comply_with agent code)) (comply_with agent code))');
    const kResult = proveCecModalFormula(formula, 'K');
    const tResult = proveCecModalFormula(formula, 'T');

    expect(kResult.isValid).toBe(false);
    expect(kResult.openBranch).toBeDefined();
    expect(tResult.isValid).toBe(true);
    expect(tResult.proofSteps).toContain('CEC BOX expansion at world 0 to 1 worlds');
  });

  it('creates accessible worlds for diamond-style permission expansion', () => {
    const tableaux = new CecModalTableaux({ logicType: 'K' });
    const result = tableaux.prove(parseCecExpression('(not (P (enter agent code)))'));

    expect(result.isValid).toBe(false);
    expect(result.openBranch?.worlds.size).toBe(2);
    expect(result.proofSteps).toContain('CEC DIAMOND: created world 1');
  });

  it('applies D seriality for obligations', () => {
    const result = proveCecModalFormula(parseCecExpression('(implies (O (comply_with agent code)) (P (comply_with agent code)))'), 'D');

    expect(result.isValid).toBe(true);
    expect(result.proofSteps).toContain('CEC BOX expansion at world 0 to 1 worlds');
    expect(result.proofSteps).toContain('CEC negated DIAMOND expansion at world 0');
  });

  it('applies S5 mutual accessibility for new modal worlds', () => {
    const result = proveCecModalFormula(parseCecExpression('(not (eventually (comply_with agent code)))'), 'S5');

    expect(result.isValid).toBe(false);
    expect(result.openBranch?.getAccessibleWorlds(0)).toEqual(new Set([0, 1]));
    expect(result.openBranch?.getAccessibleWorlds(1)).toEqual(new Set([1, 0]));
  });

  it('copies branches and tracks world contradictions by CEC expression key', () => {
    const branch = new CecTableauxBranch();
    const world = new CecTableauxWorld(0);
    const formula = parseCecExpression('(subject_to agent code)');
    world.addFormula(formula);
    branch.addWorld(world);
    const copy = branch.copy();
    copy.worlds.get(0)?.addFormula(formula, true);

    expect(branch.worlds.get(0)?.hasContradiction()).toBe(false);
    expect(copy.worlds.get(0)?.hasContradiction()).toBe(true);
  });
});

import { extractTdfolCountermodel } from './countermodels';
import { parseTdfolFormula } from './parser';
import { proveTdfolModalFormula, TdfolModalTableaux, TdfolTableauxBranch, TdfolTableauxWorld } from './modalTableaux';

describe('TDFOL modal tableaux', () => {
  it('closes direct contradictions in negated validity checks', () => {
    const result = proveTdfolModalFormula(parseTdfolFormula('Pred(x) -> Pred(x)'), 'K');

    expect(result.isValid).toBe(true);
    expect(result.closedBranches).toBe(result.totalBranches);
    expect(result.proofSteps).toContain('Negated IMPLIES expansion at world 0');
    expect(result.proofSteps.some((step) => step.includes('contradiction'))).toBe(true);
  });

  it('distinguishes K from reflexive T for box implies body', () => {
    const formula = parseTdfolFormula('always(Pred(x)) -> Pred(x)');
    const kResult = proveTdfolModalFormula(formula, 'K');
    const tResult = proveTdfolModalFormula(formula, 'T');

    expect(kResult.isValid).toBe(false);
    expect(kResult.openBranch).toBeDefined();
    expect(tResult.isValid).toBe(true);
    expect(tResult.proofSteps).toContain('BOX expansion at world 0 to 1 worlds');
  });

  it('creates open branches that feed countermodel extraction', () => {
    const formula = parseTdfolFormula('always(Pred(x)) -> Pred(x)');
    const result = proveTdfolModalFormula(formula, 'K');
    const countermodel = extractTdfolCountermodel(formula, result.openBranch!, 'K');

    expect(countermodel.kripke.worlds.has(0)).toBe(true);
    expect(countermodel.kripke.getAccessibleWorlds(0).size).toBe(0);
    expect(countermodel.explanation[0]).toContain('is not K-valid');
  });

  it('expands diamonds by creating accessible worlds', () => {
    const tableaux = new TdfolModalTableaux({ logicType: 'K' });
    const result = tableaux.prove(parseTdfolFormula('not eventually(Pred(x))'));

    expect(result.isValid).toBe(false);
    expect(result.openBranch?.worlds.size).toBe(2);
    expect(result.proofSteps).toContain('DIAMOND: created world 1');
  });

  it('applies S5 mutual accessibility for new modal worlds', () => {
    const result = proveTdfolModalFormula(parseTdfolFormula('not eventually(Pred(x))'), 'S5');

    expect(result.isValid).toBe(false);
    expect(result.openBranch?.getAccessibleWorlds(0)).toEqual(new Set([0, 1]));
    expect(result.openBranch?.getAccessibleWorlds(1)).toEqual(new Set([1, 0]));
  });

  it('copies branches and tracks world contradictions with formula keys', () => {
    const branch = new TdfolTableauxBranch();
    const world = new TdfolTableauxWorld(0);
    const formula = parseTdfolFormula('Pred(x)');
    world.addFormula(formula);
    branch.addWorld(world);
    const copy = branch.copy();
    copy.worlds.get(0)?.addFormula(formula, true);

    expect(branch.worlds.get(0)?.hasContradiction()).toBe(false);
    expect(copy.worlds.get(0)?.hasContradiction()).toBe(true);
  });
});

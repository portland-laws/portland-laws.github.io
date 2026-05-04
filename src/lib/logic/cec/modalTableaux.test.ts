import { parseCecExpression } from './parser';
import {
  CecModalTableaux,
  CecNativeTableauNode,
  CecTableauxBranch,
  CecTableauxWorld,
  createCecTableauProver,
  createTableauProver,
  proveCecModalFormula,
} from './modalTableaux';

describe('CEC modal tableaux', () => {
  it('closes direct contradictions in negated validity checks', () => {
    const result = proveCecModalFormula(
      parseCecExpression('(implies (subject_to agent code) (subject_to agent code))'),
      'K',
    );

    expect(result.isValid).toBe(true);
    expect(result.closedBranches).toBe(result.totalBranches);
    expect(result.proofSteps).toContain('CEC negated IMPLIES expansion at world 0');
    expect(result.proofSteps.some((step) => step.includes('contradiction'))).toBe(true);
  });

  it('distinguishes K from reflexive T for always implies body', () => {
    const formula = parseCecExpression(
      '(implies (always (comply_with agent code)) (comply_with agent code))',
    );
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
    const result = proveCecModalFormula(
      parseCecExpression('(implies (O (comply_with agent code)) (P (comply_with agent code)))'),
      'D',
    );

    expect(result.isValid).toBe(true);
    expect(result.proofSteps).toContain('CEC BOX expansion at world 0 to 1 worlds');
    expect(result.proofSteps).toContain('CEC negated DIAMOND expansion at world 0');
  });

  it('applies S5 mutual accessibility for new modal worlds', () => {
    const result = proveCecModalFormula(
      parseCecExpression('(not (eventually (comply_with agent code)))'),
      'S5',
    );

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

  it('ports the native TableauNode contradiction and status behavior', () => {
    const node = new CecNativeTableauNode(0, ['P']);

    expect(node.addFormula('P')).toBe(false);
    expect(node.addFormula('¬P')).toBe(true);
    expect(node.isContradictory()).toBe(true);
    node.close();
    expect(node.status).toBe('closed');
  });

  it('proves native string goals from assumptions by closing the refutation branch', () => {
    const prover = createCecTableauProver('K');
    const [success, tableau] = prover.prove('P', ['P']);

    expect(success).toBe(true);
    expect(tableau.isClosed()).toBe(true);
    expect(tableau.proofSteps[0]).toMatchObject({
      ruleName: 'Closure',
      conclusion: '⊥',
    });
  });

  it('branches native disjunctions and creates native modal worlds', () => {
    const prover = createTableauProver('K');
    const [success, tableau] = prover.prove('R', ['P∨Q']);
    const [, modalTableau] = createCecTableauProver('K').prove('R', ['◇P']);

    expect(success).toBe(false);
    expect(tableau.root.children).toHaveLength(2);
    expect(tableau.root.children[0].formulas.has('P')).toBe(true);
    expect(tableau.root.children[1].formulas.has('Q')).toBe(true);
    expect(tableau.proofSteps.some((step) => step.ruleName === 'Or')).toBe(true);
    expect(modalTableau.root.accessibleWorlds).toEqual(new Set([1]));
    expect(modalTableau.root.children[0].formulas.has('P')).toBe(true);
  });

  it('applies native T, S4, and S5 modal axiom rules without Python runtime support', () => {
    const [, tTableau] = createCecTableauProver('T').prove('R', ['□P']);
    const [, s4Tableau] = createCecTableauProver('S4').prove('R', ['□P']);
    const [, s5Tableau] = createCecTableauProver('S5').prove('R', ['◇P']);

    expect(tTableau.root.formulas.has('P')).toBe(true);
    expect(s4Tableau.root.formulas.has('□□P')).toBe(true);
    expect(s5Tableau.root.formulas.has('□◇P')).toBe(true);
    expect(tTableau.proofSteps.some((step) => step.ruleName === 'T')).toBe(true);
    expect(s4Tableau.proofSteps.some((step) => step.ruleName === 'S4')).toBe(true);
    expect(s5Tableau.proofSteps.some((step) => step.ruleName === 'S5')).toBe(true);
  });
});

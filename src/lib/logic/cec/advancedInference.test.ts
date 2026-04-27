import {
  DcecCognitiveFormula,
  DcecDeonticFormula,
  dcecAtom,
  dcecConjunction,
  dcecImplication,
} from './dcecCore';
import { DcecCognitiveOperator, DcecDeonticOperator, DcecSort, DcecVariable } from './dcecTypes';
import { DcecVariableTerm } from './dcecCore';
import {
  DcecDeonticDRule,
  DcecDeonticDistribution,
  DcecDeonticPermissionObligation,
  DcecFrameAxiom,
  DcecKnowledgeObligation,
  DcecModalKAxiom,
  DcecModalNecessitation,
  DcecModalS4Axiom,
  DcecModalTAxiom,
  DcecTemporalInduction,
  DcecTemporalObligation,
  getAllDcecAdvancedRules,
  getDcecCombinedRules,
  getDcecDeonticRules,
  getDcecModalRules,
  getDcecTemporalRules,
} from './advancedInference';

const agent = new DcecVariableTerm(new DcecVariable('agent', new DcecSort('Agent')));
const p = dcecAtom('p');
const q = dcecAtom('q');

describe('DCEC advanced inference parity rules', () => {
  it('applies modal K, T, S4, and necessitation rules', () => {
    const knowledgeImplication = new DcecCognitiveFormula(
      DcecCognitiveOperator.KNOWLEDGE,
      agent,
      dcecImplication(p, q),
    );

    const k = new DcecModalKAxiom();
    const t = new DcecModalTAxiom();
    const s4 = new DcecModalS4Axiom();
    const necessitation = new DcecModalNecessitation();

    expect(k.canApply([knowledgeImplication])).toBe(true);
    expect(k.apply([knowledgeImplication]).map(String)).toEqual(['(K(agent:Agent, p()) → K(agent:Agent, q()))']);
    expect(t.apply([knowledgeImplication]).map(String)).toEqual(['(p() → q())']);
    expect(s4.apply([knowledgeImplication]).map(String)).toEqual(['K(agent:Agent, K(agent:Agent, (p() → q())))']);
    expect(necessitation.apply([p, knowledgeImplication]).map(String)).toEqual(['K(system:System, p())']);
  });

  it('applies temporal induction and frame axiom rules', () => {
    const temporal = new DcecTemporalInduction();
    const frame = new DcecFrameAxiom();

    expect(temporal.canApply([p, dcecImplication(p, q)])).toBe(true);
    expect(temporal.apply([p, dcecImplication(p, q)]).map(String)).toEqual(['q()']);
    expect(frame.canApply([p])).toBe(true);
    expect(frame.apply([p, dcecImplication(p, q)]).map(String)).toEqual(['p()']);
  });

  it('applies deontic D, permission-obligation duality, and distribution rules', () => {
    const obligation = new DcecDeonticFormula(DcecDeonticOperator.OBLIGATION, p, agent);
    const permission = new DcecDeonticFormula(DcecDeonticOperator.PERMISSION, p, agent);
    const distributed = new DcecDeonticFormula(DcecDeonticOperator.OBLIGATION, dcecConjunction(p, q), agent);

    expect(new DcecDeonticDRule().apply([obligation]).map(String)).toEqual(['¬(O[agent:Agent](¬(p())))']);
    expect(new DcecDeonticPermissionObligation().apply([permission, obligation]).map(String)).toEqual([
      '¬(O[agent:Agent](¬(p())))',
      '¬(P[agent:Agent](¬(p())))',
    ]);
    expect(new DcecDeonticDistribution().apply([distributed]).map(String)).toEqual([
      '(O[agent:Agent](p()) ∧ O[agent:Agent](q()))',
    ]);
  });

  it('applies combined knowledge-obligation and temporal-obligation rules', () => {
    const obligation = new DcecDeonticFormula(DcecDeonticOperator.OBLIGATION, p, agent);
    const knownObligation = new DcecCognitiveFormula(DcecCognitiveOperator.KNOWLEDGE, agent, obligation);

    expect(new DcecKnowledgeObligation().apply([knownObligation]).map(String)).toEqual([
      'O[agent:Agent](K(agent:Agent, p()))',
    ]);
    expect(new DcecTemporalObligation().apply([obligation]).map(String)).toEqual(['O[agent:Agent](p())']);
  });

  it('returns grouped advanced rule registries', () => {
    expect(getDcecModalRules().map((rule) => rule.name())).toEqual([
      'Modal K Axiom',
      'Modal T Axiom',
      'Modal S4 Axiom',
      'Necessitation',
    ]);
    expect(getDcecTemporalRules()).toHaveLength(2);
    expect(getDcecDeonticRules()).toHaveLength(3);
    expect(getDcecCombinedRules()).toHaveLength(2);
    expect(getAllDcecAdvancedRules()).toHaveLength(11);
  });
});

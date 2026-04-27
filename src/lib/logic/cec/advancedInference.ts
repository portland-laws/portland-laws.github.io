import {
  DcecAtomicFormula,
  DcecCognitiveFormula,
  DcecConnectiveFormula,
  DcecDeonticFormula,
  DcecFormula,
  DcecVariableTerm,
} from './dcecCore';
import {
  DcecCognitiveOperator,
  DcecDeonticOperator,
  DcecLogicalConnective,
  DcecSort,
  DcecVariable,
} from './dcecTypes';

export interface DcecAdvancedInferenceRule {
  name(): string;
  canApply(formulas: DcecFormula[]): boolean;
  apply(formulas: DcecFormula[]): DcecFormula[];
}

export class DcecModalKAxiom implements DcecAdvancedInferenceRule {
  name(): string {
    return 'Modal K Axiom';
  }

  canApply(formulas: DcecFormula[]): boolean {
    return formulas.some((formula) => isKnowledgeImplication(formula));
  }

  apply(formulas: DcecFormula[]): DcecFormula[] {
    return formulas.flatMap((formula) => {
      if (!isKnowledgeImplication(formula)) return [];
      const implication = formula.formula;
      const [antecedent, consequent] = implication.formulas;
      return [
        new DcecConnectiveFormula(DcecLogicalConnective.IMPLIES, [
          new DcecCognitiveFormula(DcecCognitiveOperator.KNOWLEDGE, formula.agent, antecedent),
          new DcecCognitiveFormula(DcecCognitiveOperator.KNOWLEDGE, formula.agent, consequent),
        ]),
      ];
    });
  }
}

export class DcecModalTAxiom implements DcecAdvancedInferenceRule {
  name(): string {
    return 'Modal T Axiom';
  }

  canApply(formulas: DcecFormula[]): boolean {
    return formulas.some(isKnowledgeFormula);
  }

  apply(formulas: DcecFormula[]): DcecFormula[] {
    return formulas.flatMap((formula) => (isKnowledgeFormula(formula) ? [formula.formula] : []));
  }
}

export class DcecModalS4Axiom implements DcecAdvancedInferenceRule {
  name(): string {
    return 'Modal S4 Axiom';
  }

  canApply(formulas: DcecFormula[]): boolean {
    return formulas.some(isKnowledgeFormula);
  }

  apply(formulas: DcecFormula[]): DcecFormula[] {
    return formulas.flatMap((formula) => (
      isKnowledgeFormula(formula)
        ? [new DcecCognitiveFormula(DcecCognitiveOperator.KNOWLEDGE, formula.agent, formula)]
        : []
    ));
  }
}

export class DcecModalNecessitation implements DcecAdvancedInferenceRule {
  private readonly systemAgent = new DcecVariableTerm(new DcecVariable('system', new DcecSort('System')));

  name(): string {
    return 'Necessitation';
  }

  canApply(formulas: DcecFormula[]): boolean {
    return formulas.length > 0;
  }

  apply(formulas: DcecFormula[]): DcecFormula[] {
    return formulas
      .filter((formula) => !(formula instanceof DcecCognitiveFormula))
      .slice(0, 5)
      .map((formula) => new DcecCognitiveFormula(DcecCognitiveOperator.KNOWLEDGE, this.systemAgent, formula));
  }
}

export class DcecTemporalInduction implements DcecAdvancedInferenceRule {
  name(): string {
    return 'Temporal Induction';
  }

  canApply(formulas: DcecFormula[]): boolean {
    return formulas.length >= 2 && formulas.some(isImplicationFormula);
  }

  apply(formulas: DcecFormula[]): DcecFormula[] {
    const results: DcecFormula[] = [];
    for (const candidate of formulas) {
      for (const implication of formulas) {
        if (!isImplicationFormula(implication)) continue;
        const [antecedent, consequent] = implication.formulas;
        if (candidate.toString() === antecedent.toString()) results.push(consequent);
      }
    }
    return results.slice(0, 3);
  }
}

export class DcecFrameAxiom implements DcecAdvancedInferenceRule {
  name(): string {
    return 'Frame Axiom';
  }

  canApply(formulas: DcecFormula[]): boolean {
    return formulas.length > 0;
  }

  apply(formulas: DcecFormula[]): DcecFormula[] {
    return formulas.filter((formula): formula is DcecAtomicFormula => formula instanceof DcecAtomicFormula).slice(0, 5);
  }
}

export class DcecDeonticDRule implements DcecAdvancedInferenceRule {
  name(): string {
    return 'Deontic D Axiom';
  }

  canApply(formulas: DcecFormula[]): boolean {
    return formulas.some(isObligationFormula);
  }

  apply(formulas: DcecFormula[]): DcecFormula[] {
    return formulas.flatMap((formula) => {
      if (!isObligationFormula(formula)) return [];
      const negatedInner = new DcecConnectiveFormula(DcecLogicalConnective.NOT, [formula.formula]);
      const obligationOfNegation = new DcecDeonticFormula(DcecDeonticOperator.OBLIGATION, negatedInner, formula.agent);
      return [new DcecConnectiveFormula(DcecLogicalConnective.NOT, [obligationOfNegation])];
    });
  }
}

export class DcecDeonticPermissionObligation implements DcecAdvancedInferenceRule {
  name(): string {
    return 'Permission-Obligation Duality';
  }

  canApply(formulas: DcecFormula[]): boolean {
    return formulas.some((formula) => formula instanceof DcecDeonticFormula
      && (formula.operator === DcecDeonticOperator.PERMISSION || formula.operator === DcecDeonticOperator.OBLIGATION));
  }

  apply(formulas: DcecFormula[]): DcecFormula[] {
    return formulas.flatMap((formula) => {
      if (!(formula instanceof DcecDeonticFormula)) return [];
      const negatedInner = new DcecConnectiveFormula(DcecLogicalConnective.NOT, [formula.formula]);
      if (formula.operator === DcecDeonticOperator.PERMISSION) {
        const obligationOfNegation = new DcecDeonticFormula(DcecDeonticOperator.OBLIGATION, negatedInner, formula.agent);
        return [new DcecConnectiveFormula(DcecLogicalConnective.NOT, [obligationOfNegation])];
      }
      if (formula.operator === DcecDeonticOperator.OBLIGATION) {
        const permissionOfNegation = new DcecDeonticFormula(DcecDeonticOperator.PERMISSION, negatedInner, formula.agent);
        return [new DcecConnectiveFormula(DcecLogicalConnective.NOT, [permissionOfNegation])];
      }
      return [];
    });
  }
}

export class DcecDeonticDistribution implements DcecAdvancedInferenceRule {
  name(): string {
    return 'Deontic Distribution';
  }

  canApply(formulas: DcecFormula[]): boolean {
    return formulas.some(isObligationConjunction);
  }

  apply(formulas: DcecFormula[]): DcecFormula[] {
    return formulas.flatMap((formula) => {
      if (!isObligationConjunction(formula)) return [];
      const obligations = formula.formula.formulas.map(
        (conjunct) => new DcecDeonticFormula(formula.operator, conjunct, formula.agent),
      );
      return obligations.length >= 2 ? [new DcecConnectiveFormula(DcecLogicalConnective.AND, obligations)] : [];
    });
  }
}

export class DcecKnowledgeObligation implements DcecAdvancedInferenceRule {
  name(): string {
    return 'Knowledge-Obligation Interaction';
  }

  canApply(formulas: DcecFormula[]): boolean {
    return formulas.some(isKnowledgeOfDeonticFormula);
  }

  apply(formulas: DcecFormula[]): DcecFormula[] {
    return formulas.flatMap((formula) => {
      if (!isKnowledgeOfDeonticFormula(formula)) return [];
      const deontic = formula.formula;
      const knownContent = new DcecCognitiveFormula(DcecCognitiveOperator.KNOWLEDGE, formula.agent, deontic.formula);
      return [new DcecDeonticFormula(deontic.operator, knownContent, deontic.agent)];
    });
  }
}

export class DcecTemporalObligation implements DcecAdvancedInferenceRule {
  name(): string {
    return 'Temporal-Deontic Interaction';
  }

  canApply(formulas: DcecFormula[]): boolean {
    return formulas.some((formula) => formula instanceof DcecDeonticFormula);
  }

  apply(formulas: DcecFormula[]): DcecFormula[] {
    return formulas.filter((formula): formula is DcecDeonticFormula => formula instanceof DcecDeonticFormula).slice(0, 3);
  }
}

export function getAllDcecAdvancedRules(): DcecAdvancedInferenceRule[] {
  return [
    ...getDcecModalRules(),
    ...getDcecTemporalRules(),
    ...getDcecDeonticRules(),
    ...getDcecCombinedRules(),
  ];
}

export function getDcecModalRules(): DcecAdvancedInferenceRule[] {
  return [
    new DcecModalKAxiom(),
    new DcecModalTAxiom(),
    new DcecModalS4Axiom(),
    new DcecModalNecessitation(),
  ];
}

export function getDcecTemporalRules(): DcecAdvancedInferenceRule[] {
  return [new DcecTemporalInduction(), new DcecFrameAxiom()];
}

export function getDcecDeonticRules(): DcecAdvancedInferenceRule[] {
  return [
    new DcecDeonticDRule(),
    new DcecDeonticPermissionObligation(),
    new DcecDeonticDistribution(),
  ];
}

export function getDcecCombinedRules(): DcecAdvancedInferenceRule[] {
  return [new DcecKnowledgeObligation(), new DcecTemporalObligation()];
}

function isKnowledgeFormula(formula: DcecFormula): formula is DcecCognitiveFormula {
  return formula instanceof DcecCognitiveFormula && formula.operator === DcecCognitiveOperator.KNOWLEDGE;
}

function isImplicationFormula(formula: DcecFormula): formula is DcecConnectiveFormula {
  return formula instanceof DcecConnectiveFormula && formula.connective === DcecLogicalConnective.IMPLIES;
}

function isKnowledgeImplication(formula: DcecFormula): formula is DcecCognitiveFormula & { formula: DcecConnectiveFormula } {
  return isKnowledgeFormula(formula) && isImplicationFormula(formula.formula);
}

function isObligationFormula(formula: DcecFormula): formula is DcecDeonticFormula {
  return formula instanceof DcecDeonticFormula && formula.operator === DcecDeonticOperator.OBLIGATION;
}

function isObligationConjunction(formula: DcecFormula): formula is DcecDeonticFormula & { formula: DcecConnectiveFormula } {
  return isObligationFormula(formula)
    && formula.formula instanceof DcecConnectiveFormula
    && formula.formula.connective === DcecLogicalConnective.AND;
}

function isKnowledgeOfDeonticFormula(formula: DcecFormula): formula is DcecCognitiveFormula & { formula: DcecDeonticFormula } {
  return isKnowledgeFormula(formula) && formula.formula instanceof DcecDeonticFormula;
}

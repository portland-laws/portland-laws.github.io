import type { CecApplication, CecBinaryExpression, CecExpression, CecQuantifiedExpression, CecUnaryExpression } from './ast';
import { formatCecExpression } from './formatter';

export interface CecInferenceRule {
  name: string;
  description: string;
  arity: 1 | 2 | 3;
  canApply(...expressions: CecExpression[]): boolean;
  apply(...expressions: CecExpression[]): CecExpression;
}

export interface CecRuleApplication {
  rule: string;
  premises: CecExpression[];
  conclusion: CecExpression;
}

type CecRuleSpec = {
  name: string;
  description: string;
  arity: 1 | 2 | 3;
  canApply: (...expressions: CecExpression[]) => boolean;
  apply: (...expressions: CecExpression[]) => CecExpression;
};

export class CecRule implements CecInferenceRule {
  readonly name: string;
  readonly description: string;
  readonly arity: 1 | 2 | 3;
  private readonly canApplyImpl: CecRuleSpec['canApply'];
  private readonly applyImpl: CecRuleSpec['apply'];

  constructor(spec: CecRuleSpec) {
    this.name = spec.name;
    this.description = spec.description;
    this.arity = spec.arity;
    this.canApplyImpl = spec.canApply;
    this.applyImpl = spec.apply;
  }

  canApply(...expressions: CecExpression[]): boolean {
    return expressions.length === this.arity && this.canApplyImpl(...expressions);
  }

  apply(...expressions: CecExpression[]): CecExpression {
    if (!this.canApply(...expressions)) {
      throw new Error(`CEC rule ${this.name} cannot be applied to the supplied expressions`);
    }
    return this.applyImpl(...expressions);
  }
}

export const CecModusPonensRule = new CecRule({
  name: 'CecModusPonens',
  description: 'From phi and (implies phi psi), infer psi',
  arity: 2,
  canApply: (left, right) => isBinary(right, 'implies') && cecExpressionEquals(right.left, left),
  apply: (_left, right) => (right as CecBinaryExpression).right,
});

export const CecHypotheticalSyllogismRule = new CecRule({
  name: 'CecHypotheticalSyllogism',
  description: 'From (implies phi psi) and (implies psi chi), infer (implies phi chi)',
  arity: 2,
  canApply: (first, second) =>
    isBinary(first, 'implies') &&
    isBinary(second, 'implies') &&
    cecExpressionEquals(first.right, second.left),
  apply: (first, second) => ({
    kind: 'binary',
    operator: 'implies',
    left: (first as CecBinaryExpression).left,
    right: (second as CecBinaryExpression).right,
  }),
});

export const CecConjunctionIntroductionRule = new CecRule({
  name: 'CecConjunctionIntroduction',
  description: 'From phi and psi, infer (and phi psi)',
  arity: 2,
  canApply: (left, right) => !cecExpressionEquals(left, right),
  apply: (left, right) => ({ kind: 'binary', operator: 'and', left, right }),
});

export const CecConjunctionEliminationLeftRule = new CecRule({
  name: 'CecConjunctionEliminationLeft',
  description: 'From (and phi psi), infer phi',
  arity: 1,
  canApply: (expression) => isBinary(expression, 'and'),
  apply: (expression) => (expression as CecBinaryExpression).left,
});

export const CecConjunctionEliminationRightRule = new CecRule({
  name: 'CecConjunctionEliminationRight',
  description: 'From (and phi psi), infer psi',
  arity: 1,
  canApply: (expression) => isBinary(expression, 'and'),
  apply: (expression) => (expression as CecBinaryExpression).right,
});

export const CecDoubleNegationEliminationRule = new CecRule({
  name: 'CecDoubleNegationElimination',
  description: 'From (not (not phi)), infer phi',
  arity: 1,
  canApply: (expression) =>
    isUnary(expression, 'not') && expression.expression.kind === 'unary' && expression.expression.operator === 'not',
  apply: (expression) => {
    if (!isUnary(expression, 'not') || !isUnary(expression.expression, 'not')) {
      throw new Error('Invalid CEC double negation premise');
    }
    return expression.expression.expression;
  },
});

export const CecTemporalTRule = new CecRule({
  name: 'CecTemporalT',
  description: 'From (always phi), infer phi',
  arity: 1,
  canApply: (expression) => isUnary(expression, 'always'),
  apply: (expression) => {
    if (!isUnary(expression, 'always')) throw new Error('Invalid CEC temporal premise');
    return expression.expression;
  },
});

export const CecEventuallyIntroductionRule = new CecRule({
  name: 'CecEventuallyIntroduction',
  description: 'From phi, infer (eventually phi)',
  arity: 1,
  canApply: (expression) => !isUnary(expression, 'eventually'),
  apply: (expression) => ({ kind: 'unary', operator: 'eventually', expression }),
});

export const CecDeonticDRule = new CecRule({
  name: 'CecDeonticD',
  description: 'From (O phi), infer (P phi)',
  arity: 1,
  canApply: (expression) => isUnary(expression, 'O'),
  apply: (expression) => {
    if (!isUnary(expression, 'O')) throw new Error('Invalid CEC deontic premise');
    return { kind: 'unary', operator: 'P', expression: expression.expression };
  },
});

export const CecProhibitionEquivalenceRule = new CecRule({
  name: 'CecProhibitionEquivalence',
  description: 'From (F phi), infer (O (not phi))',
  arity: 1,
  canApply: (expression) => isUnary(expression, 'F'),
  apply: (expression) => {
    if (!isUnary(expression, 'F')) throw new Error('Invalid CEC prohibition premise');
    return {
      kind: 'unary',
      operator: 'O',
      expression: { kind: 'unary', operator: 'not', expression: expression.expression },
    };
  },
});

export const CecProhibitionFromObligationRule = new CecRule({
  name: 'CecProhibitionFromObligation',
  description: 'From (O (not phi)), infer (F phi)',
  arity: 1,
  canApply: (expression) =>
    isUnary(expression, 'O') &&
    expression.expression.kind === 'unary' &&
    expression.expression.operator === 'not',
  apply: (expression) => {
    if (!isUnary(expression, 'O') || !isUnary(expression.expression, 'not')) {
      throw new Error('Invalid CEC obligation prohibition premise');
    }
    return { kind: 'unary', operator: 'F', expression: expression.expression.expression };
  },
});

export const CecUniversalModusPonensRule = new CecRule({
  name: 'CecUniversalModusPonens',
  description: 'From (forall x (implies phi(x) psi(x))) and phi(a), infer psi(a)',
  arity: 2,
  canApply: (universal, premise) => {
    if (!isQuantified(universal, 'forall') || !isBinary(universal.expression, 'implies')) {
      return false;
    }
    return matchCecExpressionForVariable(universal.expression.left, premise, universal.variable) !== undefined;
  },
  apply: (universal, premise) => {
    if (!isQuantified(universal, 'forall') || !isBinary(universal.expression, 'implies')) {
      throw new Error('Invalid CEC universal premise');
    }
    const binding = matchCecExpressionForVariable(universal.expression.left, premise, universal.variable);
    if (!binding) throw new Error('CEC universal premise does not match supplied fact');
    return substituteCecAtom(universal.expression.right, universal.variable, binding);
  },
});

export const CecExistentialInstantiationRule = new CecRule({
  name: 'CecExistentialInstantiation',
  description: 'From (exists x phi(x)), infer phi(skolem_x)',
  arity: 1,
  canApply: (expression) => isQuantified(expression, 'exists'),
  apply: (expression) => {
    if (!isQuantified(expression, 'exists')) throw new Error('Invalid CEC existential premise');
    return substituteCecAtom(expression.expression, expression.variable, `skolem_${expression.variable}`);
  },
});

export const CecExistentialGeneralizationRule = new CecRule({
  name: 'CecExistentialGeneralization',
  description: 'From phi(a), infer (exists x phi(x)) by replacing the first atom argument',
  arity: 1,
  canApply: (expression) => findFirstSubstitutableAtom(expression) !== undefined,
  apply: (expression) => {
    const atom = findFirstSubstitutableAtom(expression);
    if (!atom) throw new Error('No CEC atom available for existential generalization');
    return {
      kind: 'quantified',
      quantifier: 'exists',
      variable: 'x',
      expression: substituteCecAtom(expression, atom, 'x'),
    };
  },
});

export const CecUniversalGeneralizationRule = new CecRule({
  name: 'CecUniversalGeneralization',
  description: 'From phi(x), infer (forall x phi(x)) for a free variable-like atom',
  arity: 1,
  canApply: (expression) => findFirstVariableLikeAtom(expression) !== undefined,
  apply: (expression) => {
    const variable = findFirstVariableLikeAtom(expression);
    if (!variable) throw new Error('No CEC variable-like atom available for universal generalization');
    return {
      kind: 'quantified',
      quantifier: 'forall',
      variable,
      expression,
    };
  },
});

export const CecBeliefDistributionRule = new CecRule({
  name: 'CecBeliefDistribution',
  description: 'From (B agent (and phi psi)), infer (and (B agent phi) (B agent psi))',
  arity: 1,
  canApply: (expression) => isCognitive(expression, 'B') && isBinary(expression.args[1], 'and'),
  apply: (expression) => {
    const belief = requireCognitive(expression, 'B');
    if (!isBinary(belief.args[1], 'and')) throw new Error('Invalid CEC belief distribution premise');
    return {
      kind: 'binary',
      operator: 'and',
      left: cognitiveApplication('B', belief.args[0], belief.args[1].left),
      right: cognitiveApplication('B', belief.args[0], belief.args[1].right),
    };
  },
});

export const CecKnowledgeImpliesBeliefRule = new CecRule({
  name: 'CecKnowledgeImpliesBelief',
  description: 'From (K agent phi), infer (B agent phi)',
  arity: 1,
  canApply: (expression) => isCognitive(expression, 'K'),
  apply: (expression) => {
    const knowledge = requireCognitive(expression, 'K');
    return cognitiveApplication('B', knowledge.args[0], knowledge.args[1]);
  },
});

export const CecBeliefMonotonicityRule = new CecRule({
  name: 'CecBeliefMonotonicity',
  description: 'From (B agent phi) and (implies phi psi), infer (B agent psi)',
  arity: 2,
  canApply: (belief, implication) =>
    isCognitive(belief, 'B') && isBinary(implication, 'implies') && cecExpressionEquals(belief.args[1], implication.left),
  apply: (belief, implication) => {
    const premise = requireCognitive(belief, 'B');
    if (!isBinary(implication, 'implies')) throw new Error('Invalid CEC belief monotonicity implication');
    return cognitiveApplication('B', premise.args[0], implication.right);
  },
});

export const CecIntentionCommitmentRule = new CecRule({
  name: 'CecIntentionCommitment',
  description: 'From (I agent phi) and (B agent (implies phi psi)), infer (I agent psi)',
  arity: 2,
  canApply: (intention, belief) =>
    isCognitive(intention, 'I') &&
    isCognitive(belief, 'B') &&
    cecExpressionEquals(intention.args[0], belief.args[0]) &&
    isBinary(belief.args[1], 'implies') &&
    cecExpressionEquals(intention.args[1], belief.args[1].left),
  apply: (intention, belief) => {
    const intent = requireCognitive(intention, 'I');
    const believed = requireCognitive(belief, 'B');
    if (!isBinary(believed.args[1], 'implies')) throw new Error('Invalid CEC intention commitment premise');
    return cognitiveApplication('I', intent.args[0], believed.args[1].right);
  },
});

export const CecBeliefConjunctionRule = new CecRule({
  name: 'CecBeliefConjunction',
  description: 'From (B agent phi) and (B agent psi), infer (B agent (and phi psi))',
  arity: 2,
  canApply: (left, right) =>
    isCognitive(left, 'B') &&
    isCognitive(right, 'B') &&
    cecExpressionEquals(left.args[0], right.args[0]) &&
    !cecExpressionEquals(left.args[1], right.args[1]),
  apply: (left, right) => {
    const leftBelief = requireCognitive(left, 'B');
    const rightBelief = requireCognitive(right, 'B');
    return cognitiveApplication('B', leftBelief.args[0], {
      kind: 'binary',
      operator: 'and',
      left: leftBelief.args[1],
      right: rightBelief.args[1],
    });
  },
});

export const CecKnowledgeDistributionRule = new CecRule({
  name: 'CecKnowledgeDistribution',
  description: 'From (K agent (and phi psi)), infer (and (K agent phi) (K agent psi))',
  arity: 1,
  canApply: (expression) => isCognitive(expression, 'K') && isBinary(expression.args[1], 'and'),
  apply: (expression) => {
    const knowledge = requireCognitive(expression, 'K');
    if (!isBinary(knowledge.args[1], 'and')) throw new Error('Invalid CEC knowledge distribution premise');
    return {
      kind: 'binary',
      operator: 'and',
      left: cognitiveApplication('K', knowledge.args[0], knowledge.args[1].left),
      right: cognitiveApplication('K', knowledge.args[0], knowledge.args[1].right),
    };
  },
});

export const CecIntentionMeansEndRule = new CecRule({
  name: 'CecIntentionMeansEnd',
  description: 'From (I agent goal) and (B agent (implies action goal)), infer (I agent action)',
  arity: 2,
  canApply: (intention, belief) =>
    isCognitive(intention, 'I') &&
    isCognitive(belief, 'B') &&
    cecExpressionEquals(intention.args[0], belief.args[0]) &&
    isBinary(belief.args[1], 'implies') &&
    cecExpressionEquals(intention.args[1], belief.args[1].right),
  apply: (intention, belief) => {
    const intent = requireCognitive(intention, 'I');
    const believed = requireCognitive(belief, 'B');
    if (!isBinary(believed.args[1], 'implies')) throw new Error('Invalid CEC intention means-end premise');
    return cognitiveApplication('I', intent.args[0], believed.args[1].left);
  },
});

export const CecPerceptionImpliesKnowledgeRule = new CecRule({
  name: 'CecPerceptionImpliesKnowledge',
  description: 'From (Perceives agent phi), infer (K agent phi)',
  arity: 1,
  canApply: (expression) => isCognitive(expression, 'Perceives') || isCognitive(expression, 'Perception'),
  apply: (expression) => {
    const perception = requireAnyCognitive(expression, ['Perceives', 'Perception']);
    return cognitiveApplication('K', perception.args[0], perception.args[1]);
  },
});

export const CecBeliefNegationRule = new CecRule({
  name: 'CecBeliefNegation',
  description: 'From (B agent (not phi)), infer (not (B agent phi))',
  arity: 1,
  canApply: (expression) => isCognitive(expression, 'B') && isUnary(expression.args[1], 'not'),
  apply: (expression) => {
    const belief = requireCognitive(expression, 'B');
    if (!isUnary(belief.args[1], 'not')) throw new Error('Invalid CEC belief negation premise');
    return { kind: 'unary', operator: 'not', expression: cognitiveApplication('B', belief.args[0], belief.args[1].expression) };
  },
});

export const CecKnowledgeConjunctionRule = new CecRule({
  name: 'CecKnowledgeConjunction',
  description: 'From (K agent phi) and (K agent psi), infer (K agent (and phi psi))',
  arity: 2,
  canApply: (left, right) =>
    isCognitive(left, 'K') &&
    isCognitive(right, 'K') &&
    cecExpressionEquals(left.args[0], right.args[0]) &&
    !cecExpressionEquals(left.args[1], right.args[1]),
  apply: (left, right) => {
    const leftKnowledge = requireCognitive(left, 'K');
    const rightKnowledge = requireCognitive(right, 'K');
    return cognitiveApplication('K', leftKnowledge.args[0], {
      kind: 'binary',
      operator: 'and',
      left: leftKnowledge.args[1],
      right: rightKnowledge.args[1],
    });
  },
});

export const CecIntentionPersistenceRule = new CecRule({
  name: 'CecIntentionPersistence',
  description: 'From (I agent phi) and (not (B agent phi)), infer (I agent phi)',
  arity: 2,
  canApply: (intention, notBelief) =>
    isCognitive(intention, 'I') &&
    isUnary(notBelief, 'not') &&
    isCognitive(notBelief.expression, 'B') &&
    cecExpressionEquals(intention.args[0], notBelief.expression.args[0]) &&
    cecExpressionEquals(intention.args[1], notBelief.expression.args[1]),
  apply: (intention) => intention,
});

export const CecBeliefRevisionRule = new CecRule({
  name: 'CecBeliefRevision',
  description: 'From (B agent phi) and (Perceives agent (not phi)), infer (B agent (not phi))',
  arity: 2,
  canApply: (belief, perception) =>
    isCognitive(belief, 'B') &&
    (isCognitive(perception, 'Perceives') || isCognitive(perception, 'Perception')) &&
    cecExpressionEquals(belief.args[0], perception.args[0]) &&
    isUnary(perception.args[1], 'not') &&
    cecExpressionEquals(belief.args[1], perception.args[1].expression),
  apply: (belief, perception) => {
    const premise = requireCognitive(belief, 'B');
    const perceived = requireAnyCognitive(perception, ['Perceives', 'Perception']);
    return cognitiveApplication('B', premise.args[0], perceived.args[1]);
  },
});

export const CecKnowledgeMonotonicityRule = new CecRule({
  name: 'CecKnowledgeMonotonicity',
  description: 'From (K agent phi) and (implies phi psi), infer (K agent psi)',
  arity: 2,
  canApply: (knowledge, implication) =>
    isCognitive(knowledge, 'K') && isBinary(implication, 'implies') && cecExpressionEquals(knowledge.args[1], implication.left),
  apply: (knowledge, implication) => {
    const premise = requireCognitive(knowledge, 'K');
    if (!isBinary(implication, 'implies')) throw new Error('Invalid CEC knowledge monotonicity implication');
    return cognitiveApplication('K', premise.args[0], implication.right);
  },
});

export const CecResolutionRule = new CecRule({
  name: 'CecResolution',
  description: 'From (or phi psi) and (or (not phi) chi), infer (or psi chi)',
  arity: 2,
  canApply: (left, right) => findComplementaryDisjunctPair(left, right) !== undefined,
  apply: (left, right) => {
    const pair = findComplementaryDisjunctPair(left, right);
    if (!pair) throw new Error('Invalid CEC resolution clauses');
    const remaining = [
      ...getDisjuncts(left).filter((_, index) => index !== pair.leftIndex),
      ...getDisjuncts(right).filter((_, index) => index !== pair.rightIndex),
    ];
    return buildDisjunction(uniqueExpressions(remaining));
  },
});

export const CecUnitResolutionRule = new CecRule({
  name: 'CecUnitResolution',
  description: 'From phi and (or (not phi) psi), infer psi',
  arity: 2,
  canApply: (unit, clause) =>
    !isBinary(unit, 'or') &&
    isBinary(clause, 'or') &&
    getDisjuncts(clause).some((literal) => isNegationOf(literal, unit)),
  apply: (unit, clause) => {
    if (!isBinary(clause, 'or')) throw new Error('Invalid CEC unit resolution clause');
    return buildDisjunction(getDisjuncts(clause).filter((literal) => !isNegationOf(literal, unit)));
  },
});

export const CecFactoringRule = new CecRule({
  name: 'CecFactoring',
  description: 'From a disjunction with duplicate literals, infer the deduplicated clause',
  arity: 1,
  canApply: (expression) => isBinary(expression, 'or') && uniqueExpressions(getDisjuncts(expression)).length < getDisjuncts(expression).length,
  apply: (expression) => {
    if (!isBinary(expression, 'or')) throw new Error('Invalid CEC factoring clause');
    return buildDisjunction(uniqueExpressions(getDisjuncts(expression)));
  },
});

export const CecSubsumptionRule = new CecRule({
  name: 'CecSubsumption',
  description: 'If clause C1 is a strict subset of C2, infer the shorter subsuming clause',
  arity: 2,
  canApply: (left, right) => clauseSubsumes(left, right) || clauseSubsumes(right, left),
  apply: (left, right) => {
    if (clauseSubsumes(left, right)) return left;
    if (clauseSubsumes(right, left)) return right;
    throw new Error('Invalid CEC subsumption clauses');
  },
});

export const CecCaseAnalysisRule = new CecRule({
  name: 'CecCaseAnalysis',
  description: 'From (or phi psi), (implies phi chi), and (implies psi chi), infer chi',
  arity: 3,
  canApply: (disjunction, leftImplication, rightImplication) => {
    if (!isBinary(disjunction, 'or') || !isBinary(leftImplication, 'implies') || !isBinary(rightImplication, 'implies')) return false;
    const [leftCase, rightCase] = getDisjuncts(disjunction);
    return Boolean(leftCase && rightCase) &&
      cecExpressionEquals(leftImplication.left, leftCase) &&
      cecExpressionEquals(rightImplication.left, rightCase) &&
      cecExpressionEquals(leftImplication.right, rightImplication.right);
  },
  apply: (_disjunction, leftImplication) => {
    if (!isBinary(leftImplication, 'implies')) throw new Error('Invalid CEC case analysis implication');
    return leftImplication.right;
  },
});

export const CecProofByContradictionRule = new CecRule({
  name: 'CecProofByContradiction',
  description: 'From phi and (not phi), infer contradiction',
  arity: 2,
  canApply: (left, right) => isNegationOf(left, right) || isNegationOf(right, left),
  apply: () => ({ kind: 'atom', name: 'contradiction' }),
});

export const CecBiconditionalIntroductionRule = new CecRule({
  name: 'CecBiconditionalIntroduction',
  description: 'From (implies phi psi) and (implies psi phi), infer (iff phi psi)',
  arity: 2,
  canApply: (left, right) =>
    isBinary(left, 'implies') &&
    isBinary(right, 'implies') &&
    cecExpressionEquals(left.left, right.right) &&
    cecExpressionEquals(left.right, right.left),
  apply: (left) => {
    if (!isBinary(left, 'implies')) throw new Error('Invalid CEC biconditional introduction premise');
    return { kind: 'binary', operator: 'iff', left: left.left, right: left.right };
  },
});

export const CecBiconditionalEliminationRule = new CecRule({
  name: 'CecBiconditionalElimination',
  description: 'From (iff phi psi), infer (and (implies phi psi) (implies psi phi))',
  arity: 1,
  canApply: (expression) => isBinary(expression, 'iff'),
  apply: (expression) => {
    if (!isBinary(expression, 'iff')) throw new Error('Invalid CEC biconditional elimination premise');
    return {
      kind: 'binary',
      operator: 'and',
      left: { kind: 'binary', operator: 'implies', left: expression.left, right: expression.right },
      right: { kind: 'binary', operator: 'implies', left: expression.right, right: expression.left },
    };
  },
});

export const CecConstructiveDilemmaRule = new CecRule({
  name: 'CecConstructiveDilemma',
  description: 'From (implies phi psi), (implies chi omega), and (or phi chi), infer (or psi omega)',
  arity: 3,
  canApply: (...expressions) => findDilemmaPremises(expressions, false) !== undefined,
  apply: (...expressions) => {
    const premises = findDilemmaPremises(expressions, false);
    if (!premises) throw new Error('Invalid CEC constructive dilemma premises');
    return buildDisjunction([premises.first.right, premises.second.right]);
  },
});

export const CecDestructiveDilemmaRule = new CecRule({
  name: 'CecDestructiveDilemma',
  description: 'From (implies phi psi), (implies chi omega), and (or (not psi) (not omega)), infer (or (not phi) (not chi))',
  arity: 3,
  canApply: (...expressions) => findDilemmaPremises(expressions, true) !== undefined,
  apply: (...expressions) => {
    const premises = findDilemmaPremises(expressions, true);
    if (!premises) throw new Error('Invalid CEC destructive dilemma premises');
    return buildDisjunction([
      { kind: 'unary', operator: 'not', expression: premises.first.left },
      { kind: 'unary', operator: 'not', expression: premises.second.left },
    ]);
  },
});

export const CecExportationRule = new CecRule({
  name: 'CecExportation',
  description: 'From (implies (and phi psi) chi), infer (implies phi (implies psi chi))',
  arity: 1,
  canApply: (expression) => isBinary(expression, 'implies') && isBinary(expression.left, 'and'),
  apply: (expression) => {
    if (!isBinary(expression, 'implies') || !isBinary(expression.left, 'and')) {
      throw new Error('Invalid CEC exportation premise');
    }
    return {
      kind: 'binary',
      operator: 'implies',
      left: expression.left.left,
      right: { kind: 'binary', operator: 'implies', left: expression.left.right, right: expression.right },
    };
  },
});

export const CecAbsorptionRule = new CecRule({
  name: 'CecAbsorption',
  description: 'From (implies phi psi), infer (implies phi (and phi psi))',
  arity: 1,
  canApply: (expression) => isBinary(expression, 'implies'),
  apply: (expression) => {
    if (!isBinary(expression, 'implies')) throw new Error('Invalid CEC absorption premise');
    return {
      kind: 'binary',
      operator: 'implies',
      left: expression.left,
      right: { kind: 'binary', operator: 'and', left: expression.left, right: expression.right },
    };
  },
});

export const CecAdditionRule = new CecRule({
  name: 'CecAddition',
  description: 'From phi and psi, infer (or phi psi); kept opt-in because it generates new disjunctions',
  arity: 2,
  canApply: (left, right) => !cecExpressionEquals(left, right),
  apply: (left, right) => buildDisjunction([left, right]),
});

export const CecTautologyRule = new CecRule({
  name: 'CecTautology',
  description: 'From (or phi phi), infer phi',
  arity: 1,
  canApply: (expression) =>
    isBinary(expression, 'or') &&
    getDisjuncts(expression).length > 1 &&
    uniqueExpressions(getDisjuncts(expression)).length === 1,
  apply: (expression) => {
    if (!isBinary(expression, 'or')) throw new Error('Invalid CEC tautology premise');
    return getDisjuncts(expression)[0];
  },
});

export const CecCommutativityConjunctionRule = new CecRule({
  name: 'CecCommutativityConjunction',
  description: 'From (and phi psi), infer (and psi phi)',
  arity: 1,
  canApply: (expression) => isBinary(expression, 'and') && !cecExpressionEquals(expression.left, expression.right),
  apply: (expression) => {
    if (!isBinary(expression, 'and')) throw new Error('Invalid CEC conjunction commutativity premise');
    return { kind: 'binary', operator: 'and', left: expression.right, right: expression.left };
  },
});

export function getAllCecRules(): CecInferenceRule[] {
  return [
    CecModusPonensRule,
    CecHypotheticalSyllogismRule,
    CecConjunctionEliminationLeftRule,
    CecConjunctionEliminationRightRule,
    CecDoubleNegationEliminationRule,
    CecTemporalTRule,
    CecDeonticDRule,
    CecProhibitionEquivalenceRule,
    CecProhibitionFromObligationRule,
    CecUniversalModusPonensRule,
    CecExistentialInstantiationRule,
  ];
}

export function getResolutionCecRules(): CecInferenceRule[] {
  return [
    CecResolutionRule,
    CecUnitResolutionRule,
    CecFactoringRule,
    CecSubsumptionRule,
    CecCaseAnalysisRule,
    CecProofByContradictionRule,
  ];
}

export function getSpecializedCecRules(): CecInferenceRule[] {
  return [
    CecBiconditionalIntroductionRule,
    CecBiconditionalEliminationRule,
    CecConstructiveDilemmaRule,
    CecDestructiveDilemmaRule,
    CecExportationRule,
    CecAbsorptionRule,
    CecTautologyRule,
    CecCommutativityConjunctionRule,
  ];
}

export function getCognitiveCecRules(): CecInferenceRule[] {
  return [
    CecBeliefDistributionRule,
    CecKnowledgeImpliesBeliefRule,
    CecBeliefMonotonicityRule,
    CecIntentionCommitmentRule,
    CecKnowledgeDistributionRule,
    CecIntentionMeansEndRule,
    CecPerceptionImpliesKnowledgeRule,
    CecBeliefNegationRule,
    CecIntentionPersistenceRule,
    CecBeliefRevisionRule,
    CecKnowledgeMonotonicityRule,
  ];
}

export function getGenerativeCecRules(): CecInferenceRule[] {
  return [
    CecConjunctionIntroductionRule,
    CecEventuallyIntroductionRule,
    CecExistentialGeneralizationRule,
    CecUniversalGeneralizationRule,
    CecBeliefConjunctionRule,
    CecKnowledgeConjunctionRule,
    CecAdditionRule,
  ];
}

export function applyCecRules(
  expressions: CecExpression[],
  rules: CecInferenceRule[] = getAllCecRules(),
): CecRuleApplication[] {
  const applications: CecRuleApplication[] = [];
  for (const rule of rules) {
    if (rule.arity === 1) {
      for (const expression of expressions) {
        if (rule.canApply(expression)) {
          applications.push({ rule: rule.name, premises: [expression], conclusion: rule.apply(expression) });
        }
      }
    } else if (rule.arity === 2) {
      for (const left of expressions) {
        for (const right of expressions) {
          if (rule.canApply(left, right)) {
            applications.push({ rule: rule.name, premises: [left, right], conclusion: rule.apply(left, right) });
          }
        }
      }
    } else {
      for (const first of expressions) {
        for (const second of expressions) {
          for (const third of expressions) {
            if (rule.canApply(first, second, third)) {
              applications.push({ rule: rule.name, premises: [first, second, third], conclusion: rule.apply(first, second, third) });
            }
          }
        }
      }
    }
  }
  return applications;
}

export function cecExpressionEquals(left: CecExpression, right: CecExpression): boolean {
  return cecExpressionKey(left) === cecExpressionKey(right);
}

export function cecExpressionKey(expression: CecExpression): string {
  return formatCecExpression(expression);
}

function isBinary(expression: CecExpression, operator: CecBinaryExpression['operator']): expression is CecBinaryExpression {
  return expression.kind === 'binary' && expression.operator === operator;
}

function isUnary(expression: CecExpression, operator: CecUnaryExpression['operator']): expression is CecUnaryExpression {
  return expression.kind === 'unary' && expression.operator === operator;
}

function isQuantified(
  expression: CecExpression,
  quantifier: CecQuantifiedExpression['quantifier'],
): expression is CecQuantifiedExpression {
  return expression.kind === 'quantified' && expression.quantifier === quantifier;
}

function isCognitive(expression: CecExpression, operator: string): expression is CecApplication {
  return expression.kind === 'application' && expression.name === operator && expression.args.length === 2;
}

function requireCognitive(expression: CecExpression, operator: string): CecApplication {
  if (!isCognitive(expression, operator)) throw new Error(`Invalid CEC cognitive ${operator} premise`);
  return expression;
}

function requireAnyCognitive(expression: CecExpression, operators: string[]): CecApplication {
  if (expression.kind === 'application' && operators.includes(expression.name) && expression.args.length === 2) return expression;
  throw new Error(`Invalid CEC cognitive premise; expected one of ${operators.join(', ')}`);
}

function cognitiveApplication(operator: string, agent: CecExpression, body: CecExpression): CecApplication {
  return { kind: 'application', name: operator, args: [agent, body] };
}

function getDisjuncts(expression: CecExpression): CecExpression[] {
  if (!isBinary(expression, 'or')) return [expression];
  return [...getDisjuncts(expression.left), ...getDisjuncts(expression.right)];
}

function buildDisjunction(expressions: CecExpression[]): CecExpression {
  if (expressions.length === 0) return { kind: 'atom', name: 'contradiction' };
  return expressions.slice(1).reduce<CecExpression>((left, right) => ({ kind: 'binary', operator: 'or', left, right }), expressions[0]);
}

function isNegationOf(left: CecExpression, right: CecExpression): boolean {
  return isUnary(left, 'not') && cecExpressionEquals(left.expression, right);
}

function findComplementaryDisjunctPair(
  left: CecExpression,
  right: CecExpression,
): { leftIndex: number; rightIndex: number } | undefined {
  if (!isBinary(left, 'or') || !isBinary(right, 'or')) return undefined;
  const leftDisjuncts = getDisjuncts(left);
  const rightDisjuncts = getDisjuncts(right);
  for (let leftIndex = 0; leftIndex < leftDisjuncts.length; leftIndex += 1) {
    for (let rightIndex = 0; rightIndex < rightDisjuncts.length; rightIndex += 1) {
      if (isNegationOf(leftDisjuncts[leftIndex], rightDisjuncts[rightIndex]) || isNegationOf(rightDisjuncts[rightIndex], leftDisjuncts[leftIndex])) {
        return { leftIndex, rightIndex };
      }
    }
  }
  return undefined;
}

function uniqueExpressions(expressions: CecExpression[]): CecExpression[] {
  const seen = new Set<string>();
  return expressions.filter((expression) => {
    const key = cecExpressionKey(expression);
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function clauseSubsumes(left: CecExpression, right: CecExpression): boolean {
  const leftKeys = getDisjuncts(left).map(cecExpressionKey);
  const rightKeys = getDisjuncts(right).map(cecExpressionKey);
  return leftKeys.length < rightKeys.length && leftKeys.every((key) => rightKeys.includes(key));
}

function matchCecExpressionForVariable(
  pattern: CecExpression,
  target: CecExpression,
  variableName: string,
): string | undefined {
  const bindings = new Map<string, string>();
  return matchCecExpression(pattern, target, variableName, bindings) ? bindings.get(variableName) : undefined;
}

function matchCecExpression(
  pattern: CecExpression,
  target: CecExpression,
  variableName: string,
  bindings: Map<string, string>,
): boolean {
  if (pattern.kind === 'atom' && pattern.name === variableName) {
    if (target.kind !== 'atom') return false;
    const existing = bindings.get(variableName);
    if (!existing) {
      bindings.set(variableName, target.name);
      return true;
    }
    return existing === target.name;
  }
  if (pattern.kind !== target.kind) return false;
  switch (pattern.kind) {
    case 'atom':
      return target.kind === 'atom' && pattern.name === target.name;
    case 'application':
      return target.kind === 'application' &&
        pattern.name === target.name &&
        pattern.args.length === target.args.length &&
        pattern.args.every((arg, index) => matchCecExpression(arg, target.args[index], variableName, bindings));
    case 'quantified':
      return target.kind === 'quantified' &&
        pattern.quantifier === target.quantifier &&
        matchCecExpression(pattern.expression, target.expression, variableName, bindings);
    case 'unary':
      return target.kind === 'unary' &&
        pattern.operator === target.operator &&
        matchCecExpression(pattern.expression, target.expression, variableName, bindings);
    case 'binary':
      return target.kind === 'binary' &&
        pattern.operator === target.operator &&
        matchCecExpression(pattern.left, target.left, variableName, bindings) &&
        matchCecExpression(pattern.right, target.right, variableName, bindings);
  }
}

function substituteCecAtom(expression: CecExpression, atomName: string, replacementName: string): CecExpression {
  switch (expression.kind) {
    case 'atom':
      return expression.name === atomName ? { kind: 'atom', name: replacementName } : expression;
    case 'application':
      return {
        ...expression,
        args: expression.args.map((arg) => substituteCecAtom(arg, atomName, replacementName)),
      } satisfies CecApplication;
    case 'quantified':
      return {
        ...expression,
        expression: expression.variable === atomName
          ? expression.expression
          : substituteCecAtom(expression.expression, atomName, replacementName),
      };
    case 'unary':
      return { ...expression, expression: substituteCecAtom(expression.expression, atomName, replacementName) };
    case 'binary':
      return {
        ...expression,
        left: substituteCecAtom(expression.left, atomName, replacementName),
        right: substituteCecAtom(expression.right, atomName, replacementName),
      };
  }
}

function findFirstSubstitutableAtom(expression: CecExpression): string | undefined {
  if (expression.kind === 'application') {
    const atomArg = expression.args.find((arg) => arg.kind === 'atom' && !isVariableLikeAtom(arg.name));
    if (atomArg?.kind === 'atom') return atomArg.name;
  }
  return findFirstNestedAtom(expression, (name) => !isVariableLikeAtom(name));
}

function findFirstVariableLikeAtom(expression: CecExpression): string | undefined {
  return findFirstNestedAtom(expression, isVariableLikeAtom);
}

function findFirstNestedAtom(expression: CecExpression, predicate: (name: string) => boolean): string | undefined {
  switch (expression.kind) {
    case 'atom':
      return predicate(expression.name) ? expression.name : undefined;
    case 'application':
      return expression.args.map((arg) => findFirstNestedAtom(arg, predicate)).find(Boolean);
    case 'quantified':
    case 'unary':
      return findFirstNestedAtom(expression.expression, predicate);
    case 'binary':
      return findFirstNestedAtom(expression.left, predicate) ?? findFirstNestedAtom(expression.right, predicate);
  }
}

function isVariableLikeAtom(name: string) {
  return /^[xyzuvw]$/.test(name) || /^(agent|person|actor|subject|entity)$/i.test(name);
}

export type TdfolInferenceRuleId =
  | 'modus_ponens'
  | 'modus_tollens'
  | 'hypothetical_syllogism'
  | 'disjunctive_syllogism'
  | 'conjunction_introduction'
  | 'conjunction_elimination'
  | 'disjunction_introduction'
  | 'double_negation_elimination'
  | 'biconditional_introduction'
  | 'biconditional_elimination'
  | 'temporal_k_axiom'
  | 'temporal_t_axiom'
  | 'eventually_introduction'
  | 'deontic_k_axiom'
  | 'deontic_d_axiom'
  | 'prohibition_equivalence'
  | 'prohibition_from_obligation'
  | 'obligation_weakening'
  | 'obligation_conjunction'
  | 'permission_duality'
  | 'permission_from_non_obligation'
  | 'temporal_obligation_persistence'
  | 'deontic_temporal_introduction'
  | 'until_obligation'
  | 'always_permission'
  | 'eventually_forbidden'
  | 'obligation_eventually'
  | 'permission_temporal_weakening'
  | 'always_obligation_distribution'
  | 'future_obligation_persistence'
  | 'universal_instantiation'
  | 'universal_generalization'
  | 'existential_instantiation'
  | 'existential_generalization';

export type TdfolInferenceRuleKind =
  | 'propositional'
  | 'temporal'
  | 'deontic'
  | 'temporal_deontic'
  | 'quantifier';

export interface TdfolInferenceRule {
  readonly id: TdfolInferenceRuleId;
  readonly pythonName: string;
  readonly aliases: readonly string[];
  readonly kind: TdfolInferenceRuleKind;
  readonly premiseCount: number | readonly number[];
  readonly conclusionCount: number;
  readonly description: string;
  readonly sourcePythonModule: 'logic/TDFOL/tdfol_inference_rules.py';
}

export interface TdfolRuleApplication {
  readonly rule: string;
  readonly premises: readonly unknown[];
  readonly conclusions?: readonly unknown[];
}

export interface TdfolRuleValidationResult {
  readonly ok: boolean;
  readonly rule?: TdfolInferenceRule;
  readonly reason?: string;
}

export const TDFOL_INFERENCE_RULES_METADATA = {
  sourcePythonModule: 'logic/TDFOL/tdfol_inference_rules.py',
  browserNative: true,
  runtimeDependencies: [] as Array<string>,
  parity: [
    'propositional_rules',
    'first_order_quantifier_rules',
    'temporal_rules',
    'deontic_rules',
    'temporal_deontic_rules',
    'fail_closed_application_validation',
  ] as Array<string>,
} as const;

const MONOLITHIC_RULE_SOURCE = TDFOL_INFERENCE_RULES_METADATA.sourcePythonModule;

const defineRule = (rule: Omit<TdfolInferenceRule, 'sourcePythonModule'>): TdfolInferenceRule => ({
  ...rule,
  sourcePythonModule: MONOLITHIC_RULE_SOURCE,
});

export const TDFOL_INFERENCE_RULES: readonly TdfolInferenceRule[] = (
  [
    defineRule({
      id: 'modus_ponens',
      pythonName: 'modus_ponens',
      aliases: ['mp', 'Modus Ponens'],
      kind: 'propositional',
      premiseCount: 2,
      conclusionCount: 1,
      description: 'From P and P -> Q, infer Q.',
    }),
    defineRule({
      id: 'modus_tollens',
      pythonName: 'modus_tollens',
      aliases: ['mt', 'Modus Tollens'],
      kind: 'propositional',
      premiseCount: 2,
      conclusionCount: 1,
      description: 'From P -> Q and not Q, infer not P.',
    }),
    defineRule({
      id: 'hypothetical_syllogism',
      pythonName: 'hypothetical_syllogism',
      aliases: ['hs', 'Hypothetical Syllogism'],
      kind: 'propositional',
      premiseCount: 2,
      conclusionCount: 1,
      description: 'From P -> Q and Q -> R, infer P -> R.',
    }),
    defineRule({
      id: 'disjunctive_syllogism',
      pythonName: 'disjunctive_syllogism',
      aliases: ['ds', 'Disjunctive Syllogism'],
      kind: 'propositional',
      premiseCount: 2,
      conclusionCount: 1,
      description: 'From P or Q and not P, infer Q.',
    }),
    defineRule({
      id: 'conjunction_introduction',
      pythonName: 'conjunction_introduction',
      aliases: ['and_intro', 'Conjunction Introduction'],
      kind: 'propositional',
      premiseCount: 2,
      conclusionCount: 1,
      description: 'From P and Q, infer P and Q.',
    }),
    defineRule({
      id: 'conjunction_elimination',
      pythonName: 'conjunction_elimination',
      aliases: ['and_elim', 'Conjunction Elimination'],
      kind: 'propositional',
      premiseCount: 1,
      conclusionCount: 1,
      description: 'From P and Q, infer either conjunct.',
    }),
    defineRule({
      id: 'disjunction_introduction',
      pythonName: 'disjunction_introduction',
      aliases: ['or_intro', 'Disjunction Introduction'],
      kind: 'propositional',
      premiseCount: 1,
      conclusionCount: 1,
      description: 'From P, infer P or Q.',
    }),
    defineRule({
      id: 'double_negation_elimination',
      pythonName: 'double_negation_elimination',
      aliases: ['double_negation', 'dn_elim', 'Double Negation Elimination'],
      kind: 'propositional',
      premiseCount: 1,
      conclusionCount: 1,
      description: 'From not not P, infer P.',
    }),
    defineRule({
      id: 'biconditional_introduction',
      pythonName: 'biconditional_introduction',
      aliases: ['iff_intro', 'Biconditional Introduction'],
      kind: 'propositional',
      premiseCount: 2,
      conclusionCount: 1,
      description: 'From P -> Q and Q -> P, infer P iff Q.',
    }),
    defineRule({
      id: 'biconditional_elimination',
      pythonName: 'biconditional_elimination',
      aliases: ['iff_elim', 'Biconditional Elimination'],
      kind: 'propositional',
      premiseCount: 1,
      conclusionCount: 1,
      description: 'From P iff Q, infer either conditional direction.',
    }),
    {
      id: 'temporal_k_axiom',
      pythonName: 'temporal_k_axiom',
      aliases: ['temporal_k', 'Temporal K Axiom'],
      kind: 'temporal',
      premiseCount: 2,
      conclusionCount: 1,
      description: 'From always(P -> Q) and always(P), infer always(Q).',
    },
    {
      id: 'temporal_t_axiom',
      pythonName: 'temporal_t_axiom',
      aliases: ['temporal_t', 'Temporal T Axiom'],
      kind: 'temporal',
      premiseCount: 1,
      conclusionCount: 1,
      description: 'From always(P), infer P.',
    },
    {
      id: 'eventually_introduction',
      pythonName: 'eventually_introduction',
      aliases: ['eventually_intro', 'Eventually Introduction'],
      kind: 'temporal',
      premiseCount: 1,
      conclusionCount: 1,
      description: 'From P, infer eventually(P).',
    },
    {
      id: 'deontic_k_axiom',
      pythonName: 'deontic_k_axiom',
      aliases: ['deontic_k', 'Deontic K Axiom'],
      kind: 'deontic',
      premiseCount: 2,
      conclusionCount: 1,
      description: 'From O(P -> Q) and O(P), infer O(Q).',
    },
    {
      id: 'deontic_d_axiom',
      pythonName: 'deontic_d_axiom',
      aliases: ['deontic_d', 'Deontic D Axiom'],
      kind: 'deontic',
      premiseCount: 1,
      conclusionCount: 1,
      description: 'From O(P), infer P(P).',
    },
    {
      id: 'prohibition_equivalence',
      pythonName: 'prohibition_equivalence',
      aliases: ['prohibition_to_obligation', 'Prohibition Equivalence'],
      kind: 'deontic',
      premiseCount: 1,
      conclusionCount: 1,
      description: 'From F(P), infer O(not P).',
    },
    {
      id: 'prohibition_from_obligation',
      pythonName: 'prohibition_from_obligation',
      aliases: ['obligation_to_prohibition', 'Prohibition From Obligation'],
      kind: 'deontic',
      premiseCount: 1,
      conclusionCount: 1,
      description: 'From O(not P), infer F(P).',
    },
    {
      id: 'obligation_weakening',
      pythonName: 'obligation_weakening',
      aliases: ['Obligation Weakening'],
      kind: 'deontic',
      premiseCount: 1,
      conclusionCount: 1,
      description: 'From O(P and Q), infer either conjunct obligation.',
    },
    {
      id: 'obligation_conjunction',
      pythonName: 'obligation_conjunction',
      aliases: ['Obligation Conjunction'],
      kind: 'deontic',
      premiseCount: 2,
      conclusionCount: 1,
      description: 'From O(P) and O(Q), infer O(P and Q).',
    },
    {
      id: 'permission_duality',
      pythonName: 'permission_duality',
      aliases: ['Permission Duality'],
      kind: 'deontic',
      premiseCount: 1,
      conclusionCount: 1,
      description: 'From P(phi), infer not O(not phi).',
    },
    {
      id: 'permission_from_non_obligation',
      pythonName: 'permission_from_non_obligation',
      aliases: ['Permission From Non Obligation'],
      kind: 'deontic',
      premiseCount: 1,
      conclusionCount: 1,
      description: 'From not O(not phi), infer P(phi).',
    },
    {
      id: 'temporal_obligation_persistence',
      pythonName: 'temporal_obligation_persistence',
      aliases: ['Temporal Obligation Persistence'],
      kind: 'temporal_deontic',
      premiseCount: 1,
      conclusionCount: 1,
      description: 'From O(always phi), infer always O(phi).',
    },
    {
      id: 'deontic_temporal_introduction',
      pythonName: 'deontic_temporal_introduction',
      aliases: ['Deontic Temporal Introduction'],
      kind: 'temporal_deontic',
      premiseCount: 1,
      conclusionCount: 1,
      description: 'From O(phi), infer O(next phi).',
    },
    {
      id: 'until_obligation',
      pythonName: 'until_obligation',
      aliases: ['Until Obligation'],
      kind: 'temporal_deontic',
      premiseCount: 1,
      conclusionCount: 1,
      description: 'From O(phi until psi), infer eventually O(psi).',
    },
    {
      id: 'always_permission',
      pythonName: 'always_permission',
      aliases: ['Always Permission'],
      kind: 'temporal_deontic',
      premiseCount: 1,
      conclusionCount: 1,
      description: 'From P(always phi), infer always P(phi).',
    },
    {
      id: 'eventually_forbidden',
      pythonName: 'eventually_forbidden',
      aliases: ['Eventually Forbidden'],
      kind: 'temporal_deontic',
      premiseCount: 1,
      conclusionCount: 1,
      description: 'From F(eventually phi), infer always F(phi).',
    },
    {
      id: 'obligation_eventually',
      pythonName: 'obligation_eventually',
      aliases: ['Obligation Eventually'],
      kind: 'temporal_deontic',
      premiseCount: 1,
      conclusionCount: 1,
      description: 'From O(eventually phi), infer eventually O(phi).',
    },
    {
      id: 'permission_temporal_weakening',
      pythonName: 'permission_temporal_weakening',
      aliases: ['Permission Temporal Weakening'],
      kind: 'temporal_deontic',
      premiseCount: 1,
      conclusionCount: 1,
      description: 'From P(phi), infer P(eventually phi).',
    },
    {
      id: 'always_obligation_distribution',
      pythonName: 'always_obligation_distribution',
      aliases: ['Always Obligation Distribution'],
      kind: 'temporal_deontic',
      premiseCount: 1,
      conclusionCount: 1,
      description: 'From always O(phi), infer O(always phi).',
    },
    {
      id: 'future_obligation_persistence',
      pythonName: 'future_obligation_persistence',
      aliases: ['Future Obligation Persistence'],
      kind: 'temporal_deontic',
      premiseCount: 1,
      conclusionCount: 1,
      description: 'From O(next phi), infer next O(phi).',
    },
    {
      id: 'universal_instantiation',
      pythonName: 'universal_instantiation',
      aliases: ['ui', 'Universal Instantiation'],
      kind: 'quantifier',
      premiseCount: 1,
      conclusionCount: 1,
      description: 'From forall x P(x), infer P(c) for a term c.',
    },
    defineRule({
      id: 'universal_generalization',
      pythonName: 'universal_generalization',
      aliases: ['ug', 'Universal Generalization'],
      kind: 'quantifier',
      premiseCount: 1,
      conclusionCount: 1,
      description: 'From P(x), infer forall x P(x) when x is arbitrary.',
    }),
    defineRule({
      id: 'existential_instantiation',
      pythonName: 'existential_instantiation',
      aliases: ['ei', 'Existential Instantiation'],
      kind: 'quantifier',
      premiseCount: 1,
      conclusionCount: 1,
      description: 'From exists x P(x), introduce a fresh witness term c and infer P(c).',
    }),
    defineRule({
      id: 'existential_generalization',
      pythonName: 'existential_generalization',
      aliases: ['eg', 'Existential Generalization'],
      kind: 'quantifier',
      premiseCount: 1,
      conclusionCount: 1,
      description: 'From P(c), infer exists x P(x).',
    }),
  ] as const
).map((rule) => defineRule(rule));

const normalizeRuleName = (name: string): string =>
  name
    .trim()
    .toLowerCase()
    .replace(/[\s-]+/g, '_');

const ruleLookup = new Map<string, TdfolInferenceRule>();
for (const rule of TDFOL_INFERENCE_RULES) {
  ruleLookup.set(normalizeRuleName(rule.id), rule);
  ruleLookup.set(normalizeRuleName(rule.pythonName), rule);
  for (const alias of rule.aliases) {
    ruleLookup.set(normalizeRuleName(alias), rule);
  }
}

export function getTdfolInferenceRule(name: string): TdfolInferenceRule | undefined {
  return ruleLookup.get(normalizeRuleName(name));
}

export function listTdfolInferenceRules(): readonly TdfolInferenceRule[] {
  return TDFOL_INFERENCE_RULES;
}

export function validateTdfolRuleApplication(
  application: TdfolRuleApplication,
): TdfolRuleValidationResult {
  const rule = getTdfolInferenceRule(application.rule);
  if (!rule) {
    return { ok: false, reason: `Unknown TDFOL inference rule: ${application.rule}` };
  }

  const expectedPremiseCounts = Array.isArray(rule.premiseCount)
    ? rule.premiseCount
    : [rule.premiseCount];
  if (!expectedPremiseCounts.includes(application.premises.length)) {
    return {
      ok: false,
      rule,
      reason: `${rule.id} expects ${expectedPremiseCounts.join(' or ')} premise(s), received ${application.premises.length}`,
    };
  }

  if (application.conclusions && application.conclusions.length !== rule.conclusionCount) {
    return {
      ok: false,
      rule,
      reason: `${rule.id} expects ${rule.conclusionCount} conclusion(s), received ${application.conclusions.length}`,
    };
  }

  return { ok: true, rule };
}

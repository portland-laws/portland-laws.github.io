export type TdfolInferenceRuleId =
  | 'modus_ponens'
  | 'modus_tollens'
  | 'hypothetical_syllogism'
  | 'disjunctive_syllogism'
  | 'conjunction_introduction'
  | 'conjunction_elimination'
  | 'disjunction_introduction'
  | 'biconditional_introduction'
  | 'biconditional_elimination'
  | 'universal_instantiation'
  | 'universal_generalization'
  | 'existential_instantiation'
  | 'existential_generalization';

export type TdfolInferenceRuleKind = 'propositional' | 'quantifier';

export interface TdfolInferenceRule {
  readonly id: TdfolInferenceRuleId;
  readonly pythonName: string;
  readonly aliases: readonly string[];
  readonly kind: TdfolInferenceRuleKind;
  readonly premiseCount: number | readonly number[];
  readonly conclusionCount: number;
  readonly description: string;
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

export const TDFOL_INFERENCE_RULES: readonly TdfolInferenceRule[] = [
  {
    id: 'modus_ponens',
    pythonName: 'modus_ponens',
    aliases: ['mp', 'Modus Ponens'],
    kind: 'propositional',
    premiseCount: 2,
    conclusionCount: 1,
    description: 'From P and P -> Q, infer Q.',
  },
  {
    id: 'modus_tollens',
    pythonName: 'modus_tollens',
    aliases: ['mt', 'Modus Tollens'],
    kind: 'propositional',
    premiseCount: 2,
    conclusionCount: 1,
    description: 'From P -> Q and not Q, infer not P.',
  },
  {
    id: 'hypothetical_syllogism',
    pythonName: 'hypothetical_syllogism',
    aliases: ['hs', 'Hypothetical Syllogism'],
    kind: 'propositional',
    premiseCount: 2,
    conclusionCount: 1,
    description: 'From P -> Q and Q -> R, infer P -> R.',
  },
  {
    id: 'disjunctive_syllogism',
    pythonName: 'disjunctive_syllogism',
    aliases: ['ds', 'Disjunctive Syllogism'],
    kind: 'propositional',
    premiseCount: 2,
    conclusionCount: 1,
    description: 'From P or Q and not P, infer Q.',
  },
  {
    id: 'conjunction_introduction',
    pythonName: 'conjunction_introduction',
    aliases: ['and_intro', 'Conjunction Introduction'],
    kind: 'propositional',
    premiseCount: 2,
    conclusionCount: 1,
    description: 'From P and Q, infer P and Q.',
  },
  {
    id: 'conjunction_elimination',
    pythonName: 'conjunction_elimination',
    aliases: ['and_elim', 'Conjunction Elimination'],
    kind: 'propositional',
    premiseCount: 1,
    conclusionCount: 1,
    description: 'From P and Q, infer either conjunct.',
  },
  {
    id: 'disjunction_introduction',
    pythonName: 'disjunction_introduction',
    aliases: ['or_intro', 'Disjunction Introduction'],
    kind: 'propositional',
    premiseCount: 1,
    conclusionCount: 1,
    description: 'From P, infer P or Q.',
  },
  {
    id: 'biconditional_introduction',
    pythonName: 'biconditional_introduction',
    aliases: ['iff_intro', 'Biconditional Introduction'],
    kind: 'propositional',
    premiseCount: 2,
    conclusionCount: 1,
    description: 'From P -> Q and Q -> P, infer P  Q.',
  },
  {
    id: 'biconditional_elimination',
    pythonName: 'biconditional_elimination',
    aliases: ['iff_elim', 'Biconditional Elimination'],
    kind: 'propositional',
    premiseCount: 1,
    conclusionCount: 1,
    description: 'From P  Q, infer either conditional direction.',
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
  {
    id: 'universal_generalization',
    pythonName: 'universal_generalization',
    aliases: ['ug', 'Universal Generalization'],
    kind: 'quantifier',
    premiseCount: 1,
    conclusionCount: 1,
    description: 'From P(x), infer forall x P(x) when x is arbitrary.',
  },
  {
    id: 'existential_instantiation',
    pythonName: 'existential_instantiation',
    aliases: ['ei', 'Existential Instantiation'],
    kind: 'quantifier',
    premiseCount: 1,
    conclusionCount: 1,
    description: 'From exists x P(x), introduce a fresh witness term c and infer P(c).',
  },
  {
    id: 'existential_generalization',
    pythonName: 'existential_generalization',
    aliases: ['eg', 'Existential Generalization'],
    kind: 'quantifier',
    premiseCount: 1,
    conclusionCount: 1,
    description: 'From P(c), infer exists x P(x).',
  },
] as const;

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

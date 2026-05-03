export type PropositionalExpressionKind = 'atom' | 'not' | 'and' | 'or' | 'implies' | 'iff';

export type PropositionalRuleName =
  | 'modus_ponens'
  | 'modus_tollens'
  | 'hypothetical_syllogism'
  | 'disjunctive_syllogism'
  | 'conjunction_introduction'
  | 'conjunction_elimination_left'
  | 'conjunction_elimination_right'
  | 'double_negation_elimination'
  | 'biconditional_elimination_left'
  | 'biconditional_elimination_right';

export interface PropositionalExpression {
  kind: PropositionalExpressionKind;
  name?: string;
  args: PropositionalExpression[];
}

export interface PropositionalInferenceInput {
  rule: PropositionalRuleName;
  premises: unknown[];
  target?: unknown;
}

export interface PropositionalInferenceResult {
  ok: boolean;
  rule: PropositionalRuleName;
  conclusion?: PropositionalExpression;
  reason?: string;
}

export function propositionalAtom(name: string): PropositionalExpression {
  return { kind: 'atom', name, args: [] };
}

export function propositionalNot(value: PropositionalExpression): PropositionalExpression {
  return { kind: 'not', args: [value] };
}

export function propositionalAnd(
  left: PropositionalExpression,
  right: PropositionalExpression,
): PropositionalExpression {
  return { kind: 'and', args: [left, right] };
}

export function propositionalOr(
  left: PropositionalExpression,
  right: PropositionalExpression,
): PropositionalExpression {
  return { kind: 'or', args: [left, right] };
}

export function propositionalImplies(
  left: PropositionalExpression,
  right: PropositionalExpression,
): PropositionalExpression {
  return { kind: 'implies', args: [left, right] };
}

export function propositionalIff(
  left: PropositionalExpression,
  right: PropositionalExpression,
): PropositionalExpression {
  return { kind: 'iff', args: [left, right] };
}

export function isPropositionalExpression(value: unknown): value is PropositionalExpression {
  if (typeof value !== 'object' || value === null) {
    return false;
  }

  const candidate = value as Record<string, unknown>;
  if (!isPropositionalExpressionKind(candidate.kind) || !Array.isArray(candidate.args)) {
    return false;
  }

  if (candidate.kind === 'atom') {
    return (
      typeof candidate.name === 'string' &&
      candidate.name.length >= 1 &&
      candidate.args.length === 0
    );
  }

  return (
    expectedArity(candidate.kind) === candidate.args.length &&
    candidate.args.every(isPropositionalExpression)
  );
}

export function expressionsEqual(
  left: PropositionalExpression | undefined,
  right: PropositionalExpression | undefined,
): boolean {
  if (
    left === undefined ||
    right === undefined ||
    left.kind !== right.kind ||
    left.name !== right.name
  ) {
    return false;
  }

  if (left.args.length !== right.args.length) {
    return false;
  }

  return left.args.every((child: PropositionalExpression, index: number) =>
    expressionsEqual(child, right.args[index]),
  );
}

export function applyPropositionalRule(
  input: PropositionalInferenceInput,
): PropositionalInferenceResult {
  const premises = input.premises.filter(isPropositionalExpression);
  if (premises.length !== input.premises.length) {
    return fail(input.rule, 'all premises must be well-formed propositional expressions');
  }

  const conclusion = inferConclusion(input.rule, premises);
  if (conclusion === undefined) {
    return fail(input.rule, 'premises do not match the selected propositional rule');
  }

  if (input.target !== undefined) {
    if (!isPropositionalExpression(input.target)) {
      return fail(input.rule, 'target must be a well-formed propositional expression');
    }
    if (!expressionsEqual(conclusion, input.target)) {
      return fail(input.rule, 'derived conclusion does not match target');
    }
  }

  return { ok: true, rule: input.rule, conclusion };
}

function inferConclusion(
  rule: PropositionalRuleName,
  premises: PropositionalExpression[],
): PropositionalExpression | undefined {
  const first = premises[0];
  const second = premises[1];

  if (
    rule === 'modus_ponens' &&
    premises.length === 2 &&
    second.kind === 'implies' &&
    expressionsEqual(first, second.args[0])
  ) {
    return second.args[1];
  }

  if (
    rule === 'modus_tollens' &&
    premises.length === 2 &&
    first.kind === 'not' &&
    second.kind === 'implies' &&
    expressionsEqual(first.args[0], second.args[1])
  ) {
    return propositionalNot(second.args[0]);
  }

  if (
    rule === 'hypothetical_syllogism' &&
    premises.length === 2 &&
    first.kind === 'implies' &&
    second.kind === 'implies' &&
    expressionsEqual(first.args[1], second.args[0])
  ) {
    return propositionalImplies(first.args[0], second.args[1]);
  }

  if (
    rule === 'disjunctive_syllogism' &&
    premises.length === 2 &&
    first.kind === 'or' &&
    second.kind === 'not'
  ) {
    if (expressionsEqual(first.args[0], second.args[0])) {
      return first.args[1];
    }
    if (expressionsEqual(first.args[1], second.args[0])) {
      return first.args[0];
    }
  }

  if (rule === 'conjunction_introduction' && premises.length === 2) {
    return propositionalAnd(first, second);
  }

  if (rule === 'conjunction_elimination_left' && premises.length === 1 && first.kind === 'and') {
    return first.args[0];
  }

  if (rule === 'conjunction_elimination_right' && premises.length === 1 && first.kind === 'and') {
    return first.args[1];
  }

  if (
    rule === 'double_negation_elimination' &&
    premises.length === 1 &&
    first.kind === 'not' &&
    first.args[0]?.kind === 'not'
  ) {
    return first.args[0].args[0];
  }

  if (rule === 'biconditional_elimination_left' && premises.length === 1 && first.kind === 'iff') {
    return propositionalImplies(first.args[0], first.args[1]);
  }

  if (rule === 'biconditional_elimination_right' && premises.length === 1 && first.kind === 'iff') {
    return propositionalImplies(first.args[1], first.args[0]);
  }

  return undefined;
}

function isPropositionalExpressionKind(value: unknown): value is PropositionalExpressionKind {
  return (
    value === 'atom' ||
    value === 'not' ||
    value === 'and' ||
    value === 'or' ||
    value === 'implies' ||
    value === 'iff'
  );
}

function expectedArity(kind: PropositionalExpressionKind): number {
  return kind === 'atom' ? 0 : kind === 'not' ? 1 : 2;
}

function fail(rule: PropositionalRuleName, reason: string): PropositionalInferenceResult {
  return { ok: false, rule, reason };
}

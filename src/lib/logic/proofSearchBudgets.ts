export type ProofSearchBudgetExhaustionReason = 'step_budget_exceeded' | 'time_budget_exceeded';

export interface ProofSearchBudget {
  readonly maxSteps: number;
  readonly maxMilliseconds: number;
  readonly yieldEverySteps: number;
}

export interface ProofSearchBudgetOptions {
  readonly maxSteps?: number;
  readonly maxMilliseconds?: number;
  readonly yieldEverySteps?: number;
}

export interface ProofSearchBudgetState {
  readonly budget: ProofSearchBudget;
  readonly startedAt: number;
  readonly elapsedMilliseconds: number;
  readonly stepsUsed: number;
}

export interface ProofSearchBudgetAdvanceOptions {
  readonly steps?: number;
  readonly now?: number;
}

export interface ProofSearchBudgetAdvanceResult {
  readonly state: ProofSearchBudgetState;
  readonly exhausted: boolean;
  readonly reason?: ProofSearchBudgetExhaustionReason;
  readonly shouldYield: boolean;
}

export interface ProofSearchBudgetValidationResult {
  readonly ok: boolean;
  readonly budget?: ProofSearchBudget;
  readonly errors: readonly string[];
}

export const DEFAULT_PROOF_SEARCH_BUDGET: ProofSearchBudget = Object.freeze({
  maxSteps: 10000,
  maxMilliseconds: 100,
  yieldEverySteps: 250,
});

function isPositiveInteger(value: number): boolean {
  return Number.isInteger(value) && value > 0;
}

function nowMilliseconds(): number {
  const performanceLike = globalThis.performance;
  if (performanceLike && typeof performanceLike.now === 'function') {
    return performanceLike.now();
  }
  return Date.now();
}

export function validateProofSearchBudget(
  options: ProofSearchBudgetOptions = {},
): ProofSearchBudgetValidationResult {
  const budget: ProofSearchBudget = {
    maxSteps: options.maxSteps ?? DEFAULT_PROOF_SEARCH_BUDGET.maxSteps,
    maxMilliseconds: options.maxMilliseconds ?? DEFAULT_PROOF_SEARCH_BUDGET.maxMilliseconds,
    yieldEverySteps: options.yieldEverySteps ?? DEFAULT_PROOF_SEARCH_BUDGET.yieldEverySteps,
  };
  const errors: string[] = [];

  if (!isPositiveInteger(budget.maxSteps)) {
    errors.push('maxSteps must be a positive integer');
  }
  if (!isPositiveInteger(budget.maxMilliseconds)) {
    errors.push('maxMilliseconds must be a positive integer');
  }
  if (!isPositiveInteger(budget.yieldEverySteps)) {
    errors.push('yieldEverySteps must be a positive integer');
  }
  if (
    isPositiveInteger(budget.maxSteps) &&
    isPositiveInteger(budget.yieldEverySteps) &&
    budget.yieldEverySteps > budget.maxSteps
  ) {
    errors.push('yieldEverySteps must not exceed maxSteps');
  }

  return errors.length === 0 ? { ok: true, budget, errors } : { ok: false, errors };
}

export function createProofSearchBudget(options: ProofSearchBudgetOptions = {}): ProofSearchBudget {
  const result = validateProofSearchBudget(options);
  if (!result.ok || !result.budget) {
    throw new RangeError(result.errors.join('; '));
  }
  return result.budget;
}

export function startProofSearchBudget(
  options: ProofSearchBudgetOptions = {},
  now: number = nowMilliseconds(),
): ProofSearchBudgetState {
  return {
    budget: createProofSearchBudget(options),
    startedAt: now,
    elapsedMilliseconds: 0,
    stepsUsed: 0,
  };
}

export function advanceProofSearchBudget(
  state: ProofSearchBudgetState,
  options: ProofSearchBudgetAdvanceOptions = {},
): ProofSearchBudgetAdvanceResult {
  const steps = options.steps ?? 1;
  if (!isPositiveInteger(steps)) {
    throw new RangeError('steps must be a positive integer');
  }

  const now = options.now ?? nowMilliseconds();
  const elapsedMilliseconds = Math.max(0, now - state.startedAt);
  const stepsUsed = state.stepsUsed + steps;
  const nextState: ProofSearchBudgetState = {
    budget: state.budget,
    startedAt: state.startedAt,
    elapsedMilliseconds,
    stepsUsed,
  };

  if (stepsUsed > state.budget.maxSteps) {
    return {
      state: nextState,
      exhausted: true,
      reason: 'step_budget_exceeded',
      shouldYield: false,
    };
  }
  if (elapsedMilliseconds > state.budget.maxMilliseconds) {
    return {
      state: nextState,
      exhausted: true,
      reason: 'time_budget_exceeded',
      shouldYield: false,
    };
  }

  return {
    state: nextState,
    exhausted: false,
    shouldYield: stepsUsed % state.budget.yieldEverySteps === 0,
  };
}

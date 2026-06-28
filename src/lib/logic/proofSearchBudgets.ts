export type ProofSearchBudgetExhaustionReason = 'step_budget_exceeded' | 'time_budget_exceeded';
export type ProofSearchAccelerationProfile = 'standard' | 'zkp_parallel';

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

export interface ParallelProofSearchBudgetOptions {  readonly parallelism?: number;  readonly reserveCoordinatorSteps?: number;  readonly profile?: ProofSearchAccelerationProfile;}export interface ParallelProofSearchWorkerBudget {  readonly workerIndex: number;  readonly budget: ProofSearchBudget;}export interface ParallelProofSearchBudgetPlan {  readonly profile: ProofSearchAccelerationProfile;  readonly parallelism: number;  readonly coordinatorBudget: ProofSearchBudget;  readonly workerBudgets: readonly ParallelProofSearchWorkerBudget[];  readonly distributedSteps: number;}
export const DEFAULT_PROOF_SEARCH_BUDGET: ProofSearchBudget = Object.freeze({
  maxSteps: 10000,
  maxMilliseconds: 100,
  yieldEverySteps: 250,
});

export const MAX_PARALLEL_PROOF_SEARCH_WORKERS = 32;export const DEFAULT_STANDARD_PARALLEL_PROOF_SEARCH_WORKERS = 2;export const DEFAULT_ZKP_PARALLEL_PROOF_SEARCH_WORKERS = 4;
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

function defaultReservedCoordinatorSteps(  maxSteps: number,  profile: ProofSearchAccelerationProfile,): number {  const divisor = profile === 'zkp_parallel' ? 20 : 10;  return Math.max(1, Math.floor(maxSteps / divisor));}function normalizeYieldEverySteps(  requestedYieldEverySteps: number,  maxSteps: number,  profile: ProofSearchAccelerationProfile,): number {  const acceleratedYieldEverySteps =    profile === 'zkp_parallel'      ? Math.max(1, Math.floor(requestedYieldEverySteps / 2))      : requestedYieldEverySteps;  return Math.max(1, Math.min(acceleratedYieldEverySteps, maxSteps));}
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

export function createParallelProofSearchBudgetPlan(  budgetOptions: ProofSearchBudgetOptions = {},  options: ParallelProofSearchBudgetOptions = {},): ParallelProofSearchBudgetPlan {  const baseBudget = createProofSearchBudget(budgetOptions);  const profile: ProofSearchAccelerationProfile = options.profile ?? 'standard';  const defaultParallelism =    profile === 'zkp_parallel'      ? DEFAULT_ZKP_PARALLEL_PROOF_SEARCH_WORKERS      : DEFAULT_STANDARD_PARALLEL_PROOF_SEARCH_WORKERS;  const parallelism = options.parallelism ?? defaultParallelism;  if (!isPositiveInteger(parallelism)) {    throw new RangeError('parallelism must be a positive integer');  }  if (parallelism > MAX_PARALLEL_PROOF_SEARCH_WORKERS) {    throw new RangeError(      'parallelism must not exceed ' + String(MAX_PARALLEL_PROOF_SEARCH_WORKERS),    );  }  const reserveCoordinatorSteps =    options.reserveCoordinatorSteps ?? defaultReservedCoordinatorSteps(baseBudget.maxSteps, profile);  if (!isPositiveInteger(reserveCoordinatorSteps)) {    throw new RangeError('reserveCoordinatorSteps must be a positive integer');  }  if (reserveCoordinatorSteps >= baseBudget.maxSteps) {    throw new RangeError('reserveCoordinatorSteps must be less than maxSteps');  }  const distributedSteps = baseBudget.maxSteps - reserveCoordinatorSteps;  if (parallelism > distributedSteps) {    throw new RangeError('parallelism must not exceed distributable step budget');  }  const baseWorkerSteps = Math.floor(distributedSteps / parallelism);  const workerRemainder = distributedSteps % parallelism;  const workerBudgets: ParallelProofSearchWorkerBudget[] = [];  for (let workerIndex = 0; workerIndex < parallelism; workerIndex += 1) {    const workerSteps = baseWorkerSteps + (workerIndex < workerRemainder ? 1 : 0);    const workerYieldEverySteps = normalizeYieldEverySteps(      baseBudget.yieldEverySteps,      workerSteps,      profile,    );    workerBudgets.push({      workerIndex,      budget: {        maxSteps: workerSteps,        maxMilliseconds: baseBudget.maxMilliseconds,        yieldEverySteps: workerYieldEverySteps,      },    });  }  const coordinatorBudget: ProofSearchBudget = {    maxSteps: reserveCoordinatorSteps,    maxMilliseconds: baseBudget.maxMilliseconds,    yieldEverySteps: normalizeYieldEverySteps(      baseBudget.yieldEverySteps,      reserveCoordinatorSteps,      profile,    ),  };  return {    profile,    parallelism,    coordinatorBudget,    workerBudgets,    distributedSteps,  };}
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

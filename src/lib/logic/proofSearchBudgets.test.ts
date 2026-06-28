import {
  createProofSearchBudget,
  createParallelProofSearchBudgetPlan,
  DEFAULT_PROOF_SEARCH_BUDGET,
  advanceProofSearchBudget,
  startProofSearchBudget,
  validateProofSearchBudget,
} from './proofSearchBudgets';

describe('proofSearchBudgets', () => {
  it('creates a default browser proof search budget', () => {
    expect(createProofSearchBudget()).toEqual(DEFAULT_PROOF_SEARCH_BUDGET);
  });

  it('accepts bounded overrides', () => {
    expect(
      createProofSearchBudget({
        maxSteps: 16,
        maxMilliseconds: 8,
        yieldEverySteps: 4,
      }),
    ).toEqual({
      maxSteps: 16,
      maxMilliseconds: 8,
      yieldEverySteps: 4,
    });
  });

  it('rejects invalid budgets before proof search starts', () => {
    const result = validateProofSearchBudget({
      maxSteps: 0,
      maxMilliseconds: Number.POSITIVE_INFINITY,
      yieldEverySteps: 2,
    });

    expect(result.ok).toBe(false);
    expect(result.errors).toContain('maxSteps must be a positive integer');
    expect(result.errors).toContain('maxMilliseconds must be a positive integer');
  });

  it('tracks deterministic elapsed time and cooperative yields', () => {
    let state = startProofSearchBudget(
      { maxSteps: 10, maxMilliseconds: 50, yieldEverySteps: 3 },
      100,
    );

    const first = advanceProofSearchBudget(state, { steps: 2, now: 110 });
    expect(first.exhausted).toBe(false);
    expect(first.shouldYield).toBe(false);
    expect(first.state.elapsedMilliseconds).toBe(10);
    expect(first.state.stepsUsed).toBe(2);

    state = first.state;
    const second = advanceProofSearchBudget(state, { steps: 1, now: 120 });
    expect(second.exhausted).toBe(false);
    expect(second.shouldYield).toBe(true);
    expect(second.state.elapsedMilliseconds).toBe(20);
    expect(second.state.stepsUsed).toBe(3);
  });

  it('fails closed when the step budget is exceeded', () => {
    const state = startProofSearchBudget(
      { maxSteps: 3, maxMilliseconds: 50, yieldEverySteps: 1 },
      0,
    );

    const result = advanceProofSearchBudget(state, { steps: 4, now: 1 });

    expect(result.exhausted).toBe(true);
    expect(result.reason).toBe('step_budget_exceeded');
    expect(result.shouldYield).toBe(false);
  });

  it('fails closed when the elapsed time budget is exceeded', () => {
    const state = startProofSearchBudget(
      { maxSteps: 10, maxMilliseconds: 5, yieldEverySteps: 1 },
      10,
    );

    const result = advanceProofSearchBudget(state, { steps: 1, now: 16 });

    expect(result.exhausted).toBe(true);
    expect(result.reason).toBe('time_budget_exceeded');
    expect(result.shouldYield).toBe(false);
  });
  it("splits deterministic worker budgets for parallel proof search", () => {
    const plan = createParallelProofSearchBudgetPlan(
      { maxSteps: 11, maxMilliseconds: 20, yieldEverySteps: 4 },
      { parallelism: 3, reserveCoordinatorSteps: 2, profile: "standard" },
    );

    expect(plan.profile).toBe("standard");
    expect(plan.parallelism).toBe(3);
    expect(plan.distributedSteps).toBe(9);
    expect(plan.coordinatorBudget).toEqual({
      maxSteps: 2,
      maxMilliseconds: 20,
      yieldEverySteps: 2,
    });
    expect(plan.workerBudgets.map((entry) => entry.budget)).toEqual([
      { maxSteps: 3, maxMilliseconds: 20, yieldEverySteps: 3 },
      { maxSteps: 3, maxMilliseconds: 20, yieldEverySteps: 3 },
      { maxSteps: 3, maxMilliseconds: 20, yieldEverySteps: 3 },
    ]);
  });

  it("applies zkp_parallel defaults with accelerated cooperative yielding", () => {
    const plan = createParallelProofSearchBudgetPlan(
      { maxSteps: 40, maxMilliseconds: 60, yieldEverySteps: 6 },
      { profile: "zkp_parallel" },
    );

    expect(plan.profile).toBe("zkp_parallel");
    expect(plan.parallelism).toBe(4);
    expect(plan.coordinatorBudget.maxSteps).toBe(2);
    expect(plan.workerBudgets.map((entry) => entry.budget.maxSteps)).toEqual([10, 10, 9, 9]);
    expect(plan.workerBudgets.map((entry) => entry.budget.yieldEverySteps)).toEqual([3, 3, 3, 3]);
  });

  it("fails closed when requested parallelism exceeds distributable steps", () => {
    expect(() =>
      createParallelProofSearchBudgetPlan(
        { maxSteps: 5, maxMilliseconds: 10, yieldEverySteps: 1 },
        { parallelism: 5, reserveCoordinatorSteps: 2 },
      ),
    ).toThrow("parallelism must not exceed distributable step budget");
  });

});

import {
  createProofSearchBudget,
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
});

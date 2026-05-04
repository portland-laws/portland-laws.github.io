import type { ProofResult, ProofStatus, ProofStep } from '../types';
import { analyzeCecExpression } from '../cec/analyzer';
import type { CecBinaryOperator, CecExpression } from '../cec/ast';
import { formatCecExpression } from '../cec/formatter';
import {
  applyCecRules,
  cecExpressionEquals,
  cecExpressionKey,
  getAllCecRules,
  getDeonticCecRules,
  getTemporalCecRules,
  type CecInferenceRule,
} from '../cec/inferenceRules';
import type { TdfolBinaryFormula, TdfolFormula, TdfolTerm } from './ast';
import { formatTdfolFormula } from './formatter';
import {
  applyTdfolRules,
  formulaEquals,
  formulaKey,
  getAllTdfolRules,
  type TdfolInferenceRule,
} from './inferenceRules';
import { TdfolModalTableaux, type TdfolModalTableauxOptions } from './modalTableaux';
import type { TdfolModalLogicType } from './countermodels';
import type { TdfolKnowledgeBase } from './prover';

export type TdfolStrategyType =
  | 'forward_chaining'
  | 'backward_chaining'
  | 'modal_tableaux'
  | 'cec_delegate'
  | 'bidirectional'
  | 'auto';

export interface TdfolStrategyContext {
  theorem: TdfolFormula;
  knowledgeBase: TdfolKnowledgeBase;
  timeoutMs?: number;
}

export interface TdfolStrategyInfo {
  name: string;
  type: TdfolStrategyType;
  priority: number;
  cost?: number;
}

export interface TdfolProverStrategy {
  readonly name: string;
  readonly strategyType: TdfolStrategyType;
  canHandle(formula: TdfolFormula, kb: TdfolKnowledgeBase): boolean;
  prove(formula: TdfolFormula, kb: TdfolKnowledgeBase, timeoutMs?: number): ProofResult;
  getPriority(): number;
  estimateCost(formula: TdfolFormula, kb: TdfolKnowledgeBase): number;
}

export interface TdfolBaseStrategyOptions {
  name: string;
  strategyType: TdfolStrategyType;
  priority?: number;
  sourcePythonModule?: string;
  defaultTimeoutMs?: number;
}

export interface TdfolStrategyMetadata extends TdfolStrategyInfo {
  sourcePythonModule: string;
  browserNative: true;
  defaultTimeoutMs: number;
}

export abstract class TdfolBaseProverStrategy implements TdfolProverStrategy {
  readonly name: string;
  readonly strategyType: TdfolStrategyType;
  readonly sourcePythonModule: string;
  protected readonly priority: number;
  protected readonly defaultTimeoutMs: number;

  constructor(options: TdfolBaseStrategyOptions) {
    if (!options.name.trim()) {
      throw new Error('TDFOL prover strategy name must be non-empty');
    }
    const priority = options.priority ?? 50;
    if (!Number.isFinite(priority)) {
      throw new Error(`TDFOL prover strategy ${options.name} has invalid priority`);
    }
    this.name = options.name;
    this.strategyType = options.strategyType;
    this.priority = priority;
    this.sourcePythonModule = options.sourcePythonModule ?? 'logic/TDFOL/strategies/base.py';
    this.defaultTimeoutMs = options.defaultTimeoutMs ?? 2000;
  }

  canHandle(_formula: TdfolFormula, _kb: TdfolKnowledgeBase): boolean {
    return true;
  }

  abstract prove(formula: TdfolFormula, kb: TdfolKnowledgeBase, timeoutMs?: number): ProofResult;

  getPriority(): number {
    return this.priority;
  }

  estimateCost(formula: TdfolFormula, kb: TdfolKnowledgeBase): number {
    const kbSize = kb.axioms.length + (kb.theorems?.length ?? 0);
    return Math.max(1, formulaNodeCount(formula) * Math.log2(kbSize + 2));
  }

  getMetadata(formula?: TdfolFormula, kb?: TdfolKnowledgeBase): TdfolStrategyMetadata {
    return {
      name: this.name,
      type: this.strategyType,
      priority: this.priority,
      cost: formula && kb ? this.estimateCost(formula, kb) : undefined,
      sourcePythonModule: this.sourcePythonModule,
      browserNative: true,
      defaultTimeoutMs: this.defaultTimeoutMs,
    };
  }

  toString(): string {
    return `${this.name} (${this.strategyType})`;
  }

  protected finishResult(
    status: ProofStatus,
    theorem: TdfolFormula,
    steps: ProofStep[],
    start: number,
    error?: string,
  ): ProofResult {
    return {
      status,
      theorem: formatTdfolFormula(theorem),
      steps,
      method: this.strategyType,
      timeMs: Math.max(0, nowMs() - start),
      error,
    };
  }

  protected createStep(
    index: number,
    rule: string,
    premises: TdfolFormula[],
    conclusion: TdfolFormula,
    explanation: string,
  ): ProofStep {
    return {
      id: `tdfol-base-strategy-step-${index}`,
      rule,
      premises: premises.map(formatTdfolFormula),
      conclusion: formatTdfolFormula(conclusion),
      explanation,
    };
  }
}

export interface TdfolForwardChainingStrategyOptions {
  maxIterations?: number;
  maxDerivedFormulas?: number;
  maxNewFormulasPerIteration?: number;
  binaryPremiseWindow?: number;
  rules?: TdfolInferenceRule[];
  defaultTimeoutMs?: number;
}

export class TdfolForwardChainingStrategy implements TdfolProverStrategy {
  readonly name = 'Forward Chaining';
  readonly strategyType = 'forward_chaining' satisfies TdfolStrategyType;
  private readonly maxIterations: number;
  private readonly maxDerivedFormulas: number;
  private readonly maxNewFormulasPerIteration: number;
  private readonly binaryPremiseWindow: number;
  private readonly rules: TdfolInferenceRule[];
  private readonly defaultTimeoutMs: number;

  constructor(options: TdfolForwardChainingStrategyOptions = {}) {
    this.maxIterations = options.maxIterations ?? 100;
    this.maxDerivedFormulas = options.maxDerivedFormulas ?? 500;
    this.maxNewFormulasPerIteration = options.maxNewFormulasPerIteration ?? 200;
    this.binaryPremiseWindow = options.binaryPremiseWindow ?? 20;
    this.rules = options.rules ?? getAllTdfolRules();
    this.defaultTimeoutMs = options.defaultTimeoutMs ?? 2000;
  }

  canHandle(_formula?: TdfolFormula, _kb?: TdfolKnowledgeBase): boolean {
    return true;
  }

  prove(
    formula: TdfolFormula,
    kb: TdfolKnowledgeBase,
    timeoutMs = this.defaultTimeoutMs,
  ): ProofResult {
    const start = nowMs();
    const deadline = start + Math.min(timeoutMs, this.defaultTimeoutMs);
    const derived = [...kb.axioms, ...(kb.theorems ?? [])];
    const derivedKeys = new Set(derived.map(formulaKey));
    const steps: ProofStep[] = [];
    const theoremKey = formulaKey(formula);

    if (derivedKeys.has(theoremKey)) {
      return this.finish('proved', formula, [], start);
    }

    for (let iteration = 0; iteration < this.maxIterations; iteration += 1) {
      if (nowMs() > deadline) {
        return this.finish(
          'timeout',
          formula,
          steps,
          start,
          `Timeout after ${iteration} iterations`,
        );
      }

      const newApplications = this.applyRulesBounded(derived, derivedKeys, deadline);
      if (newApplications.length === 0) {
        return this.finish(
          'unknown',
          formula,
          steps,
          start,
          `Forward chaining exhausted after ${iteration} iterations`,
        );
      }

      for (const application of newApplications) {
        const key = formulaKey(application.conclusion);
        if (derivedKeys.has(key)) {
          continue;
        }
        derived.push(application.conclusion);
        derivedKeys.add(key);
        steps.push({
          id: `tdfol-strategy-step-${steps.length + 1}`,
          rule: application.rule,
          premises: application.premises.map(formatTdfolFormula),
          conclusion: formatTdfolFormula(application.conclusion),
          explanation: `Applied ${application.rule}`,
        });

        if (formulaEquals(application.conclusion, formula)) {
          return this.finish(
            'proved',
            formula,
            steps,
            start,
            `Proved in ${iteration + 1} iterations`,
          );
        }
        if (derived.length >= this.maxDerivedFormulas) {
          return this.finish('timeout', formula, steps, start, 'Derived formula budget exceeded');
        }
        if (nowMs() > deadline) {
          return this.finish(
            'timeout',
            formula,
            steps,
            start,
            `Timeout after ${iteration + 1} iterations`,
          );
        }
      }
    }

    return this.finish('timeout', formula, steps, start, 'Iteration budget exceeded');
  }

  getPriority(): number {
    return 70;
  }

  estimateCost(_formula: TdfolFormula, kb: TdfolKnowledgeBase): number {
    const kbSize = kb.axioms.length + (kb.theorems?.length ?? 0);
    return (kbSize * this.rules.length * this.maxIterations) / 1000;
  }

  toString(): string {
    return `${this.name} (${this.strategyType})`;
  }

  private applyRulesBounded(
    derived: TdfolFormula[],
    knownKeys: Set<string>,
    deadline: number,
  ): Array<{ rule: string; premises: TdfolFormula[]; conclusion: TdfolFormula }> {
    const applications = applyTdfolRules(derived.slice(0, this.binaryPremiseWindow), this.rules);
    const newApplications: Array<{
      rule: string;
      premises: TdfolFormula[];
      conclusion: TdfolFormula;
    }> = [];
    const localKeys = new Set(knownKeys);

    for (const application of applications) {
      if (nowMs() > deadline || newApplications.length >= this.maxNewFormulasPerIteration) {
        break;
      }
      const key = formulaKey(application.conclusion);
      if (localKeys.has(key)) {
        continue;
      }
      localKeys.add(key);
      newApplications.push(application);
    }

    return newApplications;
  }

  private finish(
    status: ProofStatus,
    theorem: TdfolFormula,
    steps: ProofStep[],
    start: number,
    error?: string,
  ): ProofResult {
    return {
      status,
      theorem: formatTdfolFormula(theorem),
      steps,
      method: this.strategyType,
      timeMs: Math.max(0, nowMs() - start),
      error,
    };
  }
}

export interface TdfolBackwardChainingStrategyOptions {
  maxDepth?: number;
  maxBranches?: number;
  defaultTimeoutMs?: number;
}

export class TdfolBackwardChainingStrategy implements TdfolProverStrategy {
  readonly name = 'Backward Chaining';
  readonly strategyType = 'backward_chaining' satisfies TdfolStrategyType;
  private readonly maxDepth: number;
  private readonly maxBranches: number;
  private readonly defaultTimeoutMs: number;

  constructor(options: TdfolBackwardChainingStrategyOptions = {}) {
    this.maxDepth = options.maxDepth ?? 12;
    this.maxBranches = options.maxBranches ?? 200;
    this.defaultTimeoutMs = options.defaultTimeoutMs ?? 2000;
  }

  canHandle(formula: TdfolFormula, kb: TdfolKnowledgeBase): boolean {
    if (containsFormula(kb, formula)) return true;
    if (formula.kind === 'binary' && formula.operator === 'AND') return true;
    return getImplications(kb).some((implication) => formulaEquals(implication.right, formula));
  }

  prove(
    formula: TdfolFormula,
    kb: TdfolKnowledgeBase,
    timeoutMs = this.defaultTimeoutMs,
  ): ProofResult {
    const start = nowMs();
    const deadline = start + Math.min(timeoutMs, this.defaultTimeoutMs);
    const state = {
      steps: [] as ProofStep[],
      branchCount: 0,
      visited: new Set<string>(),
      timeout: false,
      exhausted: false,
    };
    const proved = this.proveGoal(formula, kb, 0, deadline, state);
    const status: ProofStatus = proved ? 'proved' : state.timeout ? 'timeout' : 'unknown';
    return {
      status,
      theorem: formatTdfolFormula(formula),
      steps: state.steps,
      method: this.strategyType,
      timeMs: Math.max(0, nowMs() - start),
      error: proved
        ? undefined
        : state.timeout
          ? 'Backward chaining timeout or budget exceeded'
          : 'No backward proof found',
    };
  }

  getPriority(): number {
    return 60;
  }

  estimateCost(formula: TdfolFormula, kb: TdfolKnowledgeBase): number {
    const implications = getImplications(kb).filter((implication) =>
      formulaEquals(implication.right, formula),
    ).length;
    const kbSize = kb.axioms.length + (kb.theorems?.length ?? 0);
    return Math.max(1, (implications || 1) * Math.log2(kbSize + 2));
  }

  private proveGoal(
    goal: TdfolFormula,
    kb: TdfolKnowledgeBase,
    depth: number,
    deadline: number,
    state: {
      steps: ProofStep[];
      branchCount: number;
      visited: Set<string>;
      timeout: boolean;
      exhausted: boolean;
    },
  ): boolean {
    if (nowMs() > deadline || depth > this.maxDepth || state.branchCount >= this.maxBranches) {
      state.timeout = true;
      return false;
    }

    const goalKey = formulaKey(goal);
    if (state.visited.has(goalKey)) return false;
    state.visited.add(goalKey);

    const direct = [...kb.axioms, ...(kb.theorems ?? [])].find((candidate) =>
      formulaEquals(candidate, goal),
    );
    if (direct) {
      state.steps.push({
        id: `tdfol-backward-step-${state.steps.length + 1}`,
        rule: 'KnowledgeBaseLookup',
        premises: [],
        conclusion: formatTdfolFormula(direct),
        explanation: 'Goal matched an existing knowledge-base formula',
      });
      state.visited.delete(goalKey);
      return true;
    }

    if (goal.kind === 'binary' && goal.operator === 'AND') {
      const left = this.proveGoal(goal.left, kb, depth + 1, deadline, state);
      const right = left && this.proveGoal(goal.right, kb, depth + 1, deadline, state);
      if (left && right) {
        state.steps.push({
          id: `tdfol-backward-step-${state.steps.length + 1}`,
          rule: 'ConjunctionIntroduction',
          premises: [formatTdfolFormula(goal.left), formatTdfolFormula(goal.right)],
          conclusion: formatTdfolFormula(goal),
          explanation: 'Both conjunctive subgoals were proven',
        });
        state.visited.delete(goalKey);
        return true;
      }
    }

    const candidateRules = getImplications(kb).filter((implication) =>
      formulaEquals(implication.right, goal),
    );
    for (const implication of candidateRules) {
      state.branchCount += 1;
      if (this.proveGoal(implication.left, kb, depth + 1, deadline, state)) {
        state.steps.push({
          id: `tdfol-backward-step-${state.steps.length + 1}`,
          rule: 'BackwardModusPonens',
          premises: [formatTdfolFormula(implication.left), formatTdfolFormula(implication)],
          conclusion: formatTdfolFormula(goal),
          explanation: 'Reduced the goal to the implication antecedent and proved it',
        });
        state.visited.delete(goalKey);
        return true;
      }
    }

    state.visited.delete(goalKey);
    return false;
  }
}

export interface TdfolBidirectionalStrategyOptions {
  backward?: TdfolBackwardChainingStrategy;
  forward?: TdfolForwardChainingStrategy;
}

export class TdfolBidirectionalStrategy implements TdfolProverStrategy {
  readonly name = 'Bidirectional';
  readonly strategyType = 'bidirectional' satisfies TdfolStrategyType;
  private readonly backward: TdfolBackwardChainingStrategy;
  private readonly forward: TdfolForwardChainingStrategy;

  constructor(options: TdfolBidirectionalStrategyOptions = {}) {
    this.backward = options.backward ?? new TdfolBackwardChainingStrategy();
    this.forward = options.forward ?? new TdfolForwardChainingStrategy();
  }

  canHandle(formula: TdfolFormula, kb: TdfolKnowledgeBase): boolean {
    return this.backward.canHandle(formula, kb) || this.forward.canHandle(formula, kb);
  }

  prove(formula: TdfolFormula, kb: TdfolKnowledgeBase, timeoutMs?: number): ProofResult {
    const backwardResult = this.backward.prove(formula, kb, timeoutMs);
    if (backwardResult.status === 'proved' || backwardResult.status === 'timeout') {
      return { ...backwardResult, method: this.strategyType };
    }

    const forwardResult = this.forward.prove(formula, kb, timeoutMs);
    return {
      ...forwardResult,
      method: this.strategyType,
      steps: [...backwardResult.steps, ...forwardResult.steps],
      error:
        forwardResult.status === 'proved'
          ? undefined
          : (forwardResult.error ?? backwardResult.error),
    };
  }

  getPriority(): number {
    return 75;
  }

  estimateCost(formula: TdfolFormula, kb: TdfolKnowledgeBase): number {
    return Math.min(
      this.backward.estimateCost(formula, kb),
      this.forward.estimateCost(formula, kb) * 0.8,
    );
  }
}

export interface TdfolCecDelegate {
  readonly name: string;
  canProve(formula: TdfolFormula, kb: TdfolKnowledgeBase): boolean;
  prove(formula: TdfolFormula, kb: TdfolKnowledgeBase, timeoutMs?: number): ProofResult;
}

export interface TdfolLocalCecDelegateOptions {
  maxDepth?: number;
  maxIterations?: number;
  maxDerivedExpressions?: number;
  rules?: CecInferenceRule[];
  defaultTimeoutMs?: number;
}

export class TdfolLocalCecDelegate implements TdfolCecDelegate {
  readonly name = 'Local CEC Delegate';
  private readonly maxDepth: number;
  private readonly maxIterations: number;
  private readonly maxDerivedExpressions: number;
  private readonly rules: CecInferenceRule[];
  private readonly defaultTimeoutMs: number;

  constructor(options: TdfolLocalCecDelegateOptions = {}) {
    this.maxDepth = options.maxDepth ?? 8;
    this.maxIterations = options.maxIterations ?? 6;
    this.maxDerivedExpressions = options.maxDerivedExpressions ?? 150;
    this.rules = options.rules ?? createDefaultCecDelegateRules();
    this.defaultTimeoutMs = options.defaultTimeoutMs ?? 2000;
  }

  canProve(formula: TdfolFormula, kb: TdfolKnowledgeBase): boolean {
    return (
      isCecShapedFormula(formula) ||
      containsFormula(kb, formula) ||
      getImplications(kb).some((rule) => formulaEquals(rule.right, formula))
    );
  }

  prove(
    formula: TdfolFormula,
    kb: TdfolKnowledgeBase,
    timeoutMs = this.defaultTimeoutMs,
  ): ProofResult {
    const start = nowMs();
    const deadline = start + Math.min(timeoutMs, this.defaultTimeoutMs);
    const theoremCec = tdfolToCecExpression(formula);
    const analysis = analyzeCecExpression(theoremCec);
    const steps: ProofStep[] = [];
    const proved =
      this.proveGoal(formula, kb, deadline, 0, new Set(), steps) ||
      this.proveWithCecRules(theoremCec, kb, deadline, steps);
    return {
      status: proved ? 'proved' : nowMs() > deadline ? 'timeout' : 'unknown',
      theorem: formatTdfolFormula(formula),
      steps,
      method: 'cec_delegate:local',
      timeMs: Math.max(0, nowMs() - start),
      error: proved
        ? undefined
        : `Local CEC delegate could not prove ${formatCecExpression(theoremCec)}; predicates=${analysis.predicates.join(',') || 'none'}`,
    };
  }

  private proveWithCecRules(
    theorem: CecExpression,
    kb: TdfolKnowledgeBase,
    deadline: number,
    steps: ProofStep[],
  ): boolean {
    const expressions = [...kb.axioms, ...(kb.theorems ?? [])].map(tdfolToCecExpression);
    const knownKeys = new Set<string>();
    const theoremKey = cecExpressionKey(theorem);

    for (const expression of expressions) {
      const key = cecExpressionKey(expression);
      knownKeys.add(key);
      if (key === theoremKey) {
        steps.push({
          id: `tdfol-cec-delegate-step-${steps.length + 1}`,
          rule: 'CecKnowledgeBaseLookup',
          premises: [],
          conclusion: formatCecExpression(expression),
          explanation: 'Translated TDFOL goal to CEC and matched a local knowledge-base formula',
        });
        return true;
      }
    }

    for (let iteration = 0; iteration < this.maxIterations; iteration += 1) {
      if (nowMs() > deadline || expressions.length >= this.maxDerivedExpressions) {
        return false;
      }

      const applications = applyCecRules(expressions, this.rules);
      let added = 0;
      for (const application of applications) {
        if (nowMs() > deadline || expressions.length >= this.maxDerivedExpressions) {
          return false;
        }
        const key = cecExpressionKey(application.conclusion);
        if (knownKeys.has(key)) {
          continue;
        }
        knownKeys.add(key);
        expressions.push(application.conclusion);
        added += 1;
        steps.push({
          id: `tdfol-cec-delegate-step-${steps.length + 1}`,
          rule: application.rule,
          premises: application.premises.map(formatCecExpression),
          conclusion: formatCecExpression(application.conclusion),
          explanation: 'Applied a browser-native CEC inference rule to translated TDFOL formulas',
        });
        if (cecExpressionEquals(application.conclusion, theorem)) {
          return true;
        }
      }

      if (added === 0) {
        return false;
      }
    }

    return false;
  }

  private proveGoal(
    goal: TdfolFormula,
    kb: TdfolKnowledgeBase,
    deadline: number,
    depth: number,
    visited: Set<string>,
    steps: ProofStep[],
  ): boolean {
    if (nowMs() > deadline || depth > this.maxDepth) return false;
    const key = formulaKey(goal);
    if (visited.has(key)) return false;
    visited.add(key);

    const direct = [...kb.axioms, ...(kb.theorems ?? [])].find((candidate) =>
      formulaEquals(candidate, goal),
    );
    if (direct) {
      steps.push({
        id: `tdfol-cec-delegate-step-${steps.length + 1}`,
        rule: 'CecKnowledgeBaseLookup',
        premises: [],
        conclusion: formatCecExpression(tdfolToCecExpression(direct)),
        explanation: 'Translated TDFOL goal to CEC and matched a local knowledge-base formula',
      });
      visited.delete(key);
      return true;
    }

    if (goal.kind === 'deontic' && goal.operator === 'PROHIBITION') {
      const obligationOfNot: TdfolFormula = {
        kind: 'deontic',
        operator: 'OBLIGATION',
        formula: { kind: 'unary', operator: 'NOT', formula: goal.formula },
      };
      if (this.proveGoal(obligationOfNot, kb, deadline, depth + 1, visited, steps)) {
        steps.push({
          id: `tdfol-cec-delegate-step-${steps.length + 1}`,
          rule: 'CecDeonticProhibitionEquivalence',
          premises: [formatCecExpression(tdfolToCecExpression(obligationOfNot))],
          conclusion: formatCecExpression(tdfolToCecExpression(goal)),
          explanation:
            'Used the CEC deontic equivalence between prohibition and obligation of negation',
        });
        visited.delete(key);
        return true;
      }
    }

    for (const implication of getImplications(kb).filter((rule) =>
      formulaEquals(rule.right, goal),
    )) {
      if (this.proveGoal(implication.left, kb, deadline, depth + 1, visited, steps)) {
        steps.push({
          id: `tdfol-cec-delegate-step-${steps.length + 1}`,
          rule: 'CecDelegatedModusPonens',
          premises: [
            formatCecExpression(tdfolToCecExpression(implication.left)),
            formatCecExpression(tdfolToCecExpression(implication)),
          ],
          conclusion: formatCecExpression(tdfolToCecExpression(goal)),
          explanation: 'Reduced the delegated CEC goal through a local implication',
        });
        visited.delete(key);
        return true;
      }
    }

    visited.delete(key);
    return false;
  }
}

function createDefaultCecDelegateRules(): CecInferenceRule[] {
  const rules = [...getAllCecRules(), ...getTemporalCecRules(), ...getDeonticCecRules()];
  const seen = new Set<string>();
  return rules.filter((rule) => {
    if (seen.has(rule.name)) {
      return false;
    }
    seen.add(rule.name);
    return true;
  });
}

export interface TdfolCecDelegateStrategyOptions {
  delegate?: TdfolCecDelegate;
}

export class TdfolCecDelegateStrategy implements TdfolProverStrategy {
  readonly name = 'CEC Delegate';
  readonly strategyType = 'cec_delegate' satisfies TdfolStrategyType;
  private readonly delegate: TdfolCecDelegate;

  constructor(options: TdfolCecDelegateStrategyOptions = {}) {
    this.delegate = options.delegate ?? new TdfolLocalCecDelegate();
  }

  canHandle(formula: TdfolFormula, kb: TdfolKnowledgeBase): boolean {
    return this.delegate.canProve(formula, kb);
  }

  prove(formula: TdfolFormula, kb: TdfolKnowledgeBase, timeoutMs?: number): ProofResult {
    const result = this.delegate.prove(formula, kb, timeoutMs);
    return { ...result, method: this.strategyType };
  }

  getPriority(): number {
    return 65;
  }

  estimateCost(formula: TdfolFormula, kb: TdfolKnowledgeBase): number {
    const analysis = analyzeCecExpression(tdfolToCecExpression(formula));
    const kbSize = kb.axioms.length + (kb.theorems?.length ?? 0);
    return Math.max(1, analysis.nodeCount + analysis.maxDepth + kbSize / 2);
  }
}

export interface TdfolModalTableauxStrategyOptions {
  logicType?: TdfolModalLogicType | 'auto';
  maxWorlds?: number;
  maxDepth?: number;
}

export class TdfolModalTableauxStrategy implements TdfolProverStrategy {
  readonly name = 'Modal Tableaux';
  readonly strategyType = 'modal_tableaux' satisfies TdfolStrategyType;
  private readonly logicType: TdfolModalLogicType | 'auto';
  private readonly tableauxOptions: Omit<TdfolModalTableauxOptions, 'logicType'>;

  constructor(options: TdfolModalTableauxStrategyOptions = {}) {
    this.logicType = options.logicType ?? 'auto';
    this.tableauxOptions = {
      maxWorlds: options.maxWorlds,
      maxDepth: options.maxDepth,
    };
  }

  canHandle(formula: TdfolFormula): boolean {
    return isModalFormula(formula);
  }

  prove(formula: TdfolFormula, kb: TdfolKnowledgeBase, _timeoutMs?: number): ProofResult {
    const start = nowMs();
    const direct = [...kb.axioms, ...(kb.theorems ?? [])].find((candidate) =>
      formulaEquals(candidate, formula),
    );
    if (direct) {
      return {
        status: 'proved',
        theorem: formatTdfolFormula(formula),
        steps: [
          {
            id: 'tdfol-modal-tableaux-direct-1',
            rule: 'KnowledgeBaseLookup',
            premises: [],
            conclusion: formatTdfolFormula(direct),
            explanation: 'Found in knowledge base',
          },
        ],
        method: this.strategyType,
        timeMs: Math.max(0, nowMs() - start),
      };
    }

    const logicType = this.selectModalLogicType(formula);
    const result = new TdfolModalTableaux({ ...this.tableauxOptions, logicType }).prove(formula);
    return {
      status: result.isValid ? 'proved' : 'unknown',
      theorem: formatTdfolFormula(formula),
      steps: result.proofSteps.map((step, index) => ({
        id: `tdfol-modal-tableaux-step-${index + 1}`,
        rule: 'ModalTableaux',
        premises: [],
        conclusion: step,
        explanation: step,
      })),
      method: `${this.strategyType}:${logicType}`,
      timeMs: Math.max(0, nowMs() - start),
      error: result.isValid
        ? undefined
        : `Open branch remains after ${result.totalBranches} branch(es)`,
    };
  }

  getPriority(): number {
    return 80;
  }

  estimateCost(formula: TdfolFormula): number {
    let cost = 2;
    if (hasNestedTemporalFormula(formula)) cost *= 2;
    if (hasDeonticFormula(formula) && hasTemporalFormula(formula)) cost *= 1.5;
    return cost;
  }

  selectModalLogicType(formula: TdfolFormula): TdfolModalLogicType {
    if (this.logicType !== 'auto') return this.logicType;
    if (hasDeonticFormula(formula)) return 'D';
    if (hasTemporalFormula(formula)) return 'S4';
    return 'K';
  }

  toString(): string {
    return `${this.name} (${this.strategyType})`;
  }
}

export interface TdfolStrategySelectorOptions {
  strategies?: TdfolProverStrategy[];
}

export class TdfolStrategySelector {
  private strategies: TdfolProverStrategy[];

  constructor(options: TdfolStrategySelectorOptions = {}) {
    this.strategies = [...(options.strategies ?? createDefaultTdfolStrategies())].sort(
      (left, right) => right.getPriority() - left.getPriority(),
    );
  }

  selectStrategy(
    formula: TdfolFormula,
    kb: TdfolKnowledgeBase,
    preferLowCost = false,
  ): TdfolProverStrategy {
    if (this.strategies.length === 0) {
      throw new Error('No strategies available for selection');
    }

    const applicable = this.strategies.filter((strategy) => strategy.canHandle(formula, kb));
    if (applicable.length === 0) {
      return this.getFallbackStrategy();
    }

    if (preferLowCost) {
      return applicable.reduce((best, candidate) =>
        candidate.estimateCost(formula, kb) < best.estimateCost(formula, kb) ? candidate : best,
      );
    }

    return applicable[0];
  }

  selectMultiple(
    formula: TdfolFormula,
    kb: TdfolKnowledgeBase,
    maxStrategies = 3,
  ): TdfolProverStrategy[] {
    if (this.strategies.length === 0 || maxStrategies <= 0) {
      return [];
    }

    const applicable = this.strategies.filter((strategy) => strategy.canHandle(formula, kb));
    return (applicable.length > 0 ? applicable : [this.getFallbackStrategy()]).slice(
      0,
      maxStrategies,
    );
  }

  getStrategyInfo(formula?: TdfolFormula, kb?: TdfolKnowledgeBase): TdfolStrategyInfo[] {
    return this.strategies.map((strategy) => ({
      name: strategy.name,
      type: strategy.strategyType,
      priority: strategy.getPriority(),
      cost: formula && kb ? strategy.estimateCost(formula, kb) : undefined,
    }));
  }

  addStrategy(strategy: TdfolProverStrategy): void {
    this.strategies.push(strategy);
    this.strategies.sort((left, right) => right.getPriority() - left.getPriority());
  }

  proveWithSelectedStrategy(
    formula: TdfolFormula,
    kb: TdfolKnowledgeBase,
    options: { preferLowCost?: boolean; timeoutMs?: number } = {},
  ): ProofResult {
    const strategy = this.selectStrategy(formula, kb, options.preferLowCost);
    return strategy.prove(formula, kb, options.timeoutMs);
  }

  private getFallbackStrategy(): TdfolProverStrategy {
    const forwardChaining = this.strategies.find(
      (strategy) => strategy.strategyType === 'forward_chaining',
    );
    return forwardChaining ?? this.strategies[0];
  }
}

export function createDefaultTdfolStrategies(): TdfolProverStrategy[] {
  return [
    new TdfolModalTableauxStrategy(),
    new TdfolBidirectionalStrategy(),
    new TdfolForwardChainingStrategy(),
    new TdfolCecDelegateStrategy(),
    new TdfolBackwardChainingStrategy(),
  ];
}

export function proveTdfolWithStrategySelection(
  theorem: TdfolFormula,
  kb: TdfolKnowledgeBase,
  options: { strategies?: TdfolProverStrategy[]; preferLowCost?: boolean; timeoutMs?: number } = {},
): ProofResult {
  return new TdfolStrategySelector({ strategies: options.strategies }).proveWithSelectedStrategy(
    theorem,
    kb,
    {
      preferLowCost: options.preferLowCost,
      timeoutMs: options.timeoutMs,
    },
  );
}

function nowMs(): number {
  return typeof globalThis.performance?.now === 'function'
    ? globalThis.performance.now()
    : Date.now();
}

function containsFormula(kb: TdfolKnowledgeBase, formula: TdfolFormula): boolean {
  return [...kb.axioms, ...(kb.theorems ?? [])].some((candidate) =>
    formulaEquals(candidate, formula),
  );
}

function getImplications(kb: TdfolKnowledgeBase): TdfolBinaryFormula[] {
  return [...kb.axioms, ...(kb.theorems ?? [])].filter(
    (formula): formula is TdfolBinaryFormula =>
      formula.kind === 'binary' && formula.operator === 'IMPLIES',
  );
}

function isCecShapedFormula(formula: TdfolFormula): boolean {
  return traverseFormula(
    formula,
    (node) => node.kind === 'deontic' || node.kind === 'temporal' || node.kind === 'quantified',
  );
}

export function tdfolToCecExpression(formula: TdfolFormula): CecExpression {
  switch (formula.kind) {
    case 'predicate':
      return {
        kind: 'application',
        name: formula.name,
        args: formula.args.map(tdfolTermToCecExpression),
      };
    case 'unary':
      return { kind: 'unary', operator: 'not', expression: tdfolToCecExpression(formula.formula) };
    case 'binary':
      return {
        kind: 'binary',
        operator: tdfolBinaryToCecOperator(formula.operator),
        left: tdfolToCecExpression(formula.left),
        right: tdfolToCecExpression(formula.right),
      };
    case 'quantified':
      return {
        kind: 'quantified',
        quantifier: formula.quantifier === 'FORALL' ? 'forall' : 'exists',
        variable: formula.variable.name,
        expression: tdfolToCecExpression(formula.formula),
      };
    case 'deontic':
      return {
        kind: 'unary',
        operator:
          formula.operator === 'OBLIGATION' ? 'O' : formula.operator === 'PERMISSION' ? 'P' : 'F',
        expression: tdfolToCecExpression(formula.formula),
      };
    case 'temporal':
      return {
        kind: 'unary',
        operator:
          formula.operator === 'ALWAYS'
            ? 'always'
            : formula.operator === 'EVENTUALLY'
              ? 'eventually'
              : 'next',
        expression: tdfolToCecExpression(formula.formula),
      };
  }
}

function tdfolTermToCecExpression(term: TdfolTerm): CecExpression {
  if (term.kind === 'function') {
    return { kind: 'application', name: term.name, args: term.args.map(tdfolTermToCecExpression) };
  }
  return { kind: 'atom', name: term.name };
}

function tdfolBinaryToCecOperator(operator: TdfolBinaryFormula['operator']): CecBinaryOperator {
  const operators: Record<TdfolBinaryFormula['operator'], CecBinaryOperator> = {
    AND: 'and',
    OR: 'or',
    IMPLIES: 'implies',
    IFF: 'iff',
    XOR: 'xor',
    UNTIL: 'until',
  };
  return operators[operator];
}

function isModalFormula(formula: TdfolFormula): boolean {
  return hasDeonticFormula(formula) || hasTemporalFormula(formula);
}

function hasDeonticFormula(formula: TdfolFormula): boolean {
  return traverseFormula(formula, (node) => node.kind === 'deontic');
}

function hasTemporalFormula(formula: TdfolFormula): boolean {
  return traverseFormula(formula, (node) => node.kind === 'temporal');
}

function hasNestedTemporalFormula(formula: TdfolFormula): boolean {
  return temporalDepth(formula) >= 2;
}

function traverseFormula(
  formula: TdfolFormula,
  predicate: (formula: TdfolFormula) => boolean,
): boolean {
  if (predicate(formula)) return true;
  switch (formula.kind) {
    case 'predicate':
      return false;
    case 'unary':
    case 'temporal':
    case 'deontic':
    case 'quantified':
      return traverseFormula(formula.formula, predicate);
    case 'binary':
      return traverseFormula(formula.left, predicate) || traverseFormula(formula.right, predicate);
  }
}

function temporalDepth(formula: TdfolFormula, depth = 0): number {
  const nextDepth = formula.kind === 'temporal' ? depth + 1 : depth;
  switch (formula.kind) {
    case 'predicate':
      return nextDepth;
    case 'unary':
    case 'temporal':
    case 'deontic':
    case 'quantified':
      return temporalDepth(formula.formula, nextDepth);
    case 'binary':
      return Math.max(
        temporalDepth(formula.left, nextDepth),
        temporalDepth(formula.right, nextDepth),
      );
  }
}

function formulaNodeCount(formula: TdfolFormula): number {
  switch (formula.kind) {
    case 'predicate':
      return 1;
    case 'unary':
    case 'temporal':
    case 'deontic':
    case 'quantified':
      return 1 + formulaNodeCount(formula.formula);
    case 'binary':
      return 1 + formulaNodeCount(formula.left) + formulaNodeCount(formula.right);
  }
}

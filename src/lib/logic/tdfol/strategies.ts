import type { ProofResult, ProofStatus, ProofStep } from '../types';
import type { TdfolFormula } from './ast';
import { formatTdfolFormula } from './formatter';
import { applyTdfolRules, formulaEquals, formulaKey, getAllTdfolRules, type TdfolInferenceRule } from './inferenceRules';
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

  canHandle(): boolean {
    return true;
  }

  prove(formula: TdfolFormula, kb: TdfolKnowledgeBase, timeoutMs = this.defaultTimeoutMs): ProofResult {
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
        return this.finish('timeout', formula, steps, start, `Timeout after ${iteration} iterations`);
      }

      const newApplications = this.applyRulesBounded(derived, derivedKeys, deadline);
      if (newApplications.length === 0) {
        return this.finish('unknown', formula, steps, start, `Forward chaining exhausted after ${iteration} iterations`);
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
          return this.finish('proved', formula, steps, start, `Proved in ${iteration + 1} iterations`);
        }
        if (derived.length >= this.maxDerivedFormulas) {
          return this.finish('timeout', formula, steps, start, 'Derived formula budget exceeded');
        }
        if (nowMs() > deadline) {
          return this.finish('timeout', formula, steps, start, `Timeout after ${iteration + 1} iterations`);
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
    const newApplications: Array<{ rule: string; premises: TdfolFormula[]; conclusion: TdfolFormula }> = [];
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

  private finish(status: ProofStatus, theorem: TdfolFormula, steps: ProofStep[], start: number, error?: string): ProofResult {
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
    const direct = [...kb.axioms, ...(kb.theorems ?? [])].find((candidate) => formulaEquals(candidate, formula));
    if (direct) {
      return {
        status: 'proved',
        theorem: formatTdfolFormula(formula),
        steps: [{
          id: 'tdfol-modal-tableaux-direct-1',
          rule: 'KnowledgeBaseLookup',
          premises: [],
          conclusion: formatTdfolFormula(direct),
          explanation: 'Found in knowledge base',
        }],
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
      error: result.isValid ? undefined : `Open branch remains after ${result.totalBranches} branch(es)`,
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

  selectStrategy(formula: TdfolFormula, kb: TdfolKnowledgeBase, preferLowCost = false): TdfolProverStrategy {
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

  selectMultiple(formula: TdfolFormula, kb: TdfolKnowledgeBase, maxStrategies = 3): TdfolProverStrategy[] {
    if (this.strategies.length === 0 || maxStrategies <= 0) {
      return [];
    }

    const applicable = this.strategies.filter((strategy) => strategy.canHandle(formula, kb));
    return (applicable.length > 0 ? applicable : [this.getFallbackStrategy()]).slice(0, maxStrategies);
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
    const forwardChaining = this.strategies.find((strategy) => strategy.strategyType === 'forward_chaining');
    return forwardChaining ?? this.strategies[0];
  }
}

export function createDefaultTdfolStrategies(): TdfolProverStrategy[] {
  return [new TdfolModalTableauxStrategy(), new TdfolForwardChainingStrategy()];
}

export function proveTdfolWithStrategySelection(
  theorem: TdfolFormula,
  kb: TdfolKnowledgeBase,
  options: { strategies?: TdfolProverStrategy[]; preferLowCost?: boolean; timeoutMs?: number } = {},
): ProofResult {
  return new TdfolStrategySelector({ strategies: options.strategies }).proveWithSelectedStrategy(theorem, kb, {
    preferLowCost: options.preferLowCost,
    timeoutMs: options.timeoutMs,
  });
}

function nowMs(): number {
  return typeof performance !== 'undefined' && typeof performance.now === 'function' ? performance.now() : Date.now();
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

function traverseFormula(formula: TdfolFormula, predicate: (formula: TdfolFormula) => boolean): boolean {
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
      return Math.max(temporalDepth(formula.left, nextDepth), temporalDepth(formula.right, nextDepth));
  }
}

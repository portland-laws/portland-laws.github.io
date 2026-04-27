import type { ProofStep } from '../types';
import type { CecExpression } from './ast';
import { formatCecExpression } from './formatter';
import { parseCecExpression } from './parser';
import { CecModalTableaux, type CecModalLogicType } from './modalTableaux';
import { CecProver, type CecProverOptions } from './prover';

export type CecShadowModalLogic = 'K' | 'T' | 'S4' | 'S5' | 'D' | 'LP' | 'LP1' | 'LP2';
export type CecShadowProofStatus = 'success' | 'failure' | 'timeout' | 'unknown' | 'error';
export type CecModalOperator = 'necessary' | 'possible' | 'belief' | 'knowledge' | 'says' | 'perceives';
export type CecShadowFormula = CecExpression | string;

export interface CecShadowProofTree {
  goal: CecShadowFormula;
  steps: ProofStep[];
  status: CecShadowProofStatus;
  logic: CecShadowModalLogic;
  metadata: Record<string, unknown>;
  isSuccessful(): boolean;
  getDepth(): number;
}

export interface CecShadowProblemFile {
  name: string;
  logic: CecShadowModalLogic;
  assumptions: CecShadowFormula[];
  goals: CecShadowFormula[];
  metadata?: Record<string, unknown>;
}

export interface CecShadowStatistics {
  proofsAttempted: number;
  proofsSucceeded: number;
  proofsFailed: number;
  averageSteps: number;
}

export interface CecShadowProverOptions extends CecProverOptions {
  maxWorlds?: number;
  maxDepth?: number;
}

export class CecShadowProof implements CecShadowProofTree {
  constructor(
    readonly goal: CecShadowFormula,
    readonly steps: ProofStep[],
    readonly status: CecShadowProofStatus,
    readonly logic: CecShadowModalLogic,
    readonly metadata: Record<string, unknown> = {},
  ) {}

  isSuccessful(): boolean {
    return this.status === 'success';
  }

  getDepth(): number {
    return this.steps.length;
  }
}

export class CecShadowProver {
  readonly logic: CecShadowModalLogic;
  readonly proofCache = new Map<string, CecShadowProofTree>();
  protected readonly statistics: CecShadowStatistics = {
    proofsAttempted: 0,
    proofsSucceeded: 0,
    proofsFailed: 0,
    averageSteps: 0,
  };

  constructor(logic: CecShadowModalLogic = 'K', protected readonly options: CecShadowProverOptions = {}) {
    this.logic = logic;
  }

  prove(goal: CecShadowFormula, assumptions: CecShadowFormula[] = []): CecShadowProofTree {
    this.statistics.proofsAttempted += 1;
    const cacheKey = this.cacheKey(goal, assumptions);
    const cached = this.proofCache.get(cacheKey);
    if (cached) return cached;

    let proof: CecShadowProofTree;
    try {
      proof = this.proveUncached(goal, assumptions);
    } catch (error) {
      proof = new CecShadowProof(goal, [], 'error', this.logic, {
        method: 'shadow-prover',
        error: error instanceof Error ? error.message : 'Unknown CEC ShadowProver error',
      });
    }

    this.proofCache.set(cacheKey, proof);
    this.recordProof(proof);
    return proof;
  }

  proveProblem(problem: CecShadowProblemFile): CecShadowProofTree[] {
    const prover = problem.logic === this.logic ? this : createCecShadowProver(problem.logic, this.options);
    return problem.goals.map((goal) => prover.prove(goal, problem.assumptions));
  }

  getStatistics(): CecShadowStatistics {
    return { ...this.statistics };
  }

  clearCache(): void {
    this.proofCache.clear();
  }

  protected proveUncached(goal: CecShadowFormula, assumptions: CecShadowFormula[]): CecShadowProofTree {
    if (!isTableauxLogic(this.logic)) {
      return new CecShadowProof(goal, [], 'unknown', this.logic, {
        method: 'shadow-prover',
        message: `Unsupported browser-native ShadowProver logic: ${this.logic}`,
      });
    }

    const goalExpression = toCecExpression(goal);
    const assumptionExpressions = assumptions.map(toCecExpression);
    if (assumptionExpressions.some((assumption) => formatCecExpression(assumption) === formatCecExpression(goalExpression))) {
      return new CecShadowProof(goal, [], 'success', this.logic, { method: 'direct-assumption' });
    }

    const forwardResult = new CecProver(this.options).prove(goalExpression, { axioms: assumptionExpressions });
    if (forwardResult.status === 'proved') {
      return new CecShadowProof(goal, forwardResult.steps, 'success', this.logic, {
        method: forwardResult.method ?? 'cec-forward-chaining',
      });
    }
    if (forwardResult.status === 'timeout') {
      return new CecShadowProof(goal, forwardResult.steps, 'timeout', this.logic, {
        method: forwardResult.method ?? 'cec-forward-chaining',
        message: forwardResult.error,
      });
    }

    const modalFormula = assumptionExpressions.length > 0 ? assumptionsImplyGoal(assumptionExpressions, goalExpression) : goalExpression;
    const tableaux = new CecModalTableaux({
      logicType: this.logic,
      maxDepth: this.options.maxDepth,
      maxWorlds: this.options.maxWorlds,
    }).prove(modalFormula);

    const steps = tableaux.proofSteps.map((step, index) => ({
      id: `cec-shadow-step-${index + 1}`,
      rule: 'cec-modal-tableaux',
      premises: [],
      conclusion: step,
      explanation: step,
    }));

    return new CecShadowProof(goal, steps, tableaux.isValid ? 'success' : 'failure', this.logic, {
      method: 'tableau',
      closed: tableaux.isValid,
      closedBranches: tableaux.closedBranches,
      totalBranches: tableaux.totalBranches,
      worlds: tableaux.openBranch?.worlds.size ?? tableaux.closedBranches,
    });
  }

  protected recordProof(proof: CecShadowProofTree): void {
    if (proof.status === 'success') this.statistics.proofsSucceeded += 1;
    else this.statistics.proofsFailed += 1;

    const completed = this.statistics.proofsSucceeded + this.statistics.proofsFailed;
    this.statistics.averageSteps =
      completed === 0
        ? 0
        : (this.statistics.averageSteps * (completed - 1) + proof.steps.length) / completed;
  }

  private cacheKey(goal: CecShadowFormula, assumptions: CecShadowFormula[]): string {
    return JSON.stringify({
      logic: this.logic,
      goal: formulaKey(goal),
      assumptions: assumptions.map(formulaKey).sort(),
      options: {
        maxDepth: this.options.maxDepth,
        maxWorlds: this.options.maxWorlds,
        maxSteps: this.options.maxSteps,
        maxDerivedExpressions: this.options.maxDerivedExpressions,
      },
    });
  }
}

export class CecKProver extends CecShadowProver {
  constructor(options: CecShadowProverOptions = {}) {
    super('K', options);
  }
}

export class CecS4Prover extends CecShadowProver {
  constructor(options: CecShadowProverOptions = {}) {
    super('S4', options);
  }
}

export class CecS5Prover extends CecShadowProver {
  constructor(options: CecShadowProverOptions = {}) {
    super('S5', options);
  }
}

export class CecCognitiveCalculusProver extends CecShadowProver {
  readonly cognitiveAxioms = [
    'K_distribution',
    'K_necessitation',
    'K_truth',
    'K_positive_introspection',
    'K_negative_introspection',
    'B_distribution',
    'B_consistency',
    'B_positive_introspection',
    'B_negative_introspection',
    'knowledge_implies_belief',
    'belief_revision',
    'perception_to_knowledge',
    'perception_veridical',
    'says_to_belief',
    'truthful_communication',
    'intention_consistency',
    'intention_persistence',
    'goal_consistency',
    'achievement',
  ];

  constructor(options: CecShadowProverOptions = {}) {
    super('S5', options);
  }

  applyCognitiveRules(formulas: CecShadowFormula[]): string[] {
    const derived: string[] = [];
    for (const formula of formulas.map(formulaKey)) {
      if (formula.startsWith('K(')) {
        const inner = formula.slice(2, -1);
        derived.push(inner, `B(${inner})`);
        if (!formula.startsWith('K(K(')) derived.push(`K(${formula})`);
      }
      if (formula.startsWith('B(') && !formula.startsWith('B(B(')) derived.push(`B(${formula})`);
      if (formula.startsWith('P(')) derived.push(`K(${formula.slice(2, -1)})`);
    }
    return [...new Set(derived)];
  }

  protected proveUncached(goal: CecShadowFormula, assumptions: CecShadowFormula[]): CecShadowProofTree {
    const derived = this.applyCognitiveRules(assumptions);
    if (derived.includes(formulaKey(goal))) {
      return new CecShadowProof(
        goal,
        [
          {
            id: 'cec-shadow-cognitive-step-1',
            rule: 'cognitive-calculus',
            premises: assumptions.map(formulaKey),
            conclusion: formulaKey(goal),
            explanation: 'Applied browser-native cognitive ShadowProver rule subset.',
          },
        ],
        'success',
        this.logic,
        {
          method: 'cognitive_calculus',
          axioms: this.cognitiveAxioms,
          cognitiveRulesApplied: derived.length,
        },
      );
    }

    const proof = super.proveUncached(goal, [...assumptions, ...derived.filter(isCecSource)]);
    return new CecShadowProof(proof.goal, proof.steps, proof.status, proof.logic, {
      ...proof.metadata,
      method: proof.metadata.method ?? 'cognitive_calculus',
      axioms: this.cognitiveAxioms,
      cognitiveRulesApplied: derived.length,
    });
  }
}

export function createCecShadowProver(logic: CecShadowModalLogic, options: CecShadowProverOptions = {}): CecShadowProver {
  if (logic === 'K') return new CecKProver(options);
  if (logic === 'T' || logic === 'D') return new CecShadowProver(logic, options);
  if (logic === 'S4') return new CecS4Prover(options);
  if (logic === 'S5') return new CecS5Prover(options);
  throw new Error(`Unsupported modal logic: ${logic}. Use K, T, D, S4, or S5 for browser-native ShadowProver.`);
}

export function createCecCognitiveProver(options: CecShadowProverOptions = {}): CecCognitiveCalculusProver {
  return new CecCognitiveCalculusProver(options);
}

export function readCecShadowProblemObject(problem: Partial<CecShadowProblemFile>): CecShadowProblemFile {
  return {
    name: problem.name ?? 'placeholder',
    logic: problem.logic ?? 'K',
    assumptions: problem.assumptions ?? [],
    goals: problem.goals ?? [],
    metadata: problem.metadata ?? { message: 'Browser-native object problem reader' },
  };
}

function assumptionsImplyGoal(assumptions: CecExpression[], goal: CecExpression): CecExpression {
  const premise = assumptions.reduce((left, right) => ({ kind: 'binary', operator: 'and', left, right }) as CecExpression);
  return { kind: 'binary', operator: 'implies', left: premise, right: goal };
}

function isTableauxLogic(logic: CecShadowModalLogic): logic is CecModalLogicType {
  return logic === 'K' || logic === 'T' || logic === 'D' || logic === 'S4' || logic === 'S5';
}

function formulaKey(formula: CecShadowFormula): string {
  return typeof formula === 'string' ? formula : formatCecExpression(formula);
}

function toCecExpression(formula: CecShadowFormula): CecExpression {
  return typeof formula === 'string' ? parseCecExpression(formula) : formula;
}

function isCecSource(value: string): boolean {
  try {
    parseCecExpression(value);
    return true;
  } catch {
    return false;
  }
}

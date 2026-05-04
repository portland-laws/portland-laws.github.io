import type { ProofStatus } from '../types';
import type { CecExpression } from './ast';
import { formatCecExpression } from './formatter';
import {
  CecModusPonensRule,
  CecTemporalTRule,
  CecUniversalModusPonensRule,
  type CecInferenceRule,
} from './inferenceRules';
import type { CecNativeRuleGroupName } from './nativeRuleGroups';
import {
  CecProver,
  type CecKnowledgeBase,
  type CecProofResult,
  type CecProverOptions,
} from './prover';

export const CEC_PROVER_MANAGER_RUNTIME = {
  module: 'logic/CEC/provers/prover_manager.py',
  runtime: 'browser-native-typescript',
  pythonRuntime: false,
  serverDelegation: false,
} as const;

export interface CecProverManagerStrategy {
  name: string;
  ruleGroups?: CecNativeRuleGroupName[];
  rules?: CecInferenceRule[];
  maxSteps?: number;
  maxDerivedExpressions?: number;
}

export interface CecProverManagerOptions extends CecProverOptions {
  strategies?: CecProverManagerStrategy[];
  stopOnFirstProof?: boolean;
}

export interface CecManagedProofAttempt {
  strategy: string;
  status: ProofStatus;
  method?: string;
  ruleGroups: CecNativeRuleGroupName[];
  stepCount: number;
  error?: string;
}

export interface CecProverManagerResult extends CecProofResult {
  attempts: CecManagedProofAttempt[];
  manager: {
    strategyCount: number;
    selectedStrategy?: string;
    pythonRuntime: false;
    serverDelegation: false;
  };
}

const DEFAULT_MANAGER_STRATEGIES: CecProverManagerStrategy[] = [
  { name: 'direct', rules: [] },
  {
    name: 'temporal-propositional-specialized',
    ruleGroups: ['temporal', 'propositional', 'specialized'],
    rules: [CecTemporalTRule, CecModusPonensRule, CecUniversalModusPonensRule],
  },
  { name: 'cognitive-deontic-modal', ruleGroups: ['cognitive', 'deontic', 'modal'] },
  { name: 'resolution', ruleGroups: ['resolution'] },
];

export class CecProverManager {
  private readonly strategies: CecProverManagerStrategy[];
  private readonly stopOnFirstProof: boolean;

  constructor(private readonly options: CecProverManagerOptions = {}) {
    this.strategies = (options.strategies ?? DEFAULT_MANAGER_STRATEGIES).map(copyStrategy);
    this.stopOnFirstProof = options.stopOnFirstProof ?? true;
  }

  getStrategies(): CecProverManagerStrategy[] {
    return this.strategies.map(copyStrategy);
  }

  prove(theorem: CecExpression, kb: CecKnowledgeBase): CecProverManagerResult {
    const attempts: CecManagedProofAttempt[] = [];
    let best: { strategy: string; result: CecProofResult } | undefined;
    for (const strategy of this.strategies) {
      const result = this.runStrategy(strategy, theorem, kb);
      attempts.push(toAttempt(strategy.name, result));
      if (!best || rankProofStatus(result.status) > rankProofStatus(best.result.status))
        best = { strategy: strategy.name, result };
      if (result.status === 'proved' && this.stopOnFirstProof)
        return this.withManager(result, attempts, strategy.name);
    }
    return best
      ? this.withManager(best.result, attempts, best.strategy)
      : this.withManager(toError(theorem, { name: 'empty' }, 'No strategies registered'), attempts);
  }

  private runStrategy(
    strategy: CecProverManagerStrategy,
    theorem: CecExpression,
    kb: CecKnowledgeBase,
  ): CecProofResult {
    try {
      return new CecProver({
        rules: strategy.rules,
        ruleGroups: strategy.ruleGroups,
        maxSteps: strategy.maxSteps ?? this.options.maxSteps,
        maxDerivedExpressions: strategy.maxDerivedExpressions ?? this.options.maxDerivedExpressions,
      }).prove(theorem, kb);
    } catch (error) {
      return toError(theorem, strategy, error);
    }
  }

  private withManager(
    result: CecProofResult,
    attempts: CecManagedProofAttempt[],
    selectedStrategy?: string,
  ): CecProverManagerResult {
    return {
      ...result,
      attempts: attempts.map((attempt) => ({ ...attempt, ruleGroups: [...attempt.ruleGroups] })),
      manager: {
        strategyCount: this.strategies.length,
        selectedStrategy,
        pythonRuntime: false,
        serverDelegation: false,
      },
    };
  }
}

export function proveCecManaged(
  theorem: CecExpression,
  kb: CecKnowledgeBase,
  options: CecProverManagerOptions = {},
): CecProverManagerResult {
  return new CecProverManager(options).prove(theorem, kb);
}

function copyStrategy(strategy: CecProverManagerStrategy): CecProverManagerStrategy {
  return {
    ...strategy,
    ruleGroups: strategy.ruleGroups ? [...strategy.ruleGroups] : undefined,
    rules: strategy.rules ? [...strategy.rules] : undefined,
  };
}

function toAttempt(strategy: string, result: CecProofResult): CecManagedProofAttempt {
  return {
    strategy,
    status: result.status,
    method: result.method,
    ruleGroups: [...result.ruleGroups],
    stepCount: result.steps.length,
    error: result.error,
  };
}

function rankProofStatus(status: ProofStatus): number {
  return status === 'proved'
    ? 5
    : status === 'disproved'
      ? 4
      : status === 'unknown'
        ? 3
        : status === 'timeout'
          ? 2
          : 1;
}

function toError(
  theorem: CecExpression,
  strategy: CecProverManagerStrategy,
  error: unknown,
): CecProofResult {
  return {
    status: 'error',
    theorem: formatCecExpression(theorem),
    steps: [],
    method: `cec-managed:${strategy.name}`,
    error: error instanceof Error ? error.message : String(error),
    ruleGroups: strategy.ruleGroups ? [...strategy.ruleGroups] : [],
    trace: [],
  };
}

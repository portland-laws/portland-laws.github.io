export interface LogicFact {
  id: string;
  predicate: string;
  args: string[];
  sourceIds: string[];
}

export interface LogicImplication {
  id: string;
  when: LogicFact;
  then: Omit<LogicFact, 'id' | 'sourceIds'>;
  sourceIds: string[];
}

export interface LogicProofTraceStep {
  id: string;
  rule: string;
  premises: string[];
  conclusion: string;
  sourceIds: string[];
}

export interface LogicKnowledgeBase {
  factsById: Map<string, LogicFact>;
  factsBySourceId: Map<string, LogicFact[]>;
  implications: LogicImplication[];
}

export interface ForwardChainingOptions {
  maxSteps?: number;
  maxMs?: number;
}

export interface ForwardChainingResult {
  facts: LogicFact[];
  inferredFacts: LogicFact[];
  trace: LogicProofTraceStep[];
  exhausted: boolean;
  stoppedBy: 'fixed_point' | 'max_steps' | 'time_budget';
}

export interface NormConflictHint {
  key: string;
  conflictType: 'obligation_prohibition' | 'permission_prohibition';
  severity: 'medium' | 'high';
  sourceIds: string[];
  message: string;
}


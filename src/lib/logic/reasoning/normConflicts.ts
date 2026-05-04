import type { NormConflictHint } from './types';

export const DEONTIC_CONFLICT_MIXIN_METADATA = {
  sourcePythonModule: 'logic/integration/reasoning/_deontic_conflict_mixin.py',
  browserNative: true,
  serverCallsAllowed: false,
  pythonRuntimeAllowed: false,
} as const;

export interface NormFactLike {
  sourceId: string;
  actor?: string;
  action: string;
  condition?: string;
  normOperator: 'O' | 'P' | 'F' | string;
}

export interface DeonticConflictClause {
  id?: string;
  sourceId?: string;
  actor?: string;
  subject?: string;
  action: string;
  condition?: string;
  exceptions?: string[];
  normOperator?: 'O' | 'P' | 'F' | string;
  modality?: 'obligation' | 'permission' | 'prohibition' | string;
}

export interface DeonticConflictMixinConflict {
  id: string;
  key: string;
  conflictType: 'obligation_prohibition' | 'permission_prohibition';
  severity: 'medium' | 'high';
  conditionRelationship: 'same' | 'overlap' | 'unconditional';
  sourceIds: string[];
}

interface NormalizedDeonticClause {
  original: DeonticConflictClause;
  sourceId: string;
  actor: string;
  action: string;
  condition: string;
  exceptions: string[];
  operator: 'O' | 'P' | 'F' | null;
}

export function detectNormConflicts(norms: NormFactLike[]): NormConflictHint[] {
  const byKey = new Map<string, NormFactLike[]>();
  for (const norm of norms) {
    const key = [norm.actor || 'agent', norm.action, norm.condition || ''].join('|').toLowerCase();
    const list = byKey.get(key) || [];
    list.push(norm);
    byKey.set(key, list);
  }

  const hints: NormConflictHint[] = [];
  for (const [key, list] of byKey.entries()) {
    const obligations = list.filter((norm) => norm.normOperator === 'O');
    const permissions = list.filter((norm) => norm.normOperator === 'P');
    const prohibitions = list.filter((norm) => norm.normOperator === 'F');

    if (obligations.length > 0 && prohibitions.length > 0) {
      hints.push({
        key,
        conflictType: 'obligation_prohibition',
        severity: 'high',
        sourceIds: [...new Set([...obligations, ...prohibitions].map((norm) => norm.sourceId))],
        message: `Potential conflict: the same action appears both obligatory and prohibited (${key}).`,
      });
    }

    if (permissions.length > 0 && prohibitions.length > 0) {
      hints.push({
        key,
        conflictType: 'permission_prohibition',
        severity: 'medium',
        sourceIds: [...new Set([...permissions, ...prohibitions].map((norm) => norm.sourceId))],
        message: `Potential conflict: the same action appears both permitted and prohibited (${key}).`,
      });
    }
  }
  return hints;
}

export function detectDeonticConflictMixinConflicts(
  clauses: DeonticConflictClause[],
): DeonticConflictMixinConflict[] {
  const normalized = clauses.map(normalizeClause).filter((clause) => clause.operator !== null);
  const conflicts: DeonticConflictMixinConflict[] = [];

  for (let index = 0; index < normalized.length; index += 1) {
    for (let other = index + 1; other < normalized.length; other += 1) {
      const left = normalized[index];
      const right = normalized[other];
      if (left.actor !== right.actor || left.action !== right.action) continue;
      if (isExceptionCovered(left, right) || isExceptionCovered(right, left)) continue;

      const conditionRelationship = compareConditions(left.condition, right.condition);
      if (conditionRelationship === null) continue;

      const conflictType = classifyConflict(left.operator, right.operator);
      if (conflictType === null) continue;

      const severity = conflictType === 'obligation_prohibition' ? 'high' : 'medium';
      const key = [left.actor, left.action, conditionKey(left.condition, right.condition)].join(
        '|',
      );
      conflicts.push({
        id: `deontic_conflict_${conflicts.length + 1}`,
        key,
        conflictType,
        severity,
        conditionRelationship,
        sourceIds: Array.from(new Set([left.sourceId, right.sourceId])),
      });
    }
  }

  return conflicts;
}

export const detect_deontic_conflict_mixin_conflicts = detectDeonticConflictMixinConflicts;

export const DEONTOLOGICAL_REASONING_METADATA = {
  sourcePythonModule: 'logic/integration/reasoning/deontological_reasoning.py',
  browserNative: true,
  serverCallsAllowed: false,
  pythonRuntimeAllowed: false,
} as const;
export type DeontologicalVerdict = 'compliant' | 'violation' | 'conflict' | 'permitted' | 'unknown';

export interface DeontologicalNorm extends DeonticConflictClause {
  validFrom?: Date | string;
  validUntil?: Date | string;
}

export interface DeontologicalReasoningQuery {
  actor?: string;
  action?: string;
  performedActions?: string[];
  facts?: Record<string, boolean>;
  atTime?: Date | string;
}

export interface DeontologicalViolation {
  normId: string;
  violationType: 'missing_obligation' | 'forbidden_action';
  actor: string;
  action: string;
  message: string;
}

export interface DeontologicalReasoningResult {
  verdict: DeontologicalVerdict;
  applicableNorms: DeontologicalNorm[];
  violations: DeontologicalViolation[];
  conflicts: DeonticConflictMixinConflict[];
  trace: string[];
}

interface NormalizedReasoningNorm extends NormalizedDeonticClause {
  original: DeontologicalNorm;
  operator: 'O' | 'P' | 'F';
}

export function reasonDeontologically(
  norms: DeontologicalNorm[],
  query: DeontologicalReasoningQuery = {},
): DeontologicalReasoningResult {
  const performed = new Set((query.performedActions || []).map(normalizeText));
  const applicable = norms
    .map(normalizeClause)
    .filter(isReasoningNorm)
    .filter((norm) => reasoningNormApplies(norm, query));
  const conflicts = detectDeonticConflictMixinConflicts(applicable.map((norm) => norm.original));
  const violations = applicable.flatMap((norm) => detectDeontologicalViolation(norm, performed));
  return {
    verdict: chooseDeontologicalVerdict(applicable, violations, conflicts),
    applicableNorms: applicable.map((norm) => norm.original),
    violations,
    conflicts,
    trace: applicable.map(
      (norm) => `${norm.operator}:${norm.actor}:${norm.action}:${norm.sourceId}`,
    ),
  };
}

export const reason_deontologically = reasonDeontologically;

function normalizeClause(clause: DeonticConflictClause): NormalizedDeonticClause {
  const actor = normalizeText(clause.actor || clause.subject || 'agent');
  const action = normalizeText(clause.action);
  const condition = normalizeText(clause.condition || '');
  const exceptions = (clause.exceptions || []).map(normalizeText).filter(Boolean);
  return {
    original: clause,
    sourceId: clause.sourceId || clause.id || 'unknown',
    actor,
    action,
    condition,
    exceptions,
    operator: normalizeOperator(clause.normOperator, clause.modality),
  };
}

function isReasoningNorm(clause: NormalizedDeonticClause): clause is NormalizedReasoningNorm {
  return clause.operator !== null;
}

function reasoningNormApplies(
  norm: NormalizedReasoningNorm,
  query: DeontologicalReasoningQuery,
): boolean {
  const facts = query.facts || {};
  if (query.actor !== undefined && norm.actor !== normalizeText(query.actor)) return false;
  if (query.action !== undefined && norm.action !== normalizeText(query.action)) return false;
  if (!isReasoningNormWithinTime(norm.original, query.atTime)) return false;
  if (!isConditionSatisfied(norm.condition, facts)) return false;
  return !norm.exceptions.some((exception) => isConditionSatisfied(exception, facts));
}

function isReasoningNormWithinTime(norm: DeontologicalNorm, atTime?: Date | string): boolean {
  if (atTime === undefined) return true;
  const time = toTime(atTime);
  const from = norm.validFrom === undefined ? null : toTime(norm.validFrom);
  const until = norm.validUntil === undefined ? null : toTime(norm.validUntil);
  return (from === null || time >= from) && (until === null || time <= until);
}

function isConditionSatisfied(condition: string, facts: Record<string, boolean>): boolean {
  if (!condition) return true;
  if (facts[condition] === true) return true;
  return Object.keys(facts)
    .filter((key) => facts[key] === true)
    .map(normalizeText)
    .some((fact) => fact === condition || fact.includes(condition) || condition.includes(fact));
}

function detectDeontologicalViolation(
  norm: NormalizedReasoningNorm,
  performed: Set<string>,
): DeontologicalViolation[] {
  const missing = norm.operator === 'O' && !performed.has(norm.action);
  const forbidden = norm.operator === 'F' && performed.has(norm.action);
  if (!missing && !forbidden) return [];
  return [
    {
      normId: norm.sourceId,
      violationType: missing ? 'missing_obligation' : 'forbidden_action',
      actor: norm.actor,
      action: norm.action,
      message: missing
        ? `${norm.actor} failed to perform obligatory action ${norm.action}.`
        : `${norm.actor} performed prohibited action ${norm.action}.`,
    },
  ];
}

function chooseDeontologicalVerdict(
  norms: NormalizedReasoningNorm[],
  violations: DeontologicalViolation[],
  conflicts: DeonticConflictMixinConflict[],
): DeontologicalVerdict {
  if (conflicts.length > 0) return 'conflict';
  if (violations.length > 0) return 'violation';
  if (norms.some((norm) => norm.operator === 'P')) return 'permitted';
  return norms.length > 0 ? 'compliant' : 'unknown';
}

function toTime(value: Date | string): number {
  return value instanceof Date ? value.getTime() : new Date(value).getTime();
}

function normalizeOperator(normOperator?: string, modality?: string): 'O' | 'P' | 'F' | null {
  const operator = (normOperator || '').toUpperCase();
  if (operator === 'O' || operator === 'P' || operator === 'F') return operator;
  const normalizedModality = normalizeText(modality || '');
  if (normalizedModality === 'obligation' || normalizedModality === 'obligatory') return 'O';
  if (normalizedModality === 'permission' || normalizedModality === 'permitted') return 'P';
  if (normalizedModality === 'prohibition' || normalizedModality === 'forbidden') return 'F';
  return null;
}

function classifyConflict(
  left: 'O' | 'P' | 'F' | null,
  right: 'O' | 'P' | 'F' | null,
): 'obligation_prohibition' | 'permission_prohibition' | null {
  const pair = new Set([left, right]);
  if (pair.has('O') && pair.has('F')) return 'obligation_prohibition';
  if (pair.has('P') && pair.has('F')) return 'permission_prohibition';
  return null;
}

function compareConditions(
  left: string,
  right: string,
): 'same' | 'overlap' | 'unconditional' | null {
  if (!left && !right) return 'unconditional';
  if (!left || !right) return 'unconditional';
  if (left === right) return 'same';
  if (left.includes(right) || right.includes(left)) return 'overlap';
  const leftTerms = new Set(left.split(/\s+/).filter((term) => term.length > 2));
  const rightTerms = right.split(/\s+/).filter((term) => term.length > 2);
  return rightTerms.some((term) => leftTerms.has(term)) ? 'overlap' : null;
}

function isExceptionCovered(
  clause: NormalizedDeonticClause,
  other: NormalizedDeonticClause,
): boolean {
  return (
    Boolean(other.condition) &&
    clause.exceptions.some((exception) => compareConditions(exception, other.condition) !== null)
  );
}

function conditionKey(left: string, right: string): string {
  if (!left && !right) return '';
  if (!left || !right) return '*';
  return left === right ? left : `${left}&${right}`;
}

function normalizeText(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, ' ')
    .trim()
    .replace(/\s+/g, ' ');
}

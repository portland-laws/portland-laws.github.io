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

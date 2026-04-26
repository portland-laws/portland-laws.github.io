import type { NormConflictHint } from './types';

export interface NormFactLike {
  sourceId: string;
  actor?: string;
  action: string;
  condition?: string;
  normOperator: 'O' | 'P' | 'F' | string;
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


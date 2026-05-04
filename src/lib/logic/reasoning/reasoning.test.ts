import { parseTdfolFormula } from '../tdfol';
import { createImplication, runForwardChaining } from './forwardChaining';
import { createLogicKnowledgeBase, makeFact } from './knowledgeBase';
import {
  DEONTIC_CONFLICT_MIXIN_METADATA,
  detectDeonticConflictMixinConflicts,
  detectNormConflicts,
} from './normConflicts';
import { describeTemporalSummary, summarizeTemporalOperators } from './temporal';

describe('lightweight reasoning', () => {
  it('runs bounded forward chaining with proof trace output', () => {
    const kb = createLogicKnowledgeBase(
      [makeFact('SubjectTo', ['auditor', 'Portland City Code 1.01.010'], ['cid-1'])],
      [
        createImplication(
          'requires_compliance',
          'SubjectTo',
          ['$0', '$1'],
          'ComplyWith',
          ['$0', '$1'],
          ['rule-1'],
        ),
      ],
    );

    const result = runForwardChaining(kb, { maxSteps: 5, maxMs: 100 });

    expect(result.exhausted).toBe(true);
    expect(result.inferredFacts).toEqual([
      {
        id: 'ComplyWith(auditor,Portland City Code 1.01.010)',
        predicate: 'ComplyWith',
        args: ['auditor', 'Portland City Code 1.01.010'],
        sourceIds: ['cid-1', 'rule-1'],
      },
    ]);
    expect(result.trace).toMatchObject([
      {
        rule: 'requires_compliance',
        premises: ['SubjectTo(auditor,Portland City Code 1.01.010)'],
        conclusion: 'ComplyWith(auditor,Portland City Code 1.01.010)',
        sourceIds: ['cid-1', 'rule-1'],
      },
    ]);
  });

  it('stops at the configured step budget', () => {
    const kb = createLogicKnowledgeBase(
      [makeFact('A', ['x'], ['source'])],
      [
        createImplication('a_to_b', 'A', ['$0'], 'B', ['$0'], ['rule-a']),
        createImplication('b_to_c', 'B', ['$0'], 'C', ['$0'], ['rule-b']),
      ],
    );

    const result = runForwardChaining(kb, { maxSteps: 1, maxMs: 100 });

    expect(result.stoppedBy).toBe('max_steps');
    expect(result.inferredFacts).toHaveLength(1);
  });

  it('detects obvious deontic norm conflicts', () => {
    const conflicts = detectNormConflicts([
      { sourceId: 'cid-o', action: 'comply', normOperator: 'O' },
      { sourceId: 'cid-f', action: 'comply', normOperator: 'F' },
      { sourceId: 'cid-p', action: 'appeal', normOperator: 'P' },
    ]);

    expect(conflicts).toEqual([
      {
        key: 'agent|comply|',
        conflictType: 'obligation_prohibition',
        severity: 'high',
        sourceIds: ['cid-o', 'cid-f'],
        message:
          'Potential conflict: the same action appears both obligatory and prohibited (agent|comply|).',
      },
    ]);
  });

  it('ports integration reasoning deontic conflict mixin semantics locally', () => {
    const conflicts = detectDeonticConflictMixinConflicts([
      {
        id: 'rule-o',
        actor: 'Tenant',
        action: 'Pay rent',
        condition: 'Lease is active',
        modality: 'obligation',
      },
      {
        id: 'rule-f',
        actor: 'tenant',
        action: 'pay rent',
        condition: 'the lease is active and unit is uninhabitable',
        modality: 'prohibition',
      },
      { id: 'rule-p', actor: 'Tenant', action: 'inspect records', normOperator: 'P' },
      { id: 'rule-f2', actor: 'Tenant', action: 'inspect records', normOperator: 'F' },
    ]);

    expect(DEONTIC_CONFLICT_MIXIN_METADATA).toMatchObject({
      sourcePythonModule: 'logic/integration/reasoning/_deontic_conflict_mixin.py',
      browserNative: true,
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
    });
    expect(conflicts).toMatchObject([
      {
        conflictType: 'obligation_prohibition',
        severity: 'high',
        conditionRelationship: 'overlap',
        sourceIds: ['rule-o', 'rule-f'],
      },
      {
        conflictType: 'permission_prohibition',
        severity: 'medium',
        conditionRelationship: 'unconditional',
        sourceIds: ['rule-p', 'rule-f2'],
      },
    ]);
  });

  it('treats explicit exceptions as local conflict suppressors', () => {
    const conflicts = detectDeonticConflictMixinConflicts([
      {
        id: 'general-duty',
        actor: 'Tenant',
        action: 'pay rent',
        modality: 'obligation',
        exceptions: ['unit is uninhabitable'],
      },
      {
        id: 'exception-rule',
        actor: 'Tenant',
        action: 'pay rent',
        modality: 'prohibition',
        condition: 'the unit is uninhabitable',
      },
    ]);

    expect(conflicts).toEqual([]);
  });

  it('summarizes temporal operators from TDFOL formulas', () => {
    const formula = parseTdfolFormula(
      'forall a. SubjectTo(a, section) -> O([]ComplyWith(a, section))',
    );
    const summary = summarizeTemporalOperators(formula);

    expect(summary).toEqual(['always']);
    expect(describeTemporalSummary(summary)).toBe('Always/continuing condition');
  });
});

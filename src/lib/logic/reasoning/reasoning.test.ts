import { parseTdfolFormula } from '../tdfol';
import { createImplication, runForwardChaining } from './forwardChaining';
import { createLogicKnowledgeBase, makeFact } from './knowledgeBase';
import { detectNormConflicts } from './normConflicts';
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
        message: 'Potential conflict: the same action appears both obligatory and prohibited (agent|comply|).',
      },
    ]);
  });

  it('summarizes temporal operators from TDFOL formulas', () => {
    const formula = parseTdfolFormula('forall a. SubjectTo(a, section) -> O([]ComplyWith(a, section))');
    const summary = summarizeTemporalOperators(formula);

    expect(summary).toEqual(['always']);
    expect(describeTemporalSummary(summary)).toBe('Always/continuing condition');
  });
});


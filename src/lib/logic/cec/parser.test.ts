import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

import { analyzeCecExpression } from './analyzer';
import { collectCecAtoms } from './ast';
import { formatCecExpression } from './formatter';
import { parseCecExpression, validateCecExpression } from './parser';

const portlandDcec =
  '(forall agent (implies (subject_to agent portland_city_code_1_01_010) (P (always (comply_with agent portland_city_code_1_01_010)))))';

interface GeneratedLogicProofSummary {
  identifier: string;
  deontic_cognitive_event_calculus: string;
}

const fixturePath = resolve(
  process.cwd(),
  'public/corpus/portland-or/current/generated/logic-proof-summaries.json',
);

function loadGeneratedSummaries(): GeneratedLogicProofSummary[] {
  return JSON.parse(readFileSync(fixturePath, 'utf8')) as GeneratedLogicProofSummary[];
}

describe('CEC/DCEC parser', () => {
  it('parses generated Portland DCEC quantified expressions', () => {
    const expression = parseCecExpression(portlandDcec);

    expect(expression.kind).toBe('quantified');
    if (expression.kind !== 'quantified') {
      return;
    }

    expect(expression.quantifier).toBe('forall');
    expect(expression.variable).toBe('agent');
    expect(expression.expression.kind).toBe('binary');

    if (expression.expression.kind !== 'binary') {
      return;
    }

    expect(expression.expression.operator).toBe('implies');
    expect(expression.expression.left).toMatchObject({
      kind: 'application',
      name: 'subject_to',
    });
    expect(expression.expression.right).toMatchObject({
      kind: 'unary',
      operator: 'P',
    });
  });

  it('normalizes valid DCEC expressions back to s-expression syntax', () => {
    const formatted = formatCecExpression(parseCecExpression(`  ${portlandDcec.replaceAll(' ', '\n  ')}  `));

    expect(formatted).toBe(portlandDcec);
  });

  it('collects atoms from application arguments', () => {
    const atoms = collectCecAtoms(parseCecExpression(portlandDcec));

    expect([...atoms].sort()).toEqual(['agent', 'portland_city_code_1_01_010']);
  });

  it('analyzes generated Portland DCEC metadata', () => {
    const analysis = analyzeCecExpression(parseCecExpression(portlandDcec));

    expect(analysis).toMatchObject({
      predicates: ['comply_with', 'subject_to'],
      atoms: ['agent', 'portland_city_code_1_01_010'],
      sectionRefs: ['portland_city_code_1_01_010'],
      quantifiers: ['forall'],
      deonticOperators: ['P'],
      temporalOperators: ['always'],
      maxDepth: 6,
      nodeCount: 10,
    });
  });

  it('returns validation failures for malformed expressions', () => {
    expect(validateCecExpression('(forall agent)')).toMatchObject({
      ok: false,
      error: expect.stringContaining('requires a body expression'),
    });

    expect(validateCecExpression('(and a)')).toMatchObject({
      ok: false,
      error: expect.stringContaining('requires two operands'),
    });

    expect(validateCecExpression('(subject_to agent portland_city_code_1_01_010')).toMatchObject({
      ok: false,
      error: expect.stringContaining('Unclosed application subject_to'),
    });
  });

  it('parses all generated Portland DCEC snippets', () => {
    const summaries = loadGeneratedSummaries();
    const failures: Array<{ identifier: string; error: string }> = [];

    for (const summary of summaries) {
      try {
        const expression = parseCecExpression(summary.deontic_cognitive_event_calculus);
        const analysis = analyzeCecExpression(expression);

        expect(analysis.sectionRefs.length).toBeGreaterThanOrEqual(1);
        expect(analysis.predicates).toContain('subject_to');
      } catch (error) {
        failures.push({
          identifier: summary.identifier,
          error: error instanceof Error ? error.message : String(error),
        });
      }
    }

    expect(failures).toEqual([]);
  });
});

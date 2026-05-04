import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

import { analyzeCecExpression } from './analyzer';
import { collectCecAtoms } from './ast';
import { formatCecExpression } from './formatter';
import {
  parseCecExpression,
  parseCecNaturalLanguageFrench,
  parseCecNaturalLanguageBase,
  parse_cec_natural_language_french,
  parse_cec_natural_language_base,
  validateCecExpression,
} from './parser';

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
    const formatted = formatCecExpression(
      parseCecExpression(`  ${portlandDcec.replaceAll(' ', '\n  ')}  `),
    );

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

  it('ports base_parser.py deontic natural-language clauses without runtime bridges', () => {
    const obligation = parseCecNaturalLanguageBase('Tenant shall maintain smoke alarms.');
    const prohibition = parseCecNaturalLanguageBase('Tenant must not block exits.');
    const permission = parseCecNaturalLanguageBase('Tenant may enter the unit.');

    expect(obligation).toMatchObject({
      ok: true,
      formula: '(O (maintain_smoke_alarms tenant))',
      parseMethod: 'base_parser_pattern',
      metadata: {
        sourcePythonModule: 'logic/CEC/nl/base_parser.py',
        runtime: 'browser-native-typescript',
        browserNative: true,
        pythonRuntime: false,
        serverRuntime: false,
      },
    });
    expect(prohibition.formula).toBe('(F (block_exits tenant))');
    expect(permission.formula).toBe('(P (enter_unit tenant))');
  });

  it('ports base_parser.py deterministic conditional and temporal forms', () => {
    const result = parse_cec_natural_language_base(
      'If tenant shall pay rent then always landlord may enter unit.',
    );

    expect(result.ok).toBe(true);
    expect(result.formula).toBe(
      '(implies (O (pay_rent tenant)) (always (P (enter_unit landlord))))',
    );
    expect(result.expression?.kind).toBe('binary');
  });

  it('fails closed for base_parser.py unsupported text instead of using Python or services', () => {
    const result = parseCecNaturalLanguageBase('greetings and salutations');

    expect(result).toMatchObject({
      ok: false,
      parseMethod: 'fail_closed',
      confidence: 0,
      errors: ['No deterministic base_parser pattern matched.'],
      metadata: {
        implementation: 'deterministic-base-nl-parser',
        pythonRuntime: false,
        serverRuntime: false,
      },
    });
    expect(result.expression).toBeUndefined();
  });

  it('ports french_parser.py deontic, conditional, and fail-closed clauses without runtime bridges', () => {
    const obligation = parseCecNaturalLanguageFrench(
      'Le locataire doit maintenir les detecteurs de fumee.',
    );
    const prohibition = parseCecNaturalLanguageFrench(
      'Le locataire ne doit pas bloquer les sorties.',
    );
    const conditional = parse_cec_natural_language_french(
      'Si le locataire doit payer le loyer alors toujours le bailleur peut entrer dans le logement.',
    );
    const unsupported = parseCecNaturalLanguageFrench('bonjour tout le monde');

    expect(obligation).toMatchObject({
      ok: true,
      formula: '(O (maintenir_detecteurs_fumee locataire))',
      parseMethod: 'french_parser_pattern',
      metadata: {
        sourcePythonModule: 'logic/CEC/nl/french_parser.py',
        runtime: 'browser-native-typescript',
        browserNative: true,
        pythonRuntime: false,
        serverRuntime: false,
      },
    });
    expect(prohibition.formula).toBe('(F (bloquer_sorties locataire))');
    expect(conditional.ok).toBe(true);
    expect(conditional.formula).toBe(
      '(implies (O (payer_loyer locataire)) (always (P (entrer_dans_logement bailleur))))',
    );
    expect(unsupported).toMatchObject({
      ok: false,
      parseMethod: 'fail_closed',
      confidence: 0,
      errors: ['No deterministic french_parser pattern matched.'],
      metadata: {
        implementation: 'deterministic-french-nl-parser',
        pythonRuntime: false,
        serverRuntime: false,
      },
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

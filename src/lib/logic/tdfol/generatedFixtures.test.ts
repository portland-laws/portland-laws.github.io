import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

import { formatTdfolFormula } from './formatter';
import { parseTdfolFormula } from './parser';

interface GeneratedLogicProofSummary {
  identifier: string;
  norm_type: string;
  deontic_temporal_fol: string;
}

const fixturePath = resolve(
  process.cwd(),
  'public/corpus/portland-or/current/generated/logic-proof-summaries.json',
);

function loadGeneratedSummaries(): GeneratedLogicProofSummary[] {
  return JSON.parse(readFileSync(fixturePath, 'utf8')) as GeneratedLogicProofSummary[];
}

describe('TDFOL generated Portland fixtures', () => {
  it('parses representative generated norm formulas', () => {
    const summaries = loadGeneratedSummaries();
    const samples = ['obligation', 'permission', 'prohibition'].map((normType) => {
      const summary = summaries.find((row) => row.norm_type === normType);
      if (!summary) {
        throw new Error(`Missing generated ${normType} fixture`);
      }
      return summary;
    });

    expect(samples.map((sample) => sample.identifier)).toEqual([
      'Portland City Code 1.01.020',
      'Portland City Code 1.01.010',
      'Portland City Code 1.01.090',
    ]);

    for (const sample of samples) {
      const formula = parseTdfolFormula(sample.deontic_temporal_fol);
      const formatted = formatTdfolFormula(formula);

      expect(formula.kind).toBe('quantified');
      expect(formatted).toContain('SubjectTo');
      expect(formatted).toContain('ComplyWith');
    }
  });

  it('parses at least 95 percent of generated TDFOL formulas', () => {
    const summaries = loadGeneratedSummaries();
    const failures: Array<{ identifier: string; error: string }> = [];

    for (const summary of summaries) {
      try {
        parseTdfolFormula(summary.deontic_temporal_fol);
      } catch (error) {
        failures.push({
          identifier: summary.identifier,
          error: error instanceof Error ? error.message : String(error),
        });
      }
    }

    const successRate = (summaries.length - failures.length) / summaries.length;
    expect(successRate).toBeGreaterThanOrEqual(0.95);
  });
});


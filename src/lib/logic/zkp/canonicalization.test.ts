import { webcrypto } from 'node:crypto';
import { TextEncoder } from 'node:util';

import {
  axiomsCommitmentHex,
  canonicalizeAxioms,
  canonicalizeTheorem,
  normalizeProofText,
  parseTdfolV1Axiom,
  tdfolV1AxiomsCommitmentHexV2,
  theoremHashHex,
} from './canonicalization';

Object.defineProperty(globalThis, 'crypto', {
  value: webcrypto,
  configurable: true,
});
Object.defineProperty(globalThis, 'TextEncoder', {
  value: TextEncoder,
  configurable: true,
});

describe('ZKP canonicalization', () => {
  it('normalizes theorem text and axiom sets deterministically', () => {
    expect(normalizeProofText('  All   humans\nare mortal  ')).toBe('All humans are mortal');
    expect(canonicalizeTheorem('  P  ->   Q ')).toBe('P -> Q');
    expect(canonicalizeAxioms(['Q', 'P', 'P -> Q', 'P'])).toEqual(['P', 'P -> Q', 'Q']);
  });

  it('hashes equivalent theorem text to the same digest', async () => {
    await expect(theoremHashHex('P  -> Q')).resolves.toBe(await theoremHashHex('P -> Q'));
    expect(await theoremHashHex('P -> Q')).toHaveLength(64);
  });

  it('commits to axiom sets independent of order and duplication', async () => {
    const left = await axiomsCommitmentHex(['Q', 'P', 'P -> Q']);
    const right = await axiomsCommitmentHex(['P -> Q', 'P', 'Q', 'P']);

    expect(left).toBe(right);
    expect(left).toHaveLength(64);
  });

  it('parses simple TDFOL v1 axioms', () => {
    expect(parseTdfolV1Axiom('P -> Q')).toEqual({ antecedent: 'P', consequent: 'Q' });
    expect(parseTdfolV1Axiom('Q')).toEqual({ consequent: 'Q' });
  });

  it('builds field-only TDFOL commitments deterministically', async () => {
    const left = await tdfolV1AxiomsCommitmentHexV2(['Q', 'P', 'P -> Q']);
    const right = await tdfolV1AxiomsCommitmentHexV2(['P -> Q', 'Q', 'P']);

    expect(left).toBe(right);
    expect(left).toHaveLength(64);
  });
});

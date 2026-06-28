import { CecModusPonensRule, CecTemporalTRule } from './inferenceRules';
import { parseCecExpression } from './parser';
import type { ProofResult } from '../types';
import {
  BrowserNativeCecProofStore,
  CEC_PROOF_CACHE_METADATA,
  CecProofCache,
  clearGlobalCecProofCache,
  getGlobalCecProofCache,
  proveCecWithCache,
} from './proofCache';

describe('CEC proof cache', () => {
  it('declares the browser-native CEC cec_proof_cache.py parity contract', () => {
    expect(CEC_PROOF_CACHE_METADATA).toMatchObject({
      sourcePythonModule: 'logic/CEC/native/cec_proof_cache.py',
      browserNative: true,
      runtimeDependencies: [],
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
    });
    expect(CEC_PROOF_CACHE_METADATA.parity).toEqual(
      expect.arrayContaining([
        'cec_theorem_axiom_config_keys',
        'order_insensitive_axiom_keys',
        'ttl_lru_eviction',
        'validation_metadata',
        'browser_native_content_addressed_storage',
        'cid_validation_on_storage_reads',
      ]),
    );
  });

  it('stores and retrieves proof results by normalized theorem, axioms, and prover config', () => {
    const cache = new CecProofCache();
    const theorem = parseCecExpression('(comply_with agent code)');
    const kb = {
      axioms: [parseCecExpression('(subject_to agent code)'), parseCecExpression('(active code)')],
    };
    const result = {
      status: 'proved' as const,
      theorem: '(comply_with agent code)',
      steps: [],
      method: 'manual',
    };
    const options = { maxSteps: 3, rules: [CecModusPonensRule] };
    const reversedKb = {
      axioms: [parseCecExpression('(active code)'), parseCecExpression('(subject_to agent code)')],
    };

    const cid = cache.set(theorem, kb, result, options);

    expect(cid).toMatch(/^browsets-/);
    expect(cache.computeCid(theorem, reversedKb, options)).toBe(cid);
    expect(cache.get(theorem, kb, options)).toEqual(result);
    expect(cache.get(theorem, kb, { maxSteps: 4, rules: [CecModusPonensRule] })).toBeUndefined();
    expect(cache.getStats()).toMatchObject({ hits: 1, misses: 1, sets: 1 });
  });

  it('expires and evicts CEC entries through shared TTL/LRU behavior', () => {
    let now = 0;
    const cache = new CecProofCache({ maxSize: 1, ttlMs: 10, now: () => now });
    const first = parseCecExpression('(active first)');
    const second = parseCecExpression('(active second)');
    const firstKb = { axioms: [first] };
    const secondKb = { axioms: [second] };

    cache.prove(first, firstKb);
    cache.prove(second, secondKb);

    expect(cache.get(first, firstKb)).toBeUndefined();
    expect(cache.getStats()).toMatchObject({ evictions: 1, cacheSize: 1 });
    expect(cache.snapshot()[0]).toMatchObject({ formulaString: '(active second)', expired: false });

    now = 20;
    expect(cache.get(second, secondKb)).toBeUndefined();
    expect(cache.deleteExpired()).toBe(0);
    expect(cache.getStats().cacheSize).toBe(0);
  });

  it('persists deterministic CEC proof entries in browser-native content-addressed storage', () => {
    const storage = new BrowserNativeCecProofStore();
    const cache = new CecProofCache();
    const theorem = parseCecExpression('(active code)');
    const kb = { axioms: [theorem] };
    const result: ProofResult = {
      status: 'proved',
      theorem: '(active code)',
      steps: [],
      method: 'manual',
    };
    const cid = cache.computeCid(theorem, kb);
    const query = {
      theorem: '(active code)',
      axioms: ['(active code)'],
      proverName: 'cec-forward-chaining',
      proverConfig: {
        maxDerivedExpressions: undefined,
        maxSteps: undefined,
        ruleGroups: undefined,
        rules: undefined,
      },
    };
    storage.putProof({
      cid,
      result,
      query,
      storedAt: 42,
      validation: {
        sourcePythonModule: 'logic/CEC/native/cec_proof_cache.py',
        browserNative: true,
      },
    });

    expect(storage.size).toBe(1);
    expect(storage.getProof(cid)).toMatchObject({
      cid,
      storedAt: 42,
      query: {
        theorem: '(active code)',
        axioms: ['(active code)'],
        proverName: 'cec-forward-chaining',
      },
      validation: {
        sourcePythonModule: 'logic/CEC/native/cec_proof_cache.py',
        browserNative: true,
      },
    });
    expect(() => storage.putProof({ ...storage.getProof(cid)!, cid: `${cid}-tampered` })).toThrow(
      /invalid content-addressed proof entry/,
    );
  });

  it('writes through to injected browser storage and reloads validated proof entries', () => {
    let now = 100;
    const storage = new BrowserNativeCecProofStore();
    const writer = new CecProofCache({ storage, now: () => now });
    const theorem = parseCecExpression('(active stored)');
    const kb = { axioms: [theorem] };

    const first = writer.prove(theorem, kb);
    const cid = writer.computeCid(theorem, kb);
    now = 200;
    const reader = new CecProofCache({ storage, now: () => now });

    expect(first).toMatchObject({ status: 'proved', method: 'cec-forward-chaining' });
    expect(storage.getProof(cid)).toMatchObject({ cid, storedAt: 100 });
    expect(reader.get(theorem, kb)).toMatchObject({
      status: 'proved',
      theorem: '(active stored)',
    });
    expect(reader.getStats()).toMatchObject({ misses: 1, sets: 1, cacheSize: 1 });
  });

  it('proves through the cache and marks cached method names', () => {
    const cache = new CecProofCache();
    const theorem = parseCecExpression('(comply_with agent code)');
    const kb = {
      axioms: [
        parseCecExpression('(always (subject_to agent code))'),
        parseCecExpression('(implies (subject_to agent code) (comply_with agent code))'),
      ],
    };
    const options = { rules: [CecTemporalTRule, CecModusPonensRule] };

    expect(cache.prove(theorem, kb, options)).toMatchObject({
      status: 'proved',
      method: 'cec-forward-chaining',
    });
    expect(cache.prove(theorem, kb, options)).toMatchObject({
      status: 'proved',
      method: 'cec-forward-chaining:cached',
    });
    expect(cache.getStats()).toMatchObject({ hits: 1, sets: 1 });
  });

  it('invalidates, clears, and exposes global helpers', () => {
    const cache = new CecProofCache();
    const theorem = parseCecExpression('(active code)');
    const kb = { axioms: [theorem] };

    cache.prove(theorem, kb);
    expect(cache.invalidate(theorem, kb)).toBe(true);
    expect(cache.clear()).toBe(0);

    clearGlobalCecProofCache();
    expect(proveCecWithCache(theorem, kb)).toMatchObject({ status: 'proved' });
    expect(getGlobalCecProofCache().get(theorem, kb)).toMatchObject({ status: 'proved' });
  });
});

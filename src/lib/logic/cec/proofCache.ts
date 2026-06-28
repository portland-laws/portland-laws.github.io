import {
  ProofCache,
  cidForObject,
  type ProofCacheOptions,
  type ProofCacheSnapshotEntry,
  type ProofCacheStats,
} from '../proofCache';
import type { ProofResult } from '../types';
import type { CecExpression } from './ast';
import { formatCecExpression } from './formatter';
import type { CecInferenceRule } from './inferenceRules';
import { CecProver, type CecKnowledgeBase, type CecProverOptions } from './prover';

export const CEC_PROOF_CACHE_METADATA = {
  sourcePythonModule: 'logic/CEC/native/cec_proof_cache.py',
  browserNative: true,
  runtimeDependencies: [] as Array<string>,
  serverCallsAllowed: false,
  pythonRuntimeAllowed: false,
  parity: [
    'cec_theorem_axiom_config_keys',
    'order_insensitive_axiom_keys',
    'ttl_lru_eviction',
    'cache_statistics',
    'validation_metadata',
    'browser_native_content_addressed_storage',
    'cid_validation_on_storage_reads',
  ] as Array<string>,
} as const;

export interface CecProofCacheQuery {
  theorem: string;
  axioms: Array<string>;
  proverName: string;
  proverConfig: Record<string, unknown>;
}
export interface CecStoredProofEntry {
  cid: string;
  result: ProofResult;
  query: CecProofCacheQuery;
  storedAt: number;
  validation: {
    sourcePythonModule: typeof CEC_PROOF_CACHE_METADATA.sourcePythonModule;
    browserNative: true;
  };
}

export interface CecProofCacheOptions extends ProofCacheOptions {
  proverName?: string;
  storage?: BrowserNativeCecProofStore;
}

export class CecProofCache {
  private readonly cache: ProofCache<ProofResult>;
  private readonly now: () => number;
  private readonly proverName: string;
  private readonly storage?: BrowserNativeCecProofStore;

  constructor(options: CecProofCacheOptions = {}) {
    this.now = options.now ?? (() => Date.now());
    this.cache = new ProofCache<ProofResult>({ ...options, now: this.now });
    this.proverName = options.proverName ?? 'cec-forward-chaining';
    this.storage = options.storage;
  }

  computeCid(theorem: CecExpression, kb: CecKnowledgeBase, options: CecProverOptions = {}): string {
    const query = toCecProofCacheQuery(theorem, kb, this.proverName, options);
    return this.cache.computeCid({
      formula: query.theorem,
      axioms: query.axioms,
      proverName: query.proverName,
      proverConfig: query.proverConfig,
    });
  }

  get(
    theorem: CecExpression,
    kb: CecKnowledgeBase,
    options: CecProverOptions = {},
  ): ProofResult | undefined {
    const cached = this.cache.get(
      formatCecExpression(theorem),
      normalizeCecAxioms(kb),
      this.proverName,
      normalizeCecProverConfig(options),
    );
    if (cached) {
      return cached;
    }
    if (!this.storage) {
      return undefined;
    }
    const cid = this.computeCid(theorem, kb, options);
    const stored = this.storage.getProof(cid);
    if (!stored) {
      return undefined;
    }
    if (!verifyCecStoredProofEntry(stored, cid)) {
      throw new Error('CEC proof storage returned an invalid content-addressed proof entry.');
    }
    this.cache.set(
      stored.query.theorem,
      stored.result,
      stored.query.axioms,
      stored.query.proverName,
      stored.query.proverConfig,
    );
    return stored.result;
  }

  set(
    theorem: CecExpression,
    kb: CecKnowledgeBase,
    result: ProofResult,
    options: CecProverOptions = {},
  ): string {
    const cid = this.cache.set(
      formatCecExpression(theorem),
      result,
      normalizeCecAxioms(kb),
      this.proverName,
      normalizeCecProverConfig(options),
    );
    this.storage?.putProof(this.toStoredProofEntry(theorem, kb, result, options, cid));
    return cid;
  }

  invalidate(
    theorem: CecExpression,
    kb: CecKnowledgeBase,
    options: CecProverOptions = {},
  ): boolean {
    return this.cache.invalidate(
      formatCecExpression(theorem),
      normalizeCecAxioms(kb),
      this.proverName,
      normalizeCecProverConfig(options),
    );
  }

  clear(): number {
    return this.cache.clear();
  }

  getStats(): ProofCacheStats {
    return this.cache.getStats();
  }

  deleteExpired(): number {
    return this.cache.deleteExpired();
  }

  snapshot(): Array<ProofCacheSnapshotEntry<ProofResult>> {
    return this.cache.snapshot();
  }

  prove(theorem: CecExpression, kb: CecKnowledgeBase, options: CecProverOptions = {}): ProofResult {
    const cached = this.get(theorem, kb, options);
    if (cached) {
      return {
        ...cached,
        method: `${cached.method ?? this.proverName}:cached`,
      };
    }
    const result = new CecProver(options).prove(theorem, kb);
    this.set(theorem, kb, result, options);
    return result;
  }

  toStoredProofEntry(
    theorem: CecExpression,
    kb: CecKnowledgeBase,
    result: ProofResult,
    options: CecProverOptions = {},
    cid = this.computeCid(theorem, kb, options),
  ): CecStoredProofEntry {
    return {
      cid,
      result,
      query: toCecProofCacheQuery(theorem, kb, this.proverName, options),
      storedAt: this.now(),
      validation: {
        sourcePythonModule: CEC_PROOF_CACHE_METADATA.sourcePythonModule,
        browserNative: true,
      },
    };
  }
}

let globalCecProofCache: CecProofCache | undefined;

export function getGlobalCecProofCache(): CecProofCache {
  globalCecProofCache ??= new CecProofCache();
  return globalCecProofCache;
}

export function clearGlobalCecProofCache(): void {
  globalCecProofCache?.clear();
}

export function proveCecWithCache(
  theorem: CecExpression,
  kb: CecKnowledgeBase,
  options: CecProverOptions = {},
  cache = getGlobalCecProofCache(),
): ProofResult {
  return cache.prove(theorem, kb, options);
}

function normalizeCecAxioms(kb: CecKnowledgeBase): string[] {
  const expressions: Array<CecExpression> = [...kb.axioms, ...(kb.theorems ?? [])];
  return expressions
    .map((expression): string => formatCecExpression(expression))
    .sort((left, right) => left.localeCompare(right));
}

function normalizeCecProverConfig(options: CecProverOptions): Record<string, unknown> {
  return {
    maxSteps: options.maxSteps,
    maxDerivedExpressions: options.maxDerivedExpressions,
    ruleGroups: options.ruleGroups,
    rules: options.rules?.map(ruleName),
  };
}

function ruleName(rule: CecInferenceRule): string {
  return rule.name;
}

function toCecProofCacheQuery(
  theorem: CecExpression,
  kb: CecKnowledgeBase,
  proverName: string,
  options: CecProverOptions,
): CecProofCacheQuery {
  return {
    theorem: formatCecExpression(theorem),
    axioms: normalizeCecAxioms(kb),
    proverName,
    proverConfig: normalizeCecProverConfig(options),
  };
}

function verifyCecStoredProofEntry(entry: CecStoredProofEntry, expectedCid: string): boolean {
  return (
    entry.cid === expectedCid &&
    entry.validation.sourcePythonModule === CEC_PROOF_CACHE_METADATA.sourcePythonModule &&
    entry.validation.browserNative === true &&
    entry.result.theorem === entry.query.theorem &&
    cidForObject({
      formula: entry.query.theorem,
      axioms: entry.query.axioms,
      prover: entry.query.proverName,
      config: entry.query.proverConfig,
    }) === expectedCid
  );
}

function cloneCecStoredProofEntry(entry: CecStoredProofEntry): CecStoredProofEntry {
  return {
    cid: entry.cid,
    result: entry.result,
    storedAt: entry.storedAt,
    query: {
      theorem: entry.query.theorem,
      axioms: [...entry.query.axioms],
      proverName: entry.query.proverName,
      proverConfig: { ...entry.query.proverConfig },
    },
    validation: { ...entry.validation },
  };
}

export class BrowserNativeCecProofStore {
  readonly mode = 'browser-native-cec-proof-storage' as const;
  private readonly entries = new Map<string, CecStoredProofEntry>();

  putProof(entry: CecStoredProofEntry): string {
    if (!verifyCecStoredProofEntry(entry, entry.cid)) {
      throw new Error('CEC proof storage rejected an invalid content-addressed proof entry.');
    }
    this.entries.set(entry.cid, cloneCecStoredProofEntry(entry));
    return entry.cid;
  }

  getProof(cid: string): CecStoredProofEntry | undefined {
    const entry = this.entries.get(cid);
    return entry ? cloneCecStoredProofEntry(entry) : undefined;
  }

  deleteProof(cid: string): boolean {
    return this.entries.delete(cid);
  }
  clear(): void {
    this.entries.clear();
  }

  get size(): number {
    return this.entries.size;
  }
}

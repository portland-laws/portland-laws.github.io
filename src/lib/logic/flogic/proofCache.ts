import { ProofCache, type ProofCacheOptions, type ProofCacheStats } from '../proofCache';
import { ErgoAIWrapper } from './ergoaiWrapper';
import { normalizeFLogicGoal } from './parser';
import type { FLogicOntology, FLogicQuery } from './types';

export interface FLogicProofCacheOptions extends ProofCacheOptions {
  proverName?: string;
}

export interface FLogicQueryOptions {
  mode?: 'query' | 'entails' | 'explain';
  maxSolutions?: number;
  timeoutMs?: number;
}

export const FLOGIC_PROOF_CACHE_METADATA = {
  sourcePythonModule: 'logic/flogic/flogic_proof_cache.py',
  browserNative: true,
  runtimeDependencies: [] as Array<string>,
  parity: [
    'normalized_goal_ontology_keys',
    'query_option_sensitive_lookup',
    'ttl_lru_statistics',
    'fail_closed_browser_query_facade',
    'global_cache_helpers',
  ] as Array<string>,
} as const;

export class FLogicProofCache {
  private readonly cache: ProofCache<FLogicQuery>;
  private readonly proverName: string;

  constructor(options: FLogicProofCacheOptions = {}) {
    this.cache = new ProofCache<FLogicQuery>(options);
    this.proverName = options.proverName ?? 'flogic-ergoai-browser-adapter';
  }

  computeCid(goal: string, ontology: FLogicOntology, options: FLogicQueryOptions = {}): string {
    return this.cache.computeCid({
      formula: normalizeFLogicGoal(goal),
      axioms: ontologyKey(ontology),
      proverName: this.proverName,
      proverConfig: optionKey(options),
    });
  }

  get(
    goal: string,
    ontology: FLogicOntology,
    options: FLogicQueryOptions = {},
  ): FLogicQuery | undefined {
    return this.cache.get(
      normalizeFLogicGoal(goal),
      ontologyKey(ontology),
      this.proverName,
      optionKey(options),
    );
  }

  set(
    goal: string,
    ontology: FLogicOntology,
    result: FLogicQuery,
    options: FLogicQueryOptions = {},
  ): string {
    return this.cache.set(
      normalizeFLogicGoal(goal),
      { ...result, bindings: result.bindings.map((binding) => ({ ...binding })) },
      ontologyKey(ontology),
      this.proverName,
      optionKey(options),
    );
  }

  invalidate(goal: string, ontology: FLogicOntology, options: FLogicQueryOptions = {}): boolean {
    return this.cache.invalidate(
      normalizeFLogicGoal(goal),
      ontologyKey(ontology),
      this.proverName,
      optionKey(options),
    );
  }

  clear(): number {
    return this.cache.clear();
  }

  getStats(): ProofCacheStats {
    return this.cache.getStats();
  }

  query(
    goal: string,
    ontology: FLogicOntology,
    options: FLogicQueryOptions = {},
    wrapper = new ErgoAIWrapper({ ontology }),
  ): FLogicQuery {
    const cached = this.get(goal, ontology, options);
    if (cached) {
      return cached;
    }
    wrapper.loadOntology(ontology);
    const result = wrapper.query(goal);
    this.set(goal, ontology, result, options);
    return result;
  }
}

let globalFLogicProofCache: FLogicProofCache | undefined;

export function getGlobalFLogicProofCache(): FLogicProofCache {
  globalFLogicProofCache ??= new FLogicProofCache();
  return globalFLogicProofCache;
}

export function clearGlobalFLogicProofCache(): void {
  globalFLogicProofCache?.clear();
}

export function queryFLogicWithCache(
  goal: string,
  ontology: FLogicOntology,
  options: FLogicQueryOptions = {},
  cache = getGlobalFLogicProofCache(),
): FLogicQuery {
  return cache.query(goal, ontology, options);
}

function ontologyKey(ontology: FLogicOntology): Array<string> {
  return [
    `name:${ontology.name}`,
    ...ontology.classes.map(
      (item) => `class:${item.classId}<${[...item.superclasses].sort().join(',')}>`,
    ),
    ...ontology.frames.map(
      (item) =>
        `frame:${item.objectId}|isa:${item.isa ?? ''}|isaset:${[...item.isaset].sort().join(',')}|scalar:${recordKey(item.scalarMethods)}|set:${setRecordKey(item.setMethods)}`,
    ),
    ...ontology.rules.map((rule) => `rule:${rule.trim()}`),
    ...ontology.warnings.map((warning) => `warning:${warning}`),
  ].sort((left, right) => left.localeCompare(right));
}

function optionKey(options: FLogicQueryOptions): Record<string, unknown> {
  return {
    maxSolutions: options.maxSolutions,
    mode: options.mode ?? 'query',
    timeoutMs: options.timeoutMs,
  };
}

function recordKey(record: Record<string, string>): string {
  return Object.entries(record)
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([key, value]) => `${key}=${value}`)
    .join(',');
}

function setRecordKey(record: Record<string, Array<string>>): string {
  return Object.entries(record)
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([key, values]) => `${key}={${[...values].sort().join(',')}}`)
    .join(',');
}

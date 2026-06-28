import { BoundedCache } from '../cache';
import type { CacheStats } from '../cache';
import type { CecExpression } from './ast';
import { collectCecAtoms } from './ast';
import { parseCecExpression } from './parser';

export interface CecFormulaCacheMetadata {
  readonly sourcePythonModule: 'logic/CEC/optimization/formula_cache.py';
  readonly runtime: 'browser-native-typescript';
  readonly browserNative: true;
  readonly pythonRuntime: false;
  readonly serverRuntime: false;
}

export interface CecCachedFormula {
  readonly ok: boolean;
  readonly source: string;
  readonly canonical: string;
  readonly expression?: CecExpression;
  readonly dependencies: readonly string[];
  readonly error?: string;
  readonly metadata: CecFormulaCacheMetadata;
}

export interface CecFormulaCacheOptions {
  readonly maxSize?: number;
  readonly ttlMs?: number;
  readonly now?: () => number;
  readonly parser?: (source: string) => CecExpression;
}

export type CecFormulaCacheStats = CacheStats & {
  readonly parseAttempts: number;
  readonly parseFailures: number;
};

export const CEC_FORMULA_CACHE_METADATA: CecFormulaCacheMetadata = {
  sourcePythonModule: 'logic/CEC/optimization/formula_cache.py',
  runtime: 'browser-native-typescript',
  browserNative: true,
  pythonRuntime: false,
  serverRuntime: false,
};

export class CecFormulaCache {
  private readonly parser: (source: string) => CecExpression;
  private readonly cache: BoundedCache<CecCachedFormula>;
  private parseAttempts = 0;
  private parseFailures = 0;

  constructor(options: CecFormulaCacheOptions = {}) {
    this.parser = options.parser ?? parseCecExpression;
    this.cache = new BoundedCache<CecCachedFormula>({
      maxSize: options.maxSize ?? 512,
      ttlMs: options.ttlMs ?? 30 * 60 * 1000,
      now: options.now,
    });
  }

  get size(): number {
    return this.cache.size;
  }

  getFormula(source: string): CecCachedFormula {
    const canonical = canonicalizeCecFormulaSource(source);
    const cached = this.cache.get(canonical);
    if (cached) return cached;
    const parsed = this.parseFormula(source, canonical);
    this.cache.set(canonical, parsed);
    return parsed;
  }

  get_formula(source: string): CecCachedFormula {
    return this.getFormula(source);
  }
  hasFormula(source: string): boolean {
    return this.cache.get(canonicalizeCecFormulaSource(source)) !== undefined;
  }
  has_formula(source: string): boolean {
    return this.hasFormula(source);
  }
  invalidate(source: string): boolean {
    return this.cache.remove(canonicalizeCecFormulaSource(source));
  }
  cleanupExpired(): number {
    return this.cache.cleanupExpired();
  }
  cleanup_expired(): number {
    return this.cleanupExpired();
  }

  clear(): void {
    this.cache.clear();
    this.parseAttempts = 0;
    this.parseFailures = 0;
  }

  getStats(): CecFormulaCacheStats {
    return {
      ...this.cache.getStats(),
      parseAttempts: this.parseAttempts,
      parseFailures: this.parseFailures,
    };
  }

  get_stats(): CecFormulaCacheStats {
    return this.getStats();
  }

  private parseFormula(source: string, canonical: string): CecCachedFormula {
    this.parseAttempts += 1;
    try {
      const expression = this.parser(canonical);
      return {
        ok: true,
        source,
        canonical,
        expression,
        dependencies: [...collectCecAtoms(expression)].sort(),
        metadata: CEC_FORMULA_CACHE_METADATA,
      };
    } catch (error) {
      this.parseFailures += 1;
      return {
        ok: false,
        source,
        canonical,
        dependencies: [],
        error: error instanceof Error ? error.message : 'Unable to parse CEC formula.',
        metadata: CEC_FORMULA_CACHE_METADATA,
      };
    }
  }
}

export function canonicalizeCecFormulaSource(source: string): string {
  return source.trim().replace(/\s+/g, ' ');
}

export function createCecFormulaCache(options: CecFormulaCacheOptions = {}): CecFormulaCache {
  return new CecFormulaCache(options);
}

export const create_cec_formula_cache = createCecFormulaCache;

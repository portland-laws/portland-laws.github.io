export const FLOGIC_SEMANTIC_NORMALIZER_METADATA = {
  sourcePythonModule: 'logic/flogic/semantic_normalizer.py',
  browserNative: true,
  runtimeDependencies: [] as Array<string>,
  parity: [
    'dictionary_synonym_normalization',
    'goal_identifier_replacement',
    'quoted_literal_and_variable_preservation',
    'browser_local_similarity_adapter',
    'global_normalizer_singleton',
  ],
};

const DEFAULT_FLOGIC_SYNONYM_ENTRIES =
  'canine:dog|feline:cat|equine:horse|bovine:cow|swine:pig|porcine:pig|ovine:sheep|person:person|human:person|individual:person|human being:person|homo sapiens:person|prohibited:forbidden|impermissible:forbidden|obligatory:required|must:required|shall:required|permitted:allowed|permissible:allowed|may:allowed|integer:int|string:str|boolean:bool|floating point:float';
export const DEFAULT_FLOGIC_SYNONYM_MAP: Record<string, string> = Object.fromEntries(
  DEFAULT_FLOGIC_SYNONYM_ENTRIES.split('|').map((entry) => entry.split(':') as [string, string]),
);

export interface FLogicSemanticResolution {
  canonical: string;
  confidence: number;
}
export interface BrowserSemanticSimilarityAdapter {
  resolveTerm(term: string): FLogicSemanticResolution | null;
}
export interface SemanticNormalizerOptions {
  useSemanticSimilarity?: boolean;
  synonymMap?: Record<string, string>;
  confidenceThreshold?: number;
  similarityAdapter?: BrowserSemanticSimilarityAdapter;
}

const IDENTIFIER_PATTERN = /\b([A-Za-z][A-Za-z0-9_]*)\b/g;
const QUOTED_LITERAL_PATTERN = /'[^']*'|"[^"]*"/g;
export class SemanticNormalizer {
  private readonly synonymMap: Record<string, string>;
  private readonly useSemanticSimilarity: boolean;
  private readonly confidenceThreshold: number;
  private readonly similarityAdapter?: BrowserSemanticSimilarityAdapter;
  private readonly semanticCache = new Map<string, string>();
  constructor(options: SemanticNormalizerOptions = {}) {
    this.synonymMap = normalizeMap({
      ...DEFAULT_FLOGIC_SYNONYM_MAP,
      ...(options.synonymMap ?? {}),
    });
    this.useSemanticSimilarity = options.useSemanticSimilarity ?? true;
    this.confidenceThreshold = options.confidenceThreshold ?? 0.6;
    this.similarityAdapter = options.similarityAdapter;
  }
  get semanticSimilarityAvailable(): boolean {
    return Boolean(this.useSemanticSimilarity && this.similarityAdapter);
  }
  normalizeTerm(term: string): string {
    const key = canonicalKey(term);
    const cached = this.semanticCache.get(key);
    if (cached) return cached;
    if (this.synonymMap[key]) return this.synonymMap[key];
    const resolved =
      this.useSemanticSimilarity && this.similarityAdapter
        ? this.similarityAdapter.resolveTerm(key)
        : null;
    const canonical = resolved ? canonicalKey(resolved.canonical) : '';
    if (
      resolved &&
      canonical.length > 0 &&
      canonical.length <= 50 &&
      !canonical.includes('\n') &&
      resolved.confidence >= this.confidenceThreshold
    ) {
      this.semanticCache.set(key, canonical);
      return canonical;
    }
    return key;
  }
  normalizeGoal(goal: string): string {
    const quotedRanges = collectQuotedRanges(goal);
    return goal.replace(IDENTIFIER_PATTERN, (match, identifier: string, offset: number) => {
      if (isInRanges(offset, quotedRanges)) return match;
      if (identifier.length === 1 && identifier.toUpperCase() === identifier) return identifier;
      return goal[offset - 1] === '?' ? identifier : this.normalizeTerm(identifier);
    });
  }
  addSynonym(variant: string, canonical: string): void {
    this.synonymMap[canonicalKey(variant)] = canonicalKey(canonical);
  }
  getMapSnapshot(): Record<string, string> {
    return { ...this.synonymMap, ...Object.fromEntries(this.semanticCache.entries()) };
  }
}
let globalNormalizer: SemanticNormalizer | null = null;
export function getGlobalFLogicSemanticNormalizer(
  options: SemanticNormalizerOptions = {},
): SemanticNormalizer {
  if (!globalNormalizer) globalNormalizer = new SemanticNormalizer(options);
  return globalNormalizer;
}

export function clearGlobalFLogicSemanticNormalizer(): void {
  globalNormalizer = null;
}
export function normalizeFLogicSemanticGoal(
  goal: string,
  normalizer = getGlobalFLogicSemanticNormalizer(),
): string {
  return normalizer.normalizeGoal(goal);
}

function normalizeMap(map: Record<string, string>): Record<string, string> {
  return Object.fromEntries(
    Object.entries(map).map(([variant, canonical]) => [
      canonicalKey(variant),
      canonicalKey(canonical),
    ]),
  );
}
function canonicalKey(value: string): string {
  return value.trim().toLowerCase();
}
function collectQuotedRanges(text: string): Array<[number, number]> {
  return Array.from(text.matchAll(QUOTED_LITERAL_PATTERN), (match) => [
    match.index ?? 0,
    (match.index ?? 0) + match[0].length,
  ]);
}
function isInRanges(offset: number, ranges: Array<[number, number]>): boolean {
  return ranges.some(([start, end]) => start <= offset && offset < end);
}

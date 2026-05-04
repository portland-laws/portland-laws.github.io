import { canonicalizeJson, createBrowserLocalCid } from './ipfsCacheDemo';
import { parseTdfolFormula } from './parser';

export type TdfolLlmOperatorHint =
  | 'universal'
  | 'existential'
  | 'obligation'
  | 'permission'
  | 'forbidden'
  | 'temporal_always'
  | 'temporal_eventually';
export type TdfolLlmParseMethod = 'pattern' | 'failed';
export type TdfolCachedFormula = { formula: string; confidence: number };
export type BrowserNativeTdfolLlmCacheStats = {
  size: number;
  maxSize: number;
  hits: number;
  misses: number;
  hitRate: number;
};
export type BrowserNativeTdfolLlmParseResult = {
  success: boolean;
  formula: string;
  confidence: number;
  method: TdfolLlmParseMethod;
  cacheHit: boolean;
  errors: string[];
  metadata: {
    threshold: number;
    operatorHints: TdfolLlmOperatorHint[];
    llmAvailable: false;
    serverCallsAllowed: false;
    pythonRuntime: false;
  };
};

export const TDFOL_LLM_SYSTEM_PROMPT =
  'Convert natural language to browser-native TDFOL without server, Python, subprocess, or RPC fallback.';

export const TDFOL_LLM_OPERATOR_PROMPTS: Record<TdfolLlmOperatorHint, string> = {
  universal: 'Universal: All X are Y -> forall x. X(x) -> Y(x).',
  existential: 'Existential: Some X are Y -> exists x. X(x) & Y(x).',
  obligation: 'Obligation: X must Y, is required to Y, or shall Y -> O(Y(x)).',
  permission: 'Permission: X may Y, can Y, or is allowed to Y -> P(Y(x)).',
  forbidden: 'Forbidden: X must not Y, shall not Y, or is prohibited from Y -> F(Y(x)).',
  temporal_always: 'Always: X always Y -> [](Y(x)).',
  temporal_eventually: 'Eventually: X eventually Y -> <>(Y(x)).',
};

export function buildTdfolLlmConversionPrompt(
  text: string,
  operatorHints = getTdfolOperatorHintsForText(text),
): string {
  return [
    TDFOL_LLM_SYSTEM_PROMPT,
    ...operatorHints.map((hint) => TDFOL_LLM_OPERATOR_PROMPTS[hint]),
    `Input: ${text}`,
    'Output:',
  ].join('\n');
}

export function buildTdfolLlmValidationPrompt(formula: string): string {
  return `Validate the TDFOL formula and return a corrected formula if needed.\n\nFormula: ${formula}`;
}

export function buildTdfolLlmErrorCorrectionPrompt(formula: string, errors: string[]): string {
  const lines = [
    `The following TDFOL formula has errors: ${formula}`,
    'Errors detected:',
    ...errors.map((error) => `- ${error}`),
  ];
  return lines.join('\n');
}

export function getTdfolOperatorHintsForText(text: string): TdfolLlmOperatorHint[] {
  const lower = text.toLowerCase();
  const hints: TdfolLlmOperatorHint[] = [];
  if (has(lower, ['all', 'every', 'each'])) hints.push('universal');
  if (has(lower, ['some', 'exists', 'there is', 'at least one'])) hints.push('existential');
  if (has(lower, ['must not', 'shall not', 'prohibited', 'forbidden'])) hints.push('forbidden');
  if (has(lower, ['must', 'required', 'shall', 'obligated'])) hints.push('obligation');
  if (has(lower, ['may', 'allowed', 'can', 'permitted'])) hints.push('permission');
  if (has(lower, ['always', 'perpetually', 'forever'])) hints.push('temporal_always');
  if (has(lower, ['eventually', 'someday', 'at some point'])) hints.push('temporal_eventually');
  return hints;
}

export class BrowserNativeTdfolLlmResponseCache {
  private readonly entries = new Map<string, TdfolCachedFormula>();
  private hits = 0;
  private misses = 0;

  constructor(private readonly maxSize = 1000) {}

  get(text: string, prompt: string): TdfolCachedFormula | undefined {
    const value = this.entries.get(this.key(text, prompt));
    value ? (this.hits += 1) : (this.misses += 1);
    return value;
  }

  put(text: string, prompt: string, formula: string, confidence: number): void {
    if (this.entries.size >= this.maxSize) {
      const oldest = this.entries.keys().next().value as string | undefined;
      if (oldest) this.entries.delete(oldest);
    }
    this.entries.set(this.key(text, prompt), { formula, confidence });
  }

  clear(): void {
    this.entries.clear();
    this.hits = 0;
    this.misses = 0;
  }

  stats(): BrowserNativeTdfolLlmCacheStats {
    const total = this.hits + this.misses;
    return {
      size: this.entries.size,
      maxSize: this.maxSize,
      hits: this.hits,
      misses: this.misses,
      hitRate: total > 0 ? this.hits / total : 0,
    };
  }

  private key(text: string, prompt: string): string {
    return createBrowserLocalCid(
      canonicalizeJson({ prompt, text, version: 'tdfol-llm-browser-v1' }),
    );
  }
}

export class BrowserNativeTdfolLlmConverter {
  readonly cache: BrowserNativeTdfolLlmResponseCache;

  constructor(
    private readonly options: {
      confidenceThreshold?: number;
      enableCaching?: boolean;
      cacheSize?: number;
    } = {},
  ) {
    this.cache = new BrowserNativeTdfolLlmResponseCache(options.cacheSize ?? 1000);
  }

  convert(text: string): BrowserNativeTdfolLlmParseResult {
    const threshold = this.options.confidenceThreshold ?? 0.85;
    const operatorHints = getTdfolOperatorHintsForText(text);
    const prompt = buildTdfolLlmConversionPrompt(text, operatorHints);
    const cached = this.options.enableCaching === false ? undefined : this.cache.get(text, prompt);
    if (cached)
      return makeResult(
        true,
        cached.formula,
        cached.confidence,
        'pattern',
        true,
        [],
        threshold,
        operatorHints,
      );
    const pattern = convertPattern(text, operatorHints);
    if (pattern && pattern.confidence >= threshold) {
      if (this.options.enableCaching !== false)
        this.cache.put(text, prompt, pattern.formula, pattern.confidence);
      return makeResult(
        true,
        pattern.formula,
        pattern.confidence,
        'pattern',
        false,
        [],
        threshold,
        operatorHints,
      );
    }
    return makeResult(
      false,
      '',
      0,
      'failed',
      false,
      ['Local pattern confidence too low; browser LLM router is fail-closed.'],
      threshold,
      operatorHints,
    );
  }

  getStats(): BrowserNativeTdfolLlmCacheStats {
    return this.cache.stats();
  }

  clearCache(): void {
    this.cache.clear();
  }
}

function makeResult(
  success: boolean,
  formula: string,
  confidence: number,
  method: TdfolLlmParseMethod,
  cacheHit: boolean,
  errors: string[],
  threshold: number,
  operatorHints: TdfolLlmOperatorHint[],
): BrowserNativeTdfolLlmParseResult {
  return {
    success,
    formula,
    confidence,
    method,
    cacheHit,
    errors,
    metadata: {
      threshold,
      operatorHints,
      llmAvailable: false,
      serverCallsAllowed: false,
      pythonRuntime: false,
    },
  };
}

function convertPattern(
  text: string,
  hints: TdfolLlmOperatorHint[],
): { formula: string; confidence: number } | null {
  const match = text
    .toLowerCase()
    .replace(/[.]/g, '')
    .trim()
    .match(
      /^(?:all|every|each)\s+([a-z ]+?)\s+(must not|shall not|must|shall|may|can|is required to|is allowed to|are required to|are allowed to)\s+(.+)$/,
    );
  if (!match) return null;
  const subject = match[1].trim().replace(/\s+/g, ' ').replace(/ies$/, 'y').replace(/s$/, '');
  const action = match[3].replace(/^not\s+/, '');
  const operator = match[2].includes('not') ? 'F' : hints.includes('permission') ? 'P' : 'O';
  const body = hints.includes('temporal_always')
    ? `[](${operator}(${predicate(action)}(x)))`
    : `${operator}(${predicate(action)}(x))`;
  const formula = `forall x. ${predicate(subject)}(x) -> ${body}`;
  parseTdfolFormula(formula);
  return { formula, confidence: hints.includes('universal') && hints.length >= 2 ? 0.9 : 0.8 };
}

function has(text: string, needles: string[]): boolean {
  return needles.some((needle) => text.includes(needle));
}

function predicate(value: string): string {
  return value
    .replace(/\b(the|a|an|to|from|within|without)\b/g, ' ')
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join('');
}

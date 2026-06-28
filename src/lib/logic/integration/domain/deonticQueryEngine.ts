import {
  BrowserNativeIntegrationDeonticLogicCore,
  type IntegrationDeonticConverterOptions,
} from '../converters/deonticLogicConverter';
import type { DeonticNormType, NormativeElement } from '../../deontic/parser';

export interface DeonticQuery {
  readonly normType?: DeonticNormType;
  readonly subject?: string;
  readonly action?: string;
  readonly contains?: string;
  readonly temporal?: string;
}
export interface DeonticQueryMatch {
  readonly norm: NormativeElement;
  readonly formula: string;
  readonly score: number;
  readonly matchedFields: readonly string[];
}

export const DOMAIN_DEONTIC_QUERY_ENGINE_METADATA = {
  sourcePythonModule: 'logic/integration/domain/deontic_query_engine.py',
  browserNative: true,
  wasmCompatible: true,
  serverCallsAllowed: false,
  pythonRuntimeAllowed: false,
  runtimeDependencies: [],
  failClosed: true,
  parity: [
    'typed_norm_filtering',
    'deterministic_text_query_parsing',
    'local_fail_closed_validation',
  ],
} as const;

export class BrowserNativeDomainDeonticQueryEngine {
  readonly metadata = DOMAIN_DEONTIC_QUERY_ENGINE_METADATA;
  private readonly core: BrowserNativeIntegrationDeonticLogicCore;

  constructor(options: IntegrationDeonticConverterOptions = {}) {
    this.core = new BrowserNativeIntegrationDeonticLogicCore(options);
  }

  query(text: string, query: string | DeonticQuery, options: { minConfidence?: number } = {}) {
    const normalized = typeof query === 'string' ? parseQueryText(query) : normalizeQuery(query);
    const errors = validate(text, normalized);
    if (errors.length > 0) return closed(text, normalized, errors);
    const analysis = this.core.analyze(text, { outputFormat: 'json' });
    const matches = analysis.norms
      .map((norm: NormativeElement, index: number) =>
        scoreNorm(norm, analysis.formulas[index] ?? '', normalized),
      )
      .filter(
        (match: DeonticQueryMatch) =>
          match.matchedFields.length > 0 && match.norm.confidence >= (options.minConfidence ?? 0),
      )
      .sort((left: DeonticQueryMatch, right: DeonticQueryMatch) => right.score - left.score);
    return {
      status: analysis.success ? 'success' : 'no_norms',
      success: matches.length > 0,
      sourceText: text,
      query: normalized,
      matches,
      answer: matches.length === 0 ? 'No matching deontic norms found.' : summarize(matches),
      errors: analysis.errors ?? [],
      warnings: analysis.warnings ?? [],
      metadata: {
        ...DOMAIN_DEONTIC_QUERY_ENGINE_METADATA,
        match_count: matches.length,
        norm_counts: analysis.metadata.norm_counts,
      },
    };
  }
}

export function createBrowserNativeDomainDeonticQueryEngine(
  options: IntegrationDeonticConverterOptions = {},
) {
  return new BrowserNativeDomainDeonticQueryEngine(options);
}

export function queryDeonticText(
  text: string,
  query: string | DeonticQuery,
  options: { minConfidence?: number } = {},
) {
  return new BrowserNativeDomainDeonticQueryEngine().query(text, query, options);
}

export const create_deontic_query_engine = createBrowserNativeDomainDeonticQueryEngine;
export const query_deontic_text = queryDeonticText;
export const ask_deontic_query = queryDeonticText;

function parseQueryText(query: string): DeonticQuery {
  const lower = query.toLowerCase();
  const normType =
    lower.includes('prohibit') || lower.includes('forbid')
      ? 'prohibition'
      : lower.includes('permit') ||
          lower.includes('permission') ||
          lower.includes('allow') ||
          lower.includes('may')
        ? 'permission'
        : lower.includes('oblig') || lower.includes('must') || lower.includes('shall')
          ? 'obligation'
          : undefined;
  return normalizeQuery({ normType, contains: stripQueryWords(lower) });
}

function normalizeQuery(query: DeonticQuery): DeonticQuery {
  return {
    normType: query.normType,
    subject: clean(query.subject),
    action: clean(query.action),
    contains: clean(query.contains),
    temporal: clean(query.temporal),
  };
}

function validate(text: string, query: DeonticQuery): string[] {
  const errors: string[] = [];
  if (typeof text !== 'string' || text.trim().length < 3) errors.push('source text is required');
  if (!query.normType && !query.subject && !query.action && !query.contains && !query.temporal)
    errors.push('query must include at least one local criterion');
  return errors;
}

function closed(text: string, query: DeonticQuery, errors: string[]) {
  return {
    status: 'validation_failed',
    success: false,
    sourceText: text,
    query,
    matches: [] as DeonticQueryMatch[],
    answer: '',
    errors,
    metadata: { ...DOMAIN_DEONTIC_QUERY_ENGINE_METADATA, match_count: 0 },
  };
}

function scoreNorm(
  norm: NormativeElement,
  formula: string,
  query: DeonticQuery,
): DeonticQueryMatch {
  const checks: Array<[string, boolean]> = [
    ['normType', !query.normType || norm.normType === query.normType],
    [
      'subject',
      !query.subject || norm.subjects.some((value) => includesText(value, query.subject)),
    ],
    ['action', !query.action || norm.actions.some((value) => includesText(value, query.action))],
    ['contains', !query.contains || includesText(norm.text, query.contains)],
    [
      'temporal',
      !query.temporal ||
        norm.temporalConstraints.some((item) => includesText(item.value, query.temporal)),
    ],
  ];
  const matchedFields = checks
    .filter(([field, ok]) => ok && has(field, query))
    .map(([field]) => field);
  const total = checks.filter(([field]) => has(field, query)).length || 1;
  return {
    norm,
    formula,
    matchedFields,
    score: Number(((matchedFields.length / total) * norm.confidence).toFixed(4)),
  };
}

function has(field: string, query: DeonticQuery): boolean {
  return Boolean(query[field as keyof DeonticQuery]);
}

function summarize(matches: readonly DeonticQueryMatch[]): string {
  return `Found ${matches.length} matching deontic norm(s): ${matches.map((match) => `${match.norm.deonticOperator} ${match.norm.actions[0] ?? match.norm.text}`).join('; ')}`;
}

function stripQueryWords(query: string): string {
  return query
    .replace(
      /\b(who|what|which|is|are|the|there|any|norms?|obligations?|permissions?|prohibitions?)\b/g,
      ' ',
    )
    .replace(/\s+/g, ' ')
    .trim();
}

function clean(value: string | undefined): string | undefined {
  const normalized = value?.toLowerCase().replace(/\s+/g, ' ').trim();
  return normalized && normalized.length > 0 ? normalized : undefined;
}

function includesText(value: string, expected: string | undefined): boolean {
  if (!expected) return true;
  const lower = value.toLowerCase();
  const tokens = expected.split(' ').filter((token) => token.length > 2);
  return (
    lower.includes(expected) ||
    (tokens.length > 0 && tokens.every((token) => lower.includes(token)))
  );
}

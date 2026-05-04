import { parseDeonticText, type DeonticParsedNorm } from '../../deontic/parser';

export type TemporalDeonticStatus = 'active' | 'scheduled' | 'expired' | 'recurring' | 'atemporal';
export interface TemporalDeonticApiOptions {
  readonly asOf?: string | Date;
  readonly effectiveDate?: string | Date;
  readonly minConfidence?: number;
}
export interface TemporalDeonticApiNorm {
  readonly norm: DeonticParsedNorm;
  readonly formula: string;
  readonly temporalStatus: TemporalDeonticStatus;
  readonly interval: { readonly start: string; readonly end?: string; readonly recurring?: string };
}

export const TEMPORAL_DEONTIC_API_METADATA = {
  sourcePythonModule: 'logic/integration/domain/temporal_deontic_api.py',
  browserNative: true,
  wasmCompatible: true,
  serverCallsAllowed: false,
  pythonRuntimeAllowed: false,
  runtimeDependencies: [],
  failClosed: true,
  parity: ['temporal_deontic_norm_extraction', 'deterministic_temporal_status_projection'],
} as const;

export class BrowserNativeTemporalDeonticApi {
  readonly metadata = TEMPORAL_DEONTIC_API_METADATA;
  analyze(text: string, options: TemporalDeonticApiOptions = {}) {
    const sourceText = typeof text === 'string' ? text : '';
    const asOf = date(options.asOf) ?? new Date('2026-05-04T00:00:00.000Z');
    const effectiveDate = date(options.effectiveDate) ?? asOf;
    const errors = [
      ...(sourceText.trim().length < 3 ? ['source text is required'] : []),
      ...(options.asOf && !date(options.asOf) ? ['asOf must be a valid date'] : []),
      ...(options.effectiveDate && !date(options.effectiveDate)
        ? ['effectiveDate must be a valid date']
        : []),
    ];
    if (errors.length > 0) return closed(sourceText, asOf, errors);
    const parsed = parseDeonticText(sourceText, { minConfidence: options.minConfidence ?? 0 });
    const norms = parsed.norms.map((norm: DeonticParsedNorm, index: number) =>
      project(norm, parsed.formulas[index] ?? '', asOf, effectiveDate),
    );
    return {
      status: norms.length > 0 ? 'success' : 'no_norms',
      success: norms.length > 0,
      sourceText,
      asOf: asOf.toISOString(),
      norms,
      obligations: norms.filter((entry) => entry.norm.norm_type === 'obligation'),
      permissions: norms.filter((entry) => entry.norm.norm_type === 'permission'),
      prohibitions: norms.filter((entry) => entry.norm.norm_type === 'prohibition'),
      errors: [],
      warnings: norms.length > 0 ? [] : ['No temporal deontic norms matched locally.'],
      metadata: counts(norms),
    };
  }
}

export function createTemporalDeonticApi(): BrowserNativeTemporalDeonticApi {
  return new BrowserNativeTemporalDeonticApi();
}
export function analyzeTemporalDeonticText(text: string, options: TemporalDeonticApiOptions = {}) {
  return createTemporalDeonticApi().analyze(text, options);
}
export const create_temporal_deontic_api = createTemporalDeonticApi;
export const analyze_temporal_deontic_text = analyzeTemporalDeonticText;
export const analyze_temporal_deontic = analyzeTemporalDeonticText;

function project(
  norm: DeonticParsedNorm,
  formula: string,
  asOf: Date,
  start: Date,
): TemporalDeonticApiNorm {
  const period = norm.temporal_constraints.find((item) => item.type === 'period');
  const bounded = norm.temporal_constraints.find((item) => item.type !== 'period');
  const end = bounded ? addDuration(start, bounded.value) : undefined;
  const temporalStatus = period
    ? 'recurring'
    : end
      ? compare(asOf, start, end)
      : norm.temporal_constraints.length > 0
        ? 'active'
        : 'atemporal';
  return {
    norm,
    formula,
    temporalStatus,
    interval: { start: start.toISOString(), end: end?.toISOString(), recurring: period?.value },
  };
}

function counts(norms: readonly TemporalDeonticApiNorm[]): Record<string, unknown> {
  return {
    ...TEMPORAL_DEONTIC_API_METADATA,
    norm_count: norms.length,
    temporal_count: norms.filter((entry) => entry.norm.temporal_constraints.length > 0).length,
    active_count: norms.filter((entry) => entry.temporalStatus === 'active').length,
  };
}

function closed(text: string, asOf: Date, errors: readonly string[]) {
  return {
    status: 'validation_failed',
    success: false,
    sourceText: text,
    asOf: asOf.toISOString(),
    norms: [],
    obligations: [],
    permissions: [],
    prohibitions: [],
    errors,
    warnings: [],
    metadata: { ...TEMPORAL_DEONTIC_API_METADATA, norm_count: 0, temporal_count: 0 },
  };
}

function date(value: string | Date | undefined): Date | undefined {
  if (value === undefined) return undefined;
  const parsed = value instanceof Date ? value : new Date(value);
  return Number.isNaN(parsed.getTime()) ? undefined : parsed;
}

function addDuration(start: Date, value: string): Date | undefined {
  const match = value.match(/^(\d+)\s+(day|days|week|weeks|month|months|year|years)$/i);
  if (!match) return undefined;
  const next = new Date(start.getTime());
  const amount = Number(match[1]);
  if (match[2].startsWith('day')) next.setUTCDate(next.getUTCDate() + amount);
  else if (match[2].startsWith('week')) next.setUTCDate(next.getUTCDate() + amount * 7);
  else if (match[2].startsWith('month')) next.setUTCMonth(next.getUTCMonth() + amount);
  else next.setUTCFullYear(next.getUTCFullYear() + amount);
  return next;
}

function compare(asOf: Date, start: Date, end: Date): TemporalDeonticStatus {
  if (asOf.getTime() < start.getTime()) return 'scheduled';
  return asOf.getTime() > end.getTime() ? 'expired' : 'active';
}

import { buildDecoderRecordFromIr, buildFormalLogicRecordFromIr } from './exports';
import type { LegalNormIrLike, SpanLike } from './decoder';

export type DeonticMetricRow = Record<string, unknown>;

export interface DeonticParserMetrics extends Record<string, unknown> {
  element_count: number;
  schema_valid_count: number;
  schema_valid_rate: number;
  source_span_valid_count: number;
  source_span_valid_rate: number;
  proof_ready_count: number;
  proof_ready_rate: number;
  repair_required_count: number;
  repair_required_rate: number;
  average_scaffold_quality: number;
  warning_distribution: Record<string, number>;
  formal_logic_target_distribution: Record<string, number>;
  norm_type_distribution: Record<string, number>;
  modality_distribution: Record<string, number>;
  cross_reference_resolution_rate: number;
}

type NormalizedMetricRow = DeonticMetricRow &
  LegalNormIrLike & {
    text: string;
    schema_valid: boolean;
    support_span: SpanLike[];
    scaffold_quality: number;
    export_readiness: {
      proof_ready: boolean;
      export_repair_required: boolean;
      formal_logic_targets: string[];
    };
    parser_warnings: string[];
    resolved_cross_references: Array<Record<string, unknown>>;
  };

export function summarizeParserElements(
  elements: Iterable<DeonticMetricRow> = [],
): DeonticParserMetrics {
  const rows = parserElementsForMetrics(elements);
  const phase8 = summarizePhase8Rows(rows);
  if (rows.length === 0) return emptySummary(phase8);
  let schema = 0,
    span = 0,
    proof = 0,
    repair = 0,
    quality = 0,
    refs = 0,
    resolved = 0;
  const warnings = new Map<string, number>(),
    targets = new Map<string, number>();
  const normTypes = new Map<string, number>(),
    modalities = new Map<string, number>();
  for (const row of rows) {
    if (row.schema_valid) schema += 1;
    if (validSpan(row.text, row.support_span[0])) span += 1;
    if (row.export_readiness.proof_ready) proof += 1;
    if (row.export_readiness.export_repair_required) repair += 1;
    quality += row.scaffold_quality;
    addAll(warnings, row.parser_warnings);
    addAll(targets, row.export_readiness.formal_logic_targets);
    add(normTypes, text(row.norm_type ?? row.normType));
    add(modalities, text(row.modality).toUpperCase() || text(row.deontic_operator));
    for (const ref of row.resolved_cross_references) {
      refs += 1;
      if (ref.resolution_status === 'resolved' || ref.target_exists === true) resolved += 1;
    }
  }
  return {
    element_count: rows.length,
    schema_valid_count: schema,
    schema_valid_rate: rate(schema, rows.length),
    source_span_valid_count: span,
    source_span_valid_rate: rate(span, rows.length),
    proof_ready_count: proof,
    proof_ready_rate: rate(proof, rows.length),
    repair_required_count: repair,
    repair_required_rate: rate(repair, rows.length),
    average_scaffold_quality: round6(quality / rows.length),
    warning_distribution: sorted(warnings),
    formal_logic_target_distribution: sorted(targets),
    norm_type_distribution: sorted(normTypes),
    modality_distribution: sorted(modalities),
    cross_reference_resolution_rate: refs > 0 ? rate(resolved, refs) : 0,
    ...phase8,
  };
}

export const summarize_parser_elements = summarizeParserElements;

export function summarizePhase8ParserMetrics(
  elements: Iterable<DeonticMetricRow> = [],
): Record<string, unknown> {
  return summarizePhase8Rows(parserElementsForMetrics(elements));
}

export const summarize_phase8_parser_metrics = summarizePhase8ParserMetrics;

export function parserElementsForMetrics(
  elements: Iterable<DeonticMetricRow> = [],
): NormalizedMetricRow[] {
  return [...elements].filter(isRecord).map((row) => {
    const actor = text(row.actor) || first(row.subjects);
    const action = text(row.action) || first(row.actions);
    const modality = text(row.modality).toUpperCase() || text(row.deontic_operator);
    const warnings = list(row.parser_warnings ?? row.parserWarnings);
    const blockers = list(row.blockers);
    const omitted = list(
      buildFormalLogicRecordFromIr({ ...row, actor, action, modality }).omitted_formula_slots,
    );
    const proofReady = bool(
      row.proof_ready ?? row.proofReady,
      omitted.length === 0 && blockers.length === 0 && warnings.length === 0,
    );
    const readiness = isRecord(row.export_readiness) ? row.export_readiness : {};
    const crossReferences = row.resolved_cross_references ?? row.resolvedCrossReferences;
    return {
      ...row,
      text: text(row.text),
      source_id: text(row.source_id ?? row.sourceId ?? row.id),
      norm_type: text(row.norm_type ?? row.normType) || normType(modality),
      modality,
      actor,
      action,
      support_span: spans(row.support_span ?? row.supportSpan)[0]
        ? spans(row.support_span ?? row.supportSpan)
        : offsetSpan(row),
      field_spans: record(row.field_spans ?? row.fieldSpans),
      schema_valid: bool(row.schema_valid ?? row.schemaValid, Boolean(actor && action && modality)),
      scaffold_quality: num(row.scaffold_quality ?? row.scaffoldQuality ?? row.confidence),
      parser_warnings: warnings,
      blockers,
      proof_ready: proofReady,
      export_readiness: {
        proof_ready: proofReady,
        export_repair_required: bool(row.repair_required ?? row.repairRequired, !proofReady),
        formal_logic_targets:
          list(readiness.formal_logic_targets).length > 0
            ? list(readiness.formal_logic_targets)
            : ['deontic_fol'],
      },
      resolved_cross_references: Array.isArray(crossReferences)
        ? crossReferences.filter(isRecord)
        : [],
    };
  });
}

export const parser_elements_for_metrics = parserElementsForMetrics;

function summarizePhase8Rows(rows: NormalizedMetricRow[]): Record<string, unknown> {
  const decoder = rows.map((row) => buildDecoderRecordFromIr(row));
  const syntax = rows.map((row) => buildFormalLogicRecordFromIr(row));
  const grounded = rows.map((row) => {
    const fields = record(row.field_spans);
    return rate(
      ['actor', 'action', 'modality'].filter(
        (slot) => spans(fields[slot]).length > 0 || (slot === 'modality' && text(row.modality)),
      ).length,
      3,
    );
  });
  const complete = rows.filter(
    (_, index) =>
      Number(decoder[index].missing_slot_count) === 0 &&
      syntax[index].proof_ready === true &&
      grounded[index] === 1,
  ).length;
  return {
    phase8_source_count: rows.length,
    phase8_record_build_error_count: 0,
    phase8_record_build_error_distribution: {},
    phase8_decoder_reconstruction_record_count: decoder.length,
    phase8_decoder_grounded_phrase_rate: mean(decoder, 'grounded_decoded_phrase_rate'),
    phase8_decoder_ungrounded_phrase_rate: mean(decoder, 'ungrounded_decoded_phrase_rate'),
    phase8_decoder_records_with_missing_slots: decoder.filter(
      (row) => Number(row.missing_slot_count) > 0,
    ).length,
    phase8_prover_required_target_count: rows.length > 0 ? 1 : 0,
    phase8_prover_present_required_target_count: syntax.some((row) => text(row.formula)) ? 1 : 0,
    phase8_prover_syntax_valid_rate:
      rows.length > 0
        ? rate(syntax.filter((row) => row.proof_ready === true).length, rows.length)
        : 0,
    phase8_ir_grounded_slot_rate:
      rows.length > 0
        ? round6(grounded.reduce((total, value) => total + value, 0) / rows.length)
        : 0,
    phase8_quality_record_count: rows.length,
    phase8_quality_complete_count: complete,
    phase8_quality_complete_rate: rows.length > 0 ? rate(complete, rows.length) : 0,
    phase8_quality_requires_validation_count: rows.length - complete,
    phase8_quality_requires_validation_rate:
      rows.length > 0 ? rate(rows.length - complete, rows.length) : 0,
    phase8_coverage_blocker_distribution: {},
  };
}

function emptySummary(phase8: Record<string, unknown>): DeonticParserMetrics {
  return {
    element_count: 0,
    schema_valid_count: 0,
    schema_valid_rate: 0,
    source_span_valid_count: 0,
    source_span_valid_rate: 0,
    proof_ready_count: 0,
    proof_ready_rate: 0,
    repair_required_count: 0,
    repair_required_rate: 0,
    average_scaffold_quality: 0,
    warning_distribution: {},
    formal_logic_target_distribution: {},
    norm_type_distribution: {},
    modality_distribution: {},
    cross_reference_resolution_rate: 0,
    ...phase8,
  };
}

function validSpan(source: string, span: unknown): boolean {
  const pair = Array.isArray(span) ? span : [];
  const start = Number(pair[0]),
    end = Number(pair[1]);
  return (
    Number.isInteger(start) &&
    Number.isInteger(end) &&
    start >= 0 &&
    start <= end &&
    end <= source.length
  );
}
function spans(value: unknown): SpanLike[] {
  return Array.isArray(value) &&
    value.length === 2 &&
    value.every((item) => typeof item === 'number')
    ? [value as SpanLike]
    : [];
}
function offsetSpan(row: DeonticMetricRow): SpanLike[] {
  const start = Number(row.startOffset ?? row.start_offset),
    end = Number(row.endOffset ?? row.end_offset);
  return Number.isFinite(start) && Number.isFinite(end) ? [[start, end]] : [];
}
function addAll(counter: Map<string, number>, values: string[]): void {
  for (const value of values) add(counter, value);
}
function add(counter: Map<string, number>, value: string): void {
  if (value) counter.set(value, (counter.get(value) ?? 0) + 1);
}
function sorted(counter: Map<string, number>): Record<string, number> {
  return Object.fromEntries([...counter.entries()].sort(([a], [b]) => a.localeCompare(b)));
}
function list(value: unknown): string[] {
  return Array.isArray(value) ? value.map(String).filter(Boolean) : [];
}
function first(value: unknown): string {
  return Array.isArray(value) ? text(value[0]) : '';
}
function text(value: unknown): string {
  return typeof value === 'string' ? value.trim() : '';
}
function bool(value: unknown, fallback: boolean): boolean {
  return typeof value === 'boolean' ? value : fallback;
}
function num(value: unknown): number {
  return typeof value === 'number' && Number.isFinite(value) ? value : 0;
}
function normType(modality: string): string {
  return modality === 'P' ? 'permission' : modality === 'F' ? 'prohibition' : 'obligation';
}
function mean(rows: Array<Record<string, unknown>>, field: string): number {
  return rows.length > 0
    ? round6(rows.reduce((total, row) => total + num(row[field]), 0) / rows.length)
    : 0;
}
function rate(numerator: number, denominator: number): number {
  return denominator > 0 ? round6(numerator / denominator) : 0;
}
function round6(value: number): number {
  return Math.round(value * 1_000_000) / 1_000_000;
}
function record(value: unknown): Record<string, unknown> {
  return isRecord(value) ? value : {};
}
function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}

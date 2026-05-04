import type { SpanLike } from './decoder';

export type DeonticIrModality = 'O' | 'P' | 'F' | 'DEF' | 'APP' | 'EXEMPT' | 'LIFE';
export type DeonticIrNormType =
  | 'obligation'
  | 'permission'
  | 'prohibition'
  | 'definition'
  | 'applicability'
  | 'exemption'
  | 'instrument_lifecycle'
  | 'penalty';

export interface LegalNormIrDetail {
  value?: string;
  normalized_text?: string;
  raw_text?: string;
  span?: SpanLike;
}

export interface LegalNormIr {
  source_id: string;
  norm_type: DeonticIrNormType;
  modality: DeonticIrModality;
  actor: string;
  action: string;
  recipient?: string;
  mental_state?: string;
  support_span: SpanLike[];
  field_spans: Record<string, SpanLike[]>;
  conditions: LegalNormIrDetail[];
  exceptions: LegalNormIrDetail[];
  temporal_constraints: LegalNormIrDetail[];
  cross_references: LegalNormIrDetail[];
  parser_warnings: string[];
  blockers: string[];
  proof_ready: boolean;
  schema_version: string;
}

export type LegalNormIrInput = Record<string, unknown>;

export interface LegalNormIrValidation {
  valid: boolean;
  missing_slots: string[];
  blockers: string[];
}

const MODALITY_BY_NORM_TYPE: Record<DeonticIrNormType, DeonticIrModality> = {
  obligation: 'O',
  permission: 'P',
  prohibition: 'F',
  definition: 'DEF',
  applicability: 'APP',
  exemption: 'EXEMPT',
  instrument_lifecycle: 'LIFE',
  penalty: 'F',
};

export function createLegalNormIr(input: LegalNormIrInput): LegalNormIr {
  const normType = normalizeNormType(input.norm_type ?? input.normType);
  const ir: LegalNormIr = {
    source_id:
      text(input.source_id ?? input.sourceId) || stableId(text(input.actor), text(input.action)),
    norm_type: normType,
    modality: normalizeModality(input.modality, MODALITY_BY_NORM_TYPE[normType]),
    actor: text(input.actor),
    action: text(input.action),
    recipient: optionalText(input.recipient),
    mental_state: optionalText(input.mental_state ?? input.mentalState),
    support_span: normalizeSpans(input.support_span ?? input.supportSpan),
    field_spans: normalizeFieldSpans(input.field_spans ?? input.fieldSpans),
    conditions: normalizeDetails(input.conditions),
    exceptions: normalizeDetails(input.exceptions),
    temporal_constraints: normalizeDetails(input.temporal_constraints ?? input.temporalConstraints),
    cross_references: normalizeDetails(input.cross_references ?? input.crossReferences),
    parser_warnings: stringList(input.parser_warnings ?? input.parserWarnings),
    blockers: stringList(input.blockers),
    proof_ready: input.proof_ready === true,
    schema_version: text(input.schema_version) || 'ts-deontic-ir-v1',
  };
  const validation = validateLegalNormIr(ir);
  ir.blockers = validation.blockers;
  ir.proof_ready = input.proof_ready === true && validation.valid;
  return ir;
}

export const create_legal_norm_ir = createLegalNormIr;

export function validateLegalNormIr(ir: LegalNormIr): LegalNormIrValidation {
  const missing = requiredSlots(ir).filter(
    (slot) => text((ir as unknown as Record<string, unknown>)[slot]).length === 0,
  );
  const blockers = [
    ...new Set([
      ...ir.blockers,
      ...ir.parser_warnings,
      ...missing.map((slot) => `missing_ir_slot:${slot}`),
    ]),
  ].filter(Boolean);
  return { valid: missing.length === 0 && blockers.length === 0, missing_slots: missing, blockers };
}

export const validate_legal_norm_ir = validateLegalNormIr;

export function legalNormIrToRecord(ir: LegalNormIr): Record<string, unknown> {
  return { ...ir };
}

export const legal_norm_ir_to_record = legalNormIrToRecord;

function requiredSlots(ir: LegalNormIr): string[] {
  return ir.modality === 'DEF' || ir.modality === 'APP' || ir.modality === 'LIFE'
    ? ['actor', 'action']
    : ['actor', 'action', 'modality'];
}

function normalizeNormType(value: unknown): DeonticIrNormType {
  const lowered = text(value).toLowerCase();
  if (
    lowered === 'permission' ||
    lowered === 'prohibition' ||
    lowered === 'definition' ||
    lowered === 'applicability' ||
    lowered === 'exemption' ||
    lowered === 'instrument_lifecycle' ||
    lowered === 'penalty'
  ) {
    return lowered;
  }
  return 'obligation';
}

function normalizeModality(value: unknown, fallback: DeonticIrModality): DeonticIrModality {
  const upper = text(value).toUpperCase();
  if (
    upper === 'O' ||
    upper === 'P' ||
    upper === 'F' ||
    upper === 'DEF' ||
    upper === 'APP' ||
    upper === 'EXEMPT' ||
    upper === 'LIFE'
  ) {
    return upper;
  }
  return fallback;
}

function normalizeDetails(value: unknown): LegalNormIrDetail[] {
  if (!Array.isArray(value)) return [];
  return value.map((item) => {
    const row: Record<string, unknown> = isRecord(item) ? item : { value: item };
    return {
      value: optionalText(row.value),
      normalized_text: optionalText(row.normalized_text),
      raw_text: optionalText(row.raw_text ?? row.text),
      span: normalizeSpans(row.span ?? row.source_span)[0],
    };
  });
}

function normalizeFieldSpans(value: unknown): Record<string, SpanLike[]> {
  if (!isRecord(value)) return {};
  return Object.fromEntries(
    Object.entries(value).map(([key, span]) => [key, normalizeSpans(span)]),
  );
}

function normalizeSpans(value: unknown): SpanLike[] {
  return Array.isArray(value) &&
    value.length === 2 &&
    value.every((item) => typeof item === 'number')
    ? [[value[0], value[1]]]
    : [];
}

function stringList(value: unknown): string[] {
  return Array.isArray(value) ? value.map(text).filter(Boolean) : [];
}

function optionalText(value: unknown): string | undefined {
  return text(value) || undefined;
}

function text(value: unknown): string {
  return typeof value === 'string' ? value.trim() : '';
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}

function stableId(...parts: string[]): string {
  let hash = 0x811c9dc5;
  for (const char of ['source', ...parts].join('\u001f')) {
    hash ^= char.charCodeAt(0);
    hash = Math.imul(hash, 0x01000193) >>> 0;
  }
  return `source-${hash.toString(16).padStart(8, '0')}`;
}

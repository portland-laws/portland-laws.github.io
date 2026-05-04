import { normalizePredicateName } from '../normalization';
import { decodeLegalNormIr, type LegalNormIrLike, type SpanLike } from './decoder';

export const EXPORT_TABLE_SPECS: Record<
  string,
  { primary_key: string; requires_source_id: boolean }
> = {
  canonical: { primary_key: 'source_id', requires_source_id: true },
  formal_logic: { primary_key: 'formula_id', requires_source_id: true },
  proof_obligations: { primary_key: 'proof_obligation_id', requires_source_id: true },
  repair_queue: { primary_key: 'repair_id', requires_source_id: true },
  decoder_reconstructions: { primary_key: 'reconstruction_id', requires_source_id: true },
};

export interface DeonticExportTables {
  canonical: Array<Record<string, unknown>>;
  formal_logic: Array<Record<string, unknown>>;
  proof_obligations: Array<Record<string, unknown>>;
  repair_queue: Array<Record<string, unknown>>;
  decoder_reconstructions: Array<Record<string, unknown>>;
}

export interface ExportLegalNormLike extends LegalNormIrLike {
  canonical_citation?: string;
  source_text?: string;
  support_text?: string;
  proof_ready?: boolean;
  blockers?: string[];
  schema_version?: string;
}

export function buildDocumentExportTablesFromIr(
  norms: Iterable<ExportLegalNormLike>,
): DeonticExportTables {
  const tables: DeonticExportTables = {
    canonical: [],
    formal_logic: [],
    proof_obligations: [],
    repair_queue: [],
    decoder_reconstructions: [],
  };
  for (const norm of norms) {
    const formal = buildFormalLogicRecordFromIr(norm);
    const proof = buildProofObligationRecordFromIr(norm, formal);
    tables.canonical.push(canonicalRecordFromIr(norm));
    tables.formal_logic.push(formal);
    tables.proof_obligations.push(proof);
    tables.decoder_reconstructions.push(buildDecoderRecordFromIr(norm));
    if (proof.requires_validation === true)
      tables.repair_queue.push(buildRepairQueueRecordFromIr(norm, formal));
  }
  return tables;
}

export const build_document_export_tables_from_ir = buildDocumentExportTablesFromIr;

export function parserElementsToExportTables(
  elements: Iterable<Record<string, unknown>>,
): DeonticExportTables {
  return buildDocumentExportTablesFromIr(elements as Iterable<ExportLegalNormLike>);
}

export const parser_elements_to_export_tables = parserElementsToExportTables;

export function buildFormalLogicRecordFromIr(norm: ExportLegalNormLike): Record<string, unknown> {
  const formula = deonticFormulaFromIr(norm);
  const blockers = normBlockers(norm);
  const omitted = omittedFormulaSlots(norm);
  const proofReady = (norm.proof_ready ?? blockers.length === 0) === true && omitted.length === 0;
  return {
    formula_id: stableId('formula', sourceId(norm), formula),
    source_id: sourceId(norm),
    canonical_citation: text(norm.canonical_citation),
    target_logic: 'deontic_fol',
    formula,
    modality: text(norm.modality).toUpperCase(),
    norm_type: text(norm.norm_type ?? norm.normType),
    support_span: spans(norm.support_span ?? norm.supportSpan),
    field_spans: norm.field_spans ?? norm.fieldSpans ?? {},
    proof_ready: proofReady,
    requires_validation: !proofReady,
    repair_required: !proofReady,
    blockers:
      blockers.length > 0 ? blockers : omitted.map((slot) => `missing_formula_slot:${slot}`),
    parser_warnings: parserWarnings(norm),
    omitted_formula_slots: omitted,
    schema_version: schemaVersion(norm),
  };
}

export const build_formal_logic_record_from_ir = buildFormalLogicRecordFromIr;

export function buildProofObligationRecordFromIr(
  norm: ExportLegalNormLike,
  formal: Record<string, unknown> = buildFormalLogicRecordFromIr(norm),
): Record<string, unknown> {
  return {
    proof_obligation_id: stableId('proof', sourceId(norm), text(formal.formula)),
    formula_id: formal.formula_id,
    source_id: sourceId(norm),
    formula: formal.formula,
    target_logic: formal.target_logic,
    theorem_candidate: formal.proof_ready === true,
    proof_ready: formal.proof_ready === true,
    requires_validation: formal.requires_validation === true,
    repair_required: formal.repair_required === true,
    blockers: formal.blockers,
    schema_version: schemaVersion(norm),
  };
}

export const build_proof_obligation_record_from_ir = buildProofObligationRecordFromIr;

export function buildDecoderRecordFromIr(norm: ExportLegalNormLike): Record<string, unknown> {
  const decoded = decodeLegalNormIr(norm);
  const phrases = decoded.phrases.map((phrase) => ({
    text: phrase.text,
    slot: phrase.slot,
    spans: phrase.spans,
    fixed: phrase.fixed,
    provenance_only: phrase.provenanceOnly,
  }));
  const fixed = phrases.filter((phrase) => phrase.fixed === true).length;
  const ungrounded = phrases.filter(
    (phrase) => phrase.fixed !== true && phrase.spans.length === 0,
  ).length;
  const legal = phrases.length - fixed;
  return {
    reconstruction_id: stableId('reconstruction', sourceId(norm), decoded.text),
    source_id: sourceId(norm),
    canonical_citation: text(norm.canonical_citation),
    source_text: text(norm.source_text),
    support_text: text(norm.support_text),
    decoded_text: decoded.text,
    support_span: decoded.supportSpan,
    phrase_count: phrases.length,
    fixed_phrase_count: fixed,
    legal_phrase_count: legal,
    grounded_phrase_count: legal - ungrounded,
    ungrounded_decoded_phrase_count: ungrounded,
    grounded_decoded_phrase_rate: rate(legal - ungrounded, legal, 1),
    ungrounded_decoded_phrase_rate: rate(ungrounded, legal, 0),
    missing_slot_count: decoded.missingSlots.length,
    missing_slots: decoded.missingSlots,
    parser_warnings: decoded.parserWarnings,
    phrase_provenance: phrases,
    proof_ready: (norm.proof_ready ?? normBlockers(norm).length === 0) === true,
    requires_validation: normBlockers(norm).length > 0 || decoded.missingSlots.length > 0,
    schema_version: schemaVersion(norm),
  };
}

export const build_decoder_record_from_ir = buildDecoderRecordFromIr;

function canonicalRecordFromIr(norm: ExportLegalNormLike): Record<string, unknown> {
  return {
    source_id: sourceId(norm),
    canonical_citation: text(norm.canonical_citation),
    norm_type: text(norm.norm_type ?? norm.normType),
    modality: text(norm.modality).toUpperCase(),
    actor: text(norm.actor),
    action: text(norm.action),
    support_span: spans(norm.support_span ?? norm.supportSpan),
    schema_version: schemaVersion(norm),
  };
}

function buildRepairQueueRecordFromIr(
  norm: ExportLegalNormLike,
  formal: Record<string, unknown>,
): Record<string, unknown> {
  const reasons = Array.isArray(formal.blockers) ? formal.blockers.map(String) : [];
  return {
    repair_id: stableId('repair', sourceId(norm), reasons.join('|')),
    formula_id: formal.formula_id,
    source_id: sourceId(norm),
    target_logic: formal.target_logic,
    formula: formal.formula,
    reasons,
    requires_llm_repair: false,
    allow_llm_repair: false,
    schema_version: schemaVersion(norm),
  };
}

function deonticFormulaFromIr(norm: ExportLegalNormLike): string {
  return `${text(norm.modality).toUpperCase() || 'O'}(forall x (${predicate(norm.actor, 'UnspecifiedActor')}(x) -> ${predicate(norm.action, 'UnspecifiedAction')}(x)))`;
}

function omittedFormulaSlots(norm: ExportLegalNormLike): string[] {
  return [
    ['actor', norm.actor],
    ['action', norm.action],
    ['modality', norm.modality],
  ]
    .filter((entry) => !text(entry[1]))
    .map((entry) => String(entry[0]));
}

function normBlockers(norm: ExportLegalNormLike): string[] {
  return [
    ...new Set([...(norm.blockers ?? []), ...parserWarnings(norm)].map(String).filter(Boolean)),
  ];
}

function parserWarnings(norm: ExportLegalNormLike): string[] {
  return [
    ...(norm.quality?.parser_warnings ?? norm.quality?.parserWarnings ?? []),
    ...(norm.parser_warnings ?? norm.parserWarnings ?? []),
  ];
}

function sourceId(norm: ExportLegalNormLike): string {
  return text(norm.source_id ?? norm.sourceId);
}

function schemaVersion(norm: ExportLegalNormLike): string {
  return text(norm.schema_version) || 'ts-deontic-export-v1';
}

function spans(value: unknown): SpanLike[] {
  return Array.isArray(value) &&
    value.length === 2 &&
    value.every((item) => typeof item === 'number')
    ? [value as SpanLike]
    : [];
}

function predicate(value: unknown, fallback: string): string {
  const normalized = normalizePredicateName(text(value));
  return normalized
    ? normalized
        .split('_')
        .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
        .join('')
    : fallback;
}

function text(value: unknown): string {
  return typeof value === 'string' ? value.trim() : '';
}

function stableId(prefix: string, ...parts: string[]): string {
  let hash = 0x811c9dc5;
  for (const char of [prefix, ...parts].join('\u001f')) {
    hash ^= char.charCodeAt(0);
    hash = Math.imul(hash, 0x01000193) >>> 0;
  }
  return `${prefix}-${hash.toString(16).padStart(8, '0')}`;
}

function rate(numerator: number, denominator: number, fallback: number): number {
  return denominator > 0 ? Math.round((numerator / denominator) * 1_000_000) / 1_000_000 : fallback;
}

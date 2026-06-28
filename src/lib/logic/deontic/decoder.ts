export type SpanLike = [number, number] | number[];

export interface LegalNormDetailLike {
  value?: unknown;
  normalized_text?: unknown;
  raw_text?: unknown;
  text?: unknown;
  canonical_citation?: unknown;
  citation?: unknown;
  target?: unknown;
  span?: unknown;
  source_span?: unknown;
  support_span?: unknown;
  clause_span?: unknown;
}

export interface LegalNormIrLike {
  source_id?: string;
  sourceId?: string;
  norm_type?: string;
  normType?: string;
  actor?: string;
  modality?: string;
  action?: string;
  recipient?: string;
  mental_state?: string;
  mentalState?: string;
  support_span?: unknown;
  supportSpan?: unknown;
  field_spans?: Record<string, unknown>;
  fieldSpans?: Record<string, unknown>;
  quality?: { parser_warnings?: string[]; parserWarnings?: string[] };
  parser_warnings?: string[];
  parserWarnings?: string[];
  overrides?: LegalNormDetailLike[];
  conditions?: LegalNormDetailLike[];
  exceptions?: LegalNormDetailLike[];
  temporal_constraints?: LegalNormDetailLike[];
  temporalConstraints?: LegalNormDetailLike[];
  cross_references?: LegalNormDetailLike[];
  crossReferences?: LegalNormDetailLike[];
  resolved_cross_references?: LegalNormDetailLike[];
  resolvedCrossReferences?: LegalNormDetailLike[];
  legal_frame?: Record<string, unknown>;
  legalFrame?: Record<string, unknown>;
  formal_terms?: Record<string, unknown>;
  formalTerms?: Record<string, unknown>;
  penalty?: Record<string, unknown>;
}

export interface DecodedPhrase {
  text: string;
  slot: string;
  spans: SpanLike[];
  fixed: boolean;
  provenanceOnly: boolean;
  provenance_only: boolean;
}

export interface DecodedLegalText {
  sourceId: string;
  source_id: string;
  text: string;
  phrases: DecodedPhrase[];
  supportSpan: SpanLike[];
  support_span: SpanLike[];
  parserWarnings: string[];
  parser_warnings: string[];
  missingSlots: string[];
  missing_slots: string[];
}

type DecodeResult = [DecodedPhrase[], string[]];

export function decodeLegalNormIr(norm: LegalNormIrLike): DecodedLegalText {
  const normType = textValue(norm.norm_type ?? norm.normType);
  const modality = textValue(norm.modality).toUpperCase();
  let phrases: DecodedPhrase[];
  let missingSlots: string[];

  if (modality === 'DEF' || normType === 'definition') {
    [phrases, missingSlots] = decodeDefinition(norm);
  } else if (modality === 'APP' || normType === 'applicability') {
    [phrases, missingSlots] = decodeApplicability(norm);
  } else if (modality === 'EXEMPT' || normType === 'exemption') {
    [phrases, missingSlots] = decodeExemption(norm);
  } else if (modality === 'LIFE' || normType === 'instrument_lifecycle') {
    [phrases, missingSlots] = decodeLifecycle(norm);
  } else if (normType === 'penalty') {
    [phrases, missingSlots] = decodePenalty(norm);
  } else {
    [phrases, missingSlots] = decodeDeonticClause(norm);
  }

  const sourceId = textValue(norm.source_id ?? norm.sourceId);
  const supportSpan = coerceSpans(norm.support_span ?? norm.supportSpan);
  const parserWarnings = [
    ...(norm.quality?.parser_warnings ?? norm.quality?.parserWarnings ?? []),
    ...(norm.parser_warnings ?? norm.parserWarnings ?? []),
  ];

  return {
    sourceId,
    source_id: sourceId,
    text: sentenceFromPhrases(phrases),
    phrases,
    supportSpan,
    support_span: supportSpan,
    parserWarnings,
    parser_warnings: parserWarnings,
    missingSlots,
    missing_slots: missingSlots,
  };
}

export const decode_legal_norm_ir = decodeLegalNormIr;

function decodeDeonticClause(norm: LegalNormIrLike): DecodeResult {
  const phrases: DecodedPhrase[] = [];
  const missing: string[] = [];
  const actor = cleanText(norm.actor);
  const mentalState = cleanText(norm.mental_state ?? norm.mentalState);
  const action = cleanText(actionWithoutLeadingModal(norm.action));
  const actionPhrase = actionWithoutLeadingMentalState(action, mentalState);
  const recipient = recipientPhraseText(norm.recipient);
  const modal = modalPhrase(norm.modality);

  for (const override of norm.overrides ?? []) {
    const overrideText = slotText(override);
    if (!overrideText) continue;
    if (!overrideText.toLowerCase().startsWith('notwithstanding ')) {
      phrases.push(fixedPhrase('notwithstanding', 'override_connector'));
    }
    phrases.push(detailPhrase(overrideText, 'overrides', override, norm));
    phrases.push(fixedPhrase(',', 'override_punctuation'));
  }

  if (actor) phrases.push(phrase(actor, 'actor', norm));
  else missing.push('actor');

  if (modal) phrases.push(phrase(modal, 'modality', norm));
  else missing.push('modality');

  if (mentalState) phrases.push(phrase(mentalState, 'mental_state', norm));

  if (actionPhrase) phrases.push(phrase(actionPhrase, 'action', norm));
  else missing.push('action');

  if (recipient && !textAlreadyContains(actionPhrase, recipient)) {
    phrases.push(fixedPhrase('to', 'recipient_connector'));
    phrases.push(phrase(recipient, 'recipient', norm));
  }

  for (const condition of norm.conditions ?? []) {
    const conditionText = slotText(condition);
    if (!conditionText) continue;
    phrases.push(fixedPhrase('if', 'condition_connector'));
    phrases.push(detailPhrase(conditionText, 'conditions', condition, norm));
  }

  for (const temporal of norm.temporal_constraints ?? norm.temporalConstraints ?? []) {
    const temporalText = temporalPhraseText(temporal);
    if (temporalText && !textAlreadyContains(actionPhrase, temporalText)) {
      phrases.push(detailPhrase(temporalText, 'temporal_constraints', temporal, norm));
    }
  }

  for (const exception of norm.exceptions ?? []) {
    const exceptionText = slotText(exception);
    if (!exceptionText) continue;
    const lowered = exceptionText.toLowerCase();
    if (lowered.startsWith('unless ') || lowered.startsWith('except ')) {
      phrases.push(detailPhrase(exceptionText, 'exceptions', exception, norm));
    } else {
      phrases.push(
        fixedPhrase(lowered.startsWith('as ') ? 'except' : 'unless', 'exception_connector'),
      );
      phrases.push(detailPhrase(exceptionText, 'exceptions', exception, norm));
    }
  }

  appendCrossReferenceProvenance(phrases, norm);
  return [phrases, missing];
}

function decodeDefinition(norm: LegalNormIrLike): DecodeResult {
  const phrases: DecodedPhrase[] = [];
  const missing: string[] = [];
  const term = cleanText(norm.actor);
  const body = definitionBody(norm);

  if (term) {
    phrases.push(fixedPhrase('the term', 'definition_connector'));
    phrases.push(phrase(term, 'actor', norm));
  } else {
    missing.push('defined_term');
  }

  phrases.push(fixedPhrase('means', 'definition_connector'));
  if (body) phrases.push(phrase(body, 'definition_body', norm));
  else missing.push('definition_body');
  return [phrases, missing];
}

function decodeApplicability(norm: LegalNormIrLike): DecodeResult {
  const phrases: DecodedPhrase[] = [];
  const missing: string[] = [];
  const scope = cleanText(norm.actor);
  const target = cleanText(stripPrefix(norm.action, ['apply to', 'applies to']));

  if (scope) phrases.push(phrase(scope, 'actor', norm));
  else missing.push('scope');
  phrases.push(fixedPhrase('applies to', 'applicability_connector'));
  if (target) phrases.push(phrase(target, 'action', norm));
  else missing.push('applicability_target');
  appendCrossReferenceProvenance(phrases, norm);
  return [phrases, missing];
}

function decodeExemption(norm: LegalNormIrLike): DecodeResult {
  const phrases: DecodedPhrase[] = [];
  const missing: string[] = [];
  const target = cleanText(norm.actor);
  const requirement = cleanText(stripPrefix(norm.action, ['exempt from', 'not apply to']));

  if (target) phrases.push(phrase(target, 'actor', norm));
  else missing.push('exemption_target');
  phrases.push(fixedPhrase('is exempt from', 'exemption_connector'));
  if (requirement) phrases.push(phrase(requirement, 'action', norm));
  else missing.push('requirement');
  appendCrossReferenceProvenance(phrases, norm);
  return [phrases, missing];
}

function decodeLifecycle(norm: LegalNormIrLike): DecodeResult {
  const phrases: DecodedPhrase[] = [];
  const missing: string[] = [];
  const instrument = cleanText(norm.actor);
  const action = cleanText(norm.action);

  if (instrument) phrases.push(phrase(instrument, 'actor', norm));
  else missing.push('instrument');
  if (action) {
    if (action.toLowerCase().startsWith('valid for ')) {
      phrases.push(fixedPhrase('is', 'lifecycle_connector'));
    }
    phrases.push(phrase(action, 'action', norm));
  } else {
    missing.push('lifecycle_action');
  }
  return [phrases, missing];
}

function decodePenalty(norm: LegalNormIrLike): DecodeResult {
  const phrases: DecodedPhrase[] = [];
  const missing: string[] = [];
  const actor = cleanText(norm.actor);
  const sanction = penaltySanctionText(norm);

  if (actor) phrases.push(phrase(actor, 'actor', norm));
  else missing.push('actor');
  phrases.push(fixedPhrase('is subject to', 'penalty_connector'));
  if (sanction) phrases.push(phrase(sanction, 'action', norm));
  else missing.push('penalty');
  return [phrases, missing];
}

function phrase(text: string, slot: string, norm: LegalNormIrLike): DecodedPhrase {
  return makePhrase(cleanText(text), slot, slotSpans(norm, slot));
}

function detailPhrase(
  text: string,
  slot: string,
  detail: LegalNormDetailLike,
  norm: LegalNormIrLike,
): DecodedPhrase {
  const detailSpans = coerceSpans(detail.span ?? detail.clause_span);
  return makePhrase(
    cleanText(text),
    slot,
    detailSpans.length > 0 ? detailSpans : slotSpans(norm, slot),
  );
}

function fixedPhrase(text: string, slot: string): DecodedPhrase {
  return makePhrase(text, slot, [], true);
}

function provenancePhrase(text: string, slot: string, spans: SpanLike[]): DecodedPhrase {
  return makePhrase(cleanText(text), slot, spans, false, true);
}

function makePhrase(
  text: string,
  slot: string,
  spans: SpanLike[] = [],
  fixed = false,
  provenanceOnly = false,
): DecodedPhrase {
  return {
    text,
    slot,
    spans,
    fixed,
    provenanceOnly,
    provenance_only: provenanceOnly,
  };
}

function appendCrossReferenceProvenance(phrases: DecodedPhrase[], norm: LegalNormIrLike): void {
  const seen = new Set(phrases.map((item) => phraseKey(item.slot, item.text, item.spans)));
  for (const reference of crossReferenceRecords(norm)) {
    const text = referenceText(reference);
    const spans = referenceSpans(reference);
    const key = phraseKey('cross_references', text, spans);
    if (!text || spans.length === 0 || seen.has(key)) continue;
    seen.add(key);
    phrases.push(provenancePhrase(text, 'cross_references', spans));
  }
}

function crossReferenceRecords(norm: LegalNormIrLike): LegalNormDetailLike[] {
  const records: LegalNormDetailLike[] = [];
  const seen = new Set<string>();
  for (const reference of [
    ...(norm.cross_references ?? norm.crossReferences ?? []),
    ...(norm.resolved_cross_references ?? norm.resolvedCrossReferences ?? []),
  ]) {
    const text = referenceText(reference);
    const spans = referenceSpans(reference);
    const key = phraseKey('cross_references', text, spans);
    if (!text || seen.has(key)) continue;
    seen.add(key);
    records.push(reference);
  }
  return records;
}

function referenceText(reference: LegalNormDetailLike): string {
  return slotText({
    normalized_text: reference.normalized_text,
    raw_text: reference.raw_text,
    canonical_citation: reference.canonical_citation,
    value: reference.value,
    target: reference.target,
    text: reference.text,
  });
}

function referenceSpans(reference: LegalNormDetailLike): SpanLike[] {
  return dedupeSpans([
    ...coerceSpans(reference.span),
    ...coerceSpans(reference.source_span),
    ...coerceSpans(reference.support_span),
    ...coerceSpans(reference.clause_span),
  ]);
}

function modalPhrase(modality: unknown): string {
  return { O: 'shall', P: 'may', F: 'shall not' }[textValue(modality).toUpperCase()] ?? '';
}

function temporalPhraseText(record: LegalNormDetailLike): string {
  const value = slotText(record);
  const lowered = value.toLowerCase();
  if (!value) return '';
  if (/^(within|by|before|after|not later than|no later than)\s+/i.test(value)) return value;
  if (/\b\d+\b/.test(value) || lowered.includes(' after ') || lowered.includes(' before ')) {
    return `within ${value}`;
  }
  return value;
}

function definitionBody(norm: LegalNormIrLike): string {
  const legalFrame = norm.legal_frame ?? norm.legalFrame ?? {};
  const formalTerms = norm.formal_terms ?? norm.formalTerms ?? {};
  for (const key of ['definition_body', 'body', 'defined_as']) {
    const value = legalFrame[key] ?? formalTerms[key];
    if (value) return cleanText(value);
  }
  return stripPrefix(norm.action, ['mean', 'means', 'defined as']);
}

function penaltySanctionText(norm: LegalNormIrLike): string {
  const action = cleanText(stripPrefix(norm.action, ['incur', 'be subject to', 'subject to']));
  if (action) return action;

  const penalty = norm.penalty ?? {};
  const imprisonment = mappingValue(penalty.imprisonment_duration);
  const imprisonmentText = imprisonment ? slotText(imprisonment) : '';
  if (imprisonmentText) return imprisonmentText;

  const minText = mappingValue(penalty.minimum_amount)
    ? slotText(mappingValue(penalty.minimum_amount) as LegalNormDetailLike)
    : '';
  const maxText = mappingValue(penalty.maximum_amount)
    ? slotText(mappingValue(penalty.maximum_amount) as LegalNormDetailLike)
    : '';
  const classification = cleanText(penalty.classification ?? penalty.sanction_class);
  const recurrence = mappingValue(penalty.recurrence);
  const recurrenceText = recurrence ? slotText(recurrence) : '';
  let amount = '';
  if (minText && maxText) amount = `of not less than ${minText} and not more than ${maxText}`;
  else if (maxText) amount = `of not more than ${maxText}`;
  else if (minText) amount = `of not less than ${minText}`;

  return cleanText(
    [classification, penalty.has_fine ? 'fine' : 'penalty', amount, recurrenceText]
      .filter(Boolean)
      .join(' '),
  );
}

function slotText(record: LegalNormDetailLike): string {
  for (const key of [
    'value',
    'normalized_text',
    'raw_text',
    'text',
    'canonical_citation',
    'citation',
  ] as const) {
    const value = record[key];
    if (value) return cleanText(value);
  }
  return '';
}

function slotSpans(norm: LegalNormIrLike, slot: string): SpanLike[] {
  const fieldSpans = norm.field_spans ?? norm.fieldSpans ?? {};
  if (slot === 'mental_state') {
    const spans = mentalStateSpansFromAction(norm, fieldSpans);
    if (spans.length > 0) return spans;
  }
  if (slot === 'action') {
    const spans = actionSpansWithoutLeadingMentalState(norm, fieldSpans);
    if (spans.length > 0) return spans;
  }
  const candidates = [
    slot,
    ...({ actor: ['subject'], recipient: ['action_recipient'] }[slot] ?? []),
  ];
  for (const key of candidates) {
    const spans = coerceSpans(fieldSpans[key]);
    if (spans.length > 0) return spans;
  }
  return coerceSpans(norm.support_span ?? norm.supportSpan);
}

function mentalStateSpansFromAction(
  norm: LegalNormIrLike,
  fieldSpans: Record<string, unknown>,
): SpanLike[] {
  const explicit = coerceSpans(fieldSpans.mental_state);
  if (explicit.length > 0) return explicit;
  const mentalState = cleanText(norm.mental_state ?? norm.mentalState);
  const action = cleanText(actionWithoutLeadingModal(norm.action));
  const actionSpans = coerceSpans(fieldSpans.action);
  if (!mentalState || !startsWithPhrase(action, mentalState) || actionSpans.length === 0) return [];
  return [[actionSpans[0][0], actionSpans[0][0] + mentalState.length]];
}

function actionSpansWithoutLeadingMentalState(
  norm: LegalNormIrLike,
  fieldSpans: Record<string, unknown>,
): SpanLike[] {
  const actionSpans = coerceSpans(fieldSpans.action);
  const mentalState = cleanText(norm.mental_state ?? norm.mentalState);
  const action = cleanText(actionWithoutLeadingModal(norm.action));
  if (actionSpans.length === 0 || !mentalState || !startsWithPhrase(action, mentalState)) return [];
  const mentalSpans = mentalStateSpansFromAction(norm, fieldSpans);
  if (mentalSpans.length === 0 || actionSpans[0][1] <= mentalSpans[0][1]) return [];
  return [[mentalSpans[0][1] + 1, actionSpans[0][1]]];
}

function coerceSpans(value: unknown): SpanLike[] {
  const span = coerceSpan(value);
  if (span) return [span];
  if (!Array.isArray(value)) return [];
  return value.map(coerceSpan).filter((item): item is SpanLike => Boolean(item));
}

function coerceSpan(value: unknown): SpanLike | null {
  if (!Array.isArray(value) || value.length !== 2) return null;
  const start = Number(value[0]);
  const end = Number(value[1]);
  return Number.isFinite(start) && Number.isFinite(end) ? [start, end] : null;
}

function sentenceFromPhrases(phrases: DecodedPhrase[]): string {
  let text = phrases
    .filter((item) => item.text && !item.provenanceOnly)
    .map((item) => item.text)
    .join(' ')
    .replace(/\s+/g, ' ')
    .replace(/\s+([,.;:])/g, '$1')
    .trim();
  if (text) text = text.charAt(0).toUpperCase() + text.slice(1);
  if (text && !/[.!?]$/.test(text)) text += '.';
  return text;
}

function actionWithoutLeadingModal(action: unknown): string {
  return textValue(action)
    .replace(/^(?:shall not|must not|may not|shall|must|may)\s+/i, '')
    .trim();
}

function actionWithoutLeadingMentalState(action: string, mentalState: string): string {
  if (!mentalState || !startsWithPhrase(action, mentalState)) return cleanText(action);
  return cleanText(action.slice(mentalState.length));
}

function recipientPhraseText(recipient: unknown): string {
  return cleanText(recipient).replace(/^(?:to|for)\s+/i, '');
}

function stripPrefix(text: unknown, prefixes: string[]): string {
  const value = cleanText(text);
  const lowered = value.toLowerCase();
  for (const prefix of prefixes) {
    if (lowered === prefix) return '';
    if (lowered.startsWith(`${prefix} `)) return value.slice(prefix.length).trim();
  }
  return value;
}

function cleanText(text: unknown): string {
  return textValue(text)
    .replace(/\s+/g, ' ')
    .replace(/^[\s.;:]+|[\s.;:]+$/g, '');
}

function textValue(value: unknown): string {
  return typeof value === 'string' ? value : value == null ? '' : String(value);
}

function textAlreadyContains(container: string, phrase: string): boolean {
  const left = container
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, ' ')
    .trim();
  const right = phrase
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, ' ')
    .trim();
  return Boolean(left && right && left.includes(right));
}

function startsWithPhrase(container: string, phrase: string): boolean {
  return new RegExp(`^${escapeRegExp(cleanText(phrase))}\\b`, 'i').test(cleanText(container));
}

function dedupeSpans(spans: SpanLike[]): SpanLike[] {
  const seen = new Set<string>();
  const deduped: SpanLike[] = [];
  for (const span of spans) {
    const key = `${span[0]}:${span[1]}`;
    if (seen.has(key)) continue;
    seen.add(key);
    deduped.push([span[0], span[1]]);
  }
  return deduped;
}

function phraseKey(slot: string, text: string, spans: SpanLike[]): string {
  return `${slot}\u0000${text}\u0000${spans.map((span) => `${span[0]}:${span[1]}`).join('|')}`;
}

function mappingValue(value: unknown): LegalNormDetailLike | null {
  return value && typeof value === 'object' && !Array.isArray(value)
    ? (value as LegalNormDetailLike)
    : null;
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

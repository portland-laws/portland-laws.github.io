import { buildFormalLogicRecordFromIr, type ExportLegalNormLike } from './exports';

export interface DeonticProverSyntaxValidation {
  valid: boolean;
  normalized_formula: string;
  modality?: 'O' | 'P' | 'F';
  variable?: string;
  antecedents: string[];
  consequent?: string;
  blockers: string[];
}

export interface DeonticProverSyntaxRecord extends DeonticProverSyntaxValidation {
  formula: string;
  target_logic: 'deontic_fol';
  proof_ready: boolean;
  requires_validation: boolean;
  omitted_formula_slots: string[];
  schema_version: string;
  server_calls_allowed: false;
  python_runtime: false;
}

const WRAPPED_FORMULA = /^(O|P|F)\(forall\s+([a-z][A-Za-z0-9_]*)\s+\((.+)\s+->\s+(.+)\)\)$/;
const PREDICATE = /^[A-Z][A-Za-z0-9_]*\([a-z][A-Za-z0-9_]*(?:,\s*[A-Z][A-Za-z0-9_]*)?\)$/;

export function normalizeDeonticProverFormula(formula: string): string {
  return formula
    .replace(/\u2200/g, 'forall ')
    .replace(/\u2192/g, ' -> ')
    .replace(/\u2227/g, ' and ')
    .replace(/\u00ac/g, 'not ')
    .replace(/\s+/g, ' ')
    .replace(/\(\s+/g, '(')
    .replace(/\s+\)/g, ')')
    .trim();
}

export const normalize_deontic_prover_formula = normalizeDeonticProverFormula;

export function validateDeonticProverSyntax(formula: string): DeonticProverSyntaxValidation {
  const normalized = normalizeDeonticProverFormula(formula);
  const blockers: string[] = [];
  if (normalized.length === 0) return fail(normalized, ['missing_formula']);
  if (!balancedParentheses(normalized)) return fail(normalized, ['unbalanced_parentheses']);
  const match = WRAPPED_FORMULA.exec(normalized);
  if (!match) return fail(normalized, ['unsupported_deontic_prover_syntax']);

  const modality = match[1] as 'O' | 'P' | 'F';
  const variable = match[2];
  const antecedents = match[3]
    .split(/\s+and\s+/)
    .map((value) => value.trim())
    .filter(Boolean);
  const consequent = match[4].trim();
  if (antecedents.length === 0) blockers.push('missing_antecedent');
  if (!validAtom(consequent, variable)) blockers.push('invalid_consequent');
  for (const antecedent of antecedents) {
    const atom = antecedent.startsWith('not ') ? antecedent.slice(4).trim() : antecedent;
    if (!validAtom(atom, variable)) blockers.push(`invalid_antecedent:${antecedent}`);
  }

  return {
    valid: blockers.length === 0,
    normalized_formula: normalized,
    modality,
    variable,
    antecedents,
    consequent,
    blockers,
  };
}

export const validate_deontic_prover_syntax = validateDeonticProverSyntax;

export function buildDeonticProverSyntaxRecordFromIr(
  norm: ExportLegalNormLike,
): DeonticProverSyntaxRecord {
  const formal = buildFormalLogicRecordFromIr(norm);
  const formula = String(formal.formula ?? '');
  const syntax = validateDeonticProverSyntax(formula);
  const omitted = list(formal.omitted_formula_slots);
  const blockers = [...new Set([...list(formal.blockers), ...syntax.blockers])];
  const proofReady =
    formal.proof_ready === true && syntax.valid && omitted.length === 0 && blockers.length === 0;
  return {
    ...syntax,
    formula,
    target_logic: 'deontic_fol',
    proof_ready: proofReady,
    requires_validation: !proofReady,
    omitted_formula_slots: omitted,
    blockers,
    schema_version: String(formal.schema_version || 'ts-deontic-prover-syntax-v1'),
    server_calls_allowed: false,
    python_runtime: false,
  };
}

export const build_deontic_prover_syntax_record_from_ir = buildDeonticProverSyntaxRecordFromIr;

function validAtom(value: string, variable: string): boolean {
  if (!PREDICATE.test(value)) return false;
  return (
    value
      .slice(value.indexOf('(') + 1, -1)
      .split(',')[0]
      .trim() === variable
  );
}

function balancedParentheses(value: string): boolean {
  let depth = 0;
  for (const char of value) {
    if (char === '(') depth += 1;
    if (char === ')') depth -= 1;
    if (depth < 0) return false;
  }
  return depth === 0;
}

function fail(formula: string, blockers: string[]): DeonticProverSyntaxValidation {
  return { valid: false, normalized_formula: formula, antecedents: [], blockers };
}

function list(value: unknown): string[] {
  return Array.isArray(value) ? value.map(String).filter(Boolean) : [];
}

import type { FolUtilityParseResult } from '../../fol/parser';
import { parseFolUtilityText } from '../../fol/parser';
import type { InteractiveFolQuestion, InteractiveFolSymbol } from './folConstructorIo';

export interface InteractiveFolUtilsMetadata {
  sourcePythonModule: 'logic/integration/interactive/interactive_fol_utils.py';
  browserNative: true;
  serverCallsAllowed: false;
  pythonRuntime: false;
  runtimeDependencies: Array<string>;
}

export interface InteractiveFolUtilityAnalysis {
  normalizedText: string;
  formula: string;
  questions: Array<InteractiveFolQuestion>;
  symbols: Array<InteractiveFolSymbol>;
  warnings: Array<string>;
  metadata: InteractiveFolUtilsMetadata;
}

export const INTERACTIVE_FOL_UTILS_METADATA: InteractiveFolUtilsMetadata = {
  sourcePythonModule: 'logic/integration/interactive/interactive_fol_utils.py',
  browserNative: true,
  serverCallsAllowed: false,
  pythonRuntime: false,
  runtimeDependencies: [],
};

export function normalizeInteractiveFolInput(input: unknown): string {
  if (typeof input !== 'string') return '';
  return input.replace(/\s+/g, ' ').trim();
}

export function analyzeInteractiveFolInput(
  text: string,
  formula?: string,
  errors: Array<string> = [],
): InteractiveFolUtilityAnalysis {
  const normalizedText = normalizeInteractiveFolInput(text);
  const parsed = parseFolUtilityText(normalizedText, { failOnInvalid: true });
  const resolvedFormula = formula ?? parsed.formula;
  return {
    normalizedText,
    formula: resolvedFormula,
    questions: buildInteractiveFolQuestions(normalizedText, parsed, resolvedFormula, errors),
    symbols: extractInteractiveFolSymbols(resolvedFormula),
    warnings: parsed.warnings,
    metadata: INTERACTIVE_FOL_UTILS_METADATA,
  };
}

export function buildInteractiveFolQuestions(
  text: string,
  parsed: FolUtilityParseResult,
  formula: string,
  errors: Array<string> = [],
): Array<InteractiveFolQuestion> {
  if (!normalizeInteractiveFolInput(text)) {
    return [{ id: 'question-empty-input', reason: 'empty_input' }];
  }
  if (errors.length > 0 || !parsed.validation.valid) {
    return [{ id: 'question-invalid-formula', reason: 'invalid_formula' }];
  }

  const questions: Array<InteractiveFolQuestion> = [];
  if (parsed.quantifiers.length === 0 && !/[∀∃]/.test(formula)) {
    questions.push({ id: 'question-missing-quantifier', reason: 'missing_quantifier' });
  }
  if (parsed.operators.length === 0 && parsed.clauses.length <= 1) {
    questions.push({ id: 'question-missing-relation', reason: 'missing_relation' });
  }
  return questions;
}

export function extractInteractiveFolSymbols(formula: string): Array<InteractiveFolSymbol> {
  const symbols = new Map<string, InteractiveFolSymbol>();
  for (const match of formula.matchAll(/\b([A-Z][A-Za-z0-9_]*)\s*\(/g)) {
    symbols.set(`predicate:${match[1]}`, { name: match[1], kind: 'predicate' });
  }
  for (const match of formula.matchAll(/[∀∃]([a-z][A-Za-z0-9_]*)/g)) {
    symbols.set(`variable:${match[1]}`, { name: match[1], kind: 'variable' });
  }
  for (const match of formula.matchAll(/\(([^()]*)\)/g)) {
    for (const variable of match[1].matchAll(/\b([a-z][A-Za-z0-9_]*)\b/g)) {
      symbols.set(`variable:${variable[1]}`, { name: variable[1], kind: 'variable' });
    }
  }
  return [...symbols.values()];
}

export const interactive_fol_utils_metadata = INTERACTIVE_FOL_UTILS_METADATA;
export const normalize_interactive_fol_input = normalizeInteractiveFolInput;
export const analyze_interactive_fol_input = analyzeInteractiveFolInput;
export const build_interactive_fol_questions = buildInteractiveFolQuestions;
export const extract_interactive_fol_symbols = extractInteractiveFolSymbols;

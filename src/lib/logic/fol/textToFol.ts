import { normalizePredicateName } from '../normalization';
import { createValidationResult } from '../validation';
import { extractBrowserNativeFolNlp, type BrowserNativeFolNlpExtraction } from './browserNativeNlp';
import { parseFolText, validateFolSyntax, type FolTokenMatch } from './parser';

export interface TextToFolClause {
  text: string;
  formula: string;
  quantifiers: FolTokenMatch[];
  operators: FolTokenMatch[];
}

export interface TextToFolResult {
  ok: boolean;
  formula: string;
  clauses: TextToFolClause[];
  nlp: BrowserNativeFolNlpExtraction;
  validation: ReturnType<typeof validateFolSyntax>;
  metadata: {
    sourcePythonModule: 'logic/fol/text_to_fol.py';
    browserNative: true;
    wasmCompatible: true;
    serverCallsAllowed: false;
    pythonRuntime: false;
    dependencyMode: 'deterministic-typescript';
  };
}

const TEXT_TO_FOL_METADATA = {
  sourcePythonModule: 'logic/fol/text_to_fol.py',
  browserNative: true,
  wasmCompatible: true,
  serverCallsAllowed: false,
  pythonRuntime: false,
  dependencyMode: 'deterministic-typescript',
} as const;

export function textToFol(text: string): TextToFolResult {
  const nlp = extractBrowserNativeFolNlp(text);
  const clauseTexts = splitClauses(text);

  if (clauseTexts.length === 0) {
    return {
      ok: false,
      formula: '⊥',
      clauses: [],
      nlp,
      validation: createValidationResult([
        { severity: 'error', message: 'Input text cannot be empty or whitespace only' },
      ]),
      metadata: TEXT_TO_FOL_METADATA,
    };
  }

  const clauses = clauseTexts.map((clauseText) => convertClause(clauseText));
  const formula =
    clauses.length === 1
      ? clauses[0].formula
      : clauses.map((clause) => `(${clause.formula})`).join(' ∧ ');
  const validation = validateFolSyntax(formula);

  return {
    ok: validation.valid,
    formula,
    clauses,
    nlp,
    validation,
    metadata: TEXT_TO_FOL_METADATA,
  };
}

export const text_to_fol = textToFol;

function splitClauses(text: string): string[] {
  return text
    .split(/[.;]+|\b(?:and therefore|therefore)\b/i)
    .map((part) => part.trim())
    .filter(Boolean);
}

function convertClause(text: string): TextToFolClause {
  const formula =
    convertNamedFact(text) ?? convertRuleLikeClause(text) ?? parseFolText(text).formula;
  const parsed = parseFolText(text);
  return {
    text,
    formula,
    quantifiers: parsed.quantifiers,
    operators: parsed.operators,
  };
}

function convertNamedFact(text: string): string | undefined {
  const classification = text.match(
    /^\s*([A-Z][A-Za-z0-9_-]*)\s+(?:is|are)\s+(?:a|an|the)?\s*(\w+)\s*$/,
  );
  if (classification) {
    return `${toPredicateName(classification[2])}(${toConstantName(classification[1])})`;
  }

  const transitive = text.match(/^\s*([A-Z][A-Za-z0-9_-]*)\s+(\w+)\s+(.+?)\s*$/);
  if (transitive && !/^(all|every|each|some|if|there|no)$/i.test(transitive[1])) {
    return `${toPredicateName(`${transitive[2]} ${transitive[3]}`)}(${toConstantName(transitive[1])})`;
  }

  return undefined;
}

function convertRuleLikeClause(text: string): string | undefined {
  const negativeUniversal = text.match(/^\s*no\s+(\w+)\s+(?:are|is|may be|can be)\s+(\w+)\s*$/i);
  if (negativeUniversal) {
    return `∀x (${toPredicateName(negativeUniversal[1])}(x) → ¬${toPredicateName(negativeUniversal[2])}(x))`;
  }

  const actionRule = text.match(
    /^\s*(?:all|every|each)\s+(\w+)\s+(must\s+|shall\s+|should\s+|will\s+)?(\w+)\s+(.+?)\s*$/i,
  );
  if (actionRule && !/^(are|is|be)$/.test(actionRule[3].toLowerCase())) {
    return `∀x (${toPredicateName(actionRule[1])}(x) → ${toPredicateName(
      `${actionRule[3]} ${actionRule[4]}`,
    )}(x))`;
  }

  const existentialAction = text.match(/^\s*some\s+(\w+)\s+(\w+)\s+(.+?)\s*$/i);
  if (existentialAction && !/^(are|is)$/.test(existentialAction[2].toLowerCase())) {
    return `∃x (${toPredicateName(existentialAction[1])}(x) ∧ ${toPredicateName(
      `${existentialAction[2]} ${existentialAction[3]}`,
    )}(x))`;
  }

  return undefined;
}

function toPredicateName(value: string): string {
  return normalizePredicateName(value)
    .split('_')
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join('');
}

function toConstantName(value: string): string {
  return normalizePredicateName(value).replace(/_/g, '');
}

import type { TdfolLlmOperatorHint } from './browserNativeLlm';
import { parseTdfolFormula } from './parser';

export type TdfolNlPatternKind =
  | 'universal_policy'
  | 'existential_policy'
  | 'qualified_universal_policy';
export type TdfolNlPatternResult = {
  formula: string;
  confidence: number;
  patternKind: TdfolNlPatternKind;
  subject: string;
  action: string;
  metadata: {
    browserNative: true;
    serverCallsAllowed: false;
    pythonRuntime: false;
    sourcePythonModule: 'logic/TDFOL/nl/tdfol_nl_patterns.py';
    operatorHints: TdfolLlmOperatorHint[];
  };
};

const MODAL =
  'must not|shall not|must|shall|may|can|is required to|is allowed to|are required to|are allowed to';
const UNIVERSAL = new RegExp(`^(?:all|every|each)\\s+([a-z ]+?)\\s+(${MODAL})\\s+(.+)$`);
const QUALIFIED = new RegExp(
  `^(?:all|every|each)\\s+([a-z ]+?)\\s+who\\s+(.+?)\\s+(${MODAL})\\s+(.+)$`,
);
const EXISTENTIALS = [
  new RegExp(`^(?:some|at least one)\\s+([a-z ]+?)\\s+(${MODAL})\\s+(.+)$`),
  new RegExp(`^there is (?:a|an)\\s+([a-z ]+?)\\s+that\\s+(${MODAL})\\s+(.+)$`),
];

export function matchTdfolNlPattern(
  text: string,
  operatorHints: TdfolLlmOperatorHint[],
): TdfolNlPatternResult | null {
  const normalized = normalize(text);
  const qualified = normalized.match(QUALIFIED);
  if (qualified) {
    const subject = singularize(qualified[1]);
    const action = cleanupAction(qualified[4]);
    return result(
      `forall x. (${predicate(subject)}(x) & ${predicate(cleanupAction(qualified[2]))}(x)) -> ${wrapAction(qualified[3], action, operatorHints)}`,
      0.91,
      'qualified_universal_policy',
      subject,
      action,
      operatorHints,
    );
  }
  const universal = normalized.match(UNIVERSAL);
  if (universal) {
    const subject = singularize(universal[1]);
    const action = cleanupAction(universal[3]);
    return result(
      `forall x. ${predicate(subject)}(x) -> ${wrapAction(universal[2], action, operatorHints)}`,
      operatorHints.includes('universal') ? 0.9 : 0.82,
      'universal_policy',
      subject,
      action,
      operatorHints,
    );
  }
  const existential = firstMatch(normalized, EXISTENTIALS);
  if (!existential) return null;
  const subject = singularize(existential[1]);
  const action = cleanupAction(existential[3]);
  return result(
    `exists x. ${predicate(subject)}(x) & ${wrapAction(existential[2], action, operatorHints)}`,
    operatorHints.includes('existential') ? 0.88 : 0.81,
    'existential_policy',
    subject,
    action,
    operatorHints,
  );
}

function result(
  formula: string,
  confidence: number,
  patternKind: TdfolNlPatternKind,
  subject: string,
  action: string,
  operatorHints: TdfolLlmOperatorHint[],
): TdfolNlPatternResult {
  parseTdfolFormula(formula);
  return {
    formula,
    confidence,
    patternKind,
    subject,
    action,
    metadata: {
      browserNative: true,
      serverCallsAllowed: false,
      pythonRuntime: false,
      sourcePythonModule: 'logic/TDFOL/nl/tdfol_nl_patterns.py',
      operatorHints: [...operatorHints],
    },
  };
}

function firstMatch(text: string, patterns: Array<RegExp>): RegExpMatchArray | null {
  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (match) return match;
  }
  return null;
}

function wrapAction(modal: string, action: string, hints: TdfolLlmOperatorHint[]): string {
  const operator = modal.includes('not') ? 'F' : hints.includes('permission') ? 'P' : 'O';
  const atom = `${operator}(${predicate(action)}(x))`;
  if (hints.includes('temporal_always')) return `[](${atom})`;
  if (hints.includes('temporal_eventually')) return `<>(${atom})`;
  return atom;
}

function normalize(text: string): string {
  return text.toLowerCase().replace(/[.]/g, '').replace(/\s+/g, ' ').trim();
}

function cleanupAction(value: string): string {
  return value
    .replace(/^not\s+/, '')
    .replace(/\b(always|eventually)\b/g, ' ')
    .trim();
}

function singularize(value: string): string {
  return value.trim().replace(/\s+/g, ' ').replace(/ies$/i, 'y').replace(/s$/i, '');
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

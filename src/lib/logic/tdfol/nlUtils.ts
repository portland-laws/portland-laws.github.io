import type { TdfolLlmOperatorHint } from './browserNativeLlm';

export type TdfolNlToken = { text: string; normalized: string; start: number; end: number };

export type TdfolNlUtilsMetadata = {
  browserNative: true;
  serverCallsAllowed: false;
  pythonRuntime: false;
  sourcePythonModule: 'logic/TDFOL/nl/utils.py';
};

export const TDFOL_NL_UTILS_METADATA: TdfolNlUtilsMetadata = {
  browserNative: true,
  serverCallsAllowed: false,
  pythonRuntime: false,
  sourcePythonModule: 'logic/TDFOL/nl/utils.py',
};

const STOP_WORDS = new Set([
  'a',
  'an',
  'and',
  'are',
  'be',
  'from',
  'in',
  'is',
  'of',
  'or',
  'the',
  'to',
  'under',
  'within',
  'without',
]);

const OPERATOR_RULES: Array<{ hints: readonly TdfolLlmOperatorHint[]; pattern: RegExp }> = [
  { hints: ['universal'], pattern: /\b(all|every|each|any)\b/i },
  { hints: ['existential'], pattern: /\b(some|exists|there is|at least one)\b/i },
  { hints: ['forbidden', 'obligation'], pattern: /\b(must not|shall not|prohibited|forbidden)\b/i },
  { hints: ['obligation'], pattern: /\b(must|shall|required|obligated)\b/i },
  { hints: ['permission'], pattern: /\b(may|can|allowed|permitted)\b/i },
  { hints: ['temporal_always'], pattern: /\b(always|forever|perpetually)\b/i },
  { hints: ['temporal_eventually'], pattern: /\b(eventually|someday|at some point)\b/i },
];

export function normalizeTdfolNlText(text: string): string {
  return text
    .replace(/\r\n?/g, '\n')
    .replace(/[“”]/g, '"')
    .replace(/[‘’]/g, "'")
    .replace(/\s+/g, ' ')
    .replace(/\s+([,.;:!?])/g, '$1')
    .trim();
}

export function tokenizeTdfolNl(text: string): TdfolNlToken[] {
  const normalizedText = normalizeTdfolNlText(text);
  const tokens: TdfolNlToken[] = [];
  const pattern = /[A-Za-z0-9]+(?:[.'-][A-Za-z0-9]+)*/g;
  for (const match of normalizedText.matchAll(pattern)) {
    const start = match.index ?? 0;
    const value = match[0];
    tokens.push({
      text: value,
      normalized: value.toLowerCase(),
      start,
      end: start + value.length,
    });
  }
  return tokens;
}

export function splitTdfolNlSentences(text: string): string[] {
  const normalizedText = normalizeTdfolNlText(text);
  if (normalizedText.length === 0) return [];
  const sentences: string[] = [];
  let start = 0;
  for (let index = 0; index < normalizedText.length; index += 1) {
    const char = normalizedText[index];
    if (char === ';' || (/[.!?]/.test(char) && /\s/.test(normalizedText[index + 1] ?? ''))) {
      const sentence = normalizedText.slice(start, index + 1).trim();
      if (sentence.length > 0) sentences.push(sentence);
      start = index + 1;
    }
  }
  const finalSentence = normalizedText.slice(start).trim();
  if (finalSentence.length > 0) sentences.push(finalSentence);
  return sentences;
}

export function singularizeTdfolNlNoun(noun: string): string {
  const value = normalizeTdfolNlText(noun).toLowerCase();
  if (value.endsWith('ies') && value.length > 3) return `${value.slice(0, -3)}y`;
  if (value.endsWith('ses') && value.length > 3) return value.slice(0, -2);
  if (value.endsWith('s') && !value.endsWith('ss') && value.length > 1) return value.slice(0, -1);
  return value;
}

export function toTdfolPredicateName(phrase: string): string {
  const words = tokenizeTdfolNl(phrase)
    .map((token) => token.normalized)
    .filter((word) => !STOP_WORDS.has(word));
  return words.map(capitalize).join('');
}

export function detectTdfolNlOperatorHints(text: string): TdfolLlmOperatorHint[] {
  const hints: TdfolLlmOperatorHint[] = [];
  for (const rule of OPERATOR_RULES) {
    if (rule.pattern.test(text)) {
      for (const hint of rule.hints) {
        if (!hints.includes(hint)) hints.push(hint);
      }
    }
  }
  return hints;
}

export function extractTdfolNlLegalReferences(text: string): string[] {
  const references: string[] = [];
  const pattern = /(?:\bsection\b|\bsec\.|§)\s*([0-9]+(?:\.[0-9A-Za-z-]+)*)\b/gi;
  for (const match of text.matchAll(pattern)) {
    references.push(match[1]);
  }
  return Array.from(new Set(references));
}

function capitalize(value: string): string {
  if (value.length === 0) return value;
  return `${value.charAt(0).toUpperCase()}${value.slice(1)}`;
}

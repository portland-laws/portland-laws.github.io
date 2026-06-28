import type { TdfolLlmOperatorHint } from './browserNativeLlm';

type Reason = 'spacing' | 'list_marker' | 'contraction' | 'modal' | 'legal_reference';
export type TdfolNlPreprocessReplacement = { from: string; to: string; reason: Reason };
export type TdfolNlPreprocessResult = {
  input: string;
  normalizedText: string;
  sentences: string[];
  operatorHints: TdfolLlmOperatorHint[];
  legalReferences: string[];
  replacements: TdfolNlPreprocessReplacement[];
  issues: string[];
  metadata: TdfolNlPreprocessMetadata;
};
type TdfolNlPreprocessMetadata = {
  browserNative: true;
  serverCallsAllowed: false;
  pythonRuntime: false;
  sourcePythonModule: 'logic/TDFOL/nl/tdfol_nl_preprocessor.py';
};

const METADATA: TdfolNlPreprocessMetadata = {
  browserNative: true,
  serverCallsAllowed: false,
  pythonRuntime: false,
  sourcePythonModule: 'logic/TDFOL/nl/tdfol_nl_preprocessor.py',
};
const REPLACEMENTS: Array<[RegExp, string, Reason]> = [
  [/\bcan't\b/gi, 'cannot', 'contraction'],
  [/\bcannot\b/gi, 'must not', 'contraction'],
  [/\bmustn't\b/gi, 'must not', 'contraction'],
  [/\bshan't\b/gi, 'shall not', 'contraction'],
  [/\b(?:is|are|be)\s+required\s+to\b/gi, 'must', 'modal'],
  [/\b(?:is|are|be)\s+obligated\s+to\b/gi, 'must', 'modal'],
  [/\b(?:is|are|be)\s+(?:allowed|permitted)\s+to\b/gi, 'may', 'modal'],
  [/\b(?:is|are|be)\s+prohibited\s+from\b/gi, 'must not', 'modal'],
  [/\b(?:is|are|be)\s+forbidden\s+from\b/gi, 'must not', 'modal'],
];

export function preprocessTdfolNaturalLanguage(text: string): TdfolNlPreprocessResult {
  const replacements: TdfolNlPreprocessReplacement[] = [];
  const legalReferences: string[] = [];
  let normalized = text.replace(/\r\n?/g, '\n').replace(/[“”]/g, '"').replace(/[‘’]/g, "'");
  normalized = normalized
    .split('\n')
    .map((line) => stripListMarker(line, replacements))
    .filter((line) => line.length > 0)
    .join(' ');
  normalized = replaceAndTrack(normalized, /\s+/g, ' ', 'spacing', replacements).trim();
  for (const [pattern, replacement, reason] of REPLACEMENTS) {
    normalized = replaceAndTrack(normalized, pattern, replacement, reason, replacements);
  }
  normalized = normalized.replace(
    /(?:\bsection\b|\bsec\.|§)\s*([0-9]+(?:\.[0-9A-Za-z-]+)*)\b/gi,
    (match, section: string) => {
      legalReferences.push(section);
      replacements.push({ from: match, to: `section ${section}`, reason: 'legal_reference' });
      return `section ${section}`;
    },
  );
  normalized = normalized.replace(/\s+([,.;:!?])/g, '$1').trim();
  return {
    input: text,
    normalizedText: normalized,
    sentences: splitSentences(normalized),
    operatorHints: getOperatorHints(normalized),
    legalReferences: Array.from(new Set(legalReferences)),
    replacements,
    issues: normalized.length === 0 ? ['Input text is empty after preprocessing.'] : [],
    metadata: METADATA,
  };
}

function stripListMarker(line: string, replacements: TdfolNlPreprocessReplacement[]): string {
  const trimmed = line.trim();
  const stripped = trimmed.replace(/^(?:[-*]|\d+[.)])\s+/, '');
  if (stripped !== trimmed)
    replacements.push({ from: trimmed, to: stripped, reason: 'list_marker' });
  return stripped;
}

function replaceAndTrack(
  text: string,
  pattern: RegExp,
  replacement: string,
  reason: Reason,
  replacements: TdfolNlPreprocessReplacement[],
): string {
  return text.replace(pattern, (match) => {
    if (match !== replacement) replacements.push({ from: match, to: replacement, reason });
    return replacement;
  });
}

function splitSentences(text: string): string[] {
  const sentences: string[] = [];
  let start = 0;
  for (let index = 0; index < text.length; index += 1) {
    const char = text[index];
    if (char === ';' || (/[.!?]/.test(char) && /\s/.test(text[index + 1] ?? ''))) {
      const sentence = text.slice(start, index + 1).trim();
      if (sentence.length > 0) sentences.push(sentence);
      start = index + 1;
    }
  }
  const finalSentence = text.slice(start).trim();
  if (finalSentence.length > 0) sentences.push(finalSentence);
  return sentences;
}

function getOperatorHints(text: string): TdfolLlmOperatorHint[] {
  const lower = text.toLowerCase();
  const hintRules: Array<[string[], TdfolLlmOperatorHint]> = [
    [['all', 'every', 'each'], 'universal'],
    [['some', 'exists', 'there is', 'at least one'], 'existential'],
    [['must not', 'shall not', 'prohibited', 'forbidden'], 'forbidden'],
    [['must', 'required', 'shall', 'obligated'], 'obligation'],
    [['may', 'allowed', 'can', 'permitted'], 'permission'],
    [['always', 'perpetually', 'forever'], 'temporal_always'],
    [['eventually', 'someday', 'at some point'], 'temporal_eventually'],
  ];
  return hintRules.flatMap(([needles, hint]) =>
    needles.some((needle) => lower.includes(needle)) ? [hint] : [],
  );
}

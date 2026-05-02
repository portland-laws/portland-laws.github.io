export type BrowserNativeFolNlpProvider = 'deterministic-token-classifier';
export type BrowserNativeFolNlpBackend = 'typescript-token-classifier';
export type BrowserNativeFolCandidateBackend =
  | 'transformers.js-token-classification'
  | 'onnx-webgpu'
  | 'wasm-nlp';
export type BrowserNativeFolTokenKind = 'word' | 'number' | 'symbol';
export type BrowserNativeFolTokenRole =
  | 'quantifier'
  | 'operator'
  | 'negation'
  | 'predicate_candidate'
  | 'literal';

export interface BrowserNativeFolToken {
  text: string;
  normalized: string;
  index: number;
  end: number;
  kind: BrowserNativeFolTokenKind;
  role: BrowserNativeFolTokenRole;
}

export interface BrowserNativeFolNlpExtraction {
  provider: BrowserNativeFolNlpProvider;
  backend: BrowserNativeFolNlpBackend;
  candidateBackends: BrowserNativeFolCandidateBackend[];
  wasmCompatible: true;
  serverCallsAllowed: false;
  pythonSpacy: false;
  fallback: 'none';
  tokens: BrowserNativeFolToken[];
  predicateCandidates: string[];
  metadata: {
    tokenCount: number;
    quantifierCount: number;
    operatorCount: number;
    negationCount: number;
    predicateCandidateCount: number;
  };
}

const UNIVERSAL_WORDS = new Set(['all', 'every', 'each', 'any']);
const EXISTENTIAL_WORDS = new Set(['some', 'someone', 'something', 'exists', 'exist', 'there']);
const OPERATOR_WORDS = new Set(['and', 'or', 'if', 'then', 'implies', 'imply', 'therefore']);
const NEGATION_WORDS = new Set(['not', 'no', 'none', 'never', 'nothing']);
const STOP_WORDS = new Set([
  'a',
  'an',
  'are',
  'be',
  'been',
  'being',
  'for',
  'has',
  'have',
  'is',
  'must',
  'of',
  'shall',
  'should',
  'the',
  'to',
  'was',
  'were',
  'will',
]);
const TOKEN_PATTERN = /[A-Za-z][A-Za-z0-9_'-]*|\d+(?:\.\d+)?|[^\s]/g;

export function extractBrowserNativeFolNlp(text: string): BrowserNativeFolNlpExtraction {
  const tokens = tokenizeBrowserNativeFolText(text);
  const predicateCandidates = unique(
    tokens.filter((token) => token.role === 'predicate_candidate').map((token) => token.normalized),
  );

  return {
    provider: 'deterministic-token-classifier',
    backend: 'typescript-token-classifier',
    candidateBackends: ['transformers.js-token-classification', 'onnx-webgpu', 'wasm-nlp'],
    wasmCompatible: true,
    serverCallsAllowed: false,
    pythonSpacy: false,
    fallback: 'none',
    tokens,
    predicateCandidates,
    metadata: {
      tokenCount: tokens.length,
      quantifierCount: countRole(tokens, 'quantifier'),
      operatorCount: countRole(tokens, 'operator'),
      negationCount: countRole(tokens, 'negation'),
      predicateCandidateCount: predicateCandidates.length,
    },
  };
}

export function tokenizeBrowserNativeFolText(text: string): BrowserNativeFolToken[] {
  const tokens: BrowserNativeFolToken[] = [];
  for (const match of text.matchAll(TOKEN_PATTERN)) {
    const raw = match[0];
    const index = match.index ?? 0;
    tokens.push({
      text: raw,
      normalized: raw.toLowerCase(),
      index,
      end: index + raw.length,
      kind: classifyKind(raw),
      role: classifyRole(raw),
    });
  }
  return tokens;
}

function classifyKind(token: string): BrowserNativeFolTokenKind {
  if (/^\d+(?:\.\d+)?$/.test(token)) return 'number';
  if (/^[A-Za-z]/.test(token)) return 'word';
  return 'symbol';
}

function classifyRole(token: string): BrowserNativeFolTokenRole {
  const normalized = token.toLowerCase();
  if (UNIVERSAL_WORDS.has(normalized) || EXISTENTIAL_WORDS.has(normalized)) return 'quantifier';
  if (OPERATOR_WORDS.has(normalized)) return 'operator';
  if (NEGATION_WORDS.has(normalized)) return 'negation';
  if (/^[A-Za-z]/.test(token) && !STOP_WORDS.has(normalized)) return 'predicate_candidate';
  return 'literal';
}

function countRole(tokens: BrowserNativeFolToken[], role: BrowserNativeFolTokenRole): number {
  return tokens.filter((token) => token.role === role).length;
}

function unique(values: string[]): string[] {
  return [...new Set(values.filter(Boolean))];
}

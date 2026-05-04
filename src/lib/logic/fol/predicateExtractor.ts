import { normalizePredicateName } from '../normalization';

export interface ExtractedPredicates {
  nouns: string[];
  verbs: string[];
  adjectives: string[];
  relations: string[];
}

export interface NlpPredicateToken {
  text: string;
  normalized: string;
  index: number;
  pos: 'noun' | 'verb' | 'adjective' | 'stopword' | 'unknown';
}

export interface NlpPredicateRelation {
  subject: string;
  predicate: string;
  object: string;
  confidence: number;
}

export interface NlpPredicateExtractionResult {
  predicates: ExtractedPredicates;
  logicalRelations: LogicalRelation[];
  syntacticRelations: NlpPredicateRelation[];
  tokens: NlpPredicateToken[];
  adapter: NlpPredicateAdapterMetadata;
}

export interface NlpPredicateAdapterMetadata {
  id: string;
  runtime: 'browser-native';
  pythonModule: 'logic/fol/utils/nlp_predicate_extractor.py';
  dependencies: string[];
  failClosed: boolean;
}

export type LogicalRelationType = 'implication' | 'universal' | 'existential';

export interface LogicalRelation {
  type: LogicalRelationType;
  premise?: string;
  conclusion?: string;
  subject?: string;
  predicate?: string;
}

const NOUN_PATTERN = /\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b/g;
const VERB_PATTERN = /\b(?:is|are|was|were|has|have|can|will|should|must)\s+(\w+)\b/gi;
const ADJECTIVE_PATTERN = /\b(?:is|are|was|were)\s+(\w+)(?:\s|$|\.)/gi;
const IF_THEN_PATTERN = /if\s+(.+?)\s+then\s+(.+?)(?:\.|$)/gi;
const ALL_PATTERN = /all\s+(\w+)\s+(?:are|is|have|has)\s+(.+?)(?:\.|$)/gi;
const SOME_PATTERN = /(?:some|there (?:is|are))\s+(\w+)\s+(?:are|is|have|has)\s+(.+?)(?:\.|$)/gi;
const TOKEN_PATTERN = /[A-Za-z][A-Za-z'-]*/g;
const AUXILIARY_VERBS = new Set([
  'is',
  'are',
  'was',
  'were',
  'be',
  'being',
  'been',
  'has',
  'have',
  'had',
]);
const MODAL_VERBS = new Set([
  'can',
  'could',
  'may',
  'might',
  'must',
  'shall',
  'should',
  'will',
  'would',
]);
const STOPWORDS = new Set([
  'a',
  'an',
  'and',
  'as',
  'at',
  'by',
  'for',
  'from',
  'if',
  'in',
  'of',
  'on',
  'or',
  'the',
  'then',
  'there',
  'to',
]);
const COMMON_ADJECTIVES = new Set([
  'active',
  'available',
  'compliant',
  'eligible',
  'liable',
  'required',
  'responsible',
  'safe',
  'valid',
]);
const COMMON_RELATION_VERBS = new Set([
  'applies',
  'comply',
  'complies',
  'contains',
  'denies',
  'files',
  'grants',
  'issues',
  'permits',
  'requires',
  'responds',
  'submits',
]);

export const BROWSER_NATIVE_NLP_PREDICATE_EXTRACTOR: NlpPredicateAdapterMetadata = {
  id: 'browser-native-deterministic-nlp-predicate-extractor',
  runtime: 'browser-native',
  pythonModule: 'logic/fol/utils/nlp_predicate_extractor.py',
  dependencies: [],
  failClosed: true,
};

export function extractPredicates(text: string): ExtractedPredicates {
  return {
    nouns: unique([...text.matchAll(NOUN_PATTERN)].map((match) => normalizePredicate(match[0]))),
    verbs: unique([...text.matchAll(VERB_PATTERN)].map((match) => normalizePredicate(match[1]))),
    adjectives: unique(
      [...text.matchAll(ADJECTIVE_PATTERN)].map((match) => normalizePredicate(match[1])),
    ),
    relations: [],
  };
}

export function extractNlpPredicates(text: string): NlpPredicateExtractionResult {
  const tokens = tokenizeForNlpPredicates(text);
  return {
    predicates: extractPredicates(text),
    logicalRelations: extractLogicalRelations(text),
    syntacticRelations: extractSyntacticRelations(tokens),
    tokens,
    adapter: BROWSER_NATIVE_NLP_PREDICATE_EXTRACTOR,
  };
}

export function normalizePredicate(predicate: string): string {
  const normalized = predicate
    .trim()
    .split(/\s+/)
    .filter((word) => !['the', 'a', 'an', 'of', 'in', 'on', 'at'].includes(word.toLowerCase()))
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join('');
  return normalized || 'UnknownPredicate';
}

export function extractLogicalRelations(text: string): LogicalRelation[] {
  const relations: LogicalRelation[] = [];
  for (const match of text.matchAll(IF_THEN_PATTERN)) {
    relations.push({
      type: 'implication',
      premise: match[1].trim().toLowerCase(),
      conclusion: match[2].trim().toLowerCase(),
    });
  }
  for (const match of text.matchAll(ALL_PATTERN)) {
    relations.push({
      type: 'universal',
      subject: match[1].trim().toLowerCase(),
      predicate: match[2].trim().toLowerCase(),
    });
  }
  for (const match of text.matchAll(SOME_PATTERN)) {
    relations.push({
      type: 'existential',
      subject: match[1].trim().toLowerCase(),
      predicate: match[2].trim().toLowerCase(),
    });
  }
  return relations;
}

export function extractVariables(predicates: ExtractedPredicates): string[] {
  const standardVariables = ['x', 'y', 'z', 'u', 'v', 'w'];
  const uniqueCount = new Set([...predicates.nouns, ...predicates.verbs, ...predicates.adjectives])
    .size;
  return standardVariables.slice(0, Math.max(1, uniqueCount));
}

export function buildFolFormulaFromParts(
  quantifiers: unknown[],
  predicates: ExtractedPredicates,
  operators: unknown[],
  relations: LogicalRelation[],
): string {
  void quantifiers;
  void operators;

  if (relations.length === 0) {
    if (predicates.nouns.length > 0 && predicates.adjectives.length > 0) {
      return `∀x (${predicates.nouns[0]}(x) → ${predicates.adjectives[0]}(x))`;
    }
    if (predicates.nouns.length > 0) {
      return `∃x ${predicates.nouns[0]}(x)`;
    }
    return '⊤';
  }

  const formulas = relations
    .map((relation) => {
      if (relation.type === 'universal' && relation.subject && relation.predicate) {
        return `∀x (${toFolPredicateName(relation.subject)}(x) → ${toFolPredicateName(relation.predicate)}(x))`;
      }
      if (relation.type === 'existential' && relation.subject && relation.predicate) {
        return `∃x (${toFolPredicateName(relation.subject)}(x) ∧ ${toFolPredicateName(relation.predicate)}(x))`;
      }
      if (relation.type === 'implication' && relation.premise && relation.conclusion) {
        return `∀x (${parseSimpleRelationPredicate(relation.premise)} → ${parseSimpleRelationPredicate(relation.conclusion)})`;
      }
      return '';
    })
    .filter(Boolean);

  if (formulas.length === 1) {
    return formulas[0];
  }
  if (formulas.length > 1) {
    return formulas.map((formula) => `(${formula})`).join(' ∧ ');
  }
  return '⊤';
}

export function parseSimpleRelationPredicate(text: string): string {
  const words = text.trim().split(/\s+/).filter(Boolean);
  const predicate = words.length === 1 ? words[0] : words[words.length - 1] || 'P';
  return `${toFolPredicateName(predicate)}(x)`;
}

export function toFolPredicateName(value: string): string {
  return (
    normalizePredicateName(value)
      .split('_')
      .filter(Boolean)
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join('') || 'P'
  );
}

function unique(values: string[]): string[] {
  return [...new Set(values.filter(Boolean))];
}

function tokenizeForNlpPredicates(text: string): NlpPredicateToken[] {
  return [...text.matchAll(TOKEN_PATTERN)].map((match, index) => {
    const raw = match[0];
    const lower = raw.toLowerCase();
    const normalized = normalizePredicate(raw);
    return {
      text: raw,
      normalized,
      index,
      pos: classifyToken(raw, lower),
    };
  });
}

function classifyToken(raw: string, lower: string): NlpPredicateToken['pos'] {
  if (STOPWORDS.has(lower) || AUXILIARY_VERBS.has(lower) || MODAL_VERBS.has(lower)) {
    return 'stopword';
  }
  if (COMMON_ADJECTIVES.has(lower)) {
    return 'adjective';
  }
  if (/^[A-Z]/.test(raw)) {
    return 'noun';
  }
  if (COMMON_RELATION_VERBS.has(lower) || /(?:ed|ing|ify|ise|ize|ply|mit|spond)$/.test(lower)) {
    return 'verb';
  }
  return 'noun';
}

function extractSyntacticRelations(tokens: NlpPredicateToken[]): NlpPredicateRelation[] {
  const relations: NlpPredicateRelation[] = [];
  for (let index = 0; index < tokens.length; index += 1) {
    const token = tokens[index];
    if (token.pos !== 'verb') {
      continue;
    }
    const subject = findNearestEntity(tokens, index, -1);
    const object = findNearestEntity(tokens, index, 1);
    if (!subject || !object) {
      continue;
    }
    relations.push({
      subject: subject.normalized,
      predicate: token.normalized,
      object: object.normalized,
      confidence: 0.62,
    });
  }
  return relations;
}

function findNearestEntity(
  tokens: NlpPredicateToken[],
  start: number,
  step: -1 | 1,
): NlpPredicateToken | undefined {
  let index = start + step;
  while (index >= 0 && index < tokens.length) {
    const token = tokens[index];
    if (token.pos === 'noun' || token.pos === 'adjective') {
      return token;
    }
    if (token.text === '.' || token.text === ';') {
      return undefined;
    }
    index += step;
  }
  return undefined;
}

import { normalizePredicateName } from '../normalization';

export interface ExtractedPredicates {
  nouns: string[];
  verbs: string[];
  adjectives: string[];
  relations: string[];
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

export function extractPredicates(text: string): ExtractedPredicates {
  return {
    nouns: unique([...text.matchAll(NOUN_PATTERN)].map((match) => normalizePredicate(match[0]))),
    verbs: unique([...text.matchAll(VERB_PATTERN)].map((match) => normalizePredicate(match[1]))),
    adjectives: unique([...text.matchAll(ADJECTIVE_PATTERN)].map((match) => normalizePredicate(match[1]))),
    relations: [],
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
    relations.push({ type: 'implication', premise: match[1].trim().toLowerCase(), conclusion: match[2].trim().toLowerCase() });
  }
  for (const match of text.matchAll(ALL_PATTERN)) {
    relations.push({ type: 'universal', subject: match[1].trim().toLowerCase(), predicate: match[2].trim().toLowerCase() });
  }
  for (const match of text.matchAll(SOME_PATTERN)) {
    relations.push({ type: 'existential', subject: match[1].trim().toLowerCase(), predicate: match[2].trim().toLowerCase() });
  }
  return relations;
}

export function extractVariables(predicates: ExtractedPredicates): string[] {
  const standardVariables = ['x', 'y', 'z', 'u', 'v', 'w'];
  const uniqueCount = new Set([...predicates.nouns, ...predicates.verbs, ...predicates.adjectives]).size;
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
  return normalizePredicateName(value)
    .split('_')
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join('') || 'P';
}

function unique(values: string[]): string[] {
  return [...new Set(values.filter(Boolean))];
}

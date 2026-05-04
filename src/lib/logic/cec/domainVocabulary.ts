export type DomainVocabularyCategory =
  | 'agent'
  | 'action'
  | 'fluent'
  | 'deontic'
  | 'cognitive'
  | 'temporal'
  | 'connective';

export interface DomainVocabularyTerm {
  readonly canonical: string;
  readonly category: DomainVocabularyCategory;
  readonly synonyms?: readonly string[];
  readonly predicate?: string;
}

export interface DomainVocabularyCapabilities {
  readonly browserNative: true;
  readonly pythonRuntime: false;
  readonly serverRuntime: false;
  readonly filesystem: false;
  readonly subprocess: false;
  readonly rpc: false;
  readonly wasmCompatible: true;
  readonly implementation: 'deterministic-typescript';
  readonly pythonModule: 'logic/CEC/nl/domain_vocabularies/domain_vocab.py';
}

export interface CompiledDomainVocabulary {
  readonly capabilities: DomainVocabularyCapabilities;
  readonly terms: readonly DomainVocabularyTerm[];
  readonly agents: readonly string[];
  readonly actions: readonly string[];
  readonly fluents: readonly string[];
  readonly predicatesByPhrase: ReadonlyMap<string, string>;
}

const DOMAIN_VOCABULARY_CAPABILITIES: DomainVocabularyCapabilities = {
  browserNative: true,
  pythonRuntime: false,
  serverRuntime: false,
  filesystem: false,
  subprocess: false,
  rpc: false,
  wasmCompatible: true,
  implementation: 'deterministic-typescript',
  pythonModule: 'logic/CEC/nl/domain_vocabularies/domain_vocab.py',
};

const DEFAULT_DOMAIN_TERMS: readonly DomainVocabularyTerm[] = [
  { canonical: 'tenant', category: 'agent', synonyms: ['renter', 'lessee'] },
  { canonical: 'landlord', category: 'agent', synonyms: ['lessor', 'owner'] },
  { canonical: 'system', category: 'agent', synonyms: ['service', 'platform'] },
  { canonical: 'pay', category: 'action', synonyms: ['pays', 'payment'] },
  {
    canonical: 'pay rent',
    category: 'action',
    synonyms: ['pay rental amount'],
    predicate: 'pay_rent',
  },
  { canonical: 'enter', category: 'action', synonyms: ['access', 'inspect'] },
  { canonical: 'give notice', category: 'action', synonyms: ['notify'], predicate: 'give_notice' },
  { canonical: 'evict', category: 'action', synonyms: ['remove'] },
  { canonical: 'habitable', category: 'fluent', synonyms: ['livable'] },
  { canonical: 'overdue', category: 'fluent', synonyms: ['late'] },
];

export function getDomainVocabularyCapabilities(): DomainVocabularyCapabilities {
  return DOMAIN_VOCABULARY_CAPABILITIES;
}

export function createDomainVocabulary(
  extraTerms: readonly DomainVocabularyTerm[] = [],
): CompiledDomainVocabulary {
  const terms = mergeTerms([...DEFAULT_DOMAIN_TERMS, ...extraTerms]);
  const predicatesByPhrase = new Map<string, string>();
  const byCategory = new Map<DomainVocabularyCategory, Set<string>>();

  for (const term of terms) {
    const phrases = [term.canonical, ...(term.synonyms ?? [])].map(normalizeDomainVocabularyText);
    for (const phrase of phrases) {
      if (phrase.length === 0) continue;
      predicatesByPhrase.set(phrase, term.predicate ?? toPredicateName(term.canonical));
      addCategoryMember(byCategory, term.category, phrase);
      addCategoryMember(byCategory, term.category, term.canonical);
    }
  }

  return {
    capabilities: DOMAIN_VOCABULARY_CAPABILITIES,
    terms,
    agents: sortedMembers(byCategory, 'agent'),
    actions: sortedMembers(byCategory, 'action'),
    fluents: sortedMembers(byCategory, 'fluent'),
    predicatesByPhrase,
  };
}

export function lookupDomainVocabularyTerm(
  phrase: string,
  vocabulary: CompiledDomainVocabulary = createDomainVocabulary(),
): DomainVocabularyTerm | undefined {
  const normalized = normalizeDomainVocabularyText(phrase);
  return vocabulary.terms.find(
    (term) =>
      normalizeDomainVocabularyText(term.canonical) === normalized ||
      (term.synonyms ?? []).some(
        (synonym) => normalizeDomainVocabularyText(synonym) === normalized,
      ),
  );
}

export function normalizeDomainPredicate(
  phrase: string,
  vocabulary: CompiledDomainVocabulary = createDomainVocabulary(),
): string {
  const normalized = normalizeDomainVocabularyText(phrase);
  return vocabulary.predicatesByPhrase.get(normalized) ?? toPredicateName(normalized);
}

export function normalizeDomainVocabularyText(text: string): string {
  return text.trim().toLowerCase().replace(/[_-]+/g, ' ').replace(/\s+/g, ' ');
}

function mergeTerms(terms: readonly DomainVocabularyTerm[]): readonly DomainVocabularyTerm[] {
  const merged = new Map<string, DomainVocabularyTerm>();
  for (const term of terms) {
    const key = `${term.category}:${normalizeDomainVocabularyText(term.canonical)}`;
    merged.set(key, { ...term, canonical: normalizeDomainVocabularyText(term.canonical) });
  }
  return [...merged.values()];
}

function addCategoryMember(
  byCategory: Map<DomainVocabularyCategory, Set<string>>,
  category: DomainVocabularyCategory,
  phrase: string,
): void {
  const members = byCategory.get(category) ?? new Set<string>();
  members.add(normalizeDomainVocabularyText(phrase));
  byCategory.set(category, members);
}

function sortedMembers(
  byCategory: ReadonlyMap<DomainVocabularyCategory, Set<string>>,
  category: DomainVocabularyCategory,
): readonly string[] {
  return [...(byCategory.get(category) ?? new Set<string>())].sort();
}

function toPredicateName(phrase: string): string {
  return normalizeDomainVocabularyText(phrase).replace(/\s+/g, '_');
}

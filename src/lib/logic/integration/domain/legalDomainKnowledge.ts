export type LegalDomainId =
  | 'contract'
  | 'property'
  | 'tort'
  | 'criminal'
  | 'constitutional'
  | 'administrative'
  | 'evidence';

export interface LegalDomainRule {
  readonly domain: LegalDomainId;
  readonly label: string;
  readonly keywords: readonly string[];
  readonly concepts: readonly string[];
}

export interface LegalDomainKnowledgeMatch {
  readonly domain: LegalDomainId;
  readonly label: string;
  readonly score: number;
  readonly matchedKeywords: readonly string[];
  readonly concepts: readonly string[];
}

export interface LegalDomainKnowledgeResult {
  readonly accepted: boolean;
  readonly runtime: 'browser-native';
  readonly wasmCompatible: true;
  readonly serverCallsAllowed: false;
  readonly pythonRuntimeAllowed: false;
  readonly sourceText: string;
  readonly matches: readonly LegalDomainKnowledgeMatch[];
  readonly primaryDomain?: LegalDomainId;
  readonly errors: readonly string[];
  readonly metadata: typeof LEGAL_DOMAIN_KNOWLEDGE_METADATA;
}

export const LEGAL_DOMAIN_KNOWLEDGE_METADATA = {
  sourcePythonModule: 'logic/integration/domain/legal_domain_knowledge.py',
  browserNative: true,
  wasmCompatible: true,
  serverCallsAllowed: false,
  pythonRuntimeAllowed: false,
  runtimeDependencies: [],
  parity: [
    'deterministic_domain_taxonomy',
    'keyword_concept_matching',
    'local_fail_closed_validation',
  ],
} as const;

export const DEFAULT_LEGAL_DOMAIN_RULES: readonly LegalDomainRule[] = [
  {
    domain: 'contract',
    label: 'Contract law',
    keywords: ['agreement', 'contract', 'offer', 'acceptance', 'consideration', 'breach'],
    concepts: ['formation', 'performance', 'remedies'],
  },
  {
    domain: 'property',
    label: 'Property law',
    keywords: ['tenant', 'landlord', 'lease', 'easement', 'parcel', 'zoning', 'title'],
    concepts: ['possession', 'land use', 'ownership'],
  },
  {
    domain: 'tort',
    label: 'Tort law',
    keywords: ['negligence', 'duty', 'breach', 'causation', 'damages', 'injury'],
    concepts: ['duty of care', 'liability', 'compensation'],
  },
  {
    domain: 'criminal',
    label: 'Criminal law',
    keywords: ['crime', 'defendant', 'mens rea', 'actus reus', 'sentence', 'probation'],
    concepts: ['offense elements', 'culpability', 'punishment'],
  },
  {
    domain: 'constitutional',
    label: 'Constitutional law',
    keywords: ['constitution', 'speech', 'due process', 'equal protection', 'search', 'seizure'],
    concepts: ['rights', 'state action', 'judicial review'],
  },
  {
    domain: 'administrative',
    label: 'Administrative law',
    keywords: ['agency', 'rulemaking', 'permit', 'license', 'hearing', 'regulation'],
    concepts: ['delegated authority', 'procedure', 'review'],
  },
  {
    domain: 'evidence',
    label: 'Evidence law',
    keywords: ['hearsay', 'testimony', 'witness', 'admissible', 'privilege', 'relevance'],
    concepts: ['admissibility', 'proof', 'exclusion'],
  },
];

export class BrowserNativeLegalDomainKnowledge {
  readonly metadata = LEGAL_DOMAIN_KNOWLEDGE_METADATA;
  private readonly rules: readonly LegalDomainRule[];

  constructor(rules: readonly LegalDomainRule[] = DEFAULT_LEGAL_DOMAIN_RULES) {
    this.rules = rules;
  }

  classify(text: string): LegalDomainKnowledgeResult {
    const sourceText = typeof text === 'string' ? text : '';
    const normalized = normalize(sourceText);
    if (normalized.length < 3) return closed(sourceText, ['source text is required']);
    const matches = this.rules
      .map((rule: LegalDomainRule) => scoreRule(rule, normalized))
      .filter((match: LegalDomainKnowledgeMatch) => match.matchedKeywords.length > 0)
      .sort(
        (left: LegalDomainKnowledgeMatch, right: LegalDomainKnowledgeMatch) =>
          right.score - left.score || left.label.localeCompare(right.label),
      );
    return {
      accepted: matches.length > 0,
      runtime: 'browser-native',
      wasmCompatible: true,
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
      sourceText,
      matches,
      primaryDomain: matches[0]?.domain,
      errors: matches.length > 0 ? [] : ['no legal domain knowledge matched locally'],
      metadata: this.metadata,
    };
  }
}

export function classifyLegalDomainKnowledge(text: string): LegalDomainKnowledgeResult {
  return new BrowserNativeLegalDomainKnowledge().classify(text);
}

export const create_legal_domain_knowledge = (): BrowserNativeLegalDomainKnowledge =>
  new BrowserNativeLegalDomainKnowledge();
export const classify_legal_domain_knowledge = classifyLegalDomainKnowledge;

function scoreRule(rule: LegalDomainRule, normalized: string): LegalDomainKnowledgeMatch {
  const matchedKeywords = rule.keywords.filter((keyword: string) =>
    includesKeyword(normalized, keyword),
  );
  return {
    domain: rule.domain,
    label: rule.label,
    score: Number((matchedKeywords.length / rule.keywords.length).toFixed(4)),
    matchedKeywords,
    concepts: rule.concepts,
  };
}

function closed(sourceText: string, errors: readonly string[]): LegalDomainKnowledgeResult {
  return {
    accepted: false,
    runtime: 'browser-native',
    wasmCompatible: true,
    serverCallsAllowed: false,
    pythonRuntimeAllowed: false,
    sourceText,
    matches: [],
    errors,
    metadata: LEGAL_DOMAIN_KNOWLEDGE_METADATA,
  };
}

function normalize(text: string): string {
  return text.toLowerCase().replace(/\s+/g, ' ').trim();
}

function includesKeyword(normalized: string, keyword: string): boolean {
  const value = normalize(keyword);
  if (value.includes(' ')) return normalized.includes(value);
  return new RegExp(`\\b${escapeRegExp(value)}\\b`).test(normalized);
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

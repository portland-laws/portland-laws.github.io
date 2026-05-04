export interface CaselawBulkDocument {
  readonly id: string;
  readonly text: string;
  readonly title?: string;
  readonly jurisdiction?: string;
}

export interface CaselawProcessedDocument {
  readonly id: string;
  readonly accepted: boolean;
  readonly caseName?: string;
  readonly citations: readonly string[];
  readonly year?: number;
  readonly jurisdiction?: string;
  readonly concepts: readonly string[];
  readonly issues: readonly string[];
}

const CITATION_PATTERN =
  /\b\d{1,4}\s+(?:U\.S\.|S\. Ct\.|F\.\d+d|F\. Supp\. \d+d|P\.\d+d|Or\.|Or\. App\.)\s+\d{1,5}\b/g;
const YEAR_PATTERN = /\((?:[^)]*?\s)?(\d{4})\)/;
const CASE_NAME_PATTERN =
  /\b([A-Z][\w.'&-]*(?:\s+[A-Z][\w.'&-]*){0,4})\s+v\.\s+([A-Z][\w.'&-]*(?:\s+[A-Z][\w.'&-]*){0,4})\b/;

const CONCEPT_PATTERNS: readonly [string, RegExp][] = [
  ['holding', /\b(held|holding|conclude|concluded)\b/i],
  ['reversal', /\b(reverse|reversed|remand|remanded)\b/i],
  ['duty', /\b(must|shall|required|duty)\b/i],
  ['permission', /\b(may|permitted|authorized)\b/i],
  ['prohibition', /\b(prohibit|prohibited|forbidden|may not)\b/i],
];

export function processCaselawBulk(documents: readonly CaselawBulkDocument[]) {
  const processed = documents.map((document) => processCaselawDocument(document));
  const rejected = processed.filter((document) => !document.accepted);
  const citations = processed.reduce((total, document) => total + document.citations.length, 0);

  return {
    accepted: rejected.length === 0,
    runtime: 'browser-native',
    wasmCompatible: true,
    serverCallsAllowed: false,
    pythonServiceAllowed: false,
    documents: processed,
    rejected,
    summary: {
      total: processed.length,
      accepted: processed.length - rejected.length,
      rejected: rejected.length,
      citations,
    },
  };
}

export function processCaselawDocument(document: CaselawBulkDocument): CaselawProcessedDocument {
  const issues = validateCaselawDocument(document);
  const text = document.text.trim();
  const citations = uniqueMatches(text, CITATION_PATTERN);
  const year = extractYear(text);
  const caseName = extractCaseName(document.title ?? text);
  const concepts = CONCEPT_PATTERNS.filter(([, pattern]) => pattern.test(text)).map(
    ([concept]) => concept,
  );

  if (citations.length === 0) issues.push('citation not found');
  if (!caseName) issues.push('case name not found');

  return {
    id: document.id,
    accepted: issues.length === 0,
    caseName,
    citations,
    year,
    jurisdiction: document.jurisdiction ?? inferJurisdiction(citations),
    concepts,
    issues,
  };
}

function validateCaselawDocument(document: CaselawBulkDocument): string[] {
  const issues: string[] = [];
  if (document.id.trim().length === 0) issues.push('id is required');
  if (document.text.trim().length === 0) issues.push('text is required');
  return issues;
}

function uniqueMatches(text: string, pattern: RegExp): readonly string[] {
  return [...new Set([...text.matchAll(pattern)].map((match) => match[0]))];
}

function extractYear(text: string): number | undefined {
  const match = YEAR_PATTERN.exec(text);
  return match ? Number(match[1]) : undefined;
}

function extractCaseName(text: string): string | undefined {
  const caption = text.split(',')[0].trim();
  if (caption.includes(' v. ')) return caption;
  const match = CASE_NAME_PATTERN.exec(text);
  return match ? `${match[1]} v. ${match[2]}` : undefined;
}

function inferJurisdiction(citations: readonly string[]): string | undefined {
  if (citations.some((citation) => citation.includes('U.S.') || citation.includes('S. Ct.'))) {
    return 'US';
  }
  if (citations.some((citation) => citation.includes('Or.'))) {
    return 'OR';
  }
  return undefined;
}

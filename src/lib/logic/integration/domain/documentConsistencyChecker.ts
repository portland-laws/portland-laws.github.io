export type ConsistencyIssueCode =
  | 'document_required'
  | 'text_required'
  | 'required_field_missing'
  | 'field_evidence_missing'
  | 'citation_missing'
  | 'citation_not_in_text'
  | 'contradictory_terms';

export interface ConsistencyField {
  readonly name: string;
  readonly value: string;
  readonly evidence?: string;
  readonly required?: boolean;
}

export interface ConsistencyDocument {
  readonly id: string;
  readonly text: string;
  readonly title?: string;
  readonly extractedFields?: readonly ConsistencyField[];
  readonly citations?: readonly string[];
}

export interface DocumentConsistencyIssue {
  readonly code: ConsistencyIssueCode;
  readonly severity: 'error' | 'warning';
  readonly message: string;
  readonly field?: string;
  readonly citation?: string;
}

export interface DocumentConsistencyResult {
  readonly accepted: boolean;
  readonly runtime: 'browser-native';
  readonly wasmCompatible: true;
  readonly serverCallsAllowed: false;
  readonly pythonRuntimeAllowed: false;
  readonly documentId: string;
  readonly issues: readonly DocumentConsistencyIssue[];
  readonly summary: {
    readonly checkedFields: number;
    readonly matchedFields: number;
    readonly checkedCitations: number;
    readonly matchedCitations: number;
  };
  readonly metadata: typeof DOCUMENT_CONSISTENCY_CHECKER_METADATA;
}

export const DOCUMENT_CONSISTENCY_CHECKER_METADATA = {
  sourcePythonModule: 'logic/integration/domain/document_consistency_checker.py',
  browserNative: true,
  wasmCompatible: true,
  serverCallsAllowed: false,
  pythonRuntimeAllowed: false,
  runtimeDependencies: [],
  parity: [
    'deterministic_field_evidence_checks',
    'citation_presence_checks',
    'local_contradiction_detection',
    'fail_closed_validation',
  ],
} as const;

const CONTRADICTIONS: readonly [RegExp, RegExp, string][] = [
  [
    /\bshall\b|\bmust\b|\brequired\b/i,
    /\bshall not\b|\bmust not\b|\bprohibited\b/i,
    'mandatory and prohibited terms both appear',
  ],
  [
    /\bapproved\b|\bgranted\b|\ballowed\b/i,
    /\bdenied\b|\brejected\b|\bnot approved\b/i,
    'approval and denial terms both appear',
  ],
  [
    /\bpermit required\b|\blicense required\b/i,
    /\bno permit required\b|\bexempt\b/i,
    'requirement and exemption terms both appear',
  ],
];

export class BrowserNativeDocumentConsistencyChecker {
  readonly metadata = DOCUMENT_CONSISTENCY_CHECKER_METADATA;

  check(document: ConsistencyDocument): DocumentConsistencyResult {
    const issues = validate(document);
    const text = norm(document.text ?? '');
    const fields = document.extractedFields ?? [];
    const citations = document.citations ?? [];
    let matchedFields = 0;
    let matchedCitations = 0;

    for (const field of fields) {
      const value = field.value.trim();
      const supported =
        value.length > 0 &&
        (text.includes(norm(value)) ||
          text.includes(norm(`${value} ${field.evidence ?? ''}`.trim())));
      if (field.required === true && value.length === 0)
        issues.push(
          issue(
            'required_field_missing',
            'error',
            `required field ${field.name} is empty`,
            field.name,
          ),
        );
      else if (supported) matchedFields += 1;
      else if (field.required === true)
        issues.push(
          issue(
            'field_evidence_missing',
            'error',
            `required field ${field.name} is not supported by document text`,
            field.name,
          ),
        );
      else if (value.length > 0)
        issues.push(
          issue(
            'field_evidence_missing',
            'warning',
            `field ${field.name} is not supported by document text`,
            field.name,
          ),
        );
    }

    if (citations.length === 0)
      issues.push(
        issue('citation_missing', 'warning', 'no citations supplied for consistency check'),
      );
    for (const citation of citations) {
      if (text.includes(normCitation(citation))) matchedCitations += 1;
      else
        issues.push({
          ...issue(
            'citation_not_in_text',
            'error',
            `citation ${citation} is not present in document text`,
          ),
          citation,
        });
    }
    for (const [left, right, message] of CONTRADICTIONS) {
      if (left.test(document.text) && right.test(document.text))
        issues.push(issue('contradictory_terms', 'error', message));
    }

    return {
      accepted: issues.every((candidate) => candidate.severity !== 'error'),
      runtime: 'browser-native',
      wasmCompatible: true,
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
      documentId: document.id,
      issues,
      summary: {
        checkedFields: fields.length,
        matchedFields,
        checkedCitations: citations.length,
        matchedCitations,
      },
      metadata: this.metadata,
    };
  }
}

export function checkDocumentConsistency(document: ConsistencyDocument): DocumentConsistencyResult {
  return new BrowserNativeDocumentConsistencyChecker().check(document);
}

export const create_document_consistency_checker = (): BrowserNativeDocumentConsistencyChecker =>
  new BrowserNativeDocumentConsistencyChecker();
export const check_document_consistency = checkDocumentConsistency;

function validate(document: ConsistencyDocument): DocumentConsistencyIssue[] {
  const issues: DocumentConsistencyIssue[] = [];
  if (!document || document.id.trim().length === 0)
    issues.push(issue('document_required', 'error', 'document id is required'));
  if (!document || document.text.trim().length === 0)
    issues.push(issue('text_required', 'error', 'document text is required'));
  return issues;
}

function issue(
  code: ConsistencyIssueCode,
  severity: DocumentConsistencyIssue['severity'],
  message: string,
  field?: string,
): DocumentConsistencyIssue {
  return { code, severity, message, field };
}

function norm(text: string): string {
  return text.toLowerCase().replace(/\s+/g, ' ').trim();
}

function normCitation(citation: string): string {
  return norm(citation.replace(/\bPCC\b/i, 'Portland City Code'));
}

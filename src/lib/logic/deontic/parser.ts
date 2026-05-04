import { normalizePredicateName } from '../normalization';
import { getLogicRuntimeCapabilities } from '../runtimeCapabilities';
import { predictMLConfidence } from '../mlConfidence';
import { buildDeonticFormula } from './formulaBuilder';

export {
  buildDeonticAtomicPredicate,
  buildDeonticFormula,
  buildDeonticFormulaParts,
  formatTemporalPredicate,
} from './formulaBuilder';

export type DeonticOperator = 'O' | 'P' | 'F';
export type DeonticNormType = 'obligation' | 'permission' | 'prohibition';

export interface TemporalConstraint {
  type: 'deadline' | 'period' | 'duration';
  value: string;
}

export interface NormativeElement {
  text: string;
  normType: DeonticNormType;
  deonticOperator: DeonticOperator;
  matchedIndicator: string;
  subjects: string[];
  actions: string[];
  conditions: string[];
  exceptions: string[];
  temporalConstraints: TemporalConstraint[];
  confidence: number;
}

export interface DeonticConversionResult {
  success: boolean;
  elements: NormativeElement[];
  formulas: string[];
  confidence: number;
  warnings: string[];
  capabilities: {
    mlUnavailable: boolean;
    serverCallsAllowed: false;
  };
}

const INDICATORS: Array<{
  normType: DeonticNormType;
  deonticOperator: DeonticOperator;
  phrases: string[];
}> = [
  {
    normType: 'prohibition',
    deonticOperator: 'F',
    phrases: ['must not', 'shall not', 'may not', 'forbidden to', 'prohibited from', 'cannot'],
  },
  {
    normType: 'obligation',
    deonticOperator: 'O',
    phrases: ['must', 'shall', 'required to', 'obligated to', 'duty to'],
  },
  {
    normType: 'permission',
    deonticOperator: 'P',
    phrases: ['may', 'can', 'allowed to', 'permitted to', 'entitled to', 'has the right to'],
  },
];

export function extractNormativeElements(text: string): NormativeElement[] {
  return text
    .split(/[.!?]+/)
    .map((sentence) => sentence.trim())
    .filter(Boolean)
    .map(analyzeNormativeSentence)
    .filter((element): element is NormativeElement => Boolean(element));
}

export function convertLegalTextToDeontic(text: string): DeonticConversionResult {
  const elements = extractNormativeElements(text);
  const formulas = elements.map((element) => buildDeonticFormula(element));
  const confidence =
    elements.length > 0
      ? elements.reduce((total, element) => total + element.confidence, 0) / elements.length
      : 0;

  return {
    success: elements.length > 0,
    elements,
    formulas,
    confidence,
    warnings: [
      ...(elements.length > 0 ? [] : ['No normative indicators were detected']),
      ...(getLogicRuntimeCapabilities().deontic.mlUnavailable
        ? ['Browser-native ML confidence is not yet available.']
        : []),
    ],
    capabilities: {
      mlUnavailable: getLogicRuntimeCapabilities().deontic.mlUnavailable,
      serverCallsAllowed: false,
    },
  };
}

export function analyzeNormativeSentence(sentence: string): NormativeElement | null {
  const lower = sentence.toLowerCase();
  for (const indicator of INDICATORS) {
    const phrase = indicator.phrases.find((candidate) => lower.includes(candidate));
    if (!phrase) {
      continue;
    }

    const subjects = extractLegalSubjects(sentence);
    const actions = extractLegalActions(sentence);
    const conditions = extractConditions(sentence);
    const exceptions = extractExceptions(sentence);
    const temporalConstraints = extractTemporalConstraints(sentence);

    return {
      text: sentence,
      normType: indicator.normType,
      deonticOperator: indicator.deonticOperator,
      matchedIndicator: phrase,
      subjects,
      actions,
      conditions,
      exceptions,
      temporalConstraints,
      confidence: scoreConfidence(
        sentence,
        subjects,
        actions,
        conditions,
        exceptions,
        temporalConstraints,
      ),
    };
  }
  return null;
}

export function extractLegalSubjects(sentence: string): string[] {
  const subjects = new Set<string>();
  const lower = sentence.toLowerCase();
  const subjectPattern =
    /\b(?:citizens?|residents?|persons?|individuals?|companies?|businesses?|employees?|workers?|drivers?|operators?|users?|owners?|lessees?|tenants?|students?|minors?|adults?|customers?|applicants?|employers?)\b/g;
  for (const match of lower.matchAll(subjectPattern)) {
    subjects.add(match[0]);
  }
  const capitalized = sentence.match(/\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b/g) || [];
  for (const value of capitalized.slice(0, 2)) {
    subjects.add(value);
  }
  return [...subjects];
}

export function extractLegalActions(sentence: string): string[] {
  const actions = new Set<string>();
  const lower = sentence.toLowerCase();
  const modal =
    /(?:must not|shall not|may not|must|shall|may|can|cannot)\s+(?:not\s+)?(.+?)(?:\s+(?:by|before|after|until|unless|except|when|if)|$)/g;
  for (const match of lower.matchAll(modal)) {
    actions.add(cleanAction(match[1]));
  }
  const prohibited =
    /(?:prohibited from|forbidden to|required to|permitted to|allowed to)\s+(.+?)(?:\s+(?:by|before|after|until|unless|except|when|if)|$)/g;
  for (const match of lower.matchAll(prohibited)) {
    actions.add(cleanAction(match[1]));
  }
  return [...actions].filter(Boolean);
}

export function extractConditions(sentence: string): string[] {
  return extractPatternGroups(sentence, [
    /\bif\s+([^,]+?)(?:,|\s+then|$)/gi,
    /\bwhen\s+([^,]+?)(?:,|$)/gi,
    /\bprovided that\s+([^,]+?)(?:,|$)/gi,
  ]);
}

export function extractExceptions(sentence: string): string[] {
  return extractPatternGroups(sentence, [
    /\bunless\s+([^,]+?)(?:,|$)/gi,
    /\bexcept\s+(?:for\s+)?([^,]+?)(?:,|$)/gi,
    /\bother than\s+([^,]+?)(?:,|$)/gi,
  ]);
}

export function extractTemporalConstraints(sentence: string): TemporalConstraint[] {
  const lower = sentence.toLowerCase();
  const constraints: TemporalConstraint[] = [];
  for (const match of lower.matchAll(/\bwithin\s+(\d+\s+(?:days?|weeks?|months?|years?))/g)) {
    constraints.push({ type: 'deadline', value: match[1] });
  }
  for (const match of lower.matchAll(/\bfor\s+(\d+\s+(?:days?|weeks?|months?|years?))/g)) {
    constraints.push({ type: 'duration', value: match[1] });
  }
  for (const match of lower.matchAll(/\b(annually|monthly|weekly|daily)\b/g)) {
    constraints.push({ type: 'period', value: match[1] });
  }
  return constraints;
}

function extractPatternGroups(sentence: string, patterns: RegExp[]): string[] {
  const values = new Set<string>();
  for (const pattern of patterns) {
    for (const match of sentence.matchAll(pattern)) {
      values.add(match[1].trim().toLowerCase());
    }
  }
  return [...values];
}

function cleanAction(value: string): string {
  return value
    .replace(/\s+/g, ' ')
    .replace(/[.;:]$/g, '')
    .trim();
}

function toPascalPredicate(value: string): string {
  return normalizePredicateName(value)
    .split('_')
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join('');
}

function scoreConfidence(
  sentence: string,
  subjects: string[],
  actions: string[],
  conditions: string[],
  exceptions: string[],
  temporalConstraints: TemporalConstraint[],
): number {
  const predicates = {
    nouns: subjects.map(toPascalPredicate),
    verbs: actions.map(toPascalPredicate),
    adjectives: [
      ...conditions,
      ...exceptions,
      ...temporalConstraints.map((constraint) => constraint.value),
    ].map(toPascalPredicate),
  };
  const quantifiers = subjects.length > 0 ? ['∀'] : [];
  const operators = [
    ...(conditions.length > 0 ? ['→'] : []),
    ...(exceptions.length > 0 ? ['¬'] : []),
    ...(actions.length > 1 ? Array(actions.length - 1).fill('∧') : []),
  ];
  return Math.min(
    0.95,
    0.35 +
      predictMLConfidence(
        sentence,
        buildConfidenceFormula(subjects, actions, conditions),
        predicates,
        quantifiers,
        operators,
      ) *
        0.6,
  );
}

function buildConfidenceFormula(
  subjects: string[],
  actions: string[],
  conditions: string[],
): string {
  const subject = toPascalPredicate(subjects[0] || 'Agent');
  const action = toPascalPredicate(actions[0] || 'Action');
  if (conditions.length > 0) {
    return `O(∀x (${subject}(x) ∧ ${toPascalPredicate(conditions[0])}(x) → ${action}(x)))`;
  }
  return `O(∀x (${subject}(x) → ${action}(x)))`;
}

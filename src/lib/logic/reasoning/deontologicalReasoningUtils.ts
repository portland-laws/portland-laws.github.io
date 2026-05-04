export const DEONTOLOGICAL_REASONING_UTILS_METADATA = {
  sourcePythonModule: 'logic/integration/reasoning/deontological_reasoning_utils.py',
  browserNative: true,
  serverCallsAllowed: false,
  pythonRuntimeAllowed: false,
  runtimeDependencies: [],
} as const;

export interface DeonticPatterns {
  obligationPatterns: Array<RegExp>;
  permissionPatterns: Array<RegExp>;
  prohibitionPatterns: Array<RegExp>;
  conditionalPatterns: Array<RegExp>;
  exceptionPatterns: Array<RegExp>;
}

export const DEONTIC_PATTERNS: DeonticPatterns = {
  obligationPatterns: [
    /(\w+(?:\s+\w+)*)\s+(?:must|shall|are required to|have to|need to|are obligated to)\s+([^.!?]+)/gi,
    /(\w+(?:\s+\w+)*)\s+(?:has a duty to|has an obligation to|is responsible for)\s+([^.!?]+)/gi,
    /it is (?:mandatory|required|necessary) (?:for|that)\s+(\w+(?:\s+\w+)*)\s+(?:to\s+)?([^.!?]+)/gi,
    /(\w+(?:\s+\w+)*)\s+(?:is|are) (?:required|obligated|mandated) to\s+([^.!?]+)/gi,
  ],
  permissionPatterns: [
    /(\w+(?:\s+\w+)*)\s+(?:may|can|are allowed to|are permitted to|have the right to)\s+([^.!?]+)/gi,
    /(\w+(?:\s+\w+)*)\s+(?:is|are) (?:allowed|permitted|authorized) to\s+([^.!?]+)/gi,
    /it is (?:permissible|acceptable) (?:for|that)\s+(\w+(?:\s+\w+)*)\s+(?:to\s+)?([^.!?]+)/gi,
  ],
  prohibitionPatterns: [
    /(\w+(?:\s+\w+)*)\s+(?:must not|cannot|shall not|are not allowed to|are forbidden to|are prohibited from)\s+([^.!?]+)/gi,
    /(\w+(?:\s+\w+)*)\s+(?:is|are) (?:forbidden|prohibited|banned) (?:from|to)\s+([^.!?]+)/gi,
    /it is (?:forbidden|prohibited|illegal) (?:for|that)\s+(\w+(?:\s+\w+)*)\s+(?:to\s+)?([^.!?]+)/gi,
    /no\s+(\w+(?:\s+\w+)*)\s+(?:may|can|shall)\s+([^.!?]+)/gi,
  ],
  conditionalPatterns: [
    /if\s+([^,]+),?\s+(?:then\s+)?(\w+(?:\s+\w+)*)\s+(must|shall|may|cannot|must not)\s+([^.!?]+)/gi,
    /when\s+([^,]+),?\s+(\w+(?:\s+\w+)*)\s+(must|shall|may|cannot|must not)\s+([^.!?]+)/gi,
    /in case of\s+([^,]+),?\s+(\w+(?:\s+\w+)*)\s+(must|shall|may|cannot|must not)\s+([^.!?]+)/gi,
  ],
  exceptionPatterns: [
    /(\w+(?:\s+\w+)*)\s+(must|shall|may|cannot|must not)\s+([^,]+),?\s+(?:unless|except when|except if)\s+([^.!?]+)/gi,
    /(\w+(?:\s+\w+)*)\s+(must|shall|may|cannot|must not)\s+([^,]+),?\s+(?:but not when|but not if)\s+([^.!?]+)/gi,
  ],
};

const STOP_WORDS = new Set([
  'the',
  'a',
  'an',
  'and',
  'or',
  'but',
  'in',
  'on',
  'at',
  'to',
  'for',
  'of',
  'with',
  'by',
]);

export function extractKeywords(text: string): Set<string> {
  const keywords = new Set<string>();
  for (const match of text.toLowerCase().matchAll(/\b\w+\b/g)) {
    const word = match[0];
    if (word.length > 2 && !STOP_WORDS.has(word)) keywords.add(word);
  }
  return keywords;
}

export function calculateTextSimilarity(text1: string, text2: string): number {
  const keywords1 = extractKeywords(text1);
  const keywords2 = extractKeywords(text2);
  if (keywords1.size === 0 || keywords2.size === 0) return 0;
  const union = new Set<string>([...keywords1, ...keywords2]);
  let intersectionSize = 0;
  for (const keyword of keywords1) {
    if (keywords2.has(keyword)) intersectionSize += 1;
  }
  return union.size === 0 ? 0 : intersectionSize / union.size;
}

export function areEntitiesSimilar(entity1: string, entity2: string, threshold = 0.7): boolean {
  const first = entity1.toLowerCase();
  const second = entity2.toLowerCase();
  if (first === second) return true;
  if (first.includes(second) || second.includes(first)) return true;
  return calculateTextSimilarity(entity1, entity2) >= threshold;
}

export function areActionsSimilar(action1: string, action2: string, threshold = 0.6): boolean {
  const first = action1.toLowerCase();
  const second = action2.toLowerCase();
  if (first === second) return true;
  if (first.includes(second) || second.includes(first)) return true;
  return calculateTextSimilarity(action1, action2) >= threshold;
}

export function normalizeEntity(entity: string): string {
  return entity.toLowerCase().trim();
}

export function normalizeAction(action: string): string {
  return action.toLowerCase().trim();
}

export function extractConditionsFromText(text: string): Array<string> {
  return extractClauses(text, [
    /if\s+([^,]+)/gi,
    /when\s+([^,]+)/gi,
    /unless\s+([^,]+)/gi,
    /except when\s+([^,]+)/gi,
    /provided that\s+([^,]+)/gi,
  ]);
}

export function extractExceptionsFromText(text: string): Array<string> {
  return extractClauses(text, [
    /unless\s+([^,]+)/gi,
    /except when\s+([^,]+)/gi,
    /except if\s+([^,]+)/gi,
    /but not when\s+([^,]+)/gi,
  ]);
}

export const deontological_reasoning_utils_metadata = DEONTOLOGICAL_REASONING_UTILS_METADATA;
export const DeonticPatterns = DEONTIC_PATTERNS;
export const extract_keywords = extractKeywords;
export const calculate_text_similarity = calculateTextSimilarity;
export const are_entities_similar = areEntitiesSimilar;
export const are_actions_similar = areActionsSimilar;
export const normalize_entity = normalizeEntity;
export const normalize_action = normalizeAction;
export const extract_conditions_from_text = extractConditionsFromText;
export const extract_exceptions_from_text = extractExceptionsFromText;

function extractClauses(text: string, patterns: Array<RegExp>): Array<string> {
  const clauses: Array<string> = [];
  for (const pattern of patterns) {
    pattern.lastIndex = 0;
    for (const match of text.matchAll(pattern)) {
      clauses.push(match[1].trim());
    }
  }
  return clauses;
}

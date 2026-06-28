export type CecDetectedLanguage = 'en' | 'es' | 'fr' | 'de' | 'pt' | 'unknown';
export type CecScoredLanguage = Exclude<CecDetectedLanguage, 'unknown'>;

export interface CecLanguageScores {
  en: number;
  es: number;
  fr: number;
  de: number;
  pt: number;
}

export interface CecLanguageDetectionResult {
  language: CecDetectedLanguage;
  confidence: number;
  scores: CecLanguageScores;
  matched_terms: string[];
  method: 'browser_native_keyword_profile';
  browser_native: true;
  python_module: 'logic/CEC/nl/language_detector.py';
}

interface CecLanguageProfile {
  language: CecScoredLanguage;
  terms: string[];
  legalTerms: string[];
}

const PROFILES: CecLanguageProfile[] = [
  {
    language: 'en',
    terms: ['the', 'and', 'or', 'tenant', 'landlord', 'person', 'must', 'shall', 'may'],
    legalTerms: ['required to', 'prohibited from', 'permitted to', 'liable', 'policy'],
  },
  {
    language: 'es',
    terms: ['el', 'la', 'y', 'o', 'inquilino', 'arrendador', 'debe', 'puede'],
    legalTerms: ['prohibido', 'permitido', 'politica', 'responsable'],
  },
  {
    language: 'fr',
    terms: ['le', 'la', 'et', 'ou', 'locataire', 'bailleur', 'doit', 'peut'],
    legalTerms: ['interdit', 'autorise', 'politique', 'responsable'],
  },
  {
    language: 'de',
    terms: ['der', 'die', 'und', 'oder', 'mieter', 'vermieter', 'muss', 'darf'],
    legalTerms: ['verboten', 'erlaubt', 'richtlinie', 'haftbar'],
  },
  {
    language: 'pt',
    terms: ['o', 'a', 'e', 'ou', 'inquilino', 'senhorio', 'deve', 'pode'],
    legalTerms: ['proibido', 'permitido', 'politica', 'responsavel'],
  },
];

export class CecLanguageDetector {
  detect(text: string): CecLanguageDetectionResult {
    const normalized = normalizeLanguageText(text);
    const scores: CecLanguageScores = { en: 0, es: 0, fr: 0, de: 0, pt: 0 };
    const matchedTerms: string[] = [];

    for (const profile of PROFILES) {
      for (const term of profile.terms) {
        if (containsTerm(normalized, term)) {
          scores[profile.language] += 1;
          matchedTerms.push(`${profile.language}:${term}`);
        }
      }
      for (const term of profile.legalTerms) {
        if (containsTerm(normalized, term)) {
          scores[profile.language] += 2;
          matchedTerms.push(`${profile.language}:${term}`);
        }
      }
    }

    let language: CecDetectedLanguage = 'unknown';
    let bestScore = 0;
    let totalScore = 0;
    for (const profile of PROFILES) {
      const score = scores[profile.language];
      totalScore += score;
      if (score > bestScore) {
        bestScore = score;
        language = profile.language;
      }
    }

    return {
      language: bestScore === 0 ? 'unknown' : language,
      confidence: totalScore === 0 ? 0 : bestScore / totalScore,
      scores,
      matched_terms: matchedTerms,
      method: 'browser_native_keyword_profile',
      browser_native: true,
      python_module: 'logic/CEC/nl/language_detector.py',
    };
  }

  detect_language(text: string): CecLanguageDetectionResult {
    return this.detect(text);
  }
}

export function detectCecLanguage(text: string): CecLanguageDetectionResult {
  return new CecLanguageDetector().detect(text);
}

export function detect_language(text: string): CecLanguageDetectionResult {
  return detectCecLanguage(text);
}

export function getCecLanguageDetectorCapabilities() {
  return {
    browserNative: true,
    pythonRuntime: false,
    serverRuntime: false,
    filesystem: false,
    subprocess: false,
    rpc: false,
    wasmCompatible: true,
    wasmRequired: false,
    implementation: 'deterministic-typescript',
    pythonModule: 'logic/CEC/nl/language_detector.py',
  } as const;
}

function normalizeLanguageText(text: string): string {
  return text
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^\p{L}\p{N}\s]/gu, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function containsTerm(normalized: string, term: string): boolean {
  const normalizedTerm = normalizeLanguageText(term);
  return new RegExp(`(?:^|\\s)${escapeRegExp(normalizedTerm)}(?:\\s|$)`, 'u').test(normalized);
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

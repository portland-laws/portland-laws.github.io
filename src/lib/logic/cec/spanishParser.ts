import { DcecFormula } from './dcecCore';
import { DcecNamespace } from './dcecNamespace';
import { DcecPatternMatcher } from './nlConverter';

type SpanishParserMetadata = {
  sourcePythonModule: 'logic/CEC/nl/spanish_parser.py';
  runtime: 'browser-native-typescript';
  implementation: 'deterministic-spanish-legal-patterns';
};

export interface SpanishParseResult {
  ok: boolean;
  success: boolean;
  source_text: string;
  normalized_text: string;
  english_text?: string;
  dcec_formula?: DcecFormula;
  dcec?: string;
  confidence: number;
  errors: string[];
  fail_closed_reason?: 'empty_input';
  parse_method: 'browser_native_spanish_parser';
  browser_native: true;
  metadata: SpanishParserMetadata;
}

const TERM_TRANSLATIONS: Array<[RegExp, string]> = [
  [/\b(?:el|la|los|las|un|una|unos|unas)\b/gu, ''],
  [/\binquilino\b|\barrendatario\b|\blocatario\b/gu, 'tenant'],
  [/\barrendador\b|\bpropietario\b|\bdueño\b/gu, 'landlord'],
  [/\bpersona\b/gu, 'person'],
  [/\bno debe\b|\bno puede\b|\best[aá] prohibido\b|\bse proh[ií]be\b/gu, 'must not'],
  [/\bdebe\b|\btiene que\b|\best[aá] obligado a\b|\bse obliga a\b/gu, 'must'],
  [/\bpuede\b|\btiene permiso para\b|\best[aá] permitido\b/gu, 'may'],
  [/\bsiempre\b/gu, 'always'],
  [/\beventualmente\b|\bfinalmente\b/gu, 'eventually'],
  [/\bpr[oó]ximo\b|\bsiguiente\b/gu, 'next'],
  [/\bsi\b/gu, 'if'],
  [/\bentonces\b/gu, 'then'],
  [/\bno\b/gu, 'not'],
  [/\by\b/gu, 'and'],
  [/\bo\b/gu, 'or'],
  [/\bpagar\b/gu, 'pay'],
  [/\brenta\b|\balquiler\b/gu, 'rent'],
  [/\bmantener\b/gu, 'maintain'],
  [/\breparar\b/gu, 'repair'],
  [/\bentrar\b|\bingresar\b/gu, 'enter'],
  [/\binspeccionar\b|\brevisar\b/gu, 'inspect'],
  [/\bfumar\b/gu, 'smoke'],
];

const SPANISH_METADATA: SpanishParserMetadata = {
  sourcePythonModule: 'logic/CEC/nl/spanish_parser.py',
  runtime: 'browser-native-typescript',
  implementation: 'deterministic-spanish-legal-patterns',
};

export class SpanishParser {
  readonly namespace: DcecNamespace;
  private readonly matcher: DcecPatternMatcher;

  constructor(namespace = new DcecNamespace()) {
    this.namespace = namespace;
    this.matcher = new DcecPatternMatcher(namespace);
  }

  parse(text: string): SpanishParseResult {
    const normalized = normalizeSpanishText(text);
    const baseResult = {
      source_text: text,
      normalized_text: normalized,
      parse_method: 'browser_native_spanish_parser' as const,
      browser_native: true as const,
      metadata: SPANISH_METADATA,
    };

    if (!normalized) {
      return {
        ...baseResult,
        ok: false,
        success: false,
        confidence: 0,
        errors: ['Spanish text is empty.'],
        fail_closed_reason: 'empty_input',
      };
    }

    const english = translateSpanishLegalText(normalized);
    const formula = this.matcher.convert(english);
    return {
      ...baseResult,
      ok: true,
      success: true,
      english_text: english,
      dcec_formula: formula,
      dcec: formula.toString(),
      confidence: 0.72,
      errors: [],
    };
  }

  parse_spanish(text: string): SpanishParseResult {
    return this.parse(text);
  }
}

export function parseSpanishDcec(text: string, namespace?: DcecNamespace): SpanishParseResult {
  return new SpanishParser(namespace).parse(text);
}

export function parse_spanish(text: string): SpanishParseResult {
  return parseSpanishDcec(text);
}

export function getSpanishParserCapabilities() {
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
    pythonModule: 'logic/CEC/nl/spanish_parser.py',
  } as const;
}

function translateSpanishLegalText(normalized: string): string {
  let translated = normalized;
  for (const [pattern, replacement] of TERM_TRANSLATIONS) {
    translated = translated.replace(pattern, replacement);
  }
  return translated.replace(/\s+/gu, ' ').trim();
}

function normalizeSpanishText(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^\p{L}\p{N}\s]/gu, ' ')
    .replace(/\s+/gu, ' ')
    .trim();
}

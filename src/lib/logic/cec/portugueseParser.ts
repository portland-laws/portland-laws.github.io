import { DcecFormula } from './dcecCore';
import { DcecNamespace } from './dcecNamespace';
import { DcecPatternMatcher } from './nlConverter';

type PortugueseParserMetadata = {
  sourcePythonModule: 'logic/CEC/nl/portuguese_parser.py';
  runtime: 'browser-native-typescript';
  implementation: 'deterministic-portuguese-legal-patterns';
};

export interface PortugueseParseResult {
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
  parse_method: 'browser_native_portuguese_parser';
  browser_native: true;
  metadata: PortugueseParserMetadata;
}

const TERM_TRANSLATIONS: Array<[RegExp, string]> = [
  [/\b(?:o|a|os|as)\b/gu, ''],
  [/\binquilino\b/gu, 'tenant'],
  [/\blocata?rio\b/gu, 'tenant'],
  [/\bsenhorio\b/gu, 'landlord'],
  [/\blocador\b/gu, 'landlord'],
  [/\bpessoa\b/gu, 'person'],
  [/\bnao deve\b|\bnão deve\b|\be proibido de\b|\bé proibido de\b/gu, 'must not'],
  [/\bdeve\b|\btem de\b|\be obrigado a\b|\bé obrigado a\b/gu, 'must'],
  [/\bpode\b|\btem permissao para\b|\btem permissão para\b/gu, 'may'],
  [/\bsempre\b/gu, 'always'],
  [/\beventualmente\b/gu, 'eventually'],
  [/\bproximo\b|\bpróximo\b/gu, 'next'],
  [/\bse\b/gu, 'if'],
  [/\bentao\b|\bentão\b/gu, 'then'],
  [/\bnao\b|\bnão\b/gu, 'not'],
  [/\be\b/gu, 'and'],
  [/\bou\b/gu, 'or'],
  [/\bpagar\b/gu, 'pay'],
  [/\brenda\b|\baluguel\b/gu, 'rent'],
  [/\bmanter\b/gu, 'maintain'],
  [/\breparar\b/gu, 'repair'],
  [/\bentrar\b/gu, 'enter'],
  [/\binspecionar\b/gu, 'inspect'],
  [/\bfumar\b/gu, 'smoke'],
];

const PORTUGUESE_METADATA: PortugueseParserMetadata = {
  sourcePythonModule: 'logic/CEC/nl/portuguese_parser.py',
  runtime: 'browser-native-typescript',
  implementation: 'deterministic-portuguese-legal-patterns',
};

export class PortugueseParser {
  readonly namespace: DcecNamespace;
  private readonly matcher: DcecPatternMatcher;

  constructor(namespace = new DcecNamespace()) {
    this.namespace = namespace;
    this.matcher = new DcecPatternMatcher(namespace);
  }

  parse(text: string): PortugueseParseResult {
    const normalized = normalizePortugueseText(text);
    const baseResult = {
      source_text: text,
      normalized_text: normalized,
      parse_method: 'browser_native_portuguese_parser' as const,
      browser_native: true as const,
      metadata: PORTUGUESE_METADATA,
    };

    if (!normalized) {
      return {
        ...baseResult,
        ok: false,
        success: false,
        confidence: 0,
        errors: ['Portuguese text is empty.'],
        fail_closed_reason: 'empty_input',
      };
    }

    const english = translatePortugueseLegalText(normalized);
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

  parse_portuguese(text: string): PortugueseParseResult {
    return this.parse(text);
  }
}

export function parsePortugueseDcec(
  text: string,
  namespace?: DcecNamespace,
): PortugueseParseResult {
  return new PortugueseParser(namespace).parse(text);
}

export function parse_portuguese(text: string): PortugueseParseResult {
  return parsePortugueseDcec(text);
}

export function getPortugueseParserCapabilities() {
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
    pythonModule: 'logic/CEC/nl/portuguese_parser.py',
  } as const;
}

function translatePortugueseLegalText(normalized: string): string {
  let translated = normalized;
  for (const [pattern, replacement] of TERM_TRANSLATIONS) {
    translated = translated.replace(pattern, replacement);
  }
  return translated.replace(/\s+/gu, ' ').trim();
}

function normalizePortugueseText(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^\p{L}\p{N}\s]/gu, ' ')
    .replace(/\s+/gu, ' ')
    .trim();
}

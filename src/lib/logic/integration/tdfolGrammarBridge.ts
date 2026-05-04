import { LogicParseError } from '../errors';
import type {
  TdfolDeonticOperator,
  TdfolFormula,
  TdfolTemporalOperator,
  TdfolTerm,
} from '../tdfol/ast';
import { formatTdfolFormula } from '../tdfol/formatter';
import { parseTdfolFormula } from '../tdfol/parser';

export const TDFOL_GRAMMAR_BRIDGE_METADATA = {
  sourcePythonModule: 'logic/integration/tdfol_grammar_bridge.py',
  legacySourcePythonModules: ['logic/integration/bridges/tdfol_grammar_bridge.py'],
  browserNative: true,
  runtime: 'typescript-wasm-browser',
  serverCallsAllowed: false,
  pythonRuntime: false,
  filesystemAllowed: false,
  subprocessAllowed: false,
  rpcAllowed: false,
  failClosed: true,
  grammar: 'deterministic-controlled-english-tdfol',
} as const;

export type TdfolGrammarBridgeInputKind = 'tdfol' | 'controlled_english';
export type TdfolGrammarBridgeRequest =
  | string
  | {
      source: string;
      inputKind?: TdfolGrammarBridgeInputKind;
    };

export interface TdfolGrammarBridgeParseResult {
  status: 'success' | 'failed';
  source: string;
  inputKind: TdfolGrammarBridgeInputKind;
  formula: TdfolFormula | null;
  formulaText: string;
  warnings: Array<string>;
  metadata: typeof TDFOL_GRAMMAR_BRIDGE_METADATA;
  grammarTrace: Array<string>;
  error?: string;
}

const TEMPORAL_PREFIXES: Array<[RegExp, TdfolTemporalOperator, string]> = [
  [/^always\s+/, 'ALWAYS', 'temporal:always'],
  [/^eventually\s+/, 'EVENTUALLY', 'temporal:eventually'],
  [/^next\s+/, 'NEXT', 'temporal:next'],
];

const MODAL_PATTERNS: Array<[RegExp, TdfolDeonticOperator, string]> = [
  [
    /^(.+?)\s+(?:must|shall|is required to|are required to)\s+not\s+(.+)$/,
    'PROHIBITION',
    'modal:prohibition',
  ],
  [
    /^(.+?)\s+(?:must not|shall not|is prohibited from|are prohibited from)\s+(.+)$/,
    'PROHIBITION',
    'modal:prohibition',
  ],
  [
    /^(.+?)\s+(?:must|shall|is required to|are required to)\s+(.+)$/,
    'OBLIGATION',
    'modal:obligation',
  ],
  [
    /^(.+?)\s+(?:may|is permitted to|are permitted to|can)\s+(.+)$/,
    'PERMISSION',
    'modal:permission',
  ],
];

export class BrowserNativeTdfolGrammarBridge {
  readonly metadata = TDFOL_GRAMMAR_BRIDGE_METADATA;

  parse(requestOrSource: TdfolGrammarBridgeRequest): TdfolGrammarBridgeParseResult {
    const request =
      typeof requestOrSource === 'string'
        ? { source: requestOrSource, inputKind: 'controlled_english' as const }
        : requestOrSource;
    const inputKind = request.inputKind ?? 'controlled_english';
    try {
      const parsed =
        inputKind === 'tdfol'
          ? { formula: parseTdfolFormula(request.source), trace: ['tdfol:parser'] }
          : parseControlledEnglish(request.source);
      return parseResult(
        'success',
        request.source,
        inputKind,
        parsed.formula,
        parsed.trace,
        this.metadata,
      );
    } catch (error) {
      return {
        ...parseResult('failed', request.source, inputKind, null, [], this.metadata),
        warnings: ['TDFOL grammar bridge failed closed without Python or service fallback.'],
        error: error instanceof Error ? error.message : String(error),
      };
    }
  }

  validate(requestOrSource: TdfolGrammarBridgeRequest) {
    const result = this.parse(requestOrSource);
    return {
      valid: result.status === 'success',
      errors: result.error ? [result.error] : [],
      metadata: this.metadata,
      grammarTrace: result.grammarTrace,
    };
  }
}

export function createBrowserNativeTdfolGrammarBridge(): BrowserNativeTdfolGrammarBridge {
  return new BrowserNativeTdfolGrammarBridge();
}

export function parseTdfolGrammarBridgeInput(
  requestOrSource: TdfolGrammarBridgeRequest,
): TdfolGrammarBridgeParseResult {
  return createBrowserNativeTdfolGrammarBridge().parse(requestOrSource);
}

export function validateTdfolGrammarBridgeInput(requestOrSource: TdfolGrammarBridgeRequest) {
  return createBrowserNativeTdfolGrammarBridge().validate(requestOrSource);
}

function parseControlledEnglish(source: string): { formula: TdfolFormula; trace: Array<string> } {
  const normalized = source.trim().toLowerCase().replace(/[.;]$/, '').replace(/\s+/g, ' ');
  if (normalized.length === 0) {
    throw new LogicParseError('Expected controlled-English TDFOL sentence but found empty input', {
      source,
    });
  }

  const trace: Array<string> = ['controlled_english:normalize'];
  let remaining = normalized;
  let temporal: TdfolTemporalOperator | undefined;
  for (const [pattern, operator, label] of TEMPORAL_PREFIXES) {
    if (pattern.test(remaining)) {
      temporal = operator;
      remaining = remaining.replace(pattern, '');
      trace.push(label);
      break;
    }
  }

  const parsed = parseModalSentence(remaining, source);
  trace.push(parsed.trace);
  const predicate: TdfolFormula = {
    kind: 'predicate',
    name: toPredicateName(parsed.action),
    args: [toConstant(parsed.agent)],
  };
  return {
    formula: {
      kind: 'deontic',
      operator: parsed.modality,
      formula: temporal ? { kind: 'temporal', operator: temporal, formula: predicate } : predicate,
    },
    trace,
  };
}

function parseModalSentence(
  source: string,
  originalSource: string,
): { agent: string; action: string; modality: TdfolDeonticOperator; trace: string } {
  for (const [pattern, modality, trace] of MODAL_PATTERNS) {
    const match = source.match(pattern);
    if (match) return { agent: match[1], action: match[2], modality, trace };
  }
  throw new LogicParseError('Unsupported controlled-English TDFOL grammar', {
    source: originalSource,
  });
}

function parseResult(
  status: 'success' | 'failed',
  source: string,
  inputKind: TdfolGrammarBridgeInputKind,
  formula: TdfolFormula | null,
  grammarTrace: Array<string>,
  metadata: typeof TDFOL_GRAMMAR_BRIDGE_METADATA,
): TdfolGrammarBridgeParseResult {
  return {
    status,
    source,
    inputKind,
    formula,
    formulaText: formula ? formatTdfolFormula(formula) : '',
    warnings: [],
    metadata,
    grammarTrace,
  };
}

function toConstant(value: string): TdfolTerm {
  return { kind: 'constant', name: sanitizeIdentifier(value) };
}

function toPredicateName(value: string): string {
  const sanitized = sanitizeIdentifier(value);
  return sanitized.charAt(0).toUpperCase() + sanitized.slice(1);
}

function sanitizeIdentifier(value: string): string {
  const identifier = value
    .trim()
    .replace(/^(to|the)\s+/, '')
    .replace(/[^a-z0-9_]+/g, '_')
    .replace(/^_+|_+$/g, '');
  if (/^[a-z_][a-z0-9_]*$/i.test(identifier)) return identifier;
  throw new LogicParseError(`Cannot map phrase to TDFOL identifier: ${value}`, { value });
}

import { LogicParseError } from '../errors';
import type {
  CecApplication,
  CecBinaryExpression,
  CecBinaryOperator,
  CecExpression,
  CecQuantifiedExpression,
  CecQuantifier,
  CecUnaryExpression,
  CecUnaryOperator,
} from './ast';

type CecTokenType = 'LPAREN' | 'RPAREN' | 'ATOM' | 'EOF';

interface CecToken {
  type: CecTokenType;
  value: string;
  offset: number;
}

const QUANTIFIERS = new Set(['forall', 'exists']);
const UNARY_OPERATORS = new Set(['not', 'O', 'P', 'F', 'always', 'eventually', 'next']);
const BINARY_OPERATORS = new Set(['implies', 'and', 'or', 'iff', 'xor', 'until', 'since']);
const BASE_NL_STOP_WORDS = new Set(['a', 'an', 'the', 'to']);
const FRENCH_NL_STOP_WORDS = new Set([
  'a',
  'au',
  'aux',
  'de',
  'des',
  'du',
  'en',
  'l',
  'la',
  'le',
  'les',
  'un',
  'une',
]);
const GERMAN_NL_STOP_WORDS = new Set([
  'am',
  'auf',
  'das',
  'dem',
  'den',
  'der',
  'des',
  'die',
  'ein',
  'eine',
  'einen',
  'einem',
  'einer',
  'im',
  'in',
  'zu',
  'zum',
  'zur',
]);

export interface CecBaseNlParserMetadata {
  readonly sourcePythonModule: 'logic/CEC/nl/base_parser.py';
  readonly runtime: 'browser-native-typescript';
  readonly implementation: 'deterministic-base-nl-parser';
  readonly browserNative: true;
  readonly pythonRuntime: false;
  readonly serverRuntime: false;
}

export interface CecBaseNlParseResult {
  readonly ok: boolean;
  readonly input: string;
  readonly normalizedText: string;
  readonly expression?: CecExpression;
  readonly formula?: string;
  readonly parseMethod: 'base_parser_pattern' | 'fail_closed';
  readonly confidence: number;
  readonly errors: readonly string[];
  readonly metadata: CecBaseNlParserMetadata;
}

export interface CecBaseNlParserOptions {
  readonly defaultSubject?: string;
  readonly maxInputLength?: number;
}

const CEC_BASE_NL_METADATA: CecBaseNlParserMetadata = {
  sourcePythonModule: 'logic/CEC/nl/base_parser.py',
  runtime: 'browser-native-typescript',
  implementation: 'deterministic-base-nl-parser',
  browserNative: true,
  pythonRuntime: false,
  serverRuntime: false,
};

const CEC_FRENCH_NL_METADATA = {
  sourcePythonModule: 'logic/CEC/nl/french_parser.py',
  runtime: 'browser-native-typescript',
  implementation: 'deterministic-french-nl-parser',
  browserNative: true,
  pythonRuntime: false,
  serverRuntime: false,
} as const;

const CEC_GERMAN_NL_METADATA = {
  sourcePythonModule: 'logic/CEC/nl/german_parser.py',
  runtime: 'browser-native-typescript',
  implementation: 'deterministic-german-nl-parser',
  browserNative: true,
  pythonRuntime: false,
  serverRuntime: false,
} as const;

export type CecFrenchNlParseResult = Omit<CecBaseNlParseResult, 'parseMethod' | 'metadata'> & {
  readonly parseMethod: 'french_parser_pattern' | 'fail_closed';
  readonly metadata: typeof CEC_FRENCH_NL_METADATA;
};

export type CecGermanNlParseResult = Omit<CecBaseNlParseResult, 'parseMethod' | 'metadata'> & {
  readonly parseMethod: 'german_parser_pattern' | 'fail_closed';
  readonly metadata: typeof CEC_GERMAN_NL_METADATA;
};

export function parseCecExpression(source: string): CecExpression {
  return new CecParser(source).parse();
}

export function validateCecExpression(
  source: string,
): { ok: true; expression: CecExpression } | { ok: false; error: string } {
  try {
    return { ok: true, expression: parseCecExpression(source) };
  } catch (error) {
    return {
      ok: false,
      error: error instanceof Error ? error.message : 'Unable to parse CEC expression.',
    };
  }
}

export function parseCecNaturalLanguageBase(
  source: string,
  options: CecBaseNlParserOptions = {},
): CecBaseNlParseResult {
  const normalizedText = normalizeBaseNlText(source);
  const maxInputLength = options.maxInputLength ?? 2000;
  if (source.length > maxInputLength) {
    return failBaseNl(source, normalizedText, [`Input exceeds ${maxInputLength} characters.`]);
  }
  if (normalizedText.length === 0) {
    return failBaseNl(source, normalizedText, ['Input is empty.']);
  }

  const expression = parseBaseNlClause(normalizedText, options.defaultSubject ?? 'agent');
  if (!expression) {
    return failBaseNl(source, normalizedText, ['No deterministic base_parser pattern matched.']);
  }

  return {
    ok: true,
    input: source,
    normalizedText,
    expression,
    formula: formatBaseNlExpression(expression),
    parseMethod: 'base_parser_pattern',
    confidence: 0.72,
    errors: [],
    metadata: CEC_BASE_NL_METADATA,
  };
}

export const parseCecNaturalLanguage = parseCecNaturalLanguageBase;
export const parse_cec_natural_language_base = parseCecNaturalLanguageBase;

export function parseCecNaturalLanguageFrench(
  source: string,
  options: CecBaseNlParserOptions = {},
): CecFrenchNlParseResult {
  const normalizedText = normalizeFrenchNlText(source);
  const maxInputLength = options.maxInputLength ?? 2000;
  if (source.length > maxInputLength) {
    return failFrenchNl(source, normalizedText, [`Input exceeds ${maxInputLength} characters.`]);
  }
  if (normalizedText.length === 0) {
    return failFrenchNl(source, normalizedText, ['Input is empty.']);
  }

  const expression = parseFrenchNlClause(normalizedText, options.defaultSubject ?? 'agent');
  if (!expression) {
    return failFrenchNl(source, normalizedText, [
      'No deterministic french_parser pattern matched.',
    ]);
  }

  return {
    ok: true,
    input: source,
    normalizedText,
    expression,
    formula: formatBaseNlExpression(expression),
    parseMethod: 'french_parser_pattern',
    confidence: 0.7,
    errors: [],
    metadata: CEC_FRENCH_NL_METADATA,
  };
}

export const parse_cec_natural_language_french = parseCecNaturalLanguageFrench;

export function parseCecNaturalLanguageGerman(
  source: string,
  options: CecBaseNlParserOptions = {},
): CecGermanNlParseResult {
  const normalizedText = normalizeGermanNlText(source);
  const maxInputLength = options.maxInputLength ?? 2000;
  if (source.length > maxInputLength) {
    return failGermanNl(source, normalizedText, [`Input exceeds ${maxInputLength} characters.`]);
  }
  if (normalizedText.length === 0) {
    return failGermanNl(source, normalizedText, ['Input is empty.']);
  }

  const expression = parseGermanNlClause(normalizedText, options.defaultSubject ?? 'agent');
  if (!expression) {
    return failGermanNl(source, normalizedText, [
      'No deterministic german_parser pattern matched.',
    ]);
  }

  return {
    ok: true,
    input: source,
    normalizedText,
    expression,
    formula: formatBaseNlExpression(expression),
    parseMethod: 'german_parser_pattern',
    confidence: 0.7,
    errors: [],
    metadata: CEC_GERMAN_NL_METADATA,
  };
}

export const parse_cec_natural_language_german = parseCecNaturalLanguageGerman;

class CecParser {
  private readonly tokens: CecToken[];
  private index = 0;

  constructor(private readonly source: string) {
    this.tokens = lexCec(source);
  }

  parse(): CecExpression {
    const expression = this.parseExpression();
    this.expect('EOF');
    return expression;
  }

  private parseExpression(): CecExpression {
    if (this.match('LPAREN')) {
      return this.parseList();
    }
    const atom = this.expect('ATOM');
    return { kind: 'atom', name: atom.value };
  }

  private parseList(): CecExpression {
    const operator = this.expect('ATOM');
    if (QUANTIFIERS.has(operator.value)) {
      return this.parseQuantified(operator.value as CecQuantifier, operator.offset);
    }
    if (UNARY_OPERATORS.has(operator.value)) {
      return this.parseUnary(operator.value as CecUnaryOperator);
    }
    if (BINARY_OPERATORS.has(operator.value)) {
      return this.parseBinary(operator.value as CecBinaryOperator, operator.offset);
    }
    return this.parseApplication(operator.value);
  }

  private parseQuantified(quantifier: CecQuantifier, offset: number): CecQuantifiedExpression {
    const variable = this.expect('ATOM');
    if (this.peek('RPAREN')) {
      throw new LogicParseError(`${quantifier} requires a body expression`, {
        source: this.source,
        offset,
      });
    }
    const expression = this.parseExpression();
    this.expect('RPAREN');
    return {
      kind: 'quantified',
      quantifier,
      variable: variable.value,
      expression,
    };
  }

  private parseUnary(operator: CecUnaryOperator): CecUnaryExpression {
    const expression = this.parseExpression();
    this.expect('RPAREN');
    return { kind: 'unary', operator, expression };
  }

  private parseBinary(operator: CecBinaryOperator, offset: number): CecBinaryExpression {
    const left = this.parseExpression();
    if (this.peek('RPAREN')) {
      throw new LogicParseError(`${operator} requires two operands`, {
        source: this.source,
        offset,
      });
    }
    const right = this.parseExpression();
    this.expect('RPAREN');
    return { kind: 'binary', operator, left, right };
  }

  private parseApplication(name: string): CecApplication {
    const args: CecExpression[] = [];
    while (!this.peek('RPAREN')) {
      if (this.peek('EOF')) {
        throw new LogicParseError(`Unclosed application ${name}`, {
          source: this.source,
          offset: this.current().offset,
        });
      }
      args.push(this.parseExpression());
    }
    this.expect('RPAREN');
    return { kind: 'application', name, args };
  }

  private current() {
    return this.tokens[this.index];
  }

  private peek(type: CecTokenType) {
    return this.current().type === type;
  }

  private match(type: CecTokenType) {
    if (!this.peek(type)) {
      return false;
    }
    this.index += 1;
    return true;
  }

  private expect(type: CecTokenType) {
    const token = this.current();
    if (token.type !== type) {
      throw new LogicParseError(`Expected ${type} but found ${token.type}`, {
        source: this.source,
        offset: token.offset,
      });
    }
    this.index += 1;
    return token;
  }
}

function lexCec(source: string): CecToken[] {
  const tokens: CecToken[] = [];
  let offset = 0;

  while (offset < source.length) {
    const char = source[offset];
    if (/\s/.test(char)) {
      offset += 1;
      continue;
    }
    if (char === '(') {
      tokens.push({ type: 'LPAREN', value: char, offset });
      offset += 1;
      continue;
    }
    if (char === ')') {
      tokens.push({ type: 'RPAREN', value: char, offset });
      offset += 1;
      continue;
    }

    const start = offset;
    while (offset < source.length && !/\s|\(|\)/.test(source[offset])) {
      offset += 1;
    }
    tokens.push({ type: 'ATOM', value: source.slice(start, offset), offset: start });
  }

  tokens.push({ type: 'EOF', value: '', offset: source.length });
  return tokens;
}

function parseBaseNlClause(text: string, defaultSubject: string): CecExpression | undefined {
  const conditional = /^if (.+) then (.+)$/.exec(text);
  if (conditional) {
    const left = parseBaseNlClause(conditional[1], defaultSubject);
    const right = parseBaseNlClause(conditional[2], defaultSubject);
    if (left && right) {
      return { kind: 'binary', operator: 'implies', left, right };
    }
    return undefined;
  }

  const temporal = /^(always|eventually|next) (.+)$/.exec(text);
  if (temporal) {
    const expression = parseBaseNlClause(temporal[2], defaultSubject);
    if (expression) {
      return { kind: 'unary', operator: temporal[1] as CecUnaryOperator, expression };
    }
    return undefined;
  }

  const notMatch = /^not (.+)$/.exec(text);
  if (notMatch) {
    const expression = parseBaseNlClause(notMatch[1], defaultSubject);
    if (expression) {
      return { kind: 'unary', operator: 'not', expression };
    }
    return undefined;
  }

  const words = text.split(' ').filter(Boolean);
  if (words.length < 2) {
    return undefined;
  }
  const modalIndex = words.findIndex((word) =>
    ['must', 'shall', 'may', 'can', 'must_not', 'shall_not'].includes(word),
  );
  if (modalIndex <= 0 || modalIndex >= words.length - 1) {
    return undefined;
  }

  const subject = atomName(words.slice(0, modalIndex).join('_')) || defaultSubject;
  const modal = words[modalIndex];
  const predicateWords = words
    .slice(modalIndex + 1)
    .filter((word) => !BASE_NL_STOP_WORDS.has(word));
  if (predicateWords.length === 0) {
    return undefined;
  }

  return {
    kind: 'unary',
    operator: modal === 'may' || modal === 'can' ? 'P' : modal.endsWith('_not') ? 'F' : 'O',
    expression: {
      kind: 'application',
      name: atomName(predicateWords.join('_')),
      args: [{ kind: 'atom', name: subject }],
    },
  };
}

function parseFrenchNlClause(text: string, defaultSubject: string): CecExpression | undefined {
  const conditional = /^si (.+) alors (.+)$/.exec(text);
  if (conditional) {
    const left = parseFrenchNlClause(conditional[1], defaultSubject);
    const right = parseFrenchNlClause(conditional[2], defaultSubject);
    if (left && right) {
      return { kind: 'binary', operator: 'implies', left, right };
    }
    return undefined;
  }

  const temporal = /^(toujours|eventuellement|ensuite) (.+)$/.exec(text);
  if (temporal) {
    const expression = parseFrenchNlClause(temporal[2], defaultSubject);
    if (expression) {
      const operator =
        temporal[1] === 'toujours' ? 'always' : temporal[1] === 'ensuite' ? 'next' : 'eventually';
      return { kind: 'unary', operator, expression };
    }
    return undefined;
  }

  const forbidden = /^il est interdit de (.+)$/.exec(text);
  if (forbidden) {
    return frenchApplication('F', defaultSubject, forbidden[1]);
  }

  const words = text.split(' ').filter(Boolean);
  const modalIndex = words.findIndex((word) =>
    ['doit', 'doivent', 'peut', 'peuvent', 'ne_doit_pas', 'ne_peut_pas'].includes(word),
  );
  if (modalIndex <= 0 || modalIndex >= words.length - 1) {
    return undefined;
  }

  const subject = atomName(
    words
      .slice(0, modalIndex)
      .filter((word) => !FRENCH_NL_STOP_WORDS.has(word))
      .join('_'),
  );
  const modal = words[modalIndex];
  const operator = modal.includes('peut') ? 'P' : modal.includes('pas') ? 'F' : 'O';
  return frenchApplication(
    operator,
    subject || defaultSubject,
    words.slice(modalIndex + 1).join(' '),
  );
}

function frenchApplication(
  operator: CecUnaryOperator,
  subject: string,
  predicateText: string,
): CecUnaryExpression | undefined {
  const predicate = atomName(
    predicateText
      .split(' ')
      .filter((word) => word.length > 0 && !FRENCH_NL_STOP_WORDS.has(word))
      .join('_'),
  );
  if (predicate.length === 0) {
    return undefined;
  }
  return {
    kind: 'unary',
    operator,
    expression: {
      kind: 'application',
      name: predicate,
      args: [{ kind: 'atom', name: subject }],
    },
  };
}

function parseGermanNlClause(text: string, defaultSubject: string): CecExpression | undefined {
  const conditional = /^wenn (.+) dann (.+)$/.exec(text);
  if (conditional) {
    const left = parseGermanNlClause(conditional[1], defaultSubject);
    const right = parseGermanNlClause(conditional[2], defaultSubject);
    if (left && right) {
      return { kind: 'binary', operator: 'implies', left, right };
    }
    return undefined;
  }

  const temporal = /^(immer|stets|schliesslich|danach) (.+)$/.exec(text);
  if (temporal) {
    const expression = parseGermanNlClause(temporal[2], defaultSubject);
    if (expression) {
      const operator = temporal[1] === 'immer' || temporal[1] === 'stets' ? 'always' : 'eventually';
      return { kind: 'unary', operator, expression };
    }
    return undefined;
  }

  const words = text.split(' ').filter(Boolean);
  const modalIndex = words.findIndex((word) =>
    [
      'muss',
      'muessen',
      'soll',
      'sollen',
      'darf',
      'duerfen',
      'darf_nicht',
      'duerfen_nicht',
    ].includes(word),
  );
  if (modalIndex <= 0 || modalIndex >= words.length - 1) {
    return undefined;
  }

  const subject = atomName(
    words
      .slice(0, modalIndex)
      .filter((word) => !GERMAN_NL_STOP_WORDS.has(word))
      .join('_'),
  );
  const modal = words[modalIndex];
  const operator =
    modal.includes('darf') || modal.includes('duerfen')
      ? modal.includes('nicht')
        ? 'F'
        : 'P'
      : 'O';
  return germanApplication(
    operator,
    subject || defaultSubject,
    words.slice(modalIndex + 1).join(' '),
  );
}

function germanApplication(
  operator: CecUnaryOperator,
  subject: string,
  predicateText: string,
): CecUnaryExpression | undefined {
  const predicate = atomName(
    predicateText
      .split(' ')
      .filter((word) => word.length > 0 && !GERMAN_NL_STOP_WORDS.has(word))
      .join('_'),
  );
  if (predicate.length === 0) {
    return undefined;
  }
  return {
    kind: 'unary',
    operator,
    expression: {
      kind: 'application',
      name: predicate,
      args: [{ kind: 'atom', name: subject }],
    },
  };
}

function normalizeBaseNlText(source: string): string {
  return source
    .toLowerCase()
    .replace(/[^\p{L}\p{N}_\s-]/gu, ' ')
    .replace(/\b(must|shall)\s+not\b/g, '$1_not')
    .replace(/\s+/g, ' ')
    .trim();
}

function normalizeFrenchNlText(source: string): string {
  return source
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^\p{L}\p{N}_\s-]/gu, ' ')
    .replace(/\bne\s+(doit|doivent|peut|peuvent)\s+pas\b/g, 'ne_$1_pas')
    .replace(/\bn\s+(est|sont)\s+pas\s+autorise(?:e|es|s)?\s+a\b/g, 'ne_peut_pas')
    .replace(/\s+/g, ' ')
    .trim();
}

function normalizeGermanNlText(source: string): string {
  return source
    .toLowerCase()
    .replace(/[äöüß]/g, (char) => ({ ä: 'ae', ö: 'oe', ü: 'ue', ß: 'ss' })[char] ?? char)
    .replace(/[^\p{L}\p{N}_\s-]/gu, ' ')
    .replace(/\b(darf|duerfen)\s+nicht\b/g, '$1_nicht')
    .replace(/\s+/g, ' ')
    .trim();
}

function atomName(value: string): string {
  return value
    .replace(/[^a-z0-9_]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .replace(/_{2,}/g, '_');
}

function formatBaseNlExpression(expression: CecExpression): string {
  switch (expression.kind) {
    case 'atom':
      return expression.name;
    case 'application':
      return `(${[expression.name, ...expression.args.map(formatBaseNlExpression)].join(' ')})`;
    case 'quantified':
      return `(${expression.quantifier} ${expression.variable} ${formatBaseNlExpression(expression.expression)})`;
    case 'unary':
      return `(${expression.operator} ${formatBaseNlExpression(expression.expression)})`;
    case 'binary':
      return `(${expression.operator} ${formatBaseNlExpression(expression.left)} ${formatBaseNlExpression(expression.right)})`;
  }
}

function failBaseNl(
  source: string,
  normalizedText: string,
  errors: readonly string[],
): CecBaseNlParseResult {
  return {
    ok: false,
    input: source,
    normalizedText,
    parseMethod: 'fail_closed',
    confidence: 0,
    errors,
    metadata: CEC_BASE_NL_METADATA,
  };
}

function failFrenchNl(
  source: string,
  normalizedText: string,
  errors: readonly string[],
): CecFrenchNlParseResult {
  return {
    ok: false,
    input: source,
    normalizedText,
    parseMethod: 'fail_closed',
    confidence: 0,
    errors,
    metadata: CEC_FRENCH_NL_METADATA,
  };
}

function failGermanNl(
  source: string,
  normalizedText: string,
  errors: readonly string[],
): CecGermanNlParseResult {
  return {
    ok: false,
    input: source,
    normalizedText,
    parseMethod: 'fail_closed',
    confidence: 0,
    errors,
    metadata: CEC_GERMAN_NL_METADATA,
  };
}

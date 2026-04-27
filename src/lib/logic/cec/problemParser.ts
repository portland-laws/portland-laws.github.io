import type { CecShadowModalLogic, CecShadowProblemFile } from './shadowProver';

export type CecProblemFormat = 'tptp' | 'custom';

export interface CecTptpFormula {
  name: string;
  role: string;
  formula: string;
  annotations?: string;
  kind: 'fof' | 'cnf';
}

export interface CecProblemParseOptions {
  name?: string;
  formatHint?: CecProblemFormat;
}

export class CecProblemParseError extends Error {
  constructor(
    message: string,
    readonly details: { source?: string; offset?: number; expected?: string } = {},
  ) {
    super(message);
    this.name = 'CecProblemParseError';
  }
}

export class CecTptpParser {
  formulas: CecTptpFormula[] = [];
  includes: string[] = [];

  parseString(content: string, name = 'tptp_problem'): CecShadowProblemFile {
    this.formulas = [];
    this.includes = [];
    const source = stripTptpComments(content);
    this.includes = parseIncludes(source);
    this.formulas = parseTptpFormulas(source);

    const assumptions: string[] = [];
    const goals: string[] = [];
    for (const formula of this.formulas) {
      if (formula.role === 'axiom' || formula.role === 'hypothesis') {
        assumptions.push(formula.formula);
      } else if (formula.role === 'conjecture' || formula.role === 'theorem') {
        goals.push(formula.formula);
      } else if (formula.role === 'negated_conjecture') {
        goals.push(`not(${formula.formula})`);
      }
    }

    return {
      name,
      logic: 'K',
      assumptions,
      goals,
      metadata: {
        format: 'tptp',
        includes: [...this.includes],
        totalFormulas: this.formulas.length,
        formulas: this.formulas.map((formula) => ({ ...formula })),
      },
    };
  }
}

export class CecCustomProblemParser {
  parseString(content: string, name = 'custom_problem'): CecShadowProblemFile {
    let logic: CecShadowModalLogic = 'K';
    const assumptions: string[] = [];
    const goals: string[] = [];
    let currentSection: 'assumptions' | 'goals' | undefined;

    for (const rawLine of content.split(/\r?\n/)) {
      const line = rawLine.trim();
      if (!line || line.startsWith('#') || line.startsWith('//')) continue;

      if (/^LOGIC\s*:/i.test(line)) {
        logic = parseProblemLogic(line.split(':', 2)[1]?.trim() ?? '');
      } else if (/^ASSUMPTIONS\s*:/i.test(line)) {
        currentSection = 'assumptions';
      } else if (/^GOALS\s*:/i.test(line)) {
        currentSection = 'goals';
      } else if (currentSection === 'assumptions') {
        assumptions.push(line);
      } else if (currentSection === 'goals') {
        goals.push(line);
      }
    }

    return {
      name,
      logic,
      assumptions,
      goals,
      metadata: { format: 'custom' },
    };
  }
}

export class CecProblemParser {
  readonly tptpParser = new CecTptpParser();
  readonly customParser = new CecCustomProblemParser();

  parseString(content: string, options: CecProblemParseOptions = {}): CecShadowProblemFile {
    const format = options.formatHint ?? detectProblemFormat(content);
    const name = options.name ?? (format === 'tptp' ? 'tptp_problem' : 'custom_problem');
    return format === 'tptp'
      ? this.tptpParser.parseString(content, name)
      : this.customParser.parseString(content, name);
  }
}

export function parseCecProblemString(content: string, formatHint?: CecProblemFormat): CecShadowProblemFile {
  return new CecProblemParser().parseString(content, { formatHint });
}

export function detectProblemFormat(content: string): CecProblemFormat {
  return /\b(?:fof|cnf)\s*\(/i.test(content) ? 'tptp' : 'custom';
}

function parseProblemLogic(logic: string): CecShadowModalLogic {
  const normalized = logic.toUpperCase();
  if (normalized === 'T' || normalized === 'S4' || normalized === 'S5' || normalized === 'D') return normalized;
  if (normalized === 'COGNITIVE') return 'S5';
  return 'K';
}

function stripTptpComments(content: string): string {
  return content
    .split(/\r?\n/)
    .map((line) => {
      const commentIndex = line.indexOf('%');
      return commentIndex === -1 ? line : line.slice(0, commentIndex);
    })
    .join('\n');
}

function parseIncludes(source: string): string[] {
  const includes: string[] = [];
  const includePattern = /include\s*\(\s*["']([^"']+)["']\s*\)/gi;
  for (const match of source.matchAll(includePattern)) {
    includes.push(match[1]);
  }
  return includes;
}

function parseTptpFormulas(source: string): CecTptpFormula[] {
  const formulas: CecTptpFormula[] = [];
  const startPattern = /\b(fof|cnf)\s*\(/gi;
  for (const match of source.matchAll(startPattern)) {
    const kind = match[1].toLowerCase() as CecTptpFormula['kind'];
    const openParenIndex = source.indexOf('(', match.index);
    const closeParenIndex = findMatchingParen(source, openParenIndex);
    if (closeParenIndex === -1) {
      throw new CecProblemParseError(`Unclosed ${kind} formula`, {
        source,
        offset: match.index,
        expected: 'matching closing parenthesis',
      });
    }
    const afterClose = source.slice(closeParenIndex + 1).trimStart();
    if (!afterClose.startsWith('.')) {
      throw new CecProblemParseError(`TPTP ${kind} formula must end with a period`, {
        source,
        offset: closeParenIndex + 1,
        expected: '.',
      });
    }

    const args = splitTopLevel(source.slice(openParenIndex + 1, closeParenIndex), ',');
    if (args.length < 3) {
      throw new CecProblemParseError(`TPTP ${kind} formula requires name, role, and formula`, {
        source,
        offset: match.index,
        expected: `${kind}(name, role, formula).`,
      });
    }
    formulas.push({
      kind,
      name: unquote(args[0].trim()),
      role: args[1].trim().toLowerCase(),
      formula: args[2].trim(),
      annotations: args.slice(3).join(',').trim() || undefined,
    });
  }
  return formulas;
}

function findMatchingParen(source: string, openIndex: number): number {
  let depth = 0;
  let quote: string | undefined;
  for (let index = openIndex; index < source.length; index += 1) {
    const char = source[index];
    if (quote) {
      if (char === quote && source[index - 1] !== '\\') quote = undefined;
      continue;
    }
    if (char === '"' || char === "'") {
      quote = char;
      continue;
    }
    if (char === '(') depth += 1;
    if (char === ')') {
      depth -= 1;
      if (depth === 0) return index;
    }
  }
  return -1;
}

function splitTopLevel(source: string, delimiter: string): string[] {
  const parts: string[] = [];
  let depth = 0;
  let quote: string | undefined;
  let start = 0;
  for (let index = 0; index < source.length; index += 1) {
    const char = source[index];
    if (quote) {
      if (char === quote && source[index - 1] !== '\\') quote = undefined;
      continue;
    }
    if (char === '"' || char === "'") {
      quote = char;
      continue;
    }
    if (char === '(' || char === '[' || char === '{') depth += 1;
    if (char === ')' || char === ']' || char === '}') depth -= 1;
    if (char === delimiter && depth === 0) {
      parts.push(source.slice(start, index).trim());
      start = index + 1;
    }
  }
  parts.push(source.slice(start).trim());
  return parts;
}

function unquote(value: string): string {
  if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
    return value.slice(1, -1);
  }
  return value;
}

import type { CecShadowModalLogic, CecShadowProblemFile } from './shadowProver';

export type CecProblemFormat = 'tptp' | 'custom';

export interface CecTptpFormula {
  name: string;
  role: string;
  formula: string;
  annotations?: string;
  kind: 'fof' | 'cnf' | 'tff' | 'thf';
}

export interface CecTptpInclude {
  path: string;
  selections: string[];
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
  includeDirectives: CecTptpInclude[] = [];

  parseString(content: string, name = 'tptp_problem'): CecShadowProblemFile {
    this.formulas = [];
    this.includes = [];
    this.includeDirectives = [];
    const source = stripTptpComments(content);
    this.includeDirectives = parseIncludes(source);
    this.includes = this.includeDirectives.map((include) => include.path);
    this.formulas = parseTptpFormulas(source);

    const assumptions: string[] = [];
    const goals: string[] = [];
    const declarations: CecTptpFormula[] = [];
    for (const formula of this.formulas) {
      const role = classifyProblemRole(formula.role);
      if (role === 'assumption') {
        assumptions.push(formula.formula);
      } else if (role === 'goal') {
        goals.push(formula.formula);
      } else if (role === 'negated_goal') {
        goals.push(`not(${formula.formula})`);
      } else if (formula.role === 'type') {
        declarations.push(formula);
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
        includeDirectives: this.includeDirectives.map((include) => ({ ...include })),
        totalFormulas: this.formulas.length,
        declarations: declarations.map((formula) => ({ ...formula })),
        formulas: this.formulas.map((formula) => ({ ...formula })),
        includeResolution: 'browser-native-metadata-only',
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
      const line = stripInlineComment(rawLine).trim();
      if (!line) continue;

      const assignment = line.match(/^([A-Za-z_ -]+)\s*[:=]\s*(.*)$/);
      if (assignment) {
        const key = normalizeProblemRole(assignment[1]);
        const value = assignment[2].trim();
        if (key === 'logic') {
          logic = parseProblemLogic(value);
          currentSection = undefined;
          continue;
        }
        const role = classifyProblemRole(key);
        if (role === 'assumption') {
          currentSection = value ? undefined : 'assumptions';
          if (value) assumptions.push(value);
          continue;
        }
        if (role === 'goal' || role === 'negated_goal') {
          currentSection = value ? undefined : 'goals';
          if (value) goals.push(role === 'negated_goal' ? `not(${value})` : value);
          continue;
        }
      }

      const section = line.match(/^\[?([A-Za-z_ -]+)\]?$/);
      if (section) {
        const role = classifyProblemRole(section[1]);
        if (role === 'assumption') {
          currentSection = 'assumptions';
          continue;
        }
        if (role === 'goal' || role === 'negated_goal') {
          currentSection = 'goals';
          continue;
        }
      }

      if (currentSection === 'assumptions') {
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

export function parseCecProblemString(
  content: string,
  formatHint?: CecProblemFormat,
): CecShadowProblemFile {
  return new CecProblemParser().parseString(content, { formatHint });
}

export function detectProblemFormat(content: string): CecProblemFormat {
  return /\b(?:fof|cnf|tff|thf)\s*\(/i.test(content) ? 'tptp' : 'custom';
}

function parseProblemLogic(logic: string): CecShadowModalLogic {
  const normalized = logic.toUpperCase();
  if (normalized === 'T' || normalized === 'S4' || normalized === 'S5' || normalized === 'D')
    return normalized;
  if (normalized === 'COGNITIVE') return 'S5';
  return 'K';
}

function classifyProblemRole(role: string): 'assumption' | 'goal' | 'negated_goal' | undefined {
  const normalized = normalizeProblemRole(role);
  if (
    ['axiom', 'hypothesis', 'assumption', 'assumptions', 'premise', 'premises', 'given'].includes(
      normalized,
    )
  ) {
    return 'assumption';
  }
  if (
    ['conjecture', 'theorem', 'goal', 'goals', 'query', 'queries', 'prove'].includes(normalized)
  ) {
    return 'goal';
  }
  if (['negated_conjecture', 'negated_goal', 'negated_query'].includes(normalized))
    return 'negated_goal';
  return undefined;
}

function normalizeProblemRole(role: string): string {
  return role
    .trim()
    .toLowerCase()
    .replace(/[\s-]+/g, '_');
}

function stripInlineComment(line: string): string {
  const hash = line.indexOf('#');
  const slash = line.indexOf('//');
  const indexes = [hash, slash].filter((index) => index >= 0);
  return indexes.length === 0 ? line : line.slice(0, Math.min(...indexes));
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

function parseIncludes(source: string): CecTptpInclude[] {
  const includes: CecTptpInclude[] = [];
  const includePattern = /\binclude\s*\(/gi;
  for (const match of source.matchAll(includePattern)) {
    const openParenIndex = source.indexOf('(', match.index);
    const closeParenIndex = findMatchingParen(source, openParenIndex);
    if (closeParenIndex === -1) {
      throw new CecProblemParseError('Unclosed TPTP include directive', {
        source,
        offset: match.index,
        expected: 'matching closing parenthesis',
      });
    }
    const args = splitTopLevel(source.slice(openParenIndex + 1, closeParenIndex), ',');
    if (args.length < 1 || args.length > 2) {
      throw new CecProblemParseError('TPTP include requires a path and optional selection list', {
        source,
        offset: match.index,
        expected: "include('path', [name]).",
      });
    }
    includes.push({
      path: unquote(args[0].trim()),
      selections: args.length === 2 ? parseIncludeSelections(args[1]) : [],
    });
  }
  return includes;
}

function parseTptpFormulas(source: string): CecTptpFormula[] {
  const formulas: CecTptpFormula[] = [];
  const startPattern = /\b(fof|cnf|tff|thf)\s*\(/gi;
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
      role: normalizeProblemRole(args[1]),
      formula: args[2].trim(),
      annotations: args.slice(3).join(',').trim() || undefined,
    });
  }
  return formulas;
}

function parseIncludeSelections(selectionSource: string): string[] {
  const trimmed = selectionSource.trim();
  if (!trimmed.startsWith('[') || !trimmed.endsWith(']')) {
    throw new CecProblemParseError('TPTP include selections must be a list', {
      source: selectionSource,
      expected: '[formula_name, ...]',
    });
  }
  const body = trimmed.slice(1, -1).trim();
  if (!body) return [];
  return splitTopLevel(body, ',').map((selection) => unquote(selection.trim()));
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
  if (
    (value.startsWith('"') && value.endsWith('"')) ||
    (value.startsWith("'") && value.endsWith("'"))
  ) {
    return value.slice(1, -1);
  }
  return value;
}

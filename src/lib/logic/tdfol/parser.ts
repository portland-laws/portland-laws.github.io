import { LogicParseError } from '../errors';
import type {
  TdfolBinaryFormula,
  TdfolBinaryOperator,
  TdfolDeonticFormula,
  TdfolDeonticOperator,
  TdfolFormula,
  TdfolQuantifiedFormula,
  TdfolQuantifier,
  TdfolTemporalFormula,
  TdfolTemporalOperator,
  TdfolTerm,
} from './ast';
import { lexTdfol, type TdfolToken, type TdfolTokenType } from './lexer';

export function parseTdfolFormula(source: string): TdfolFormula {
  return new TdfolParser(source).parse();
}

export function parseTdfolSafeFormula(source: string): TdfolFormula | null {
  try {
    return parseTdfolFormula(source);
  } catch {
    return null;
  }
}

export function parseTdfolTerm(source: string): TdfolTerm {
  return new TdfolParser(source).parseTermOnly();
}

export const TDFOL_PARSER_METADATA = {
  sourcePythonModule: 'logic/TDFOL/tdfol_parser.py',
  browserNative: true,
  runtimeDependencies: [] as Array<string>,
  parity: [
    'lexer',
    'recursive_descent_formula_parser',
    'recursive_descent_term_parser',
    'safe_parse_null_on_error',
  ] as Array<string>,
} as const;

export const TDFOL_DCEC_PARSER_METADATA = {
  sourcePythonModule: 'logic/TDFOL/tdfol_dcec_parser.py',
  browserNative: true,
  runtimeDependencies: [] as Array<string>,
} as const;

export function parseTdfolDcecFormula(source: string): TdfolFormula {
  const trimmed = source.trim();
  if (trimmed.length === 0) {
    throw new LogicParseError('Expected DCEC/TDFOL formula but found empty input', { source });
  }
  return parseTdfolFormula(normalizeDcecExpression(trimmed, source));
}

class TdfolParser {
  private readonly tokens: TdfolToken[];
  private index = 0;
  private readonly boundVariables: string[] = [];

  constructor(private readonly source: string) {
    this.tokens = lexTdfol(source);
  }

  parse(): TdfolFormula {
    const formula = this.parseIff();
    this.expect('EOF');
    return formula;
  }

  parseTermOnly(): TdfolTerm {
    const term = this.parseTerm();
    this.expect('EOF');
    return term;
  }

  private parseIff(): TdfolFormula {
    let left = this.parseImplication();
    while (this.match('IFF')) {
      left = this.binary('IFF', left, this.parseImplication());
    }
    return left;
  }

  private parseImplication(): TdfolFormula {
    const left = this.parseOr();
    if (this.match('IMPLIES')) {
      return this.binary('IMPLIES', left, this.parseImplication());
    }
    return left;
  }

  private parseOr(): TdfolFormula {
    let left = this.parseUntil();
    while (this.match('OR')) {
      left = this.binary('OR', left, this.parseUntil());
    }
    return left;
  }

  private parseUntil(): TdfolFormula {
    let left = this.parseAnd();
    while (this.match('UNTIL')) {
      left = this.binary('UNTIL', left, this.parseAnd());
    }
    return left;
  }

  private parseAnd(): TdfolFormula {
    let left = this.parseUnary();
    while (this.match('AND')) {
      left = this.binary('AND', left, this.parseUnary());
    }
    return left;
  }

  private parseUnary(): TdfolFormula {
    if (this.match('NOT')) {
      return { kind: 'unary', operator: 'NOT', formula: this.parseUnary() };
    }
    if (this.peek('FORALL') || this.peek('EXISTS')) {
      return this.parseQuantified();
    }
    if (this.peek('OBLIGATION') || this.peek('PERMISSION') || this.peek('PROHIBITION')) {
      return this.parseDeontic();
    }
    if (this.peek('ALWAYS') || this.peek('EVENTUALLY') || this.peek('NEXT')) {
      return this.parseTemporal();
    }
    return this.parsePrimary();
  }

  private parseQuantified(): TdfolQuantifiedFormula {
    const token = this.advance();
    const variable = this.expect('IDENTIFIER');
    let sort: string | undefined;
    if (this.match('COLON')) {
      sort = this.expect('IDENTIFIER').value;
    }
    this.match('DOT');

    this.boundVariables.push(variable.value);
    const formula = this.parseIff();
    this.boundVariables.pop();

    return {
      kind: 'quantified',
      quantifier: token.type === 'FORALL' ? 'FORALL' : 'EXISTS',
      variable: { kind: 'variable', name: variable.value, sort },
      formula,
    };
  }

  private parseDeontic(): TdfolDeonticFormula {
    const token = this.advance();
    const formula = this.parseOperatorArgument();
    const operatorByToken: Record<string, TdfolDeonticOperator> = {
      OBLIGATION: 'OBLIGATION',
      PERMISSION: 'PERMISSION',
      PROHIBITION: 'PROHIBITION',
    };
    return {
      kind: 'deontic',
      operator: operatorByToken[token.type],
      formula,
    };
  }

  private parseTemporal(): TdfolTemporalFormula {
    const token = this.advance();
    const formula = this.parseOperatorArgument();
    const operatorByToken: Record<string, TdfolTemporalOperator> = {
      ALWAYS: 'ALWAYS',
      EVENTUALLY: 'EVENTUALLY',
      NEXT: 'NEXT',
    };
    return {
      kind: 'temporal',
      operator: operatorByToken[token.type],
      formula,
    };
  }

  private parseOperatorArgument(): TdfolFormula {
    if (this.match('LPAREN')) {
      const formula = this.parseIff();
      this.expect('RPAREN');
      return formula;
    }
    return this.parseUnary();
  }

  private parsePrimary(): TdfolFormula {
    if (this.match('LPAREN')) {
      const formula = this.parseIff();
      this.expect('RPAREN');
      return formula;
    }
    return this.parsePredicate();
  }

  private parsePredicate(): TdfolFormula {
    const name = this.expect('IDENTIFIER').value;
    const args: TdfolTerm[] = [];
    if (this.match('LPAREN')) {
      if (!this.peek('RPAREN')) {
        do {
          args.push(this.parseTerm());
        } while (this.match('COMMA'));
      }
      this.expect('RPAREN');
    }
    return { kind: 'predicate', name, args };
  }

  private parseTerm(): TdfolTerm {
    const token = this.advance();
    if (!isTermToken(token.type)) {
      throw new LogicParseError(`Expected term but found ${token.type}`, {
        source: this.source,
        offset: token.position.offset,
      });
    }

    let sort: string | undefined;
    const name = token.value;

    if (this.match('LPAREN')) {
      const args: TdfolTerm[] = [];
      if (!this.peek('RPAREN')) {
        do {
          args.push(this.parseTerm());
        } while (this.match('COMMA'));
      }
      this.expect('RPAREN');
      if (this.match('COLON')) {
        sort = this.expect('IDENTIFIER').value;
      }
      return { kind: 'function', name, args, sort };
    }

    if (this.match('COLON')) {
      sort = this.expect('IDENTIFIER').value;
      if (token.type === 'IDENTIFIER') {
        return { kind: 'variable', name, sort };
      }
    }

    if (token.type === 'NUMBER') {
      return { kind: 'constant', name, sort };
    }

    if (this.boundVariables.includes(name) || /^[a-z]$/.test(name)) {
      return { kind: 'variable', name, sort };
    }
    return { kind: 'constant', name, sort };
  }

  private binary(
    operator: TdfolBinaryOperator,
    left: TdfolFormula,
    right: TdfolFormula,
  ): TdfolBinaryFormula {
    return { kind: 'binary', operator, left, right };
  }

  private peek(type: TdfolTokenType): boolean {
    return this.current().type === type;
  }

  private match(type: TdfolTokenType): boolean {
    if (!this.peek(type)) {
      return false;
    }
    this.index += 1;
    return true;
  }

  private expect(type: TdfolTokenType): TdfolToken {
    const token = this.current();
    if (token.type !== type) {
      throw new LogicParseError(`Expected ${type} but found ${token.type}`, {
        source: this.source,
        offset: token.position.offset,
        line: token.position.line,
        column: token.position.column,
        value: token.value,
      });
    }
    this.index += 1;
    return token;
  }

  private advance(): TdfolToken {
    const token = this.current();
    this.index += 1;
    return token;
  }

  private current(): TdfolToken {
    return this.tokens[this.index] || this.tokens[this.tokens.length - 1];
  }
}

function isTermToken(type: TdfolTokenType): boolean {
  return (
    type === 'IDENTIFIER' ||
    type === 'NUMBER' ||
    type === 'AND' ||
    type === 'OR' ||
    type === 'NOT' ||
    type === 'ALWAYS' ||
    type === 'EVENTUALLY' ||
    type === 'NEXT' ||
    type === 'OBLIGATION' ||
    type === 'PERMISSION' ||
    type === 'PROHIBITION'
  );
}

interface DcecCall {
  name: string;
  args: string[];
}

const DCEC_BINARY_OPERATORS: Record<string, TdfolBinaryOperator> = {
  and: 'AND',
  or: 'OR',
  implies: 'IMPLIES',
  iff: 'IFF',
};

const DCEC_DEONTIC_OPERATORS: Record<string, string> = {
  obligation: 'O',
  permission: 'P',
  prohibition: 'F',
};

const DCEC_TEMPORAL_OPERATORS: Record<string, string> = {
  always: 'always',
  eventually: 'eventually',
  next: 'next',
};

function normalizeDcecExpression(expression: string, source: string): string {
  const call = parseDcecCall(expression);
  if (!call) {
    return expression;
  }

  const name = call.name.toLowerCase();
  if (name === 'forall' || name === 'exists') {
    const quantifier = name === 'forall' ? 'forall' : 'exists';
    const { variable, body } = normalizeDcecQuantifier(call, source);
    return `${quantifier} ${variable}. ${normalizeDcecExpression(body, source)}`;
  }
  if (name === 'not' || name === 'neg' || name === 'negation') {
    expectDcecArity(call, 1, source);
    return `not (${normalizeDcecExpression(call.args[0], source)})`;
  }

  const binary = DCEC_BINARY_OPERATORS[name];
  if (binary) {
    expectDcecArity(call, 2, source);
    return `(${normalizeDcecExpression(call.args[0], source)}) ${dcecBinarySymbol(binary)} (${normalizeDcecExpression(
      call.args[1],
      source,
    )})`;
  }

  const deontic = DCEC_DEONTIC_OPERATORS[name];
  if (deontic) {
    expectDcecArity(call, 1, source);
    return `${deontic}(${normalizeDcecExpression(call.args[0], source)})`;
  }

  const temporal = DCEC_TEMPORAL_OPERATORS[name];
  if (temporal) {
    expectDcecArity(call, 1, source);
    return `${temporal}(${normalizeDcecExpression(call.args[0], source)})`;
  }

  return expression;
}

function normalizeDcecQuantifier(
  call: DcecCall,
  source: string,
): { variable: string; body: string } {
  if (call.args.length === 2) {
    return { variable: call.args[0], body: call.args[1] };
  }
  if (call.args.length === 3) {
    return { variable: `${call.args[0]}:${call.args[1]}`, body: call.args[2] };
  }
  throw new LogicParseError(`${call.name} expects 2 or 3 arguments`, { source, value: call.name });
}

function parseDcecCall(expression: string): DcecCall | null {
  const open = expression.indexOf('(');
  if (open <= 0 || !expression.endsWith(')')) {
    return null;
  }
  const name = expression.slice(0, open).trim();
  if (!/^[A-Za-z_][A-Za-z0-9_]*$/.test(name)) {
    return null;
  }
  const body = expression.slice(open + 1, -1);
  const args = splitDcecArgs(body);
  if (!args) {
    return null;
  }
  return { name, args };
}

function splitDcecArgs(body: string): string[] | null {
  const args: string[] = [];
  let depth = 0;
  let start = 0;
  for (let index = 0; index < body.length; index += 1) {
    const char = body[index];
    if (char === '(') {
      depth += 1;
    } else if (char === ')') {
      depth -= 1;
      if (depth < 0) {
        return null;
      }
    } else if (char === ',' && depth === 0) {
      args.push(body.slice(start, index).trim());
      start = index + 1;
    }
  }
  const finalArg = body.slice(start).trim();
  if (finalArg.length > 0) {
    args.push(finalArg);
  }
  return depth === 0 ? args : null;
}

function expectDcecArity(call: DcecCall, arity: number, source: string): void {
  if (call.args.length !== arity) {
    throw new LogicParseError(`${call.name} expects ${arity} arguments`, {
      source,
      value: call.name,
    });
  }
}

function dcecBinarySymbol(operator: TdfolBinaryOperator): string {
  switch (operator) {
    case 'AND':
      return 'and';
    case 'OR':
      return 'or';
    case 'IMPLIES':
      return '->';
    case 'IFF':
      return '<->';
    default:
      throw new LogicParseError(`Unsupported DCEC binary operator: ${operator}`);
  }
}

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

export function parseCecExpression(source: string): CecExpression {
  return new CecParser(source).parse();
}

export function validateCecExpression(source: string): { ok: true; expression: CecExpression } | { ok: false; error: string } {
  try {
    return { ok: true, expression: parseCecExpression(source) };
  } catch (error) {
    return {
      ok: false,
      error: error instanceof Error ? error.message : 'Unable to parse CEC expression.',
    };
  }
}

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

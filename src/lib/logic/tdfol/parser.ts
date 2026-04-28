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
    let left = this.parseAnd();
    while (this.match('OR')) {
      left = this.binary('OR', left, this.parseAnd());
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
    }

    if (token.type === 'NUMBER') {
      return { kind: 'constant', name, sort };
    }

    if (this.boundVariables.includes(name) || /^[a-z]$/.test(name)) {
      return { kind: 'variable', name, sort };
    }
    return { kind: 'constant', name, sort };
  }

  private binary(operator: TdfolBinaryOperator, left: TdfolFormula, right: TdfolFormula): TdfolBinaryFormula {
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

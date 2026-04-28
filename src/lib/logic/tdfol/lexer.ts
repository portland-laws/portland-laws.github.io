import { LogicParseError } from '../errors';
import type { ParsePosition } from '../types';

export type TdfolTokenType =
  | 'AND'
  | 'OR'
  | 'NOT'
  | 'IMPLIES'
  | 'IFF'
  | 'XOR'
  | 'FORALL'
  | 'EXISTS'
  | 'OBLIGATION'
  | 'PERMISSION'
  | 'PROHIBITION'
  | 'ALWAYS'
  | 'EVENTUALLY'
  | 'NEXT'
  | 'LPAREN'
  | 'RPAREN'
  | 'COMMA'
  | 'DOT'
  | 'COLON'
  | 'IDENTIFIER'
  | 'NUMBER'
  | 'EOF';

export interface TdfolToken {
  type: TdfolTokenType;
  value: string;
  position: ParsePosition;
}

const WORD_TOKENS: Record<string, TdfolTokenType> = {
  forall: 'FORALL',
  exists: 'EXISTS',
  and: 'AND',
  or: 'OR',
  not: 'NOT',
  always: 'ALWAYS',
  eventually: 'EVENTUALLY',
  next: 'NEXT',
};

export function lexTdfol(source: string): TdfolToken[] {
  const tokens: TdfolToken[] = [];
  let offset = 0;
  let line = 1;
  let column = 1;

  const position = (): ParsePosition => ({ offset, line, column });

  const advance = (count = 1) => {
    for (let index = 0; index < count; index += 1) {
      const char = source[offset];
      offset += 1;
      if (char === '\n') {
        line += 1;
        column = 1;
      } else {
        column += 1;
      }
    }
  };

  const push = (type: TdfolTokenType, value: string, start: ParsePosition) => {
    tokens.push({ type, value, position: start });
  };

  while (offset < source.length) {
    const char = source[offset];
    if (/\s/.test(char)) {
      advance();
      continue;
    }

    const start = position();
    const two = source.slice(offset, offset + 2);
    const three = source.slice(offset, offset + 3);

    if (three === '<->' || three === '<=>') {
      push('IFF', three, start);
      advance(3);
      continue;
    }
    if (two === '->' || two === '=>') {
      push('IMPLIES', two, start);
      advance(2);
      continue;
    }
    if (two === '[]') {
      push('ALWAYS', two, start);
      advance(2);
      continue;
    }
    if (two === '<>') {
      push('EVENTUALLY', two, start);
      advance(2);
      continue;
    }

    if (/[0-9]/.test(char)) {
      const match = source.slice(offset).match(/^[0-9]+(?:\.[0-9]+)?/);
      if (!match) {
        throw new LogicParseError('Invalid number token', { offset });
      }
      push('NUMBER', match[0], start);
      advance(match[0].length);
      continue;
    }

    if (/[A-Za-z_]/.test(char)) {
      const match = source.slice(offset).match(/^[A-Za-z_][A-Za-z0-9_]*/);
      if (!match) {
        throw new LogicParseError('Invalid identifier token', { offset });
      }
      const word = match[0];
      const wordToken = WORD_TOKENS[word.toLowerCase()];
      push(wordToken || deonticOrIdentifier(word), word, start);
      advance(word.length);
      continue;
    }

    const single = singleCharToken(char);
    if (single) {
      push(single, char, start);
      advance();
      continue;
    }

    throw new LogicParseError(`Unexpected character "${char}"`, { offset, line, column });
  }

  tokens.push({ type: 'EOF', value: '', position: position() });
  return tokens;
}

function singleCharToken(char: string): TdfolTokenType | null {
  switch (char) {
    case '∧':
    case '&':
    case '^':
      return 'AND';
    case '∨':
    case '|':
      return 'OR';
    case '¬':
    case '~':
    case '!':
      return 'NOT';
    case '→':
      return 'IMPLIES';
    case '↔':
      return 'IFF';
    case '⊕':
      return 'XOR';
    case '∀':
      return 'FORALL';
    case '∃':
      return 'EXISTS';
    case '□':
      return 'ALWAYS';
    case '◊':
    case '◇':
      return 'EVENTUALLY';
    case 'O':
      return 'OBLIGATION';
    case 'P':
      return 'PERMISSION';
    case 'F':
      return 'PROHIBITION';
    case 'X':
      return 'NEXT';
    case '(':
      return 'LPAREN';
    case ')':
      return 'RPAREN';
    case ',':
      return 'COMMA';
    case '.':
      return 'DOT';
    case ':':
      return 'COLON';
    default:
      return null;
  }
}

function deonticOrIdentifier(word: string): TdfolTokenType {
  if (word === 'O') {
    return 'OBLIGATION';
  }
  if (word === 'P') {
    return 'PERMISSION';
  }
  if (word === 'F') {
    return 'PROHIBITION';
  }
  if (word === 'X') {
    return 'NEXT';
  }
  return 'IDENTIFIER';
}

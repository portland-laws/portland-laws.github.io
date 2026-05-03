const SYMBOL_REPLACEMENTS: Record<string, string> = {
  '<->': 'ifAndOnlyIf',
  '->': 'implies',
  '>=': 'greaterOrEqual',
  '<=': 'lessOrEqual',
  '===': 'tautology',
  '==': 'equals',
  '=': 'equals',
  '>': 'greater',
  '<': 'less',
  '^': 'exponent',
  '*': '*',
  '/': 'divide',
  '+': 'add',
  '-': '-',
  '&': '&',
  '|': '|',
  '~': 'not',
};

const DCEC_SYMBOLS = Object.keys(SYMBOL_REPLACEMENTS).sort((left, right) => right.length - left.length);

export function stripDcecWhitespace(expression: string): string {
  let text = expression.trim();
  text = text.replaceAll('[', ' [').replaceAll(']', '] ');
  text = text.replaceAll(',', ' ');

  while (true) {
    const previousLength = text.length;
    text = text.replaceAll('  ', ' ').replaceAll('( ', '(').replaceAll(' )', ')');
    if (previousLength === text.length) {
      break;
    }
  }

  return text.replaceAll(')(', ') (').replaceAll(' ', ',');
}

export function stripDcecComments(expression: string): string {
  const commentIndex = expression.indexOf('#');
  return commentIndex === -1 ? expression : expression.slice(0, commentIndex);
}

export function removeDcecSemicolonComments(expression: string): string {
  const commentIndex = expression.indexOf(';');
  return commentIndex === -1 ? expression : expression.slice(0, commentIndex);
}

export function checkDcecParens(expression: string): boolean {
  let depth = 0;
  for (let index = 0; index < expression.length; index += 1) {
    const char = expression[index];
    if (char === '(') {
      depth += 1;
    } else if (char === ')') {
      depth -= 1;
      if (depth < 0) {
        return false;
      }
    }
  }
  return depth === 0;
}

export function getMatchingDcecCloseParen(input: string, openParenIndex = 0): number | undefined {
  if (openParenIndex < 0 || openParenIndex >= input.length || input[openParenIndex] !== '(') {
    return undefined;
  }

  let depth = 0;
  for (let index = openParenIndex; index < input.length; index += 1) {
    const char = input[index];
    if (char === '(') {
      depth += 1;
    } else if (char === ')') {
      depth -= 1;
      if (depth === 0) {
        return index;
      }
    }
  }

  return undefined;
}

export function consolidateDcecParens(expression: string): string {
  const text = `(${expression})`;
  const deleteIndexes = new Set<number>();
  let firstParen = 0;

  while (firstParen < text.length) {
    firstParen = text.indexOf('((', firstParen);
    if (firstParen === -1) {
      break;
    }

    const secondOpen = firstParen + 1;
    const firstClose = getMatchingDcecCloseParen(text, firstParen);
    const secondClose = getMatchingDcecCloseParen(text, secondOpen);
    if (firstClose !== undefined && secondClose !== undefined && firstClose === secondClose + 1) {
      deleteIndexes.add(firstParen);
      deleteIndexes.add(firstClose);
    }
    firstParen += 1;
  }

  let result = Array.from(text).filter((_, index) => !deleteIndexes.has(index)).join('');
  if (result.includes(' ')) {
    const innerAtomPattern = /(?<![A-Za-z0-9_])\(([A-Za-z_][A-Za-z0-9_]*)\)(?![A-Za-z0-9_])/g;
    let previous: string | undefined;
    while (previous !== result) {
      previous = result;
      result = result.replace(innerAtomPattern, '$1');
    }
  }

  return result;
}

export function tuckDcecFunctions(expression: string): string {
  let result = '';
  let index = 0;

  while (index < expression.length) {
    const char = expression[index];
    if (isIdentifierStart(char)) {
      const nameStart = index;
      index += 1;
      while (index < expression.length && isIdentifierPart(expression[index])) {
        index += 1;
      }

      const name = expression.slice(nameStart, index);
      if (index < expression.length && expression[index] === '(') {
        const closeParen = getMatchingDcecCloseParen(expression, index);
        if (closeParen !== undefined) {
          const args = tuckFunctionArguments(expression.slice(index + 1, closeParen));
          if (name === 'not' || name === 'negate') {
            result += `(${name},(${args}))`;
          } else {
            result += `(${name},${args})`;
          }
          index = closeParen + 1;
          continue;
        }
      }

      result += name;
      continue;
    }

    result += char;
    index += 1;
  }

  return result.replaceAll('``', '`').replaceAll(',,', ',').replaceAll('`', ' ');
}

export function functorizeDcecSymbols(expression: string): string {
  let result = '';
  let index = 0;

  while (index < expression.length) {
    const symbol = DCEC_SYMBOLS.find((candidate) => expression.startsWith(candidate, index));
    if (symbol !== undefined) {
      result += ` ${SYMBOL_REPLACEMENTS[symbol]} `;
      index += symbol.length;
    } else {
      result += expression[index];
      index += 1;
    }
  }

  return result.replaceAll('( ', '(');
}

export function cleanDcecExpression(expression: string): string {
  const uncommented = removeDcecSemicolonComments(stripDcecComments(expression)).trim();
  if (uncommented.length === 0 || !checkDcecParens(uncommented)) {
    return '';
  }

  const functorized = functorizeDcecSymbols(uncommented);
  const tucked = tuckDcecFunctions(functorized);
  return consolidateDcecParens(stripDcecWhitespace(tucked));
}

function tuckFunctionArguments(input: string): string {
  const tucked = tuckDcecFunctions(input);
  const parts = splitTopLevelArguments(tucked);
  return parts.length === 0 ? tucked.trim() : parts.join(',');
}

function splitTopLevelArguments(input: string): Array<string> {
  const parts: Array<string> = [];
  let depth = 0;
  let start = 0;

  for (let index = 0; index < input.length; index += 1) {
    const char = input[index];
    if (char === '(') {
      depth += 1;
    } else if (char === ')') {
      depth -= 1;
    } else if (char === ',' && depth === 0) {
      parts.push(input.slice(start, index).trim());
      start = index + 1;
    }
  }

  const finalPart = input.slice(start).trim();
  if (finalPart.length > 0) {
    parts.push(finalPart);
  }
  return parts;
}

function isIdentifierStart(value: string | undefined): boolean {
  return value !== undefined && /[A-Za-z_]/.test(value);
}

function isIdentifierPart(value: string | undefined): boolean {
  return value !== undefined && /[A-Za-z0-9_]/.test(value);
}

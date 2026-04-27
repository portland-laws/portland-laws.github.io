export function stripDcecWhitespace(expression: string): string {
  let text = expression.trim();
  text = text.replaceAll('[', ' [').replaceAll(']', '] ');
  text = text.replaceAll(',', ' ');

  while (true) {
    const previousLength = text.length;
    text = text.replaceAll('  ', ' ').replaceAll('( ', '(').replaceAll(' )', ')');
    if (previousLength === text.length) break;
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
  return countChar(expression, '(') === countChar(expression, ')');
}

export function getMatchingDcecCloseParen(input: string, openParenIndex = 0): number | undefined {
  let parenCounter = 1;
  let currentIndex = openParenIndex;
  if (currentIndex === -1 || input[currentIndex] !== '(') return undefined;

  while (parenCounter > 0) {
    const closeIndex = input.indexOf(')', currentIndex + 1);
    const openIndex = input.indexOf('(', currentIndex + 1);

    if ((openIndex < closeIndex || closeIndex === -1) && openIndex !== -1) {
      currentIndex = openIndex;
      parenCounter += 1;
    } else if ((closeIndex < openIndex || openIndex === -1) && closeIndex !== -1) {
      currentIndex = closeIndex;
      parenCounter -= 1;
    } else {
      return undefined;
    }
  }
  return currentIndex;
}

export function consolidateDcecParens(expression: string): string {
  const text = `(${expression})`;
  const deleteIndexes = new Set<number>();
  let firstParen = 0;

  while (firstParen < text.length) {
    firstParen = text.indexOf('((', firstParen);
    if (firstParen === -1) break;
    const secondOpen = firstParen + 1;
    const firstClose = getMatchingDcecCloseParen(text, firstParen);
    const secondClose = getMatchingDcecCloseParen(text, secondOpen);
    if (firstClose !== undefined && secondClose !== undefined && firstClose === secondClose + 1) {
      deleteIndexes.add(firstParen);
      deleteIndexes.add(firstClose);
    }
    firstParen += 1;
  }

  let result = [...text].filter((_, index) => !deleteIndexes.has(index)).join('');
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
  let firstParen = 0;
  let newIndex = 0;
  let temp = '';
  let source = expression;

  while (firstParen < source.length) {
    firstParen = source.indexOf('(', firstParen);
    if (firstParen === -1) break;

    const previous = source[firstParen - 1];
    if (previous !== undefined && ![',', ' ', '(', ')'].includes(previous)) {
      let funcStart = firstParen - 1;
      while (funcStart >= 0) {
        if (source[funcStart] === ',' || source[funcStart] === '(') {
          funcStart += 1;
          break;
        }
        funcStart -= 1;
      }
      if (funcStart === -1) funcStart = 0;

      const funcName = source.slice(funcStart, firstParen);
      if (funcName === 'not' || funcName === 'negate') {
        const adder = `${source.slice(newIndex, funcStart)}(${funcName},(`;
        const closeParen = getMatchingDcecCloseParen(source, funcStart + funcName.length);
        if (closeParen !== undefined) {
          source = `${source.slice(0, funcStart)}${source.slice(funcStart, closeParen)}))${source.slice(closeParen + 1)}`;
        }
        temp += adder;
        newIndex += adder.length - 2;
      } else {
        const adder = `${source.slice(newIndex, funcStart)}(${funcName},`;
        temp += adder;
        newIndex += adder.length - 1;
      }
    }
    firstParen += 1;
  }

  return `${temp}${source.slice(newIndex)}`
    .replaceAll('``', '`')
    .replaceAll(',,', ',')
    .replaceAll('`', ' ');
}

export function functorizeDcecSymbols(expression: string): string {
  const symbols = ['^', '*', '/', '+', '<->', '->', '-', '&', '|', '~', '>=', '==', '<=', '===', '=', '>', '<'];
  const symbolMap: Record<string, string> = {
    '^': 'exponent',
    '*': '*',
    '/': 'divide',
    '+': 'add',
    '-': '-',
    '&': '&',
    '|': '|',
    '~': 'not',
    '->': 'implies',
    '<->': 'ifAndOnlyIf',
    '>': 'greater',
    '<': 'less',
    '>=': 'greaterOrEqual',
    '<=': 'lessOrEqual',
    '=': 'equals',
    '==': 'equals',
    '===': 'tautology',
  };
  let result = expression;
  for (const symbol of symbols) {
    result = result.replaceAll(symbol, ` ${symbolMap[symbol]} `);
  }
  return result.replaceAll('( ', '(');
}

export function cleanDcecExpression(expression: string): string {
  return consolidateDcecParens(stripDcecWhitespace(stripDcecComments(expression)));
}

function countChar(value: string, char: string): number {
  return [...value].filter((candidate) => candidate === char).length;
}

import type { CecExpression } from './ast';

export function formatCecExpression(expression: CecExpression): string {
  switch (expression.kind) {
    case 'atom':
      return expression.name;
    case 'application':
      return `(${[expression.name, ...expression.args.map(formatCecExpression)].join(' ')})`;
    case 'quantified':
      return `(${expression.quantifier} ${expression.variable} ${formatCecExpression(expression.expression)})`;
    case 'unary':
      return `(${expression.operator} ${formatCecExpression(expression.expression)})`;
    case 'binary':
      return `(${expression.operator} ${formatCecExpression(expression.left)} ${formatCecExpression(expression.right)})`;
  }
}

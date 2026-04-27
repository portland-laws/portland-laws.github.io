export type CecTerm = CecAtom | CecApplication;

export interface CecAtom {
  kind: 'atom';
  name: string;
}

export interface CecApplication {
  kind: 'application';
  name: string;
  args: CecExpression[];
}

export type CecExpression =
  | CecAtom
  | CecApplication
  | CecQuantifiedExpression
  | CecUnaryExpression
  | CecBinaryExpression;

export type CecQuantifier = 'forall' | 'exists';
export type CecUnaryOperator = 'not' | 'O' | 'P' | 'F' | 'always' | 'eventually' | 'next';
export type CecBinaryOperator = 'implies' | 'and' | 'or' | 'iff' | 'xor';

export interface CecQuantifiedExpression {
  kind: 'quantified';
  quantifier: CecQuantifier;
  variable: string;
  expression: CecExpression;
}

export interface CecUnaryExpression {
  kind: 'unary';
  operator: CecUnaryOperator;
  expression: CecExpression;
}

export interface CecBinaryExpression {
  kind: 'binary';
  operator: CecBinaryOperator;
  left: CecExpression;
  right: CecExpression;
}

export function collectCecAtoms(expression: CecExpression): Set<string> {
  const atoms = new Set<string>();
  visitCecExpression(expression, (node) => {
    if (node.kind === 'atom') {
      atoms.add(node.name);
    }
  });
  return atoms;
}

export function visitCecExpression(
  expression: CecExpression,
  visitor: (expression: CecExpression) => void,
) {
  visitor(expression);
  switch (expression.kind) {
    case 'atom':
      return;
    case 'application':
      expression.args.forEach((arg) => visitCecExpression(arg, visitor));
      return;
    case 'quantified':
    case 'unary':
      visitCecExpression(expression.expression, visitor);
      return;
    case 'binary':
      visitCecExpression(expression.left, visitor);
      visitCecExpression(expression.right, visitor);
      return;
  }
}

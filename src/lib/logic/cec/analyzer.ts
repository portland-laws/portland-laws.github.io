import type {
  CecApplication,
  CecExpression,
  CecQuantifier,
  CecUnaryOperator,
} from './ast';
import { visitCecExpression } from './ast';

export interface CecAnalysis {
  predicates: string[];
  atoms: string[];
  sectionRefs: string[];
  quantifiers: CecQuantifier[];
  deonticOperators: CecUnaryOperator[];
  temporalOperators: CecUnaryOperator[];
  maxDepth: number;
  nodeCount: number;
}

const DEONTIC_OPERATORS = new Set<CecUnaryOperator>(['O', 'P', 'F']);
const TEMPORAL_OPERATORS = new Set<CecUnaryOperator>(['always', 'eventually', 'next']);

export function analyzeCecExpression(expression: CecExpression): CecAnalysis {
  const predicates = new Set<string>();
  const atoms = new Set<string>();
  const sectionRefs = new Set<string>();
  const quantifiers: CecQuantifier[] = [];
  const deonticOperators: CecUnaryOperator[] = [];
  const temporalOperators: CecUnaryOperator[] = [];
  let nodeCount = 0;

  visitCecExpression(expression, (node) => {
    nodeCount += 1;
    switch (node.kind) {
      case 'application':
        predicates.add(node.name);
        collectApplicationAtoms(node, atoms, sectionRefs);
        return;
      case 'atom':
        atoms.add(node.name);
        if (isPortlandSectionRef(node.name)) {
          sectionRefs.add(node.name);
        }
        return;
      case 'quantified':
        quantifiers.push(node.quantifier);
        return;
      case 'unary':
        if (DEONTIC_OPERATORS.has(node.operator)) {
          deonticOperators.push(node.operator);
        }
        if (TEMPORAL_OPERATORS.has(node.operator)) {
          temporalOperators.push(node.operator);
        }
        return;
      case 'binary':
        return;
    }
  });

  return {
    predicates: [...predicates].sort(),
    atoms: [...atoms].sort(),
    sectionRefs: [...sectionRefs].sort(),
    quantifiers,
    deonticOperators,
    temporalOperators,
    maxDepth: measureCecDepth(expression),
    nodeCount,
  };
}

export function measureCecDepth(expression: CecExpression): number {
  switch (expression.kind) {
    case 'atom':
      return 1;
    case 'application':
      return 1 + Math.max(0, ...expression.args.map(measureCecDepth));
    case 'quantified':
    case 'unary':
      return 1 + measureCecDepth(expression.expression);
    case 'binary':
      return 1 + Math.max(measureCecDepth(expression.left), measureCecDepth(expression.right));
  }
}

function collectApplicationAtoms(
  application: CecApplication,
  atoms: Set<string>,
  sectionRefs: Set<string>,
) {
  application.args.forEach((arg) => {
    if (arg.kind !== 'atom') {
      return;
    }
    atoms.add(arg.name);
    if (isPortlandSectionRef(arg.name)) {
      sectionRefs.add(arg.name);
    }
  });
}

function isPortlandSectionRef(value: string) {
  return /^portland_city_code_[a-z0-9]+(?:_[a-z0-9]+)+$/i.test(value);
}

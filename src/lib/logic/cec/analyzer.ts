import type {
  CecApplication,
  CecBinaryOperator,
  CecExpression,
  CecQuantifier,
  CecUnaryOperator,
} from './ast';
import { visitCecExpression } from './ast';
import { parseCecExpression } from './parser';

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

export type ExternalProverFormulaClass =
  | 'propositional'
  | 'first-order'
  | 'modal-deontic'
  | 'temporal'
  | 'unsupported';
export type ExternalProverDecidableFragment =
  | 'propositional'
  | 'monadic-first-order'
  | 'guarded-first-order'
  | 'modal-temporal'
  | 'unknown';

export interface ExternalProverAnalyzerMetadata {
  sourcePythonModule: 'logic/external_provers/formula_analyzer.py';
  runtime: 'browser-native-typescript';
  browserNative: true;
  pythonRuntime: false;
  serverRuntime: false;
}

export interface ExternalProverFormulaAnalysis {
  ok: boolean;
  formula: string;
  formulaClass: ExternalProverFormulaClass;
  decidableFragment: ExternalProverDecidableFragment;
  predicates: string[];
  constants: string[];
  variables: string[];
  quantifiers: CecQuantifier[];
  unaryOperators: CecUnaryOperator[];
  binaryOperators: CecBinaryOperator[];
  arityByPredicate: Record<string, number>;
  maxDepth: number;
  nodeCount: number;
  errors: string[];
  metadata: ExternalProverAnalyzerMetadata;
}

const DEONTIC_OPERATORS = new Set<CecUnaryOperator>(['O', 'P', 'F']);
const TEMPORAL_OPERATORS = new Set<CecUnaryOperator>(['always', 'eventually', 'next']);
const ANALYZER_METADATA = {
  sourcePythonModule: 'logic/external_provers/formula_analyzer.py',
  runtime: 'browser-native-typescript',
  browserNative: true,
  pythonRuntime: false,
  serverRuntime: false,
} satisfies ExternalProverAnalyzerMetadata;

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

export function analyzeExternalProverFormula(formula: string): ExternalProverFormulaAnalysis {
  try {
    return analyzeExternalProverExpression(parseCecExpression(formula), formula);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unable to parse formula.';
    return emptyExternalProverAnalysis(formula, message);
  }
}

export function analyzeExternalProverExpression(
  expression: CecExpression,
  formula = '',
): ExternalProverFormulaAnalysis {
  const predicates = new Set<string>();
  const variables = new Set<string>();
  const quantifiers: CecQuantifier[] = [];
  const unaryOperators: CecUnaryOperator[] = [];
  const binaryOperators: CecBinaryOperator[] = [];
  const arityByPredicate: Record<string, number> = {};
  const atoms = new Set<string>();
  let nodeCount = 0;

  visitCecExpression(expression, (node) => {
    nodeCount += 1;
    if (node.kind === 'atom') {
      atoms.add(node.name);
      return;
    }
    if (node.kind === 'application') {
      predicates.add(node.name);
      arityByPredicate[node.name] = Math.max(arityByPredicate[node.name] ?? 0, node.args.length);
      return;
    }
    if (node.kind === 'quantified') {
      quantifiers.push(node.quantifier);
      variables.add(node.variable);
      return;
    }
    if (node.kind === 'unary') {
      unaryOperators.push(node.operator);
      return;
    }
    binaryOperators.push(node.operator);
  });

  const constants = [...atoms].filter((atom) => !variables.has(atom));
  return {
    ok: true,
    formula,
    formulaClass: classifyFormula(quantifiers, unaryOperators, predicates),
    decidableFragment: classifyDecidableFragment(quantifiers, unaryOperators, arityByPredicate),
    predicates: [...predicates].sort(),
    constants: constants.sort(),
    variables: [...variables].sort(),
    quantifiers,
    unaryOperators,
    binaryOperators,
    arityByPredicate,
    maxDepth: measureCecDepth(expression),
    nodeCount,
    errors: [],
    metadata: ANALYZER_METADATA,
  };
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

function classifyFormula(
  quantifiers: CecQuantifier[],
  unaryOperators: CecUnaryOperator[],
  predicates: Set<string>,
): ExternalProverFormulaClass {
  if (unaryOperators.some((operator) => TEMPORAL_OPERATORS.has(operator))) {
    return 'temporal';
  }
  if (unaryOperators.some((operator) => DEONTIC_OPERATORS.has(operator))) {
    return 'modal-deontic';
  }
  if (quantifiers.length > 0 || predicates.size > 0) {
    return 'first-order';
  }
  return 'propositional';
}

function classifyDecidableFragment(
  quantifiers: CecQuantifier[],
  unaryOperators: CecUnaryOperator[],
  arityByPredicate: Record<string, number>,
): ExternalProverDecidableFragment {
  if (
    unaryOperators.some(
      (operator) => DEONTIC_OPERATORS.has(operator) || TEMPORAL_OPERATORS.has(operator),
    )
  ) {
    return 'modal-temporal';
  }
  if (quantifiers.length === 0) {
    return 'propositional';
  }
  const arities = Object.values(arityByPredicate);
  if (arities.every((arity) => arity <= 1)) {
    return 'monadic-first-order';
  }
  if (arities.every((arity) => arity <= 2)) {
    return 'guarded-first-order';
  }
  return 'unknown';
}

function emptyExternalProverAnalysis(
  formula: string,
  error: string,
): ExternalProverFormulaAnalysis {
  return {
    ok: false,
    formula,
    formulaClass: 'unsupported',
    decidableFragment: 'unknown',
    predicates: [],
    constants: [],
    variables: [],
    quantifiers: [],
    unaryOperators: [],
    binaryOperators: [],
    arityByPredicate: {},
    maxDepth: 0,
    nodeCount: 0,
    errors: [error],
    metadata: ANALYZER_METADATA,
  };
}

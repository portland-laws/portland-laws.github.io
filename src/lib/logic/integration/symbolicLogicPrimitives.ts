import {
  BrowserNativeLogicSymbol,
  type LogicPrimitiveOutputFormat,
  SYMBOLIC_LOGIC_PRIMITIVES_METADATA,
} from './symbolic/symbolicLogicPrimitives';

export interface BrowserNativeLogicOperand {
  readonly value: string;
  readonly semantic?: boolean;
}

export const INTEGRATION_SYMBOLIC_LOGIC_PRIMITIVES_METADATA = {
  ...SYMBOLIC_LOGIC_PRIMITIVES_METADATA,
  sourcePythonModule: 'logic/integration/symbolic_logic_primitives.py',
  implementationModule: 'logic/integration/symbolic/symbolic_logic_primitives.py',
  parity: [
    ...SYMBOLIC_LOGIC_PRIMITIVES_METADATA.parity,
    'root_integration_module_compatibility',
    'python_style_free_function_exports',
  ],
} as const;

export class BrowserNativeIntegrationLogicSymbol {
  readonly metadata = INTEGRATION_SYMBOLIC_LOGIC_PRIMITIVES_METADATA;
  readonly value: string;
  readonly semantic: boolean;

  constructor(value: string, semantic = true) {
    this.value = typeof value === 'string' ? value : String(value);
    this.semantic = semantic;
  }

  toFol(
    outputFormat: LogicPrimitiveOutputFormat = 'symbolic',
  ): BrowserNativeIntegrationLogicSymbol {
    return this.wrap(this.base().toFol(outputFormat));
  }

  to_fol(
    outputFormat: LogicPrimitiveOutputFormat = 'symbolic',
  ): BrowserNativeIntegrationLogicSymbol {
    return this.toFol(outputFormat);
  }

  extractQuantifiers(): BrowserNativeIntegrationLogicSymbol {
    return this.wrap(this.base().extractQuantifiers());
  }

  extract_quantifiers(): BrowserNativeIntegrationLogicSymbol {
    return this.extractQuantifiers();
  }

  extractPredicates(): BrowserNativeIntegrationLogicSymbol {
    return this.wrap(this.base().extractPredicates());
  }

  extract_predicates(): BrowserNativeIntegrationLogicSymbol {
    return this.extractPredicates();
  }

  logicalAnd(other: BrowserNativeLogicOperand): BrowserNativeIntegrationLogicSymbol {
    return this.wrap(this.base().logicalAnd(toBaseSymbol(other)));
  }

  logical_and(other: BrowserNativeLogicOperand): BrowserNativeIntegrationLogicSymbol {
    return this.logicalAnd(other);
  }

  logicalOr(other: BrowserNativeLogicOperand): BrowserNativeIntegrationLogicSymbol {
    return this.wrap(this.base().logicalOr(toBaseSymbol(other)));
  }

  logical_or(other: BrowserNativeLogicOperand): BrowserNativeIntegrationLogicSymbol {
    return this.logicalOr(other);
  }

  implies(other: BrowserNativeLogicOperand): BrowserNativeIntegrationLogicSymbol {
    return this.wrap(this.base().implies(toBaseSymbol(other)));
  }

  negate(): BrowserNativeIntegrationLogicSymbol {
    return this.wrap(this.base().negate());
  }

  analyzeLogicalStructure(): BrowserNativeIntegrationLogicSymbol {
    return this.wrap(this.base().analyzeLogicalStructure());
  }

  analyze_logical_structure(): BrowserNativeIntegrationLogicSymbol {
    return this.analyzeLogicalStructure();
  }

  simplifyLogic(): BrowserNativeIntegrationLogicSymbol {
    return this.wrap(this.base().simplifyLogic());
  }

  simplify_logic(): BrowserNativeIntegrationLogicSymbol {
    return this.simplifyLogic();
  }

  private wrap(symbol: BrowserNativeLogicSymbol): BrowserNativeIntegrationLogicSymbol {
    return new BrowserNativeIntegrationLogicSymbol(symbol.value, symbol.semantic);
  }

  private base(): BrowserNativeLogicSymbol {
    return new BrowserNativeLogicSymbol(this.value, this.semantic);
  }
}

export const IntegrationLogicSymbol = BrowserNativeIntegrationLogicSymbol;
export const createIntegrationLogicSymbol = (
  text: string,
  semantic = true,
): BrowserNativeIntegrationLogicSymbol => new BrowserNativeIntegrationLogicSymbol(text, semantic);
export const create_integration_logic_symbol = createIntegrationLogicSymbol;
export const create_logic_symbol = createIntegrationLogicSymbol;
export const getIntegrationAvailablePrimitives = (): Array<string> => [
  'to_fol',
  'extract_quantifiers',
  'extract_predicates',
  'logical_and',
  'logical_or',
  'implies',
  'negate',
  'analyze_logical_structure',
  'simplify_logic',
];
export const get_integration_available_primitives = getIntegrationAvailablePrimitives;
export const get_available_primitives = getIntegrationAvailablePrimitives;

function toBaseSymbol(symbol: BrowserNativeLogicOperand): BrowserNativeLogicSymbol {
  return new BrowserNativeLogicSymbol(symbol.value, symbol.semantic ?? true);
}

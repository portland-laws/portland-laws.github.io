import {
  BrowserNativeSymbolicContracts,
  type SymbolicContractAnalysisResult,
  type SymbolicContractClause,
  type SymbolicContractClauseType,
} from './domain/symbolicContracts';

export type IntegrationSymbolicContractElement = SymbolicContractClauseType;

export interface IntegrationSymbolicContractClause {
  readonly element: IntegrationSymbolicContractElement;
  readonly text: string;
  readonly symbolicFormula: string;
  readonly confidence: number;
}

export interface IntegrationSymbolicContractResult {
  readonly accepted: boolean;
  readonly runtime: 'browser-native';
  readonly wasmCompatible: true;
  readonly serverCallsAllowed: false;
  readonly pythonRuntimeAllowed: false;
  readonly sourceText: string;
  readonly clauses: readonly IntegrationSymbolicContractClause[];
  readonly requiredElementsPresent: boolean;
  readonly missingRequiredElements: readonly IntegrationSymbolicContractElement[];
  readonly issues: readonly string[];
  readonly metadata: typeof INTEGRATION_SYMBOLIC_CONTRACTS_METADATA;
}

export const INTEGRATION_SYMBOLIC_CONTRACTS_METADATA = {
  sourcePythonModule: 'logic/integration/symbolic_contracts.py',
  browserNative: true,
  wasmCompatible: true,
  serverCallsAllowed: false,
  pythonRuntimeAllowed: false,
  runtimeDependencies: [],
  parity: [
    'top_level_symbolic_contract_adapter',
    'deterministic_contract_element_extraction',
    'formation_requirement_validation',
    'local_fail_closed_no_python_runtime',
  ],
} as const;

export class BrowserNativeIntegrationSymbolicContracts {
  readonly metadata = INTEGRATION_SYMBOLIC_CONTRACTS_METADATA;
  private readonly domainAnalyzer = new BrowserNativeSymbolicContracts();

  analyze(text: string): IntegrationSymbolicContractResult {
    const result = this.domainAnalyzer.analyze(text);
    return toIntegrationResult(result);
  }

  extract_contract_elements(text: string): readonly IntegrationSymbolicContractClause[] {
    return this.analyze(text).clauses;
  }

  validate_contract_formation(text: string): boolean {
    return this.analyze(text).requiredElementsPresent;
  }
}

export function analyzeIntegrationSymbolicContract(
  text: string,
): IntegrationSymbolicContractResult {
  return new BrowserNativeIntegrationSymbolicContracts().analyze(text);
}

export const create_symbolic_contracts = (): BrowserNativeIntegrationSymbolicContracts =>
  new BrowserNativeIntegrationSymbolicContracts();
export const analyze_symbolic_contract = analyzeIntegrationSymbolicContract;
export const analyze_symbolic_contracts = analyzeIntegrationSymbolicContract;

function toIntegrationResult(
  result: SymbolicContractAnalysisResult,
): IntegrationSymbolicContractResult {
  return {
    accepted: result.accepted,
    runtime: 'browser-native',
    wasmCompatible: true,
    serverCallsAllowed: false,
    pythonRuntimeAllowed: false,
    sourceText: result.sourceText,
    clauses: result.clauses.map(toIntegrationClause),
    requiredElementsPresent: result.formationComplete,
    missingRequiredElements: result.missingFormationElements,
    issues: result.issues.map((issue: string) =>
      issue.startsWith('missing formation elements:')
        ? issue.replace('missing formation elements:', 'missing required elements:')
        : issue,
    ),
    metadata: INTEGRATION_SYMBOLIC_CONTRACTS_METADATA,
  };
}

function toIntegrationClause(clause: SymbolicContractClause): IntegrationSymbolicContractClause {
  return {
    element: clause.clauseType,
    text: clause.text,
    symbolicFormula: clause.formula,
    confidence: clause.confidence,
  };
}

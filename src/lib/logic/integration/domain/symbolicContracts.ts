export type SymbolicContractClauseType =
  | 'offer'
  | 'acceptance'
  | 'consideration'
  | 'obligation'
  | 'condition'
  | 'breach'
  | 'remedy'
  | 'termination';

export interface SymbolicContractClause {
  readonly clauseType: SymbolicContractClauseType;
  readonly text: string;
  readonly formula: string;
  readonly confidence: number;
}

export interface SymbolicContractAnalysisResult {
  readonly accepted: boolean;
  readonly runtime: 'browser-native';
  readonly wasmCompatible: true;
  readonly serverCallsAllowed: false;
  readonly pythonRuntimeAllowed: false;
  readonly sourceText: string;
  readonly clauses: readonly SymbolicContractClause[];
  readonly formationComplete: boolean;
  readonly missingFormationElements: readonly SymbolicContractClauseType[];
  readonly issues: readonly string[];
  readonly metadata: typeof SYMBOLIC_CONTRACTS_METADATA;
}

export const SYMBOLIC_CONTRACTS_METADATA = {
  sourcePythonModule: 'logic/integration/domain/symbolic_contracts.py',
  browserNative: true,
  wasmCompatible: true,
  serverCallsAllowed: false,
  pythonRuntimeAllowed: false,
  runtimeDependencies: [],
  parity: [
    'deterministic_clause_classification',
    'contract_formation_validation',
    'local_fail_closed_analysis',
  ],
} as const;

const FORMATION: readonly SymbolicContractClauseType[] = ['offer', 'acceptance', 'consideration'];
const PATTERNS: readonly [SymbolicContractClauseType, string, RegExp][] = [
  ['offer', 'Offer', /\b(offer|proposal|proposes|bid|quote)\b/i],
  ['acceptance', 'Accept', /\b(accepts?|acceptance|agrees? to|assents?|approval)\b/i],
  [
    'consideration',
    'Consideration',
    /\b(consideration|payment|fee|price|exchange for|compensation)\b/i,
  ],
  ['obligation', 'Obligation', /\b(shall|must|required to|covenants? to|is obligated to)\b/i],
  ['condition', 'Condition', /\b(if|unless|provided that|conditioned on|subject to)\b/i],
  ['breach', 'Breach', /\b(breach|default|failure to|fails to|non[- ]performance)\b/i],
  ['remedy', 'Remedy', /\b(remedy|damages|specific performance|injunction|cure|relief)\b/i],
  ['termination', 'Terminate', /\b(terminate|termination|expire|cancellation|rescind)\b/i],
];

export class BrowserNativeSymbolicContracts {
  readonly metadata = SYMBOLIC_CONTRACTS_METADATA;

  analyze(text: string): SymbolicContractAnalysisResult {
    const sourceText = typeof text === 'string' ? text : '';
    const normalized = sourceText.replace(/\s+/g, ' ').trim();
    if (normalized.length < 3) return closed(sourceText, ['source text is required']);

    const clauses = normalized
      .split(/[.;\n]+/)
      .map((item: string) => item.trim())
      .filter((item: string) => item.length > 0)
      .flatMap(classifyClause);
    const present = new Set(clauses.map((clause: SymbolicContractClause) => clause.clauseType));
    const missingFormationElements = FORMATION.filter(
      (element: SymbolicContractClauseType) => !present.has(element),
    );
    const issues = [
      ...(clauses.length === 0 ? ['no symbolic contract clauses matched locally'] : []),
      ...(missingFormationElements.length > 0
        ? [`missing formation elements: ${missingFormationElements.join(', ')}`]
        : []),
    ];
    return {
      accepted: clauses.length > 0 && missingFormationElements.length === 0,
      runtime: 'browser-native',
      wasmCompatible: true,
      serverCallsAllowed: false,
      pythonRuntimeAllowed: false,
      sourceText,
      clauses,
      formationComplete: missingFormationElements.length === 0,
      missingFormationElements,
      issues,
      metadata: this.metadata,
    };
  }
}

export function analyzeSymbolicContract(text: string): SymbolicContractAnalysisResult {
  return new BrowserNativeSymbolicContracts().analyze(text);
}

export const create_symbolic_contracts = (): BrowserNativeSymbolicContracts =>
  new BrowserNativeSymbolicContracts();
export const analyze_symbolic_contract = analyzeSymbolicContract;
export const analyze_symbolic_contracts = analyzeSymbolicContract;

function classifyClause(text: string): readonly SymbolicContractClause[] {
  return PATTERNS.filter(([, , pattern]) => pattern.test(text)).map(([clauseType, predicate]) => ({
    clauseType,
    text,
    formula: `${predicate}(${toAtom(text)})`,
    confidence: Number(Math.min(0.96, 0.7 + text.split(/\s+/).length / 200).toFixed(2)),
  }));
}

function toAtom(text: string): string {
  const atom = text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .slice(0, 96);
  return atom.length > 0 ? atom : 'contract_clause';
}

function closed(sourceText: string, issues: readonly string[]): SymbolicContractAnalysisResult {
  return {
    accepted: false,
    runtime: 'browser-native',
    wasmCompatible: true,
    serverCallsAllowed: false,
    pythonRuntimeAllowed: false,
    sourceText,
    clauses: [],
    formationComplete: false,
    missingFormationElements: FORMATION,
    issues,
    metadata: SYMBOLIC_CONTRACTS_METADATA,
  };
}

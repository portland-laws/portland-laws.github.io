export interface LogicInventoryCoverageTask {
  readonly pythonArea: string;
  readonly uncoveredFiles: number;
  readonly task: string;
  readonly browserNative: true;
  readonly serverCallsAllowed: false;
  readonly pythonRuntimeAllowed: false;
}

export interface LogicInventoryReconciliation {
  readonly pythonInventoryFiles: 269;
  readonly typescriptWasmImplementationFiles: 253;
  readonly uncoveredPythonFiles: 16;
  readonly browserNative: true;
  readonly serverCallsAllowed: false;
  readonly pythonRuntimeAllowed: false;
  readonly tasks: readonly LogicInventoryCoverageTask[];
}

export interface AcceptedLogicParityEvidence {
  readonly area: string;
  readonly pythonBehavior: string;
  readonly acceptedWorkEvidence: string;
  readonly runtimeFiles: readonly string[];
  readonly validationFiles: readonly string[];
  readonly browserNative: true;
  readonly serverCallsAllowed: false;
  readonly pythonRuntimeAllowed: false;
}

export interface AcceptedLogicParityReview {
  readonly reviewedAgainstGoal: 'browser-native TypeScript/WASM logic port';
  readonly acceptedEvidenceCount: number;
  readonly missingParityTasks: readonly LogicInventoryCoverageTask[];
  readonly evidence: readonly AcceptedLogicParityEvidence[];
  readonly browserNative: true;
  readonly serverCallsAllowed: false;
  readonly pythonRuntimeAllowed: false;
}

export interface LogicPortParityMatrixEntry {
  readonly pythonLogicModules: string;
  readonly typescriptWasmFiles: readonly string[];
  readonly validationEvidence: readonly string[];
  readonly acceptedWork: readonly string[];
  readonly remainingBrowserNativeTasks: readonly string[];
  readonly browserNative: true;
  readonly serverCallsAllowed: false;
  readonly pythonRuntimeAllowed: false;
}

const UNCOVERED_TASKS: readonly LogicInventoryCoverageTask[] = [
  {
    pythonArea: 'logic/CEC/native grammar loading',
    uncoveredFiles: 2,
    task: 'Port CEC native grammar loader and external grammar registry semantics to deterministic in-memory TypeScript artifacts.',
    browserNative: true,
    serverCallsAllowed: false,
    pythonRuntimeAllowed: false,
  },
  {
    pythonArea: 'logic/CEC/native cognitive and modal rule groups',
    uncoveredFiles: 4,
    task: 'Complete CEC cognitive, deontic, modal, and base inference-rule parity using browser-native rule tables.',
    browserNative: true,
    serverCallsAllowed: false,
    pythonRuntimeAllowed: false,
  },
  {
    pythonArea: 'logic/CEC/native diagnostics',
    uncoveredFiles: 2,
    task: 'Port CEC native error-handling and namespace diagnostics as fail-closed TypeScript validation results.',
    browserNative: true,
    serverCallsAllowed: false,
    pythonRuntimeAllowed: false,
  },
  {
    pythonArea: 'logic/TDFOL P2P and visualization helpers',
    uncoveredFiles: 3,
    task: 'Replace TDFOL P2P, dashboard, and visualization helper surfaces with browser-local state and serializable exports.',
    browserNative: true,
    serverCallsAllowed: false,
    pythonRuntimeAllowed: false,
  },
  {
    pythonArea: 'logic/external_provers routing',
    uncoveredFiles: 3,
    task: 'Map remaining external prover routing modules to WASM-capable local adapters or explicit unsupported-local results.',
    browserNative: true,
    serverCallsAllowed: false,
    pythonRuntimeAllowed: false,
  },
  {
    pythonArea: 'logic/top-level operational scripts',
    uncoveredFiles: 2,
    task: 'Convert remaining operational benchmark and validation script behavior into browser/devtools TypeScript entry points.',
    browserNative: true,
    serverCallsAllowed: false,
    pythonRuntimeAllowed: false,
  },
];

const UNCOVERED_PYTHON_FILE_TOTAL = 16;

const ACCEPTED_LOGIC_PARITY_EVIDENCE: readonly AcceptedLogicParityEvidence[] = [
  {
    area: 'FOL and spaCy-style NLP extraction',
    pythonBehavior: 'logic/fol conversion and predicate extraction from natural language',
    acceptedWorkEvidence:
      '20260505T041556Z-preserved-direct-fol-browser-native-nlp-conversion-success-while-restoring-bridg',
    runtimeFiles: ['src/lib/logic/fol/textToFol.ts', 'src/lib/logic/fol/browserNativeNlp.ts'],
    validationFiles: ['src/lib/logic/fol/converter.test.ts', 'src/lib/logic/parity/parity.test.ts'],
    browserNative: true,
    serverCallsAllowed: false,
    pythonRuntimeAllowed: false,
  },
  {
    area: 'ML confidence scoring',
    pythonBehavior:
      'logic/ml_confidence.py feature extraction, scoring, training facade, and artifacts',
    acceptedWorkEvidence:
      '20260504T151908Z-ported-the-remaining-ml_confidence.py-slice-with-browser-native-deterministic-mo',
    runtimeFiles: ['src/lib/logic/mlConfidence.ts'],
    validationFiles: ['src/lib/logic/mlConfidence.test.ts'],
    browserNative: true,
    serverCallsAllowed: false,
    pythonRuntimeAllowed: false,
  },
  {
    area: 'ZKP and verifier surfaces',
    pythonBehavior: 'logic/zkp prover, verifier, witness, public-input, registry, and EVM helpers',
    acceptedWorkEvidence:
      '20260505T041104Z-ported-the-remaining-zkp_verifier.py-facade-surface-for-structured-and-batch-ver',
    runtimeFiles: ['src/lib/logic/zkp'],
    validationFiles: [
      'src/lib/logic/zkp/facade.test.ts',
      'src/lib/logic/zkp/witnessManager.test.ts',
    ],
    browserNative: true,
    serverCallsAllowed: false,
    pythonRuntimeAllowed: false,
  },
  {
    area: 'CEC, DCEC, and deontic reasoning',
    pythonBehavior:
      'logic/CEC native parsing, grammar, event calculus, proof routing, and deontic rules',
    acceptedWorkEvidence:
      '20260504T021854Z-ported-the-remaining-dcec-nl_converter-grammar-surface-to-a-browser-native-types',
    runtimeFiles: ['src/lib/logic/cec', 'src/lib/logic/deontic', 'src/lib/logic/integration'],
    validationFiles: [
      'src/lib/logic/deontic/parser.test.ts',
      'src/lib/logic/integration/bridge.test.ts',
    ],
    browserNative: true,
    serverCallsAllowed: false,
    pythonRuntimeAllowed: false,
  },
  {
    area: 'Public API, CLI/devtools, config, monitoring, and security',
    pythonBehavior:
      'top-level logic API, operational helpers, telemetry, validation, and security modules',
    acceptedWorkEvidence:
      '20260505T022813Z-ported-remaining-security-rate_limiting.py-parity-into-the-browser-native-typesc',
    runtimeFiles: ['src/lib/logic/api.ts', 'src/lib/logic/cli.ts', 'src/lib/logic/security'],
    validationFiles: ['src/lib/logic/cli.test.ts', 'src/lib/logic/security/security.test.ts'],
    browserNative: true,
    serverCallsAllowed: false,
    pythonRuntimeAllowed: false,
  },
];

const LOGIC_PORT_PARITY_MATRIX: readonly LogicPortParityMatrixEntry[] = [
  {
    pythonLogicModules: 'logic/fol and logic/deontic',
    typescriptWasmFiles: [
      'src/lib/logic/fol',
      'src/lib/logic/deontic',
      'src/lib/logic/mlConfidence.ts',
    ],
    validationEvidence: [
      'src/lib/logic/fol/converter.test.ts',
      'src/lib/logic/deontic/parser.test.ts',
      'src/lib/logic/mlConfidence.test.ts',
      'src/lib/logic/parity/parity.test.ts',
    ],
    acceptedWork: [
      'FOL and spaCy-style NLP extraction',
      'ML confidence scoring',
      'CEC, DCEC, and deontic reasoning',
    ],
    remainingBrowserNativeTasks: [
      'Load optional browser-native model artifacts for trained ML/spaCy-equivalent behavior.',
    ],
    browserNative: true,
    serverCallsAllowed: false,
    pythonRuntimeAllowed: false,
  },
  {
    pythonLogicModules: 'logic/TDFOL',
    typescriptWasmFiles: ['src/lib/logic/tdfol', 'src/lib/logic/modalTableaux.ts'],
    validationEvidence: [
      'src/lib/logic/tdfol/prover.test.ts',
      'src/lib/logic/tdfol/modalTableaux.test.ts',
      'src/lib/logic/modalTableaux.test.ts',
    ],
    acceptedWork: ['CEC, DCEC, and deontic reasoning'],
    remainingBrowserNativeTasks: [
      'Replace remaining P2P, dashboard, and visualization helper surfaces with browser-local state and serializable exports.',
    ],
    browserNative: true,
    serverCallsAllowed: false,
    pythonRuntimeAllowed: false,
  },
  {
    pythonLogicModules: 'logic/CEC and logic/integration',
    typescriptWasmFiles: ['src/lib/logic/deontic', 'src/lib/logic/integration'],
    validationEvidence: [
      'src/lib/logic/integration/bridge.test.ts',
      'src/lib/logic/integration/coreBridge.test.ts',
      'src/lib/logic/integration/domain/deonticQueryEngine.test.ts',
    ],
    acceptedWork: ['CEC, DCEC, and deontic reasoning'],
    remainingBrowserNativeTasks: [
      'Complete browser-native CEC grammar loading, cognitive/modal rule groups, namespace diagnostics, and selected native prover behavior.',
    ],
    browserNative: true,
    serverCallsAllowed: false,
    pythonRuntimeAllowed: false,
  },
  {
    pythonLogicModules: 'logic/zkp',
    typescriptWasmFiles: ['src/lib/logic/zkp', 'src/lib/logic/groth16.ts'],
    validationEvidence: [
      'src/lib/logic/zkp/facade.test.ts',
      'src/lib/logic/zkp/witnessManager.test.ts',
      'src/lib/logic/groth16.test.ts',
    ],
    acceptedWork: ['ZKP and verifier surfaces'],
    remainingBrowserNativeTasks: [
      'Finish browser crypto and chain-library parity for Groth16, EVM public inputs, and VK registry helpers.',
    ],
    browserNative: true,
    serverCallsAllowed: false,
    pythonRuntimeAllowed: false,
  },
  {
    pythonLogicModules: 'logic/external_provers and top-level operational modules',
    typescriptWasmFiles: [
      'src/lib/logic/integration/proverAdapters.ts',
      'src/lib/logic/cli.ts',
      'src/lib/logic/monitoring.ts',
      'src/lib/logic/security',
    ],
    validationEvidence: [
      'src/lib/logic/cli.test.ts',
      'src/lib/logic/monitoring.test.ts',
      'src/lib/logic/security/security.test.ts',
    ],
    acceptedWork: ['Public API, CLI/devtools, config, monitoring, and security'],
    remainingBrowserNativeTasks: [
      'Map remaining external prover routing to WASM-capable local adapters or explicit unsupported-local results.',
      'Convert remaining benchmark and validation script behavior into browser/devtools TypeScript entry points.',
    ],
    browserNative: true,
    serverCallsAllowed: false,
    pythonRuntimeAllowed: false,
  },
];

export function reconcilePythonLogicInventory(): LogicInventoryReconciliation {
  const uncoveredPythonFiles = UNCOVERED_TASKS.reduce(
    (total, task) => total + task.uncoveredFiles,
    0,
  );

  if (uncoveredPythonFiles !== UNCOVERED_PYTHON_FILE_TOTAL) {
    throw new Error('Python logic inventory reconciliation task total is inconsistent.');
  }

  return {
    pythonInventoryFiles: 269,
    typescriptWasmImplementationFiles: 253,
    uncoveredPythonFiles: UNCOVERED_PYTHON_FILE_TOTAL,
    browserNative: true,
    serverCallsAllowed: false,
    pythonRuntimeAllowed: false,
    tasks: UNCOVERED_TASKS,
  };
}

export function reviewAcceptedLogicParity(): AcceptedLogicParityReview {
  const reconciliation = reconcilePythonLogicInventory();
  for (const evidence of ACCEPTED_LOGIC_PARITY_EVIDENCE) {
    if (
      evidence.runtimeFiles.length === 0 ||
      evidence.validationFiles.length === 0 ||
      evidence.serverCallsAllowed !== false ||
      evidence.pythonRuntimeAllowed !== false
    ) {
      throw new Error(`Accepted parity evidence is incomplete for ${evidence.area}`);
    }
  }

  return {
    reviewedAgainstGoal: 'browser-native TypeScript/WASM logic port',
    acceptedEvidenceCount: ACCEPTED_LOGIC_PARITY_EVIDENCE.length,
    missingParityTasks: reconciliation.tasks,
    evidence: ACCEPTED_LOGIC_PARITY_EVIDENCE,
    browserNative: true,
    serverCallsAllowed: false,
    pythonRuntimeAllowed: false,
  };
}

export function buildLogicPortParityMatrix(): readonly LogicPortParityMatrixEntry[] {
  const review = reviewAcceptedLogicParity();
  const acceptedAreas = new Set(review.evidence.map((evidence) => evidence.area));

  for (const entry of LOGIC_PORT_PARITY_MATRIX) {
    if (
      entry.typescriptWasmFiles.length === 0 ||
      entry.validationEvidence.length === 0 ||
      entry.acceptedWork.length === 0 ||
      entry.serverCallsAllowed !== false ||
      entry.pythonRuntimeAllowed !== false
    ) {
      throw new Error(`Logic parity matrix row is incomplete for ${entry.pythonLogicModules}`);
    }
    for (const acceptedWork of entry.acceptedWork) {
      if (!acceptedAreas.has(acceptedWork)) {
        throw new Error(`Logic parity matrix references unknown accepted work: ${acceptedWork}`);
      }
    }
  }

  return LOGIC_PORT_PARITY_MATRIX;
}

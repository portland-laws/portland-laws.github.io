import type { ProofStatus } from '../types';
import type { CecProblemFormat } from './problemParser';
import type { CecShadowModalLogic } from './shadowProver';

export interface CecPythonParityProblemCapture {
  name: string;
  logic: CecShadowModalLogic;
  assumptions: string[];
  goals: string[];
  metadata: {
    format: CecProblemFormat;
  };
}

export interface CecPythonParityProofCapture {
  status: ProofStatus;
  theorem: string;
  method: string;
  stepRules: string[];
  stepConclusions: string[];
}

export interface CecPythonParityProofFixture {
  id: string;
  pythonModule: string;
  format: CecProblemFormat;
  problem: string;
  expectedProblem: CecPythonParityProblemCapture;
  expectedProof: CecPythonParityProofCapture;
  rules: string[];
  maxSteps: number;
  maxDerivedExpressions?: number;
}

export const PYTHON_CEC_DCEC_PARITY_FIXTURES: CecPythonParityProofFixture[] = [
  {
    id: 'dcec_quantified_portland_obligation',
    pythonModule: 'ipfs_datasets_py.logic.CEC.native_prover',
    format: 'custom',
    problem: `
      # Captured from Python DCEC parser/prover parity run.
      LOGIC: D
      ASSUMPTIONS:
      (subject_to ada portland_city_code_1_05_040)
      (forall agent (implies (subject_to agent portland_city_code_1_05_040) (O (always (comply_with agent portland_city_code_1_05_040)))))
      GOALS:
      (O (always (comply_with ada portland_city_code_1_05_040)))
    `,
    expectedProblem: {
      name: 'custom_problem',
      logic: 'D',
      assumptions: [
        '(subject_to ada portland_city_code_1_05_040)',
        '(forall agent (implies (subject_to agent portland_city_code_1_05_040) (O (always (comply_with agent portland_city_code_1_05_040)))))',
      ],
      goals: ['(O (always (comply_with ada portland_city_code_1_05_040)))'],
      metadata: { format: 'custom' },
    },
    expectedProof: {
      status: 'proved',
      theorem: '(O (always (comply_with ada portland_city_code_1_05_040)))',
      method: 'cec-forward-chaining',
      stepRules: ['CecUniversalModusPonens'],
      stepConclusions: ['(O (always (comply_with ada portland_city_code_1_05_040)))'],
    },
    rules: ['CecUniversalModusPonens'],
    maxSteps: 3,
  },
  {
    id: 'cec_cognitive_perception_to_belief',
    pythonModule: 'ipfs_datasets_py.logic.CEC.cognitive_inference',
    format: 'custom',
    problem: `
      # Cognitive custom logic maps to S5 in the Python problem parser.
      LOGIC: Cognitive
      ASSUMPTIONS:
      (Perceives alice (notice_filed case_17))
      GOALS:
      (B alice (notice_filed case_17))
    `,
    expectedProblem: {
      name: 'custom_problem',
      logic: 'S5',
      assumptions: ['(Perceives alice (notice_filed case_17))'],
      goals: ['(B alice (notice_filed case_17))'],
      metadata: { format: 'custom' },
    },
    expectedProof: {
      status: 'proved',
      theorem: '(B alice (notice_filed case_17))',
      method: 'cec-forward-chaining',
      stepRules: ['CecPerceptionImpliesKnowledge', 'CecKnowledgeImpliesBelief'],
      stepConclusions: ['(K alice (notice_filed case_17))', '(B alice (notice_filed case_17))'],
    },
    rules: ['CecPerceptionImpliesKnowledge', 'CecKnowledgeImpliesBelief'],
    maxSteps: 4,
  },
  {
    id: 'dcec_obligation_distribution_capture',
    pythonModule: 'ipfs_datasets_py.logic.CEC.deontic_rules',
    format: 'custom',
    problem: `
      LOGIC: D
      ASSUMPTIONS:
      (O (and (submit_notice tenant city) (preserve_records tenant)))
      GOALS:
      (O (submit_notice tenant city))
    `,
    expectedProblem: {
      name: 'custom_problem',
      logic: 'D',
      assumptions: ['(O (and (submit_notice tenant city) (preserve_records tenant)))'],
      goals: ['(O (submit_notice tenant city))'],
      metadata: { format: 'custom' },
    },
    expectedProof: {
      status: 'proved',
      theorem: '(O (submit_notice tenant city))',
      method: 'cec-forward-chaining',
      stepRules: ['CecObligationDistribution', 'CecConjunctionEliminationLeft'],
      stepConclusions: [
        '(and (O (submit_notice tenant city)) (O (preserve_records tenant)))',
        '(O (submit_notice tenant city))',
      ],
    },
    rules: ['CecObligationDistribution', 'CecConjunctionEliminationLeft'],
    maxSteps: 4,
  },
];

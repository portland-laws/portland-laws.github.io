import type {
  BrowserGroth16Backend,
  Groth16Proof,
  Groth16ProvingArtifacts,
  Groth16VerificationKey,
} from '../groth16';
import { createGroth16BackupBackend, isGroth16Proof } from '../groth16';
import type { Eip1193Provider } from './ethIntegration';
import { callEth } from './ethIntegration';
import { buildEvmGroth16VerificationRequest } from './evmHarness';
import {
  buildRegisterVkCalldata,
  buildRegisterVkPayload,
  circuitIdTextToBytes32,
} from './ethVkRegistryPayloads';
import type { ZKPProof } from './simulatedBackend';

export const ONCHAIN_PIPELINE_METADATA = {
  pythonSource: 'logic/zkp/onchain_pipeline.py',
  runtime: 'browser-native',
  proofSystem: 'Groth16',
  requiresPythonRuntime: false,
  allowsServerRpcFallback: false,
  providerContract: 'eip1193-injected',
} as const;

export interface OnchainPipelineOptions {
  theorem: string;
  privateAxioms: Array<string>;
  verifierAddress: string;
  backend?: BrowserGroth16Backend;
  provingArtifacts?: Groth16ProvingArtifacts;
  verificationKey?: Groth16VerificationKey;
  circuitId?: string;
  circuitVersion?: number;
  rulesetId?: string;
  vkHashHex?: string;
  overwriteVk?: boolean;
  provider?: Eip1193Provider;
  verifyOnchain?: boolean;
}

export async function buildOnchainProofPipeline(options: OnchainPipelineOptions) {
  const circuitId = options.circuitId ?? 'legal_theorem_groth16';
  const circuitVersion = options.circuitVersion ?? 1;
  const rulesetId = options.rulesetId ?? 'TDFOL_v1';
  const proof = await createGroth16BackupBackend({
    backend: options.backend,
    circuitId,
    circuitVersion,
    provingArtifacts: options.provingArtifacts,
    rulesetId,
    verificationKey: options.verificationKey,
  }).generateProof(options.theorem, options.privateAxioms, {
    circuit_version: circuitVersion,
    groth16_verification_key: options.verificationKey,
    ruleset_id: rulesetId,
  });
  const groth16Proof = readGroth16Proof(proof);
  const publicInputs = readPipelinePublicInputs(proof.publicInputs);
  const verificationRequest = await buildEvmGroth16VerificationRequest({
    proof: groth16Proof,
    publicInputs,
    verifierAddress: options.verifierAddress,
  });
  const registryPayload =
    options.vkHashHex === undefined
      ? undefined
      : buildRegisterVkPayload({
          circuitIdBytes32: circuitIdTextToBytes32(circuitId),
          version: circuitVersion,
          vkHashHex: options.vkHashHex,
        });
  const registryCalldata =
    registryPayload === undefined
      ? undefined
      : buildRegisterVkCalldata({ overwrite: options.overwriteVk, payload: registryPayload });
  const onchainVerified =
    options.verifyOnchain === true
      ? decodeEvmBool(await callEth(options.provider, verificationRequest.readCall))
      : undefined;

  return {
    evmPublicInputs: verificationRequest.publicInputs,
    groth16Proof,
    metadata: {
      ...ONCHAIN_PIPELINE_METADATA,
      circuitId,
      circuitVersion,
      registerVkPrepared: registryPayload !== undefined,
    },
    onchainVerified,
    proof,
    publicInputs,
    registryCalldata,
    registryPayload,
    verifierCalldata: verificationRequest.calldata,
    verifierReadCall: verificationRequest.readCall,
  };
}

export const build_onchain_proof_pipeline = buildOnchainProofPipeline;

function readGroth16Proof(proof: ZKPProof): Groth16Proof {
  const candidate = proof.metadata.groth16_proof;
  if (!isGroth16Proof(candidate))
    throw new Error('groth16_proof metadata is required for on-chain pipeline');
  return candidate;
}

function readPipelinePublicInputs(publicInputs: Record<string, unknown>) {
  return {
    axiomsCommitmentHex: readString(publicInputs.axioms_commitment, 'axioms_commitment'),
    circuitVersion: readInteger(publicInputs.circuit_version, 'circuit_version'),
    rulesetId: readString(publicInputs.ruleset_id, 'ruleset_id'),
    theoremHashHex: readString(publicInputs.theorem_hash, 'theorem_hash'),
  };
}

function readString(value: unknown, field: string): string {
  if (typeof value !== 'string' || value.length === 0)
    throw new Error(`${field} must be a non-empty string`);
  return value;
}

function readInteger(value: unknown, field: string): number | bigint {
  if (typeof value === 'bigint') return value;
  if (typeof value === 'number' && Number.isInteger(value)) return value;
  throw new Error(`${field} must be an integer`);
}

function decodeEvmBool(value: unknown): boolean {
  if (typeof value !== 'string' || !/^0x[0-9a-f]*$/i.test(value) || value.length < 66) {
    return false;
  }
  return BigInt(`0x${value.slice(-64)}`) === BigInt(1);
}

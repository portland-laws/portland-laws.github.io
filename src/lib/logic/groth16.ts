export type Groth16JsonScalar = string | number | boolean | null;
export type Groth16JsonValue =
  | Groth16JsonScalar
  | Groth16JsonValue[]
  | { [key: string]: Groth16JsonValue | undefined };
export type Groth16PublicSignals = Groth16JsonScalar[];
export type Groth16ArtifactBytes = Uint8Array | ArrayBuffer | string;
export type Groth16WitnessInput = { [key: string]: Groth16JsonValue | undefined };

export interface Groth16Proof {
  pi_a: Groth16JsonValue[];
  pi_b: Groth16JsonValue[][];
  pi_c: Groth16JsonValue[];
  protocol?: string;
  curve?: string;
  [key: string]: Groth16JsonValue | undefined;
}

export interface Groth16VerificationKey {
  protocol?: string;
  curve?: string;
  vk_alpha_1?: Groth16JsonValue;
  vk_beta_2?: Groth16JsonValue;
  vk_gamma_2?: Groth16JsonValue;
  vk_delta_2?: Groth16JsonValue;
  IC?: Groth16JsonValue[];
  [key: string]: Groth16JsonValue | undefined;
}

export interface Groth16ProvingArtifacts {
  wasm: Groth16ArtifactBytes;
  zkey: Groth16ArtifactBytes;
}

export interface Groth16ProvingSuccess {
  ok: true;
  proof: Groth16Proof;
  publicSignals: Groth16PublicSignals;
}

export interface Groth16ProvingFailure {
  ok: false;
  error: string;
}

export type Groth16ProvingResult = Groth16ProvingSuccess | Groth16ProvingFailure;

export interface BrowserGroth16Backend {
  verify: (
    verificationKey: Groth16VerificationKey,
    publicSignals: Groth16PublicSignals,
    proof: Groth16Proof,
  ) => unknown;
  prove?: (artifacts: Groth16ProvingArtifacts, input: Groth16WitnessInput) => unknown;
}

export interface Groth16Adapter {
  supportsVerification: boolean;
  supportsProving: boolean;
  verify: (verificationKey: unknown, publicSignals: unknown, proof: unknown) => unknown;
  prove: (artifacts: unknown, input: unknown) => unknown;
}

function isObject(value: unknown): value is { [key: string]: unknown } {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function isScalar(value: unknown): value is Groth16JsonScalar {
  return (
    value === null ||
    typeof value === 'string' ||
    typeof value === 'number' ||
    typeof value === 'boolean'
  );
}

function isJsonValue(value: unknown): value is Groth16JsonValue {
  if (isScalar(value)) {
    return true;
  }

  if (Array.isArray(value)) {
    return value.every(isJsonValue);
  }

  if (!isObject(value)) {
    return false;
  }

  return Object.keys(value).every((key) => value[key] === undefined || isJsonValue(value[key]));
}

function isJsonArray(value: unknown): value is Groth16JsonValue[] {
  return Array.isArray(value) && value.every(isJsonValue);
}

function isNestedJsonArray(value: unknown): value is Groth16JsonValue[][] {
  return Array.isArray(value) && value.every(isJsonArray);
}

export function isGroth16Proof(value: unknown): value is Groth16Proof {
  if (!isObject(value)) {
    return false;
  }

  return (
    isJsonArray(value.pi_a) &&
    value.pi_a.length >= 2 &&
    isNestedJsonArray(value.pi_b) &&
    value.pi_b.length >= 2 &&
    isJsonArray(value.pi_c) &&
    value.pi_c.length >= 2 &&
    (value.protocol === undefined || value.protocol === 'groth16') &&
    (value.curve === undefined || typeof value.curve === 'string')
  );
}

export function isGroth16PublicSignals(value: unknown): value is Groth16PublicSignals {
  return Array.isArray(value) && value.every(isScalar);
}

export function isGroth16VerificationKey(value: unknown): value is Groth16VerificationKey {
  if (!isObject(value)) {
    return false;
  }

  const hasProtocol = value.protocol === 'groth16';
  const hasSnarkJsShape =
    isJsonValue(value.vk_alpha_1) &&
    isJsonValue(value.vk_beta_2) &&
    isJsonValue(value.vk_gamma_2) &&
    isJsonValue(value.vk_delta_2) &&
    isJsonArray(value.IC);

  return (
    (hasProtocol || hasSnarkJsShape) &&
    (value.curve === undefined || typeof value.curve === 'string')
  );
}

function isArtifactBytes(value: unknown): value is Groth16ArtifactBytes {
  return typeof value === 'string' || value instanceof Uint8Array || value instanceof ArrayBuffer;
}

export function isGroth16ProvingArtifacts(value: unknown): value is Groth16ProvingArtifacts {
  return isObject(value) && isArtifactBytes(value.wasm) && isArtifactBytes(value.zkey);
}

export function isGroth16WitnessInput(value: unknown): value is Groth16WitnessInput {
  if (!isObject(value)) {
    return false;
  }

  return Object.keys(value).every((key) => value[key] === undefined || isJsonValue(value[key]));
}

function normalizeProvingResult(value: unknown): Groth16ProvingResult {
  if (
    !isObject(value) ||
    !isGroth16Proof(value.proof) ||
    !isGroth16PublicSignals(value.publicSignals)
  ) {
    return { ok: false, error: 'groth16_backend_returned_invalid_result' };
  }

  return { ok: true, proof: value.proof, publicSignals: value.publicSignals };
}

export function createGroth16Adapter(backend?: BrowserGroth16Backend): Groth16Adapter {
  return {
    supportsVerification: typeof backend?.verify === 'function',
    supportsProving: typeof backend?.prove === 'function',

    async verify(verificationKey: unknown, publicSignals: unknown, proof: unknown) {
      if (
        !backend ||
        !isGroth16VerificationKey(verificationKey) ||
        !isGroth16PublicSignals(publicSignals) ||
        !isGroth16Proof(proof)
      ) {
        return false;
      }

      try {
        return (await backend.verify(verificationKey, publicSignals, proof)) === true;
      } catch {
        return false;
      }
    },

    async prove(artifacts: unknown, input: unknown) {
      if (!backend?.prove) {
        return { ok: false, error: 'groth16_proving_backend_unavailable' };
      }

      if (!isGroth16ProvingArtifacts(artifacts)) {
        return { ok: false, error: 'groth16_invalid_proving_artifacts' };
      }

      if (!isGroth16WitnessInput(input)) {
        return { ok: false, error: 'groth16_invalid_witness_input' };
      }

      try {
        return normalizeProvingResult(await backend.prove(artifacts, input));
      } catch {
        return { ok: false, error: 'groth16_backend_proving_failed' };
      }
    },
  };
}

export async function verifyGroth16Proof(
  verificationKey: unknown,
  publicSignals: unknown,
  proof: unknown,
  backend?: BrowserGroth16Backend,
) {
  return createGroth16Adapter(backend).verify(verificationKey, publicSignals, proof);
}

export async function proveGroth16(
  artifacts: unknown,
  input: unknown,
  backend?: BrowserGroth16Backend,
) {
  return createGroth16Adapter(backend).prove(artifacts, input);
}

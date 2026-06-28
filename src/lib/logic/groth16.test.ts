import { webcrypto } from 'node:crypto';
import { TextDecoder, TextEncoder } from 'node:util';

import {
  GROTH16_FFI_BACKEND_METADATA,
  createGroth16Adapter,
  createGroth16FfiBackend,
  isGroth16Proof,
  proveGroth16,
  verifyGroth16Proof,
} from './groth16';

Object.defineProperty(globalThis, 'crypto', {
  value: webcrypto,
  configurable: true,
});
Object.defineProperty(globalThis, 'TextEncoder', {
  value: TextEncoder,
  configurable: true,
});
Object.defineProperty(globalThis, 'TextDecoder', {
  value: TextDecoder,
  configurable: true,
});

const proof = {
  pi_a: ['1', '2', '1'],
  pi_b: [
    ['3', '4'],
    ['5', '6'],
    ['1', '0'],
  ],
  pi_c: ['7', '8', '1'],
  protocol: 'groth16',
  curve: 'bn128',
};

const verificationKey = {
  protocol: 'groth16',
  curve: 'bn128',
};

describe('Groth16 browser-native adapter', () => {
  it('fails closed when no browser or WASM backend is supplied', async () => {
    const adapter = createGroth16Adapter();

    expect(adapter.supportsVerification).toBe(false);
    expect(adapter.supportsProving).toBe(false);
    await expect(adapter.verify(verificationKey, ['9'], proof)).resolves.toBe(false);
    await expect(
      adapter.prove({ wasm: 'compiled.wasm', zkey: 'circuit.zkey' }, { value: '9' }),
    ).resolves.toEqual({
      ok: false,
      error: 'groth16_proving_backend_unavailable',
    });
  });

  it('rejects malformed proofs before delegating to the backend', async () => {
    const calls: unknown[] = [];
    const adapter = createGroth16Adapter({
      verify: (_verificationKey, _signals, candidateProof) => {
        calls.push(candidateProof);
        return true;
      },
    });

    expect(isGroth16Proof({ pi_a: ['1'], pi_b: [], pi_c: ['2'] })).toBe(false);
    await expect(
      adapter.verify(verificationKey, ['9'], { pi_a: ['1'], pi_b: [], pi_c: ['2'] }),
    ).resolves.toBe(false);
    expect(calls).toEqual([]);
  });

  it('delegates valid verification requests to an injected browser-compatible backend', async () => {
    const seen: unknown[] = [];

    await expect(
      verifyGroth16Proof(verificationKey, ['9', '10'], proof, {
        verify: (key, publicSignals, candidateProof) => {
          seen.push(key, publicSignals, candidateProof);
          return publicSignals.length === 2;
        },
      }),
    ).resolves.toBe(true);

    expect(seen).toEqual([verificationKey, ['9', '10'], proof]);
  });

  it('validates proving artifacts and normalizes backend proving output', async () => {
    const adapter = createGroth16Adapter({
      verify: () => false,
      prove: (_artifacts, input) => ({ proof, publicSignals: [String(input.value)] }),
    });

    await expect(adapter.prove({ wasm: 'compiled.wasm' }, { value: '11' })).resolves.toEqual({
      ok: false,
      error: 'groth16_invalid_proving_artifacts',
    });

    await expect(
      proveGroth16({ wasm: 'compiled.wasm', zkey: 'circuit.zkey' }, { value: '11' }, adapter),
    ).resolves.toEqual({
      ok: true,
      proof,
      publicSignals: ['11'],
    });
  });

  it('ports groth16_ffi.py as an injected browser-native WASM backend', async () => {
    const backend = createGroth16FfiBackend({
      backend: {
        prove: async (artifacts, input) => ({
          ok: true,
          proof,
          publicSignals: [String(input.theorem), String(artifacts.wasm)],
        }),
        verify: async (key, publicSignals, candidateProof) =>
          key === verificationKey &&
          publicSignals[0] === 'Q' &&
          publicSignals[1] === 'ffi.wasm' &&
          JSON.stringify(candidateProof) === JSON.stringify(proof),
      },
      provingArtifacts: { wasm: 'ffi.wasm', zkey: 'ffi.zkey' },
      verificationKey,
    });

    const generated = await backend.generateProof('Q', ['P', 'P -> Q']);

    expect(GROTH16_FFI_BACKEND_METADATA).toEqual({
      backendId: 'groth16_ffi',
      browserNative: true,
      proofSystem: 'Groth16',
      pythonRuntimeAllowed: false,
      requiresInjectedWasmBackend: true,
      serverCallsAllowed: false,
      sourcePythonModule: 'logic/zkp/backends/groth16_ffi.py',
    });
    expect(generated.metadata).toMatchObject({
      backend: 'groth16_ffi',
      browser_native: true,
      groth16_proof: proof,
      source_python_module: 'logic/zkp/backends/groth16_ffi.py',
    });
    expect(generated.publicInputs.groth16_public_signals).toEqual(['Q', 'ffi.wasm']);
    await expect(backend.verifyProof(generated)).resolves.toBe(true);
  });

  it('fails closed when the groth16_ffi local WASM backend is absent', async () => {
    const backend = createGroth16FfiBackend();

    await expect(backend.generateProof('Q', ['P'])).rejects.toThrow(
      'groth16_proving_backend_unavailable',
    );
  });
});

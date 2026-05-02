import { createGroth16Adapter, isGroth16Proof, proveGroth16, verifyGroth16Proof } from './groth16';

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
});

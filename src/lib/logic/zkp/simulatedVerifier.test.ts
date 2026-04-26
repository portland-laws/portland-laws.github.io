import { verifySimulatedCertificate } from './simulatedVerifier';

describe('simulated ZKP verifier', () => {
  it('reports simulated certificate metadata without cryptographic claims', () => {
    expect(
      verifySimulatedCertificate({
        zkp_backend: 'simulated',
        zkp_verified: true,
        zkp_security_note: 'simulated educational certificate; not cryptographically secure',
      }),
    ).toMatchObject({
      ok: true,
      status: 'simulated_certificate_present',
      cryptographic: false,
      message: 'Simulated educational certificate metadata is present.',
    });
  });

  it('rejects missing or unsupported metadata with warnings', () => {
    expect(verifySimulatedCertificate({ zkp_backend: 'groth16', zkp_verified: true })).toMatchObject({
      ok: false,
      status: 'unsupported_backend',
      cryptographic: false,
    });
    expect(verifySimulatedCertificate({ zkp_backend: 'simulated', zkp_verified: false })).toMatchObject({
      ok: false,
      status: 'missing',
      cryptographic: false,
    });
  });
});


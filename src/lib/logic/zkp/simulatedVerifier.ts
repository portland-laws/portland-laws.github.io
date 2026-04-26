export interface SimulatedCertificateInput {
  zkp_backend?: string;
  zkp_verified?: boolean;
  zkp_security_note?: string;
}

export interface SimulatedVerificationResult {
  ok: boolean;
  status: 'simulated_certificate_present' | 'missing' | 'unsupported_backend';
  cryptographic: false;
  message: string;
  warnings: string[];
}

export function verifySimulatedCertificate(input: SimulatedCertificateInput): SimulatedVerificationResult {
  if (input.zkp_backend !== 'simulated') {
    return {
      ok: false,
      status: input.zkp_backend ? 'unsupported_backend' : 'missing',
      cryptographic: false,
      message: 'No simulated certificate metadata was verified.',
      warnings: ['Only simulated certificate metadata checks are supported until browser-native cryptographic verification is ported.'],
    };
  }

  if (!input.zkp_verified) {
    return {
      ok: false,
      status: 'missing',
      cryptographic: false,
      message: 'Simulated certificate metadata is absent or marked unverified.',
      warnings: ['This does not prove the formalization is invalid; it only reflects available metadata.'],
    };
  }

  return {
    ok: true,
    status: 'simulated_certificate_present',
    cryptographic: false,
    message: 'Simulated educational certificate metadata is present.',
    warnings: [
      input.zkp_security_note || 'Simulated educational certificate; not cryptographically secure.',
      'This is not cryptographic verification.',
    ],
  };
}

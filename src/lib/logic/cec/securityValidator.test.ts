import { CecRateLimiter, CecSecurityValidator, calculateCecDepth } from './securityValidator';

describe('CecSecurityValidator', () => {
  it('validates ordinary CEC expressions and reports metadata', () => {
    const validator = new CecSecurityValidator({ now: () => 0 });

    expect(validator.validateExpression('(forall agent (O (comply_with agent code)))')).toMatchObject({
      valid: true,
      errors: [],
      metadata: {
        expression_length: 43,
        expression_depth: 3,
        security_level: 'medium',
      },
    });
  });

  it('detects malformed input, null bytes, size, depth, atom, and operator limits', () => {
    expect(new CecSecurityValidator().validateExpression(null)).toMatchObject({
      valid: false,
      threats: ['malformed_input'],
    });
    expect(new CecSecurityValidator().validateExpression('(p x)\x00')).toMatchObject({
      valid: false,
      threats: ['injection'],
    });

    const validator = new CecSecurityValidator({
      maxExpressionSize: 5,
      maxExpressionDepth: 1,
      maxAtoms: 1,
      maxOperators: 1,
    });
    const result = validator.validateExpression('(and (p x) (q y))', 'id', { parse: false });

    expect(result.valid).toBe(false);
    expect(result.threats).toContain('resource_exhaustion');
  });

  it('detects injection, parse errors, and DoS patterns according to security level', () => {
    const validator = new CecSecurityValidator({ securityLevel: 'high' });

    expect(validator.validateExpression('(p eval)')).toMatchObject({
      valid: false,
      threats: expect.arrayContaining(['injection']),
    });
    expect(validator.validateExpression('(p x); rm -rf /')).toMatchObject({
      valid: false,
      threats: expect.arrayContaining(['injection']),
    });
    expect(validator.validateExpression('(and (p x))')).toMatchObject({
      valid: false,
      threats: expect.arrayContaining(['parse_error']),
    });
    expect(validator.detectDosPattern('a'.repeat(120))).toBe(true);
  });

  it('sanitizes input and checks resource limits', () => {
    const validator = new CecSecurityValidator({ maxExpressionSize: 8 });

    expect(validator.sanitizeInput(' eval((p x))\x00 '.repeat(2))).toBe('((p x))');
    expect(validator.checkResourceLimits('(p x)', 1, 1)).toBe(true);
    expect(validator.checkResourceLimits('(p x)', 999, 1)).toBe(false);
    expect(calculateCecDepth('(a (b (c)))')).toBe(3);
  });

  it('rate limits repeated identifiers', () => {
    let now = 0;
    const limiter = new CecRateLimiter(2, 1000, () => now);

    expect(limiter.checkRateLimit('a').allowed).toBe(true);
    expect(limiter.checkRateLimit('a').allowed).toBe(true);
    expect(limiter.checkRateLimit('a').allowed).toBe(false);
    now = 1001;
    expect(limiter.checkRateLimit('a').allowed).toBe(true);
  });

  it('audits CEC proof result structure', () => {
    const validator = new CecSecurityValidator();

    expect(validator.auditProofResult({
      status: 'proved',
      theorem: '(q x)',
      steps: [{ id: 's1', rule: 'Rule', premises: ['(p x)'], conclusion: '(q x)' }],
      method: 'cec-forward-chaining',
      timeMs: 1,
    })).toMatchObject({
      passed: true,
      riskLevel: 'low',
    });

    expect(validator.auditProofResult({
      status: 'proved',
      theorem: '(q x)',
      steps: [{ id: '', rule: '', premises: [], conclusion: '(p x)' }],
      method: 'cec-forward-chaining',
    })).toMatchObject({
      passed: false,
      riskLevel: 'critical',
    });
  });

  it('records security events in reports', () => {
    const validator = new CecSecurityValidator({ maxRequestsPerMinute: 1, now: () => 0 });
    validator.validateExpression('(p x)', 'id');
    validator.validateExpression('(p x)', 'id');

    expect(validator.getSecurityReport()).toMatchObject({
      total_events: 1,
      threat_counts: { dos: 1 },
    });
  });
});

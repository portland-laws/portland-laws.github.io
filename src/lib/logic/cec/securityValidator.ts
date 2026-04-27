import type { ProofResult } from '../types';
import { validateCecExpression } from './parser';

export type CecSecurityLevel = 'low' | 'medium' | 'high' | 'paranoid';
export type CecThreatType =
  | 'injection'
  | 'dos'
  | 'resource_exhaustion'
  | 'malformed_input'
  | 'recursive_bomb'
  | 'parse_error'
  | 'invalid_proof';

export interface CecSecurityConfig {
  maxExpressionSize: number;
  maxExpressionDepth: number;
  maxAtoms: number;
  maxOperators: number;
  maxMemoryMb: number;
  maxProofTimeSeconds: number;
  maxRequestsPerMinute: number;
  maxConcurrentRequests: number;
  securityLevel: CecSecurityLevel;
  allowedChars: Set<string>;
  dangerousPatterns: RegExp[];
  now: () => number;
}

export interface CecSecurityValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
  threats: CecThreatType[];
  metadata: Record<string, unknown>;
}

export interface CecProofAuditResult {
  passed: boolean;
  vulnerabilities: string[];
  recommendations: string[];
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
  auditTime: number;
}

export interface CecSecurityEvent {
  timestamp: string;
  threatType: CecThreatType;
  details: string;
  context: string;
  securityLevel: CecSecurityLevel;
}

export class CecRateLimiter {
  private readonly requests = new Map<string, number[]>();

  constructor(
    private readonly maxRequests: number,
    private readonly timeWindowMs: number,
    private readonly now: () => number = () => Date.now(),
  ) {}

  checkRateLimit(identifier: string): { allowed: boolean; error?: string } {
    const currentTime = this.now();
    const recent = (this.requests.get(identifier) ?? []).filter((time) => currentTime - time < this.timeWindowMs);
    if (recent.length >= this.maxRequests) {
      this.requests.set(identifier, recent);
      return {
        allowed: false,
        error: `Rate limit exceeded: ${recent.length}/${this.maxRequests} requests in ${this.timeWindowMs / 1000}s`,
      };
    }
    recent.push(currentTime);
    this.requests.set(identifier, recent);
    return { allowed: true };
  }
}

export class CecSecurityValidator {
  readonly config: CecSecurityConfig;
  readonly securityEvents: CecSecurityEvent[] = [];

  private readonly rateLimiter: CecRateLimiter;
  private concurrentRequests = 0;

  constructor(config: Partial<CecSecurityConfig> = {}) {
    this.config = {
      maxExpressionSize: config.maxExpressionSize ?? 10000,
      maxExpressionDepth: config.maxExpressionDepth ?? 100,
      maxAtoms: config.maxAtoms ?? 1000,
      maxOperators: config.maxOperators ?? 5000,
      maxMemoryMb: config.maxMemoryMb ?? 500,
      maxProofTimeSeconds: config.maxProofTimeSeconds ?? 30,
      maxRequestsPerMinute: config.maxRequestsPerMinute ?? 100,
      maxConcurrentRequests: config.maxConcurrentRequests ?? 10,
      securityLevel: config.securityLevel ?? 'medium',
      allowedChars: config.allowedChars ?? new Set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789()_-.:/ '),
      dangerousPatterns:
        config.dangerousPatterns ??
        [/__.*__/, /eval/i, /exec/i, /compile/i, /import/i, /__import__/i, /getattr/i, /setattr/i, /delattr/i],
      now: config.now ?? (() => Date.now()),
    };
    this.rateLimiter = new CecRateLimiter(this.config.maxRequestsPerMinute, 60_000, this.config.now);
  }

  validateExpression(expression: unknown, identifier = 'default', options: { parse?: boolean } = {}): CecSecurityValidationResult {
    const result = createCecSecurityValidationResult();
    const rate = this.rateLimiter.checkRateLimit(identifier);
    if (!rate.allowed) {
      result.valid = false;
      result.errors.push(rate.error ?? 'Rate limit exceeded');
      result.threats.push('dos');
      this.logSecurityEvent('dos', rate.error ?? 'Rate limit exceeded', identifier);
      return result;
    }
    if (!this.acquireConcurrentSlot()) {
      result.valid = false;
      result.errors.push('Too many concurrent requests');
      result.threats.push('dos');
      return result;
    }

    try {
      this.validateInput(expression, result);
      if (typeof expression === 'string') {
        this.checkSizeLimits(expression, result);
        this.validateCharacters(expression, result);
        this.detectInjection(expression, result);
        this.detectDosPatterns(expression, result);
        this.detectRecursiveBombs(expression, result);
        if (options.parse ?? true) this.validateParse(expression, result);
        result.metadata = {
          expression_length: expression.length,
          expression_depth: calculateCecDepth(expression),
          validation_time: this.config.now(),
          security_level: this.config.securityLevel,
        };
      }
    } finally {
      this.concurrentRequests = Math.max(0, this.concurrentRequests - 1);
    }

    return result;
  }

  sanitizeInput(input: string): string {
    if (!input) return '';
    let sanitized = input.replace(/\x00/g, '');
    for (const pattern of this.config.dangerousPatterns) {
      let previous = '';
      while (previous !== sanitized) {
        previous = sanitized;
        sanitized = sanitized.replace(pattern, '');
      }
    }
    sanitized = sanitized.replace(/\s+/g, ' ');
    sanitized = [...sanitized].filter((char) => /[\n\t]/.test(char) || char >= ' ').join('');
    return sanitized.slice(0, this.config.maxExpressionSize).trim();
  }

  checkResourceLimits(expression: string, memoryMb?: number, timeSeconds?: number): boolean {
    if (memoryMb !== undefined && memoryMb > this.config.maxMemoryMb) return false;
    if (timeSeconds !== undefined && timeSeconds > this.config.maxProofTimeSeconds) return false;
    const result = createCecSecurityValidationResult();
    this.checkSizeLimits(expression, result);
    return result.valid;
  }

  detectDosPattern(expression: string): boolean {
    const result = createCecSecurityValidationResult();
    this.detectDosPatterns(expression, result);
    this.detectRecursiveBombs(expression, result);
    return result.threats.includes('dos') || result.threats.includes('recursive_bomb');
  }

  auditProofResult(proof: ProofResult): CecProofAuditResult {
    const startedAt = nowMs();
    const result: CecProofAuditResult = {
      passed: true,
      vulnerabilities: [],
      recommendations: [],
      riskLevel: 'low',
      auditTime: 0,
    };

    if (!proof.theorem) {
      result.passed = false;
      result.vulnerabilities.push('Proof result missing theorem');
    }
    if (!Array.isArray(proof.steps)) {
      result.passed = false;
      result.vulnerabilities.push('Proof result steps must be an array');
    }
    if (proof.status === 'proved' && proof.steps.length > 0) {
      const finalConclusion = proof.steps[proof.steps.length - 1]?.conclusion;
      if (finalConclusion !== proof.theorem) {
        result.passed = false;
        result.vulnerabilities.push('Final proof step does not conclude theorem');
      }
    }
    for (const step of proof.steps) {
      if (!step.id || !step.rule || !step.conclusion) {
        result.passed = false;
        result.vulnerabilities.push(`Malformed proof step: ${step.id || '<missing id>'}`);
      }
      if (step.premises.length > 100) {
        result.recommendations.push(`Proof step ${step.id} has many premises`);
      }
    }
    if ((proof.timeMs ?? 0) > this.config.maxProofTimeSeconds * 1000) {
      result.recommendations.push('Proof exceeded configured proof-time budget');
    }
    result.riskLevel = calculateProofRiskLevel(result);
    result.auditTime = nowMs() - startedAt;
    return result;
  }

  getSecurityReport(): Record<string, unknown> {
    const threatCounts = this.securityEvents.reduce<Record<string, number>>((counts, event) => {
      counts[event.threatType] = (counts[event.threatType] ?? 0) + 1;
      return counts;
    }, {});
    return {
      total_events: this.securityEvents.length,
      threat_counts: threatCounts,
      recent_events: this.securityEvents.slice(-20),
      security_level: this.config.securityLevel,
    };
  }

  private acquireConcurrentSlot(): boolean {
    if (this.concurrentRequests >= this.config.maxConcurrentRequests) return false;
    this.concurrentRequests += 1;
    return true;
  }

  private validateInput(expression: unknown, result: CecSecurityValidationResult): void {
    if (typeof expression !== 'string') {
      result.valid = false;
      result.errors.push('CEC expression must be a string');
      result.threats.push('malformed_input');
      return;
    }
    if (!expression) {
      result.valid = false;
      result.errors.push('Empty CEC expression');
      result.threats.push('malformed_input');
    }
    if (expression.includes('\x00')) {
      result.valid = false;
      result.errors.push('Null bytes not allowed');
      result.threats.push('injection');
    }
  }

  private checkSizeLimits(expression: string, result: CecSecurityValidationResult): void {
    if (expression.length > this.config.maxExpressionSize) {
      result.valid = false;
      result.errors.push(`CEC expression too large: ${expression.length} > ${this.config.maxExpressionSize}`);
      result.threats.push('resource_exhaustion');
    }
    const depth = calculateCecDepth(expression);
    if (depth > this.config.maxExpressionDepth) {
      result.valid = false;
      result.errors.push(`CEC expression too deep: ${depth} > ${this.config.maxExpressionDepth}`);
      result.threats.push('resource_exhaustion');
    }
    const atomCount = [...expression.matchAll(/[A-Za-z_][A-Za-z0-9_:/.-]*/g)].length;
    if (atomCount > this.config.maxAtoms) {
      result.valid = false;
      result.errors.push(`Too many CEC atoms: ${atomCount} > ${this.config.maxAtoms}`);
      result.threats.push('resource_exhaustion');
    }
    const operatorCount = [...expression.matchAll(/\b(?:forall|exists|not|O|P|F|always|eventually|next|implies|and|or|iff|xor)\b/g)].length;
    if (operatorCount > this.config.maxOperators) {
      result.valid = false;
      result.errors.push(`Too many CEC operators: ${operatorCount} > ${this.config.maxOperators}`);
      result.threats.push('resource_exhaustion');
    }
  }

  private validateCharacters(expression: string, result: CecSecurityValidationResult): void {
    if (this.config.securityLevel !== 'high' && this.config.securityLevel !== 'paranoid') return;
    const invalidChars = [...new Set([...expression].filter((char) => !this.config.allowedChars.has(char)))];
    if (invalidChars.length === 0) return;
    const message = `Invalid CEC characters: ${invalidChars.map((char) => JSON.stringify(char)).join(', ')}`;
    if (this.config.securityLevel === 'paranoid') {
      result.valid = false;
      result.errors.push(message);
      result.threats.push('injection');
    } else {
      result.warnings.push(message);
    }
  }

  private detectInjection(expression: string, result: CecSecurityValidationResult): void {
    for (const pattern of this.config.dangerousPatterns) {
      if (pattern.test(expression)) {
        result.valid = false;
        result.errors.push(`Dangerous pattern detected: ${pattern.source}`);
        result.threats.push('injection');
        this.logSecurityEvent('injection', `Pattern: ${pattern.source}`, expression.slice(0, 100));
      }
    }
    for (const sequence of ['$(' , '`', '${', '|', ';', '&&', '||']) {
      if (!expression.includes(sequence)) continue;
      if (this.config.securityLevel === 'high' || this.config.securityLevel === 'paranoid') {
        result.valid = false;
        result.errors.push(`Dangerous sequence detected: ${sequence}`);
        result.threats.push('injection');
      } else {
        result.warnings.push(`Potentially dangerous sequence: ${sequence}`);
      }
    }
  }

  private detectDosPatterns(expression: string, result: CecSecurityValidationResult): void {
    if (hasExcessiveRepetition(expression)) {
      result.valid = false;
      result.errors.push('Excessive character repetition detected');
      result.threats.push('dos');
    }
    if (hasNestedQuantifierPattern(expression)) {
      result.warnings.push('Potentially expensive quantified CEC expression detected');
      if (this.config.securityLevel === 'paranoid') {
        result.valid = false;
        result.threats.push('dos');
      }
    }
  }

  private detectRecursiveBombs(expression: string, result: CecSecurityValidationResult): void {
    if (/\((\w+)\s+\1(?:\s+\1){10,}/.test(expression)) {
      result.warnings.push('Self-referential CEC application pattern detected');
      if (this.config.securityLevel === 'high' || this.config.securityLevel === 'paranoid') {
        result.threats.push('recursive_bomb');
      }
    }
    const atoms = [...expression.matchAll(/[A-Za-z_][A-Za-z0-9_:/.-]*/g)].map((match) => match[0]);
    const duplicates = atoms.length - new Set(atoms).size;
    if (duplicates > 25) result.warnings.push(`High CEC atom reuse: ${duplicates} duplicates`);
  }

  private validateParse(expression: string, result: CecSecurityValidationResult): void {
    if (!result.valid) return;
    const parsed = validateCecExpression(expression);
    if (!parsed.ok) {
      result.valid = false;
      result.errors.push(parsed.error);
      result.threats.push('parse_error');
    }
  }

  private logSecurityEvent(threatType: CecThreatType, details: string, context: string): void {
    this.securityEvents.push({
      timestamp: new Date(this.config.now()).toISOString(),
      threatType,
      details,
      context,
      securityLevel: this.config.securityLevel,
    });
  }
}

export function createCecSecurityValidationResult(): CecSecurityValidationResult {
  return { valid: true, errors: [], warnings: [], threats: [], metadata: {} };
}

export function calculateCecDepth(expression: string): number {
  let maxDepth = 0;
  let currentDepth = 0;
  for (const char of expression) {
    if (char === '(') {
      currentDepth += 1;
      maxDepth = Math.max(maxDepth, currentDepth);
    } else if (char === ')') {
      currentDepth = Math.max(0, currentDepth - 1);
    }
  }
  return maxDepth;
}

function hasExcessiveRepetition(expression: string, threshold = 100): boolean {
  for (let index = 0; index <= expression.length - threshold; index += 1) {
    if (new Set(expression.slice(index, index + threshold)).size < 5) return true;
  }
  return false;
}

function hasNestedQuantifierPattern(expression: string): boolean {
  return [...expression.matchAll(/\((forall|exists)\b/g)].length > 10;
}

function calculateProofRiskLevel(result: CecProofAuditResult): CecProofAuditResult['riskLevel'] {
  if (!result.passed) return 'critical';
  if (result.vulnerabilities.length > 0) return 'high';
  if (result.recommendations.length > 3) return 'medium';
  return 'low';
}

function nowMs(): number {
  return typeof globalThis.performance?.now === 'function' ? globalThis.performance.now() : Date.now();
}

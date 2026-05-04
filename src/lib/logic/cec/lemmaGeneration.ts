import type { ProofResult, ProofStatus, ProofStep } from '../types';
import type { CecExpression } from './ast';
import { formatCecExpression } from './formatter';
import { cecExpressionEquals, cecExpressionKey, type CecInferenceRule } from './inferenceRules';
import { parseCecExpression } from './parser';
import { CecKnowledgeBase, CecProver, type CecProverOptions } from './prover';

export const CecLemmaType = {
  DERIVED: 'derived',
  REUSABLE: 'reusable',
  PATTERN: 'pattern',
} as const;

export type CecLemmaTypeValue = (typeof CecLemmaType)[keyof typeof CecLemmaType];

export interface CecLemmaOptions {
  formula: CecExpression;
  premises?: CecExpression[];
  rule: string;
  lemmaType?: CecLemmaTypeValue;
  usageCount?: number;
  exactHash?: string;
  patternHash?: string;
}

export interface CecLemmaJson {
  formula: string;
  premises?: Array<string>;
  rule: string;
  lemma_type?: CecLemmaTypeValue;
  usage_count?: number;
  exact_hash?: string;
  pattern_hash?: string;
}

export class CecLemma {
  readonly formula: CecExpression;
  readonly premises: CecExpression[];
  readonly rule: string;
  lemmaType: CecLemmaTypeValue;
  usageCount: number;
  readonly exactHash: string;
  readonly patternHash: string;

  constructor(options: CecLemmaOptions) {
    this.formula = options.formula;
    this.premises = [...(options.premises ?? [])];
    this.rule = options.rule;
    this.lemmaType = options.lemmaType ?? CecLemmaType.DERIVED;
    this.usageCount = options.usageCount ?? 0;
    this.exactHash = options.exactHash ?? hashCecLemmaPattern(formatCecExpression(options.formula));
    this.patternHash =
      options.patternHash ?? hashCecLemmaPattern(normalizeCecLemmaPattern(options.formula));
  }

  matchesPattern(otherFormula: CecExpression): boolean {
    return normalizeCecLemmaPattern(this.formula) === normalizeCecLemmaPattern(otherFormula);
  }

  incrementUsage(): void {
    this.usageCount += 1;
  }

  static fromJSON(json: CecLemmaJson): CecLemma {
    return cecLemmaFromJSON(json);
  }

  toJSON(): CecLemmaJson {
    return {
      formula: formatCecExpression(this.formula),
      premises: this.premises.map(formatCecExpression),
      rule: this.rule,
      lemma_type: this.lemmaType,
      usage_count: this.usageCount,
      exact_hash: this.exactHash,
      pattern_hash: this.patternHash,
    };
  }
}

export interface CecLemmaCacheStatistics {
  size: number;
  max_size: number;
  hits: number;
  misses: number;
  hit_rate: number;
  total_requests: number;
}

export class CecLemmaCache {
  readonly maxSize: number;
  private readonly cache = new Map<string, CecLemma>();
  private readonly patternIndex = new Map<string, Set<string>>();
  hits = 0;
  misses = 0;

  constructor(maxSize = 100) {
    this.maxSize = Math.max(1, maxSize);
  }

  add(lemma: CecLemma): void {
    const key = lemma.exactHash || cecExpressionKey(lemma.formula);
    if (this.cache.has(key)) {
      const existing = this.cache.get(key)!;
      this.cache.delete(key);
      this.cache.set(key, existing);
      return;
    }

    this.cache.set(key, lemma);
    const pattern = lemma.patternHash;
    const bucket = this.patternIndex.get(pattern) ?? new Set<string>();
    bucket.add(key);
    this.patternIndex.set(pattern, bucket);

    if (this.cache.size > this.maxSize) {
      const evictedKey = this.cache.keys().next().value as string | undefined;
      if (evictedKey === undefined) return;
      const evictedLemma = this.cache.get(evictedKey);
      this.cache.delete(evictedKey);
      if (evictedLemma) this.removePatternIndex(evictedKey, evictedLemma.formula);
    }
  }

  get(formula: CecExpression): CecLemma | undefined {
    const key = hashCecLemmaPattern(formatCecExpression(formula));
    const lemma = this.cache.get(key);
    if (!lemma) {
      this.misses += 1;
      return undefined;
    }
    this.hits += 1;
    lemma.incrementUsage();
    this.cache.delete(key);
    this.cache.set(key, lemma);
    return lemma;
  }

  findByPattern(formula: CecExpression): CecLemma[] {
    const pattern = hashCecLemmaPattern(normalizeCecLemmaPattern(formula));
    const keys = this.patternIndex.get(pattern);
    if (!keys) return [];
    const matches: CecLemma[] = [];
    for (const key of keys) {
      const lemma = this.cache.get(key);
      if (lemma?.matchesPattern(formula)) matches.push(lemma);
    }
    return matches;
  }

  values(): CecLemma[] {
    return [...this.cache.values()];
  }

  importJSON(entries: Array<CecLemmaJson>): CecLemma[] {
    const imported: CecLemma[] = [];
    for (const entry of entries) {
      const lemma = cecLemmaFromJSON(entry);
      this.add(lemma);
      imported.push(lemma);
    }
    return imported;
  }

  exportJSON(): Array<CecLemmaJson> {
    return this.values().map((lemma) => lemma.toJSON());
  }

  getStatistics(): CecLemmaCacheStatistics {
    const total = this.hits + this.misses;
    return {
      size: this.cache.size,
      max_size: this.maxSize,
      hits: this.hits,
      misses: this.misses,
      hit_rate: total > 0 ? this.hits / total : 0,
      total_requests: total,
    };
  }

  clear(): void {
    this.cache.clear();
    this.patternIndex.clear();
    this.hits = 0;
    this.misses = 0;
  }

  private removePatternIndex(key: string, formula: CecExpression): void {
    const pattern = hashCecLemmaPattern(normalizeCecLemmaPattern(formula));
    const bucket = this.patternIndex.get(pattern);
    if (!bucket) return;
    bucket.delete(key);
    if (bucket.size === 0) this.patternIndex.delete(pattern);
  }
}

export interface CecLemmaProofStep {
  formula: CecExpression;
  premises: number[];
  rule: string;
}

export interface CecLemmaProofTree {
  result: ProofStatus;
  axioms: CecExpression[];
  steps: CecLemmaProofStep[];
}

export interface CecLemmaProofValidationResult {
  valid: boolean;
  errors: string[];
}

export interface CecLemmaGeneratorStatistics {
  discovery_count: number;
  reuse_count: number;
  cache_size: number;
  cache_hit_rate: number;
  cache_hits: number;
  cache_misses: number;
}

export class CecLemmaGenerator {
  readonly cache: CecLemmaCache;
  discoveryCount = 0;
  reuseCount = 0;

  constructor(maxLemmas = 100) {
    this.cache = new CecLemmaCache(maxLemmas);
  }

  importLemmas(entries: Array<CecLemmaJson>): CecLemma[] {
    const imported = this.cache.importJSON(entries);
    this.discoveryCount += imported.length;
    this.identifyReusableLemmas(imported);
    return imported;
  }

  discoverLemmas(proofTree: CecLemmaProofTree, minComplexity = 2): CecLemma[] {
    if (proofTree.result !== 'proved') return [];
    if (!validateCecLemmaProofTree(proofTree).valid) return [];

    const lemmas: CecLemma[] = [];
    for (const step of proofTree.steps) {
      if (step.premises.length < minComplexity) continue;
      const premises = step.premises.flatMap((premiseIndex) =>
        resolveCecLemmaPremise(proofTree, premiseIndex),
      );

      const lemma = new CecLemma({
        formula: step.formula,
        premises,
        rule: step.rule,
        lemmaType: CecLemmaType.DERIVED,
      });
      lemmas.push(lemma);
      this.cache.add(lemma);
      this.discoveryCount += 1;
    }

    this.identifyReusableLemmas(lemmas);
    return lemmas;
  }

  getApplicableLemmas(_goal: CecExpression, derived: CecExpression[]): CecLemma[] {
    const applicable: CecLemma[] = [];
    for (const formula of derived) {
      const exact = this.cache.get(formula);
      if (exact) applicable.push(exact);
    }
    for (const formula of derived) {
      applicable.push(...this.cache.findByPattern(formula));
    }

    const unique = new Map<string, CecLemma>();
    for (const lemma of applicable) unique.set(lemma.patternHash, lemma);
    return [...unique.values()];
  }

  proveWithLemmas(
    goal: CecExpression,
    kb: CecKnowledgeBase,
    rules: CecInferenceRule[] = [],
    options: CecProverOptions = {},
  ): ProofResult {
    const known = [...kb.axioms, ...(kb.theorems ?? [])];
    if (known.some((formula) => cecExpressionEquals(formula, goal))) {
      return this.proofResult('proved', goal, [], 'Goal is an axiom');
    }

    const goalLemma = this.cache.get(goal);
    if (goalLemma) {
      this.reuseCount += 1;
      return this.proofResult(
        'proved',
        goal,
        [lemmaProofStep(goalLemma)],
        'Proved by cached CEC lemma',
      );
    }

    for (const lemma of this.getApplicableLemmas(goal, known)) {
      if (!known.some((formula) => cecExpressionEquals(formula, lemma.formula))) {
        known.push(lemma.formula);
        lemma.incrementUsage();
        this.reuseCount += 1;
      }
    }

    const prover = new CecProver({ ...options, ...(rules.length > 0 ? { rules } : {}) });
    const result = prover.prove(goal, { ...kb, axioms: known });
    if (result.status === 'proved') {
      this.discoverFromProofResult(goal, kb.axioms, result);
    }
    return result;
  }

  getStatistics(): CecLemmaGeneratorStatistics {
    const cache = this.cache.getStatistics();
    return {
      discovery_count: this.discoveryCount,
      reuse_count: this.reuseCount,
      cache_size: cache.size,
      cache_hit_rate: cache.hit_rate,
      cache_hits: cache.hits,
      cache_misses: cache.misses,
    };
  }

  clear(): void {
    this.cache.clear();
    this.discoveryCount = 0;
    this.reuseCount = 0;
  }

  private identifyReusableLemmas(lemmas: CecLemma[]): void {
    const groups = new Map<string, CecLemma[]>();
    for (const lemma of lemmas) {
      const pattern = lemma.patternHash;
      const group = groups.get(pattern) ?? [];
      group.push(lemma);
      groups.set(pattern, group);
    }
    for (const group of groups.values()) {
      if (group.length > 1) {
        for (const lemma of group) lemma.lemmaType = CecLemmaType.REUSABLE;
      }
    }
  }

  private discoverFromProofResult(
    goal: CecExpression,
    axioms: CecExpression[],
    result: ProofResult,
  ): void {
    if (result.steps.length === 0) return;
    const finalStep = result.steps[result.steps.length - 1];
    const lemma = new CecLemma({
      formula: goal,
      premises: axioms,
      rule: finalStep.rule,
      lemmaType: CecLemmaType.DERIVED,
    });
    this.cache.add(lemma);
    this.discoveryCount += 1;
  }

  private proofResult(
    status: ProofStatus,
    theorem: CecExpression,
    steps: ProofStep[],
    explanation?: string,
  ): ProofResult {
    return {
      status,
      theorem: formatCecExpression(theorem),
      steps,
      method: 'cec-lemma-generation',
      error: status === 'proved' ? undefined : explanation,
    };
  }
}

export function createCecLemmaGenerator(maxLemmas = 100): CecLemmaGenerator {
  return new CecLemmaGenerator(maxLemmas);
}

export function cecLemmaFromJSON(json: CecLemmaJson): CecLemma {
  if (json.rule.trim().length === 0) {
    throw new Error('CEC lemma JSON rule must be non-empty');
  }
  if (json.lemma_type !== undefined && !Object.values(CecLemmaType).includes(json.lemma_type)) {
    throw new Error(`Unsupported CEC lemma type: ${json.lemma_type}`);
  }

  const formula = parseCecExpression(json.formula);
  const premises = (json.premises ?? []).map((premise) => parseCecExpression(premise));
  const exactHash = hashCecLemmaPattern(formatCecExpression(formula));
  const patternHash = hashCecLemmaPattern(normalizeCecLemmaPattern(formula));

  if (json.exact_hash !== undefined && json.exact_hash !== exactHash) {
    throw new Error(
      `CEC lemma exact hash mismatch: expected ${exactHash} but received ${json.exact_hash}`,
    );
  }
  if (json.pattern_hash !== undefined && json.pattern_hash !== patternHash) {
    throw new Error(
      `CEC lemma pattern hash mismatch: expected ${patternHash} but received ${json.pattern_hash}`,
    );
  }

  return new CecLemma({
    formula,
    premises,
    rule: json.rule,
    lemmaType: json.lemma_type,
    usageCount: json.usage_count,
    exactHash,
    patternHash,
  });
}

export function hashCecLemmaPattern(value: string): string {
  let hash = 0x811c9dc5;
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 0x01000193) >>> 0;
  }
  return hash.toString(16).padStart(8, '0').slice(0, 16);
}

export function normalizeCecLemmaPattern(formula: CecExpression): string {
  if (formula.kind === 'atom') return `atom:${formula.name}`;

  const atomBindings = new Map<string, string>();

  const normalize = (expression: CecExpression): string => {
    switch (expression.kind) {
      case 'atom':
        return bindCecLemmaAtom(atomBindings, expression.name);
      case 'application':
        return `(${[expression.name, ...expression.args.map(normalize)].join(' ')})`;
      case 'quantified':
        return `(${expression.quantifier} ${bindCecLemmaAtom(atomBindings, expression.variable)} ${normalize(expression.expression)})`;
      case 'unary':
        return `(${expression.operator} ${normalize(expression.expression)})`;
      case 'binary':
        return `(${expression.operator} ${normalize(expression.left)} ${normalize(expression.right)})`;
    }
  };

  return normalize(formula);
}

export function validateCecLemmaProofTree(
  proofTree: CecLemmaProofTree,
): CecLemmaProofValidationResult {
  const errors: string[] = [];
  const validStatuses: Array<ProofStatus> = ['proved', 'disproved', 'unknown', 'timeout', 'error'];
  if (!validStatuses.includes(proofTree.result)) {
    errors.push(`unsupported proof result: ${proofTree.result}`);
  }

  const axiomCount = Array.isArray(proofTree.axioms) ? proofTree.axioms.length : 0;
  proofTree.steps.forEach((step, stepIndex) => {
    if (step.rule.trim().length === 0) {
      errors.push(`step ${stepIndex} has an empty rule`);
    }
    step.premises.forEach((premiseIndex) => {
      const upperBound = axiomCount + stepIndex;
      if (!Number.isInteger(premiseIndex) || premiseIndex < 0 || premiseIndex >= upperBound) {
        errors.push(
          `step ${stepIndex} premise ${premiseIndex} does not reference an earlier axiom or step`,
        );
      }
    });
  });

  return { valid: errors.length === 0, errors };
}

function bindCecLemmaAtom(bindings: Map<string, string>, name: string): string {
  const existing = bindings.get(name);
  if (existing !== undefined) return existing;
  const bound = `?v${bindings.size}`;
  bindings.set(name, bound);
  return bound;
}

function resolveCecLemmaPremise(
  proofTree: CecLemmaProofTree,
  premiseIndex: number,
): CecExpression[] {
  if (premiseIndex < proofTree.axioms.length) return [proofTree.axioms[premiseIndex]];
  const stepIndex = premiseIndex - proofTree.axioms.length;
  const prior = proofTree.steps[stepIndex];
  return prior ? [prior.formula] : [];
}

function lemmaProofStep(lemma: CecLemma): ProofStep {
  return {
    id: 'cec-lemma-1',
    rule: `Lemma: ${lemma.rule}`,
    premises: lemma.premises.map(formatCecExpression),
    conclusion: formatCecExpression(lemma.formula),
    explanation: 'Reused cached CEC lemma',
  };
}

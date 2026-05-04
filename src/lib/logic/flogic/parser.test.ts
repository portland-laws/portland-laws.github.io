import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { webcrypto } from 'node:crypto';
import { TextEncoder } from 'node:util';

import { frameToDisplayRow, formatFLogicOntology } from './formatter';
import { ERGOAI_AVAILABLE, ErgoAIWrapper, parseErgoOutput } from './ergoaiWrapper';
import { normalizeFLogicGoal, parseFLogicOntology } from './parser';
import {
  FLOGIC_PROOF_CACHE_METADATA,
  FLogicProofCache,
  clearGlobalFLogicProofCache,
  getGlobalFLogicProofCache,
  queryFLogicWithCache,
} from './proofCache';
import {
  HAVE_FLOGIC_ZKP,
  ZkpFLogicProver,
  createHybridFLogicProver,
  evaluateFLogicGoal,
} from './zkpIntegration';
import {
  FLOGIC_SEMANTIC_NORMALIZER_METADATA,
  SemanticNormalizer,
  clearGlobalFLogicSemanticNormalizer,
  getGlobalFLogicSemanticNormalizer,
  normalizeFLogicSemanticGoal,
} from './semanticNormalizer';
import {
  FLOGIC_TYPES_METADATA,
  createFLogicFrame,
  createFLogicOntology,
  flogicOntologyFromDict,
  flogicOntologyToDict,
  flogicQueryFromDict,
  flogicQueryToDict,
  validateFLogicOntology,
} from './types';

Object.defineProperty(globalThis, 'crypto', { value: webcrypto, configurable: true });
Object.defineProperty(globalThis, 'TextEncoder', { value: TextEncoder, configurable: true });

const generatedProgram = `
MunicipalLaw :: LegalNorm.
CityCodeSection :: MunicipalLaw.
PortlandCityCodeSection :: CityCodeSection.
portland_city_code_1_01_010[identifier -> "Portland City Code 1.01.010", ipfs_cid -> "bafkreiff5aekddkof2im56ecdlztslhphkgmxvcrxg62lzkezttnewbb3e", source_url -> "https://www.portland.gov/code/1/01/010", jurisdiction -> "City of Portland, Oregon", state_code -> "OR", gnis -> "2411471", norm_operator -> "P", norm_type -> "permission"] : PortlandCityCodeSection.
requires_compliance(?Agent, ?Section) :- ?Section : PortlandCityCodeSection, subject_to(?Agent, ?Section).
`;

describe('F-logic parser', () => {
  it('parses generated Portland F-logic frames, classes, and rules', () => {
    const ontology = parseFLogicOntology(generatedProgram, 'Portland fixture');

    expect(ontology.warnings).toEqual([]);
    expect(ontology.classes).toMatchObject([
      { classId: 'MunicipalLaw', superclasses: ['LegalNorm'] },
      { classId: 'CityCodeSection', superclasses: ['MunicipalLaw'] },
      { classId: 'PortlandCityCodeSection', superclasses: ['CityCodeSection'] },
    ]);
    expect(ontology.frames[0]).toMatchObject({
      objectId: 'portland_city_code_1_01_010',
      isa: 'PortlandCityCodeSection',
      scalarMethods: {
        identifier: 'Portland City Code 1.01.010',
        norm_operator: 'P',
        norm_type: 'permission',
      },
    });
    expect(ontology.rules[0]).toContain('requires_compliance');
  });

  it('renders structured display rows with Portland labels', () => {
    const ontology = parseFLogicOntology(generatedProgram);
    const row = frameToDisplayRow(ontology.frames[0]);

    expect(row).toMatchObject({
      objectId: 'portland_city_code_1_01_010',
      label: 'Portland City Code 1.01.010',
      className: 'PortlandCityCodeSection',
    });
    expect(row.attributes).toContainEqual({ name: 'norm_type', value: 'permission' });
  });

  it('round-trips supported ontology structures to Ergo source', () => {
    const ontology = parseFLogicOntology(generatedProgram);
    const formatted = formatFLogicOntology(ontology);

    expect(formatted).toContain('MunicipalLaw :: LegalNorm.');
    expect(formatted).toContain('portland_city_code_1_01_010');
    expect(formatted).toContain('requires_compliance');
  });

  it('keeps unsupported statements as warnings', () => {
    const ontology = parseFLogicOntology('this is not supported.');

    expect(ontology.warnings).toEqual(['Unsupported F-logic statement: this is not supported']);
  });

  it('normalizes goal identifiers without changing variables', () => {
    expect(normalizeFLogicGoal('?Section : PortlandCityCodeSection')).toBe(
      '?Section : portland_city_code_section',
    );
  });

  it('parses all generated Portland F-logic snippets without warnings', () => {
    const rows = JSON.parse(
      readFileSync(
        resolve(
          process.cwd(),
          'public/corpus/portland-or/current/generated/logic-proof-summaries.json',
        ),
        'utf8',
      ),
    ) as Array<{ frame_logic_ergo: string }>;

    const warningCount = rows.reduce((count, row) => {
      const ontology = parseFLogicOntology(row.frame_logic_ergo);
      return count + ontology.warnings.length;
    }, 0);

    expect(warningCount).toBe(0);
  });

  it('exposes a browser-native ErgoAI wrapper for structural operations', () => {
    const wrapper = new ErgoAIWrapper('Portland wrapper');
    wrapper.addClass({
      classId: 'PortlandCityCodeSection',
      superclasses: ['CityCodeSection'],
      signatureMethods: {},
    });
    wrapper.addFrame({
      objectId: 'portland_city_code_1_01_010',
      scalarMethods: { identifier: 'Portland City Code 1.01.010' },
      setMethods: {},
      isa: 'PortlandCityCodeSection',
      isaset: ['PortlandCityCodeSection'],
    });
    wrapper.addRule('requires_compliance(?Agent, ?Section) :- ?Section : PortlandCityCodeSection.');

    expect(ERGOAI_AVAILABLE).toBe(false);
    expect(wrapper.getStatistics()).toEqual({
      ontologyName: 'Portland wrapper',
      frames: 1,
      classes: 1,
      rules: 1,
      simulationMode: true,
      ergoaiBinary: null,
    });
    expect(wrapper.getProgram()).toContain('portland_city_code_1_01_010');
    expect(wrapper.buildErgoProgram('?Section : PortlandCityCodeSection')).toContain(
      '?- ?Section : PortlandCityCodeSection.',
    );
  });

  it('fails closed for browser-local ErgoAI queries while preserving query shape', () => {
    const wrapper = new ErgoAIWrapper();
    const [first, second] = wrapper.batchQuery(['?X : Dog', '?Y : Cat']);

    expect(first).toMatchObject({
      goal: '?X : Dog',
      bindings: [],
      status: 'unknown',
    });
    expect(first.errorMessage).toContain('browser-native TypeScript runtime');
    expect(second.goal).toBe('?Y : Cat');
  });

  it('parses ErgoAI-style textual bindings deterministically', () => {
    const bindings = parseErgoOutput('% comment\n?X = rex, ?Y = Dog\nunrelated\n?X = fido');

    expect(bindings).toEqual([{ '?X': 'rex', '?Y': 'Dog' }, { '?X': 'fido' }]);
  });

  it('declares browser-native flogic_proof_cache.py parity metadata and keys cached queries', () => {
    expect(FLOGIC_PROOF_CACHE_METADATA).toMatchObject({
      sourcePythonModule: 'logic/flogic/flogic_proof_cache.py',
      browserNative: true,
      runtimeDependencies: [],
    });
    expect(FLOGIC_PROOF_CACHE_METADATA.parity).toEqual(
      expect.arrayContaining([
        'normalized_goal_ontology_keys',
        'query_option_sensitive_lookup',
        'ttl_lru_statistics',
        'fail_closed_browser_query_facade',
      ]),
    );

    const ontology = parseFLogicOntology(generatedProgram, 'Portland fixture');
    const cache = new FLogicProofCache();
    const result = {
      goal: '?Section : PortlandCityCodeSection',
      bindings: [{ '?Section': 'portland_city_code_1_01_010' }],
      status: 'success' as const,
    };

    const cid = cache.set('?Section : PortlandCityCodeSection', ontology, result, {
      maxSolutions: 1,
    });

    expect(cid).toMatch(/^browsets-/);
    expect(
      cache.computeCid('?Section : portland_city_code_section', ontology, { maxSolutions: 1 }),
    ).toBe(cid);
    expect(
      cache.get('?Section : portland_city_code_section', ontology, { maxSolutions: 1 }),
    ).toEqual(result);
    expect(
      cache.get('?Section : portland_city_code_section', ontology, { maxSolutions: 2 }),
    ).toBeUndefined();
    expect(cache.getStats()).toMatchObject({ hits: 1, misses: 1, sets: 1 });
  });

  it('uses fail-closed browser-local query caching and global helpers', () => {
    const ontology = parseFLogicOntology(generatedProgram, 'Portland fixture');
    const cache = new FLogicProofCache();

    expect(cache.query('?Section : PortlandCityCodeSection', ontology)).toMatchObject({
      goal: '?Section : PortlandCityCodeSection',
      bindings: [],
      status: 'unknown',
    });
    expect(cache.query('?Section : PortlandCityCodeSection', ontology)).toMatchObject({
      errorMessage: expect.stringContaining('browser-native TypeScript runtime'),
    });
    expect(cache.getStats()).toMatchObject({ hits: 1, sets: 1 });

    clearGlobalFLogicProofCache();
    expect(queryFLogicWithCache('?Section : PortlandCityCodeSection', ontology)).toMatchObject({
      status: 'unknown',
    });
    expect(
      getGlobalFLogicProofCache().get('?Section : PortlandCityCodeSection', ontology),
    ).toMatchObject({
      status: 'unknown',
    });
  });

  it('ports flogic_types.py dataclass defaults, dictionaries, and validation', () => {
    expect(FLOGIC_TYPES_METADATA).toMatchObject({
      sourcePythonModule: 'logic/flogic/flogic_types.py',
      browserNative: true,
      runtimeDependencies: [],
    });

    const frame = createFLogicFrame({
      objectId: 'portland_city_code_1_01_010',
      scalarMethods: { identifier: 'Portland City Code 1.01.010' },
      setMethods: { tags: ['procedure', 'general'] },
      isa: 'PortlandCityCodeSection',
    });
    const ontology = createFLogicOntology({
      name: 'Portland fixture',
      frames: [frame],
      classes: [
        {
          classId: 'PortlandCityCodeSection',
          superclasses: ['CityCodeSection'],
          signatureMethods: { identifier: 'string' },
        },
      ],
      rules: ['requires_compliance(?Agent, ?Section).'],
    });
    const query = flogicQueryFromDict({
      goal: '?Section : PortlandCityCodeSection',
      bindings: [{ '?Section': 'portland_city_code_1_01_010' }],
      status: 'success',
      error_message: 'ignored by success callers',
    });

    expect(frame.isaset).toEqual(['PortlandCityCodeSection']);
    const dict = flogicOntologyToDict(ontology);
    expect(dict.frames[0]).toMatchObject({ object_id: 'portland_city_code_1_01_010' });
    expect(dict.classes[0]).toMatchObject({ class_id: 'PortlandCityCodeSection' });
    expect(flogicOntologyFromDict(dict)).toEqual(ontology);
    expect(flogicQueryToDict(query)).toMatchObject({
      status: 'success',
      error_message: 'ignored by success callers',
    });

    const invalidOntology = {
      name: 'Invalid fixture',
      frames: [
        {
          objectId: 'section',
          scalarMethods: {},
          setMethods: {},
          isa: 'UndeclaredClass',
          isaset: ['OtherClass'],
        },
        { objectId: 'section', scalarMethods: {}, setMethods: {}, isaset: [] },
      ],
      classes: [],
      rules: [],
      warnings: [],
    };

    const result = validateFLogicOntology(invalidOntology);
    expect(result.valid).toBe(false);
    expect(result.errors).toEqual([
      'F-logic frame section isa must also appear in isaset',
      'Duplicate F-logic frame objectId: section',
    ]);
    expect(result.warnings).toEqual([
      'F-logic frame section references undeclared class UndeclaredClass',
    ]);
  });

  it('ports flogic_zkp_integration.py with local simulated ZKP certificates', async () => {
    const ontology = parseFLogicOntology(generatedProgram, 'Portland fixture');
    const direct = evaluateFLogicGoal('?Section : MunicipalLaw', ontology);
    const prover = createHybridFLogicProver({ enableZkp: true });
    const result = await prover.proveTheorem('?Section : MunicipalLaw', ontology, {
      preferZkp: true,
      privateOntology: true,
    });

    expect(HAVE_FLOGIC_ZKP).toBe(true);
    expect(direct.bindings).toEqual([{ '?Section': 'portland_city_code_1_01_010' }]);
    expect(
      evaluateFLogicGoal('?Section[identifier -> ?Identifier]', ontology).bindings[0],
    ).toMatchObject({
      '?Identifier': 'Portland City Code 1.01.010',
      '?Section': 'portland_city_code_1_01_010',
    });
    expect(result.isProved).toBe(true);
    expect(result.zkpProof?.publicInputs.ruleset_id).toBe('FLOGIC_v1');
    expect(result.toDict()).toMatchObject({
      is_proved: true,
      bindings: ['<private>'],
      method: 'flogic_zkp',
      zkp_backend: 'simulated',
    });
    expect(result.toDict().zkp_security_note).toContain('not cryptographically secure');
  });

  it('falls back to deterministic standard F-logic query mode when ZKP is disabled', async () => {
    const ontology = parseFLogicOntology(generatedProgram, 'Portland fixture');
    const prover = new ZkpFLogicProver({ enableZkp: false });
    const result = await prover.proveTheorem(
      'portland_city_code_1_01_010 : MunicipalLaw',
      ontology,
      {
        preferZkp: true,
      },
    );

    expect(result.toDict()).toMatchObject({
      is_proved: true,
      method: 'flogic_standard',
      status: 'success',
    });
    expect(prover.getStatistics()).toMatchObject({ standard_queries: 1, zkp_attempts: 0 });
  });

  it('ports semantic_normalizer.py dictionary, adapter, and singleton behavior', () => {
    const normalizer = new SemanticNormalizer({
      synonymMap: { 'city code section': 'municipal law section' },
      similarityAdapter: {
        resolveTerm(term) {
          return term === 'ordinance' ? { canonical: 'law', confidence: 0.92 } : null;
        },
      },
    });

    expect(FLOGIC_SEMANTIC_NORMALIZER_METADATA).toMatchObject({
      sourcePythonModule: 'logic/flogic/semantic_normalizer.py',
      browserNative: true,
      runtimeDependencies: [],
    });
    expect(normalizer.semanticSimilarityAvailable).toBe(true);
    expect([
      normalizer.normalizeTerm('Canine'),
      normalizer.normalizeTerm('city code section'),
      normalizer.normalizeTerm('ordinance'),
    ]).toEqual(['dog', 'municipal law section', 'law']);
    expect(
      normalizer.normalizeGoal('?X : Canine, ?Y[status -> "Permitted", citation -> ?Citation]'),
    ).toBe('?X : dog, ?Y[status -> "Permitted", citation -> ?Citation]');
    expect(normalizer.getMapSnapshot()).toMatchObject({ ordinance: 'law' });

    const failClosed = new SemanticNormalizer({
      confidenceThreshold: 0.8,
      similarityAdapter: {
        resolveTerm() {
          return { canonical: 'required', confidence: 0.4 };
        },
      },
    });

    expect(failClosed.normalizeTerm('compulsory')).toBe('compulsory');
    failClosed.addSynonym('compulsory', 'required');
    expect(failClosed.normalizeTerm('compulsory')).toBe('required');
    clearGlobalFLogicSemanticNormalizer();
    const first = getGlobalFLogicSemanticNormalizer({ synonymMap: { vehicle: 'conveyance' } });
    expect(normalizeFLogicSemanticGoal('?Thing : Vehicle')).toBe('?Thing : conveyance');
    expect(getGlobalFLogicSemanticNormalizer()).toBe(first);
  });
});

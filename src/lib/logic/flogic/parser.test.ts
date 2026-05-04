import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

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
});

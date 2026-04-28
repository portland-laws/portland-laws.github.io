import fixtures from './python-parity-fixtures.json';
import { analyzeNormativeSentence, buildDeonticFormula } from '../deontic';
import { parseFolText } from '../fol';
import { FOLConverter, type FolPredicate } from '../fol/converter';
import {
  extractLogicalRelations,
  extractPredicates,
  type ExtractedPredicates,
  type LogicalRelation,
} from '../fol/predicateExtractor';
import {
  FeatureExtractor,
  ML_CONFIDENCE_FEATURE_NAMES,
  predictMLConfidence,
  type ConfidencePredicates,
} from '../mlConfidence';
import { formatTdfolFormula, parseTdfolFormula } from '../tdfol';

type FolFixture = {
  id: string;
  kind: 'fol';
  input: string;
  python_regex_formula: string;
};

type FolConverterMlNlpFixture = {
  id: string;
  kind: 'fol_converter_ml_nlp';
  input: string;
  python_status: 'success' | 'partial';
  python_success: boolean;
  python_confidence: number;
  python_formula_string: string;
  python_predicates: FolPredicate[];
  python_quantifier_symbols: string[];
  python_operator_symbols: string[];
  python_metadata: {
    predicates_count: number;
    quantifiers_count: number;
    extracted_predicates: ExtractedPredicates;
    extracted_relations: LogicalRelation[];
    variables: string[];
    output_format: 'json';
  };
  python_warnings: string[];
  python_feature_vector: number[];
};

type DeonticFixture = {
  id: string;
  kind: 'deontic';
  input: string;
  python_norm_type: string;
  python_deontic_operator: string;
  python_formula_prefix: string;
};

type TdfolFixture = {
  id: string;
  kind: 'tdfol';
  input: string;
  python_parseable: boolean;
  python_contains: string[];
};

type MLConfidenceFixture = {
  id: string;
  kind: 'ml_confidence';
  sentence: string;
  fol_formula: string;
  predicates: ConfidencePredicates;
  quantifiers: string[];
  operators: string[];
  python_feature_vector: number[];
  python_heuristic_confidence: number;
};

type SpacyNlpFixture = {
  id: string;
  kind: 'spacy_nlp';
  input: string;
  python_predicates: ExtractedPredicates;
  python_relations: LogicalRelation[];
};

type ProofSummaryCategory =
  | 'obligation'
  | 'permission'
  | 'prohibition'
  | 'parse_success'
  | 'parse_failure'
  | 'simulated_certificate'
  | 'missing_logic'
  | 'long_flogic'
  | 'citation_match'
  | 'kg_linked_section';

type ProofSummaryFixture = {
  id: string;
  kind: 'proof_summary';
  category: ProofSummaryCategory;
  section_id: string;
  citation: string;
  title: string;
  source_text: string;
  norm_type: string | null;
  norm_operator: string | null;
  parse_status: 'success' | 'failure';
  deontic_temporal_fol: string | null;
  deontic_cognitive_event_calculus: string | null;
  frame_logic_ergo: string | null;
  zkp_backend: 'none' | 'simulated';
  zkp_verified: boolean;
  citation_matches_section: boolean;
  kg_section_id: string | null;
  notes: string;
};

type Fixture =
  | FolFixture
  | FolConverterMlNlpFixture
  | DeonticFixture
  | TdfolFixture
  | MLConfidenceFixture
  | SpacyNlpFixture
  | ProofSummaryFixture;

const proofSummaryCategories: ProofSummaryCategory[] = [
  'obligation',
  'permission',
  'prohibition',
  'parse_success',
  'parse_failure',
  'simulated_certificate',
  'missing_logic',
  'long_flogic',
  'citation_match',
  'kg_linked_section',
];

describe('Python parity fixtures', () => {
  it.each(fixtures as Fixture[])('matches fixture $id', (fixture) => {
    if (fixture.kind === 'fol') {
      const result = parseFolText(fixture.input);
      expect(result.formula).toBe(fixture.python_regex_formula);
      expect(result.validation.valid).toBe(true);
      return;
    }

    if (fixture.kind === 'fol_converter_ml_nlp') {
      const converter = new FOLConverter({ useMl: true, useNlp: true, useCache: false });
      const result = converter.convert(fixture.input);

      expect(result.status).toBe(fixture.python_status);
      expect(result.success).toBe(fixture.python_success);
      expect(result.confidence).toBeCloseTo(fixture.python_confidence, 10);
      expect(result.warnings).toEqual(fixture.python_warnings);
      expect(result.output).toBeDefined();
      expect(result.output?.formulaString).toBe(fixture.python_formula_string);
      expect(result.output?.predicates).toEqual(fixture.python_predicates);
      expect(result.output?.quantifiers.map((quantifier) => quantifier.symbol)).toEqual(
        fixture.python_quantifier_symbols,
      );
      expect(result.output?.operators.map((operator) => operator.symbol)).toEqual(
        fixture.python_operator_symbols,
      );
      expect(result.metadata).toMatchObject(fixture.python_metadata);
      const features = FeatureExtractor.extractFeatures(
        fixture.input,
        fixture.python_formula_string,
        fixture.python_metadata.extracted_predicates,
        fixture.python_quantifier_symbols,
        fixture.python_operator_symbols,
      );
      expect(features).toEqual(fixture.python_feature_vector);
      return;
    }

    if (fixture.kind === 'deontic') {
      const element = analyzeNormativeSentence(fixture.input);
      expect(element).toMatchObject({
        normType: fixture.python_norm_type,
        deonticOperator: fixture.python_deontic_operator,
      });
      expect(buildDeonticFormula(element!)).toContain(fixture.python_formula_prefix);
      return;
    }

    if (fixture.kind === 'tdfol') {
      const formula = parseTdfolFormula(fixture.input);
      const formatted = formatTdfolFormula(formula);
      for (const expected of fixture.python_contains) {
        expect(formatted).toContain(expected);
      }
      return;
    }

    if (fixture.kind === 'ml_confidence') {
      const features = FeatureExtractor.extractFeatures(
        fixture.sentence,
        fixture.fol_formula,
        fixture.predicates,
        fixture.quantifiers,
        fixture.operators,
      );
      expect(features).toHaveLength(ML_CONFIDENCE_FEATURE_NAMES.length);
      expect(features).toHaveLength(fixture.python_feature_vector.length);
      fixture.python_feature_vector.forEach((expected, index) => {
        expect(features[index]).toBeCloseTo(expected, 10);
      });
      expect(
        predictMLConfidence(
          fixture.sentence,
          fixture.fol_formula,
          fixture.predicates,
          fixture.quantifiers,
          fixture.operators,
        ),
      ).toBeCloseTo(fixture.python_heuristic_confidence, 10);
      return;
    }

    if (fixture.kind === 'spacy_nlp') {
      expect(extractPredicates(fixture.input)).toEqual(fixture.python_predicates);
      expect(extractLogicalRelations(fixture.input)).toEqual(fixture.python_relations);
      return;
    }

    expect(fixture.section_id).toMatch(/^portland_city_code_\d+_\d+_\d+$/);
    expect(fixture.citation).toMatch(/^PCC \d+\.\d+\.\d+$/);
    expect(fixture.title.length).toBeGreaterThan(0);
    expect(fixture.source_text.length).toBeGreaterThan(0);

    if (fixture.parse_status === 'failure' || fixture.category === 'missing_logic') {
      expect(fixture.deontic_temporal_fol).toBeNull();
      expect(fixture.zkp_verified).toBe(false);
    } else {
      expect(fixture.deontic_temporal_fol).toEqual(expect.any(String));
    }
  });

  it('keeps explicit Python ML confidence and spaCy NLP parity fixtures', () => {
    const parityFixtures = (fixtures as Fixture[]).filter(
      (fixture) => fixture.kind === 'ml_confidence' || fixture.kind === 'spacy_nlp',
    );

    expect(parityFixtures.map((fixture) => fixture.kind).sort()).toEqual([
      'ml_confidence',
      'spacy_nlp',
    ]);
  });

  it('keeps representative Python FOLConverter ML/NLP legal clause captures', () => {
    const converterFixtures = (fixtures as Fixture[]).filter(
      (fixture): fixture is FolConverterMlNlpFixture => fixture.kind === 'fol_converter_ml_nlp',
    );

    expect(converterFixtures.map((fixture) => fixture.id).sort()).toEqual([
      'fol_converter_ml_nlp_all_landlords_responsible',
      'fol_converter_ml_nlp_if_applicant_then_eligible',
      'fol_converter_ml_nlp_some_permits_revocable',
    ]);
  });

  it('keeps 10 representative proof summary fixtures for deterministic parser parity', () => {
    const proofSummaries = (fixtures as Fixture[]).filter(
      (fixture): fixture is ProofSummaryFixture => fixture.kind === 'proof_summary',
    );

    expect(proofSummaries).toHaveLength(10);
    expect(proofSummaries.map((fixture) => fixture.category).sort()).toEqual(
      [...proofSummaryCategories].sort(),
    );
    expect(
      proofSummaries.find((fixture) => fixture.category === 'simulated_certificate'),
    ).toMatchObject({
      zkp_backend: 'simulated',
      zkp_verified: true,
    });
    expect(
      proofSummaries.find((fixture) => fixture.category === 'long_flogic')?.frame_logic_ergo
        ?.length,
    ).toBeGreaterThan(180);
    expect(proofSummaries.find((fixture) => fixture.category === 'citation_match')).toMatchObject({
      citation_matches_section: true,
    });
    expect(
      proofSummaries.find((fixture) => fixture.category === 'kg_linked_section')?.kg_section_id,
    ).toBe('portland_city_code_16_20_130');
  });
});

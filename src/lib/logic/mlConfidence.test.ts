import {
  FeatureExtractor,
  ML_CONFIDENCE_FEATURE_NAMES,
  MLConfidenceScorer,
  predictMLConfidence,
} from './mlConfidence';

describe('browser-native ML confidence parity slice', () => {
  it('extracts the same 22 feature slots as the Python FeatureExtractor', () => {
    const features = FeatureExtractor.extractFeatures(
      'All tenants must pay rent, and some landlords may inspect.',
      '∀x (Tenant(x) → PayRent(x))',
      { nouns: ['Tenant'], verbs: ['PayRent', 'Inspect'], adjectives: [] },
      ['∀'],
      ['→', '∧'],
    );

    expect(features).toHaveLength(ML_CONFIDENCE_FEATURE_NAMES.length);
    expect(features[1]).toBe(10);
    expect(features[7]).toBe(3);
    expect(features[13]).toBe(1);
    expect(features[17]).toBe(1);
    expect(features[21]).toBeGreaterThanOrEqual(3);
  });

  it('scores logical conversions locally without server dependencies', () => {
    const high = predictMLConfidence(
      'If a tenant receives notice then the tenant must respond.',
      '∀x (Notice(x) → Respond(x))',
      { nouns: ['Tenant'], verbs: ['Respond'], adjectives: ['Notice'] },
      ['∀'],
      ['→'],
    );
    const low = predictMLConfidence('', 'P', {}, [], []);

    expect(high).toBeGreaterThan(low);
    expect(high).toBeGreaterThanOrEqual(0.7);
    expect(low).toBeLessThanOrEqual(0.3);
  });

  it('provides an in-browser training-compatible facade and importance map', () => {
    const scorer = new MLConfidenceScorer();
    const good = FeatureExtractor.extractFeatures('All people are mortal.', '∀x (Person(x) → Mortal(x))', { nouns: ['Person'], adjectives: ['Mortal'] }, ['∀'], ['→']);
    const weak = FeatureExtractor.extractFeatures('hello', 'P', {}, [], []);
    const metrics = scorer.train([good, weak], [0.95, 0.1], 0.5);

    expect(metrics).toMatchObject({ n_train: 1, n_val: 1 });
    expect(scorer.isTrained).toBe(true);
    expect(scorer.getFeatureImportance()).toHaveProperty('sentence_length');
  });
});

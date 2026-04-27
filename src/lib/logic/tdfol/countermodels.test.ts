import { parseTdfolFormula } from './parser';
import {
  extractTdfolCountermodel,
  TdfolCounterModel,
  TdfolCounterModelExtractor,
  TdfolCounterModelVisualizer,
  TdfolKripkeStructure,
  visualizeTdfolCountermodel,
} from './countermodels';

describe('TDFOL countermodels', () => {
  it('models Kripke worlds, accessibility, valuation, and JSON export', () => {
    const kripke = new TdfolKripkeStructure({ logicType: 'S4' });
    kripke.addWorld(0);
    kripke.addAccessibility(0, 1);
    kripke.setAtomTrue(1, 'Permit(x)');

    expect(kripke.getAccessibleWorlds(0)).toEqual(new Set([1]));
    expect(kripke.isAtomTrue(1, 'Permit(x)')).toBe(true);
    expect(kripke.toDict()).toEqual({
      worlds: [0, 1],
      accessibility: { '0': [1], '1': [] },
      valuation: { '0': [], '1': ['Permit(x)'] },
      initial_world: 0,
      logic_type: 'S4',
    });
    expect(JSON.parse(kripke.toJson()).logic_type).toBe('S4');
  });

  it('extracts a countermodel from an open tableaux-like branch', () => {
    const formula = parseTdfolFormula('always(Pred(x)) -> Pred(x)');
    const branch = {
      isClosed: false,
      worlds: {
        0: { id: 0, formulas: [parseTdfolFormula('Q(x)')] },
        1: { id: 1, formulas: [parseTdfolFormula('Pred(x)')] },
      },
      accessibility: { 0: [1] },
    };

    const countermodel = extractTdfolCountermodel(formula, branch, 'K');

    expect(countermodel.kripke.logicType).toBe('K');
    expect(countermodel.kripke.isAtomTrue(0, 'Q(x)')).toBe(true);
    expect(countermodel.kripke.isAtomTrue(1, 'Pred(x)')).toBe(true);
    expect(countermodel.explanation[0]).toContain('is not K-valid');
    expect(countermodel.explanation[0]).toContain('Pred(x)');
  });

  it('rejects closed branches during extraction', () => {
    const extractor = new TdfolCounterModelExtractor();

    expect(() =>
      extractor.extract(parseTdfolFormula('P(x)'), {
        isClosed: true,
        worlds: {},
        accessibility: {},
      }),
    ).toThrow('Cannot extract countermodel from closed branch');
  });

  it('renders countermodels as text, DOT, JSON, ASCII, and HTML', () => {
    const formula = parseTdfolFormula('Pred(x)');
    const kripke = new TdfolKripkeStructure({ logicType: 'D' });
    kripke.addAccessibility(0, 1);
    kripke.setAtomTrue(0, 'Q(x)');
    const countermodel = new TdfolCounterModel(formula, kripke, ['Pred(x) fails at w0']);

    expect(countermodel.toString()).toContain('Countermodel for: Pred(x)');
    expect(countermodel.toAsciiArt()).toContain('-> w0: {Q(x)}');
    expect(countermodel.toDot()).toContain('w0 -> w1;');
    expect(JSON.parse(countermodel.toJson()).kripke_structure.logic_type).toBe('D');
    expect(visualizeTdfolCountermodel(countermodel, 'compact-ascii')).toContain('Kripke(D)');
    expect(visualizeTdfolCountermodel(countermodel, 'html')).toContain('<script type="application/json" id="kripke-data">');
  });

  it('checks modal accessibility properties for visualizer summaries', () => {
    const kripke = new TdfolKripkeStructure({ logicType: 'S5' });
    kripke.addAccessibility(0, 0);
    kripke.addAccessibility(0, 1);
    kripke.addAccessibility(1, 0);
    kripke.addAccessibility(1, 1);

    const visualizer = new TdfolCounterModelVisualizer(kripke);

    expect(visualizer.getPropertyChecks()).toEqual({
      reflexive: true,
      symmetric: true,
      transitive: true,
      serial: true,
    });
    expect(visualizer.renderLogicProperties()).toContain('Expected for S5: Reflexive, Symmetric, Transitive');
    expect(visualizer.renderAsciiEnhanced()).toContain('Kripke Structure (Logic: S5)');
  });
});

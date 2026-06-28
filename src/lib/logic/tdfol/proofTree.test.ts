import type { ProofResult } from '../types';
import { visualizeTdfolProofTree } from './proofTree';
import {
  buildTdfolQuickstartVisualizerSnapshot,
  TDFOL_QUICKSTART_VISUALIZER_METADATA,
} from './quickstartVisualizer';

const proof: ProofResult = {
  status: 'proved',
  theorem: 'Permitted(Alice, DatasetAlpha)',
  method: 'tdfol-forward-chaining',
  steps: [
    {
      id: 's1',
      rule: 'UniversalInstantiation',
      premises: ['Policy<AccessReview>', 'RequestsAccess(Alice, DatasetAlpha)'],
      conclusion: 'OBLIGATION(ReviewAccess(Alice, DatasetAlpha))',
      explanation: 'Instantiate the access-review policy for Alice.',
    },
    {
      id: 's2',
      rule: 'DeonticDischarge',
      premises: ['OBLIGATION(ReviewAccess(Alice, DatasetAlpha))', 'Approved(Alice, DatasetAlpha)'],
      conclusion: 'Permitted(Alice, DatasetAlpha)',
      explanation: 'Discharge the review obligation into permission.',
    },
  ],
};

describe('TdfolProofTreeVisualizer', () => {
  it('renders ASCII, JSON, DOT, and HTML proof tree views', () => {
    const visualizer = visualizeTdfolProofTree(proof, 'detailed');

    expect(visualizer.root).toMatchObject({
      formula: 'Permitted(Alice, DatasetAlpha)',
      nodeType: 'theorem',
      ruleName: 'DeonticDischarge',
    });
    expect(visualizer.renderAscii()).toContain('Permitted(Alice, DatasetAlpha) [DeonticDischarge]');
    expect(visualizer.renderJson()).toMatchObject({
      theorem: 'Permitted(Alice, DatasetAlpha)',
      status: 'proved',
      method: 'tdfol-forward-chaining',
    });
    expect(visualizer.renderDot()).toContain('DeonticDischarge');
    expect(visualizer.renderHtml()).toContain('tdfol-proof-tree');
    expect(visualizer.renderHtml()).toContain('Policy&lt;AccessReview&gt;');
  });

  it('supports minimal labels for compact displays', () => {
    const visualizer = visualizeTdfolProofTree(proof, 'minimal');

    expect(visualizer.renderAscii()).toContain('Permitted(Alice, DatasetAlpha)');
    expect(visualizer.renderAscii()).not.toContain('[DeonticDischarge]');
  });

  it('exports browser-native graph layout, path lookup, subtrees, and SVG', () => {
    const visualizer = visualizeTdfolProofTree(proof, 'detailed');
    const graph = visualizer.renderGraphJson();

    expect(graph.nodes).toHaveLength(5);
    expect(graph.edges).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ rule: 'DeonticDischarge' }),
        expect.objectContaining({ rule: 'UniversalInstantiation' }),
      ]),
    );
    expect(
      visualizer.getLayout().find((node) => node.formula === 'Policy<AccessReview>'),
    ).toMatchObject({
      depth: 2,
      x: 464,
    });
    expect(visualizer.findPath('Policy<AccessReview>')).toEqual([
      'Permitted(Alice, DatasetAlpha)',
      'OBLIGATION(ReviewAccess(Alice, DatasetAlpha))',
      'Policy<AccessReview>',
    ]);
    expect(visualizer.getSubtree('OBLIGATION(ReviewAccess(Alice, DatasetAlpha))')).toMatchObject({
      ruleName: 'UniversalInstantiation',
      premises: expect.arrayContaining([
        expect.objectContaining({ formula: 'Policy<AccessReview>' }),
      ]),
    });
    expect(visualizer.renderSvg()).toContain('tdfol-proof-tree-svg');
    expect(visualizer.renderSvg()).toContain('Policy&lt;AccessReview&gt;');
  });

  it('ports quickstart_visualizer.py as a browser-native deterministic snapshot', () => {
    const snapshot = buildTdfolQuickstartVisualizerSnapshot();

    expect(TDFOL_QUICKSTART_VISUALIZER_METADATA).toMatchObject({
      sourcePythonModule: 'logic/TDFOL/quickstart_visualizer.py',
      runtime: 'browser-native-typescript',
      serverCallsAllowed: false,
      pythonRuntimeRequired: false,
    });
    expect(snapshot.proofStatus).toBe('proved');
    expect(snapshot.asciiTree).toContain('Permitted(Alice, DatasetAlpha) [DeonticDischarge]');
    expect(snapshot.treeJson).toMatchObject({ theorem: 'Permitted(Alice, DatasetAlpha)' });
    expect(snapshot.graphJson.edges).toEqual(
      expect.arrayContaining([expect.objectContaining({ rule: 'UniversalInstantiation' })]),
    );
    expect(snapshot.dependencyJson.statistics).toMatchObject({ num_edges: 4 });
    expect(snapshot.dot).toContain('digraph TDFOLProof');
    expect(snapshot.svg).toContain('tdfol-proof-tree-svg');
    expect(snapshot.html).toContain('tdfol-quickstart-visualizer');
    expect(snapshot.html).toContain('logic/TDFOL/quickstart_visualizer.py');
    expect(snapshot.quickstartSteps).toContain(
      'Render deterministic ASCII, JSON, DOT, SVG, and HTML outputs without Python or server calls.',
    );
  });
});

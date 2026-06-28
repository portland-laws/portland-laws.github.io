import type { ProofResult } from '../types';
import { buildTdfolDependencyGraph, type TdfolDependencyGraphJson } from './dependencyGraph';
import {
  visualizeTdfolProofTree,
  type TdfolProofTreeGraphJson,
  type TdfolVerbosityLevel,
} from './proofTree';

export interface TdfolQuickstartVisualizerMetadata {
  sourcePythonModule: 'logic/TDFOL/quickstart_visualizer.py';
  runtime: 'browser-native-typescript';
  serverCallsAllowed: false;
  pythonRuntimeRequired: false;
  outputs: Array<'ascii' | 'json' | 'dot' | 'svg' | 'html'>;
}

export interface TdfolQuickstartVisualizerOptions {
  proofResult?: ProofResult;
  title?: string;
  verbosity?: TdfolVerbosityLevel;
}

export interface TdfolQuickstartVisualizerSnapshot {
  metadata: TdfolQuickstartVisualizerMetadata;
  title: string;
  proofResult: ProofResult;
  proofStatus: ProofResult['status'];
  theorem: string;
  asciiTree: string;
  treeJson: Record<string, unknown>;
  graphJson: TdfolProofTreeGraphJson;
  dependencyJson: TdfolDependencyGraphJson;
  dot: string;
  svg: string;
  html: string;
  quickstartSteps: Array<string>;
}

export const TDFOL_QUICKSTART_VISUALIZER_METADATA: TdfolQuickstartVisualizerMetadata = {
  sourcePythonModule: 'logic/TDFOL/quickstart_visualizer.py',
  runtime: 'browser-native-typescript',
  serverCallsAllowed: false,
  pythonRuntimeRequired: false,
  outputs: ['ascii', 'json', 'dot', 'svg', 'html'],
};

export const TDFOL_QUICKSTART_VISUALIZER_PROOF: ProofResult = {
  status: 'proved',
  theorem: 'Permitted(Alice, DatasetAlpha)',
  method: 'tdfol-quickstart-visualizer',
  steps: [
    {
      id: 'quickstart-1',
      rule: 'UniversalInstantiation',
      premises: ['Policy<AccessReview>', 'RequestsAccess(Alice, DatasetAlpha)'],
      conclusion: 'OBLIGATION(ReviewAccess(Alice, DatasetAlpha))',
      explanation: 'Instantiate the access-review policy for Alice.',
    },
    {
      id: 'quickstart-2',
      rule: 'DeonticDischarge',
      premises: ['OBLIGATION(ReviewAccess(Alice, DatasetAlpha))', 'Approved(Alice, DatasetAlpha)'],
      conclusion: 'Permitted(Alice, DatasetAlpha)',
      explanation: 'Completed approval discharges the review obligation into permission.',
    },
  ],
};

export function buildTdfolQuickstartVisualizerSnapshot(
  options: TdfolQuickstartVisualizerOptions = {},
): TdfolQuickstartVisualizerSnapshot {
  const proofResult = options.proofResult ?? TDFOL_QUICKSTART_VISUALIZER_PROOF;
  const title = options.title ?? 'TDFOL Proof Visualizer Quickstart';
  const visualizer = visualizeTdfolProofTree(proofResult, options.verbosity ?? 'detailed');
  const dependencyGraph = buildTdfolDependencyGraph(proofResult);
  const asciiTree = visualizer.renderAscii('detailed');
  const snapshotWithoutHtml: Omit<TdfolQuickstartVisualizerSnapshot, 'html'> = {
    metadata: TDFOL_QUICKSTART_VISUALIZER_METADATA,
    title,
    proofResult,
    proofStatus: proofResult.status,
    theorem: proofResult.theorem,
    asciiTree,
    treeJson: visualizer.renderJson(),
    graphJson: visualizer.renderGraphJson(),
    dependencyJson: dependencyGraph.toJson(),
    dot: visualizer.renderDot(),
    svg: visualizer.renderSvg(),
    quickstartSteps: [
      'Create or load a local TDFOL proof result.',
      'Build the browser-native proof tree and dependency graph.',
      'Render deterministic ASCII, JSON, DOT, SVG, and HTML outputs without Python or server calls.',
    ],
  };
  return {
    ...snapshotWithoutHtml,
    html: renderTdfolQuickstartVisualizerHtml(snapshotWithoutHtml),
  };
}

export function renderTdfolQuickstartVisualizerHtml(
  snapshot: Omit<TdfolQuickstartVisualizerSnapshot, 'html'> | TdfolQuickstartVisualizerSnapshot,
): string {
  const payload = JSON.stringify({
    metadata: snapshot.metadata,
    proofStatus: snapshot.proofStatus,
    theorem: snapshot.theorem,
    graphJson: snapshot.graphJson,
    dependencyJson: snapshot.dependencyJson,
  });
  return [
    '<section class="tdfol-quickstart-visualizer">',
    `<h1>${escapeHtml(snapshot.title)}</h1>`,
    `<p data-proof-status="${escapeHtml(snapshot.proofStatus)}">${escapeHtml(snapshot.theorem)}</p>`,
    `<pre class="tdfol-quickstart-ascii">${escapeHtml(snapshot.asciiTree)}</pre>`,
    snapshot.svg,
    `<script type="application/json" data-source-python-module="${snapshot.metadata.sourcePythonModule}">${escapeHtml(payload)}</script>`,
    '</section>',
  ].join('');
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

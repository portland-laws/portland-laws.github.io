#!/usr/bin/env node

import { access, mkdir, readdir, stat, writeFile } from 'node:fs/promises';
import { constants as fsConstants } from 'node:fs';
import { spawn } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, '..');
const corpusRoot = path.join(repoRoot, 'public', 'corpus', 'portland-or', 'current');
const datasetId = 'justicedao/american_municipal_law';
const datasetPath = 'municipal_laws_portland_or_current_code';
const resolveBase = `https://huggingface.co/datasets/${datasetId}/resolve/main/${datasetPath}`;
const rawBase = `https://huggingface.co/datasets/${datasetId}/raw/main/${datasetPath}`;

const artifacts = [
  {
    id: 'readme',
    path: 'README.md',
    url: `${rawBase}/README.md`,
    expectedBytes: 2221,
    role: 'metadata',
  },
  {
    id: 'canonical_manifest',
    path: 'canonical/manifest.json',
    url: `${rawBase}/canonical/manifest.json`,
    expectedBytes: 6108,
    role: 'metadata',
  },
  {
    id: 'canonical_sections',
    path: 'canonical/STATE-OR.parquet',
    url: `${resolveBase}/canonical/STATE-OR.parquet`,
    expectedBytes: 5954924,
    role: 'core',
  },
  {
    id: 'faiss_index',
    path: 'canonical/STATE-OR.faiss',
    url: `${resolveBase}/canonical/STATE-OR.faiss`,
    expectedBytes: 4687917,
    role: 'core',
  },
  {
    id: 'bm25',
    path: 'canonical/STATE-OR_bm25.parquet',
    url: `${resolveBase}/canonical/STATE-OR_bm25.parquet`,
    expectedBytes: 6442722,
    role: 'core',
  },
  {
    id: 'embeddings',
    path: 'canonical/STATE-OR_embeddings.parquet',
    url: `${resolveBase}/canonical/STATE-OR_embeddings.parquet`,
    expectedBytes: 11111755,
    role: 'core',
  },
  {
    id: 'faiss_metadata',
    path: 'canonical/STATE-OR_faiss_metadata.parquet',
    url: `${resolveBase}/canonical/STATE-OR_faiss_metadata.parquet`,
    expectedBytes: 3746830,
    role: 'core',
  },
  {
    id: 'cid_index',
    path: 'canonical/STATE-OR_cid_index.parquet',
    url: `${resolveBase}/canonical/STATE-OR_cid_index.parquet`,
    expectedBytes: 5203040,
    role: 'core',
  },
  {
    id: 'kg_entities',
    path: 'canonical/STATE-OR_knowledge_graph_entities.parquet',
    url: `${resolveBase}/canonical/STATE-OR_knowledge_graph_entities.parquet`,
    expectedBytes: 912594,
    role: 'core',
  },
  {
    id: 'kg_relationships',
    path: 'canonical/STATE-OR_knowledge_graph_relationships.parquet',
    url: `${resolveBase}/canonical/STATE-OR_knowledge_graph_relationships.parquet`,
    expectedBytes: 1920315,
    role: 'core',
  },
  {
    id: 'kg_summary',
    path: 'canonical/STATE-OR_knowledge_graph_summary.json',
    url: `${rawBase}/canonical/STATE-OR_knowledge_graph_summary.json`,
    expectedBytes: 52183,
    role: 'core',
  },
  {
    id: 'ontology',
    path: 'canonical/municipal_law_ontology.json',
    url: `${rawBase}/canonical/municipal_law_ontology.json`,
    expectedBytes: 45741,
    role: 'core',
  },
  {
    id: 'logic_manifest',
    path: 'logic_proofs/manifest.json',
    url: `${rawBase}/logic_proofs/manifest.json`,
    expectedBytes: 930,
    role: 'lazy',
  },
  {
    id: 'logic_proofs',
    path: 'logic_proofs/STATE-OR_logic_proof_artifacts.parquet',
    url: `${resolveBase}/logic_proofs/STATE-OR_logic_proof_artifacts.parquet`,
    expectedBytes: 10806216,
    role: 'lazy',
  },
  {
    id: 'codex_spark_logic_manifest',
    path: 'logic_proofs_codex_spark/manifest.json',
    url: `${rawBase}/logic_proofs_codex_spark/manifest.json`,
    expectedBytes: 1412,
    role: 'lazy',
  },
  {
    id: 'codex_spark_logic_proofs',
    path: 'logic_proofs_codex_spark/STATE-OR_logic_proof_artifacts.parquet',
    url: `${resolveBase}/logic_proofs_codex_spark/STATE-OR_logic_proof_artifacts.parquet`,
    expectedBytes: 47144859,
    role: 'lazy',
  },
  {
    id: 'codex_spark_groth16_logic_manifest',
    path: 'logic_proofs_codex_spark_groth16/manifest.json',
    url: `${rawBase}/logic_proofs_codex_spark_groth16/manifest.json`,
    expectedBytes: 1467,
    role: 'lazy',
  },
  {
    id: 'codex_spark_groth16_logic_proofs',
    path: 'logic_proofs_codex_spark_groth16/STATE-OR_logic_proof_artifacts.parquet',
    url: `${resolveBase}/logic_proofs_codex_spark_groth16/STATE-OR_logic_proof_artifacts.parquet`,
    expectedBytes: 47301779,
    role: 'lazy',
  },
  {
    id: 'raw_manifest',
    path: 'raw/manifest.json',
    url: `${rawBase}/raw/manifest.json`,
    expectedBytes: 494,
    role: 'source',
  },
  {
    id: 'raw_pages',
    path: 'raw/pages.parquet',
    url: `${resolveBase}/raw/pages.parquet`,
    expectedBytes: 73592650,
    role: 'source',
  },
];

const args = new Set(process.argv.slice(2));
const force = args.has('--force');
const validateOnly = args.has('--validate-only');
const skipDownload = args.has('--skip-download') || validateOnly;
const noExtract = args.has('--no-extract');

async function exists(filePath) {
  try {
    await access(filePath, fsConstants.F_OK);
    return true;
  } catch {
    return false;
  }
}

async function downloadArtifact(artifact) {
  const target = path.join(corpusRoot, artifact.path);
  await mkdir(path.dirname(target), { recursive: true });

  const currentExists = await exists(target);
  if (currentExists && !force) {
    const current = await stat(target);
    if (current.size === artifact.expectedBytes) {
      console.log(`ok ${artifact.path} (${current.size} bytes)`);
      return;
    }
    console.log(`refresh ${artifact.path}: expected ${artifact.expectedBytes}, found ${current.size}`);
  } else {
    console.log(`download ${artifact.path}`);
  }

  const response = await fetch(artifact.url);
  if (!response.ok) {
    throw new Error(`Failed to download ${artifact.path}: ${response.status} ${response.statusText}`);
  }

  const body = Buffer.from(await response.arrayBuffer());
  if (body.length !== artifact.expectedBytes) {
    console.warn(`Downloaded ${artifact.path} with size ${body.length}; manifest expected ${artifact.expectedBytes}.`);
  }
  await writeFile(target, body);
}

async function validateArtifact(artifact) {
  const target = path.join(corpusRoot, artifact.path);
  const current = await stat(target);
  if (current.size !== artifact.expectedBytes) {
    console.warn(`${artifact.path} is ${current.size} bytes; manifest expected ${artifact.expectedBytes}.`);
  }
  return {
    id: artifact.id,
    path: artifact.path,
    bytes: current.size,
    role: artifact.role,
    sourceUrl: artifact.url,
  };
}

function run(command, args) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, { cwd: repoRoot, stdio: 'inherit' });
    child.on('error', reject);
    child.on('close', (code) => {
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(`${command} ${args.join(' ')} exited with ${code}`));
      }
    });
  });
}

async function hasPythonExtractorDeps() {
  return new Promise((resolve) => {
    const child = spawn('python3', ['-c', 'import pyarrow.parquet'], { stdio: 'ignore' });
    child.on('error', () => resolve(false));
    child.on('close', (code) => resolve(code === 0));
  });
}

async function writeManifest(validatedArtifacts) {
  const files = await readdir(corpusRoot, { recursive: true });
  const manifest = {
    schemaVersion: 1,
    generatedAt: new Date().toISOString(),
    datasetId,
    datasetPath,
    corpus: {
      jurisdiction: 'City of Portland, Oregon',
      stateCode: 'OR',
      gnis: '2411471',
      canonicalRowCount: 3052,
      embeddingModel: 'thenlper/gte-small',
      browserEmbeddingModel: 'Xenova/gte-small',
      embeddingDimension: 384,
    },
    artifacts: validatedArtifacts,
    generatedFiles: files
      .filter((file) => typeof file === 'string')
      .filter((file) => !file.endsWith('artifacts.manifest.json'))
      .sort(),
  };
  await writeFile(
    path.join(corpusRoot, 'artifacts.manifest.json'),
    `${JSON.stringify(manifest, null, 2)}\n`,
  );
}

async function main() {
  await mkdir(corpusRoot, { recursive: true });

  if (!skipDownload) {
    for (const artifact of artifacts) {
      await downloadArtifact(artifact);
    }
  }

  const validatedArtifacts = [];
  for (const artifact of artifacts) {
    validatedArtifacts.push(await validateArtifact(artifact));
  }
  if (!validateOnly) {
    await writeManifest(validatedArtifacts);
  }

  if (!noExtract) {
    if (await hasPythonExtractorDeps()) {
      await run('python3', [path.join('scripts', 'extract-portland-corpus.py'), corpusRoot]);
      const refreshedArtifacts = [];
      for (const artifact of artifacts) {
        refreshedArtifacts.push(await validateArtifact(artifact));
      }
      if (!validateOnly) {
        await writeManifest(refreshedArtifacts);
      }
    } else {
      console.warn('Skipping optimized extraction: python3 with pyarrow is not available.');
    }
  }

  console.log(`Portland corpus artifacts are ready in ${path.relative(repoRoot, corpusRoot)}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});

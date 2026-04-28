export type SearchMode = 'keyword' | 'vector' | 'hybrid';

export interface CorpusSection {
  ipfs_cid: string;
  identifier: string;
  title: string;
  text: string;
  source_url: string;
  official_cite: string;
  bluebook_citation: string;
  chapter: string;
  title_number: string;
  jsonld: string;
}

export interface CorpusEntity {
  id: string;
  type: string;
  label: string;
  properties: Record<string, unknown>;
}

export interface CorpusRelationship {
  id: string;
  source: string;
  target: string;
  type: string;
  properties?: Record<string, unknown>;
}

export interface SearchFilters {
  titleNumber?: string;
  entityTypes?: string[];
  limit?: number;
}

export interface SearchResult {
  ipfs_cid: string;
  section: CorpusSection;
  score: number;
  scoreParts: {
    keyword: number;
    vector: number;
    title: number;
    citation: number;
  };
  snippet: string;
  citation: string;
}

export interface GraphRagEvidence {
  sections: SearchResult[];
  entities: CorpusEntity[];
  relationships: CorpusRelationship[];
}

interface EmbeddingIndex {
  count: number;
  dimension: number;
  embeddingModel: string;
  browserEmbeddingModel: string;
  binary: string;
  ipfs_cids: string[];
}

interface Bm25Document {
  id: string;
  document_id: string;
  title: string;
  document_length: number;
  terms: Record<string, number>;
}

interface Bm25Payload {
  documents: Bm25Document[];
  documentFrequency: Record<string, number>;
  k1: number;
  b: number;
  avgdl: number;
  documentCount: number;
}

interface GraphAdjacency {
  outgoing: Record<string, CorpusRelationship[]>;
  incoming: Record<string, CorpusRelationship[]>;
}

export interface CorpusArtifact {
  id: string;
  path: string;
  bytes: number;
  role: string;
  sourceUrl?: string;
}

export interface PortlandCorpusManifest {
  schemaVersion: number;
  generatedAt: string;
  datasetId: string;
  datasetPath: string;
  corpus: {
    jurisdiction: string;
    name: string;
    source: string;
  };
  artifacts: CorpusArtifact[];
  generatedFiles: string[];
}

export interface CorpusState {
  sections: CorpusSection[];
  sectionByCid: Map<string, CorpusSection>;
  manifest: PortlandCorpusManifest;
}

const DEFAULT_CORPUS_BASE_URL = '/corpus/portland-or/current';
const CORPUS_BASE_URL = DEFAULT_CORPUS_BASE_URL;

let manifestPromise: Promise<PortlandCorpusManifest> | null = null;
let corpusPromise: Promise<CorpusState> | null = null;
let bm25Promise: Promise<Bm25Payload> | null = null;
let embeddingPromise: Promise<{ index: EmbeddingIndex; vectors: Float32Array }> | null = null;
let graphPromise: Promise<{
  entities: CorpusEntity[];
  entityById: Map<string, CorpusEntity>;
  relationships: CorpusRelationship[];
  adjacency: GraphAdjacency;
}> | null = null;

export async function loadPortlandCorpusManifest(): Promise<PortlandCorpusManifest> {
  if (!manifestPromise) {
    manifestPromise = fetch(`${CORPUS_BASE_URL}/artifacts.manifest.json`, { cache: 'no-store' }).then(
      async (response) => {
        if (!response.ok) {
          throw new Error(`Failed to load corpus manifest: ${response.status}`);
        }
        return response.json() as Promise<PortlandCorpusManifest>;
      },
    );
  }
  return manifestPromise;
}

export function getPortlandCorpusAssetUrl(relativePath: string, manifest: PortlandCorpusManifest): string {
  const params = new URLSearchParams({ v: manifest.generatedAt });
  return `${CORPUS_BASE_URL}/${relativePath}?${params.toString()}`;
}

export async function fetchCorpusJson<T>(relativePath: string): Promise<T> {
  const manifest = await loadPortlandCorpusManifest();
  const response = await fetch(getPortlandCorpusAssetUrl(relativePath, manifest));
  if (!response.ok) {
    throw new Error(`Failed to load corpus asset ${relativePath}: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function fetchCorpusArrayBuffer(relativePath: string): Promise<ArrayBuffer> {
  const manifest = await loadPortlandCorpusManifest();
  const response = await fetch(getPortlandCorpusAssetUrl(relativePath, manifest));
  if (!response.ok) {
    throw new Error(`Failed to load corpus asset ${relativePath}: ${response.status}`);
  }
  return response.arrayBuffer();
}

export async function loadPortlandCorpus(): Promise<CorpusState> {
  if (!corpusPromise) {
    corpusPromise = Promise.all([
      loadPortlandCorpusManifest(),
      fetchCorpusJson<CorpusSection[]>('generated/sections.json'),
    ]).then(([manifest, sections]) => ({
      sections,
      sectionByCid: new Map(sections.map((section) => [section.ipfs_cid, section])),
      manifest,
    }));
  }
  return corpusPromise;
}

async function loadBm25(): Promise<Bm25Payload> {
  if (!bm25Promise) {
    bm25Promise = fetchCorpusJson<Bm25Payload>('generated/bm25-documents.json');
  }
  return bm25Promise;
}

export async function loadPortlandEmbeddings(): Promise<{
  index: EmbeddingIndex;
  vectors: Float32Array;
}> {
  if (!embeddingPromise) {
    embeddingPromise = Promise.all([
      fetchCorpusJson<EmbeddingIndex>('generated/embedding-index.json'),
      fetchCorpusArrayBuffer('generated/embeddings.f32'),
    ]).then(([index, buffer]) => {
      const vectors = new Float32Array(buffer);
      const expectedLength = index.count * index.dimension;
      if (vectors.length !== expectedLength) {
        throw new Error(`Embedding vector length ${vectors.length} did not match ${expectedLength}`);
      }
      return { index, vectors };
    });
  }
  return embeddingPromise;
}

async function loadGraph() {
  if (!graphPromise) {
    graphPromise = Promise.all([
      fetchCorpusJson<CorpusEntity[]>('generated/entities.json'),
      fetchCorpusJson<CorpusRelationship[]>('generated/relationships.json'),
      fetchCorpusJson<GraphAdjacency>('generated/graph-adjacency.json'),
    ]).then(([entities, relationships, adjacency]) => ({
      entities,
      entityById: new Map(entities.map((entity) => [entity.id, entity])),
      relationships,
      adjacency,
    }));
  }
  return graphPromise;
}

export async function getSection(ipfs_cid: string): Promise<CorpusSection | null> {
  const { sectionByCid } = await loadPortlandCorpus();
  return sectionByCid.get(ipfs_cid) || null;
}

export async function getRelatedGraph(
  ipfs_cid: string,
  depth = 1,
): Promise<{ entities: CorpusEntity[]; relationships: CorpusRelationship[] }> {
  const graph = await loadGraph();
  const seenEntities = new Set<string>([ipfs_cid]);
  const seenRelationships = new Set<string>();
  let frontier = [ipfs_cid];

  for (let level = 0; level < depth; level += 1) {
    const nextFrontier: string[] = [];
    for (const entityId of frontier) {
      const edges = [
        ...(graph.adjacency.outgoing[entityId] || []),
        ...(graph.adjacency.incoming[entityId] || []),
      ];
      for (const edge of edges) {
        seenRelationships.add(edge.id);
        for (const candidate of [edge.source, edge.target]) {
          if (!seenEntities.has(candidate)) {
            seenEntities.add(candidate);
            nextFrontier.push(candidate);
          }
        }
      }
    }
    frontier = nextFrontier;
  }

  return {
    entities: [...seenEntities]
      .map((id) => graph.entityById.get(id))
      .filter((entity): entity is CorpusEntity => Boolean(entity)),
    relationships: graph.relationships.filter((relationship) => seenRelationships.has(relationship.id)),
  };
}

export async function searchCorpus(
  query: string,
  filters: SearchFilters = {},
  mode: SearchMode = 'hybrid',
  queryEmbedding?: Float32Array | number[],
): Promise<SearchResult[]> {
  const limit = filters.limit || 20;
  const [{ sections, sectionByCid }, keywordScores, vectorScores] = await Promise.all([
    loadPortlandCorpus(),
    mode !== 'vector' ? keywordSearch(query) : Promise.resolve(new Map<string, number>()),
    mode !== 'keyword' && queryEmbedding
      ? vectorSearch(queryEmbedding)
      : Promise.resolve(new Map<string, number>()),
  ]);

  const normalizedQuery = query.trim().toLowerCase();
  const candidateIds = new Set<string>([...keywordScores.keys(), ...vectorScores.keys()]);

  if (candidateIds.size === 0 && normalizedQuery) {
    for (const section of sections) {
      if (matchesTitleOrCitation(section, normalizedQuery)) {
        candidateIds.add(section.ipfs_cid);
      }
    }
  }

  const results: SearchResult[] = [];
  for (const cid of candidateIds) {
    const section = sectionByCid.get(cid);
    if (!section || !matchesFilters(section, filters)) {
      continue;
    }

    const keyword = keywordScores.get(cid) || 0;
    const vector = vectorScores.get(cid) || 0;
    const title = normalizedQuery && section.title.toLowerCase().includes(normalizedQuery) ? 1 : 0;
    const citation = normalizedQuery && matchesTitleOrCitation(section, normalizedQuery) ? 1 : 0;
    const score =
      mode === 'keyword'
        ? keyword + citation * 2 + title
        : mode === 'vector'
          ? vector + citation * 0.25 + title * 0.1
          : keyword + vector * 3 + citation * 2 + title;

    results.push({
      ipfs_cid: cid,
      section,
      score,
      scoreParts: { keyword, vector, title, citation },
      snippet: buildSnippet(section.text, query),
      citation: section.bluebook_citation || section.official_cite || section.identifier,
    });
  }

  return results.sort((left, right) => right.score - left.score).slice(0, limit);
}

export async function buildGraphRagEvidence(
  query: string,
  queryEmbedding?: Float32Array | number[],
  limit = 6,
): Promise<GraphRagEvidence> {
  const sections = await searchCorpus(query, { limit }, 'hybrid', queryEmbedding);
  const entityById = new Map<string, CorpusEntity>();
  const relationshipById = new Map<string, CorpusRelationship>();

  for (const result of sections) {
    const related = await getRelatedGraph(result.ipfs_cid, 1);
    for (const entity of related.entities) {
      entityById.set(entity.id, entity);
    }
    for (const relationship of related.relationships) {
      relationshipById.set(relationship.id, relationship);
    }
  }

  return {
    sections,
    entities: [...entityById.values()],
    relationships: [...relationshipById.values()],
  };
}

export async function buildSectionGraphRagEvidence(
  ipfs_cid: string,
  query: string,
  queryEmbedding?: Float32Array | number[],
  limit = 6,
): Promise<GraphRagEvidence> {
  const [{ sectionByCid }, related, retrieved] = await Promise.all([
    loadPortlandCorpus(),
    getRelatedGraph(ipfs_cid, 1),
    query.trim() ? searchCorpus(query, { limit }, 'hybrid', queryEmbedding) : Promise.resolve([]),
  ]);
  const primarySection = sectionByCid.get(ipfs_cid);
  if (!primarySection) {
    return { sections: [], entities: related.entities, relationships: related.relationships };
  }

  const sectionResults = new Map<string, SearchResult>();
  sectionResults.set(primarySection.ipfs_cid, sectionToContextResult(primarySection, query, 100));

  for (const entity of related.entities) {
    const relatedSection = sectionByCid.get(entity.id);
    if (relatedSection && relatedSection.ipfs_cid !== primarySection.ipfs_cid) {
      sectionResults.set(relatedSection.ipfs_cid, sectionToContextResult(relatedSection, query, 25));
    }
  }

  for (const result of retrieved) {
    if (sectionResults.size >= limit) break;
    sectionResults.set(result.ipfs_cid, result);
  }

  return {
    sections: [...sectionResults.values()].slice(0, limit),
    entities: related.entities,
    relationships: related.relationships,
  };
}

function sectionToContextResult(section: CorpusSection, query: string, score: number): SearchResult {
  return {
    ipfs_cid: section.ipfs_cid,
    section,
    score,
    scoreParts: {
      keyword: score,
      vector: 0,
      title: 0,
      citation: 0,
    },
    snippet: buildSnippet(section.text, query) || section.text.slice(0, 900),
    citation: section.bluebook_citation || section.official_cite || section.identifier,
  };
}

async function keywordSearch(query: string): Promise<Map<string, number>> {
  const tokens = tokenize(query);
  const scores = new Map<string, number>();
  if (tokens.length === 0) {
    return scores;
  }

  const bm25 = await loadBm25();
  for (const doc of bm25.documents) {
    let score = 0;
    for (const token of tokens) {
      const tf = doc.terms[token] || 0;
      if (!tf) {
        continue;
      }
      const df = bm25.documentFrequency[token] || 0;
      const idf = Math.log(1 + (bm25.documentCount - df + 0.5) / (df + 0.5));
      const denominator =
        tf + bm25.k1 * (1 - bm25.b + bm25.b * (doc.document_length / bm25.avgdl));
      score += idf * ((tf * (bm25.k1 + 1)) / denominator);
    }
    if (score > 0) {
      scores.set(doc.document_id, score);
    }
  }
  return scores;
}

async function vectorSearch(queryEmbedding: Float32Array | number[]): Promise<Map<string, number>> {
  const { index, vectors } = await loadPortlandEmbeddings();
  const query = queryEmbedding instanceof Float32Array ? queryEmbedding : new Float32Array(queryEmbedding);
  if (query.length !== index.dimension) {
    throw new Error(`Query embedding dimension ${query.length} did not match ${index.dimension}`);
  }

  const queryNorm = vectorNorm(query);
  const scores = new Map<string, number>();
  for (let row = 0; row < index.count; row += 1) {
    const offset = row * index.dimension;
    let dot = 0;
    let norm = 0;
    for (let col = 0; col < index.dimension; col += 1) {
      const value = vectors[offset + col];
      dot += query[col] * value;
      norm += value * value;
    }
    const similarity = dot / (queryNorm * Math.sqrt(norm) || 1);
    if (Number.isFinite(similarity)) {
      scores.set(index.ipfs_cids[row], similarity);
    }
  }
  return scores;
}

function tokenize(query: string): string[] {
  return query
    .toLowerCase()
    .split(/[^a-z0-9]+/g)
    .map((token) => token.trim())
    .filter((token) => token.length > 1);
}

function matchesFilters(section: CorpusSection, filters: SearchFilters): boolean {
  if (filters.titleNumber && section.title_number !== filters.titleNumber) {
    return false;
  }
  return true;
}

function matchesTitleOrCitation(section: CorpusSection, normalizedQuery: string): boolean {
  return [
    section.identifier,
    section.official_cite,
    section.bluebook_citation,
    section.title,
  ].some((value) => value.toLowerCase().includes(normalizedQuery));
}

function buildSnippet(text: string, query: string): string {
  const compactText = text.replace(/\s+/g, ' ').trim();
  if (!compactText) {
    return '';
  }

  const firstToken = tokenize(query)[0];
  const matchIndex = firstToken ? compactText.toLowerCase().indexOf(firstToken) : -1;
  const start = Math.max(0, matchIndex > -1 ? matchIndex - 80 : 0);
  const end = Math.min(compactText.length, start + 320);
  const prefix = start > 0 ? '...' : '';
  const suffix = end < compactText.length ? '...' : '';
  return `${prefix}${compactText.slice(start, end)}${suffix}`;
}

function vectorNorm(vector: Float32Array): number {
  let sum = 0;
  for (const value of vector) {
    sum += value * value;
  }
  return Math.sqrt(sum) || 1;
}

export function __resetPortlandCorpusCacheForTests(): void {
  manifestPromise = null;
  corpusPromise = null;
  bm25Promise = null;
  embeddingPromise = null;
  graphPromise = null;
}

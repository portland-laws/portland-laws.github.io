# Portland Legal Corpus Client-Side GraphRAG Plan

## Summary

Pivot the app from AI Town into a static, browser-only Portland City Code research site while reusing the existing Transformers.js/Web Worker inference stack.

Use the Hugging Face corpus at `justicedao/american_municipal_law`, specifically the Portland current-code artifacts: 3,052 canonical rows, BM25 parquet, 384-dimensional `thenlper/gte-small` embeddings, knowledge graph entities/relationships, and logic proof artifacts. Dataset Viewer is disabled for this dataset, so runtime must not depend on Dataset Viewer APIs.

## Progress Tracker

- [x] Create this implementation plan in `docs/`.
- [x] Add static corpus artifact ingestion and validation.
- [x] Add optimized browser artifact generation.
- [x] Add corpus data services and TypeScript contracts.
- [x] Replace AI Town first screen with Portland Code research UI.
- [x] Add hybrid keyword/vector/KG search.
- [x] Add citation-grounded GraphRAG chat.
- [x] Add proof artifact explorer.
- [x] Add norm-aware filters and proof badges to search results.
- [x] Research browser theorem-prover port. Initial browser logic package, cache/errors/validation helpers, TDFOL lexer/parser/formatter, and proof-explorer parse status are implemented.
- [x] Add plain-language proof explanations and temporal-scope summaries.
- [x] Redesign the UI as a Portland-style legal directory plus research workbench with tabs for section text, GraphRAG chat, knowledge graph, and logic proofs.
- [x] Improve accessibility with skip links, labelled landmarks/forms, ARIA tabs, live status regions, larger targets, stronger focus indicators, and reduced-motion support.

## Key Changes

- Replace the AI Town UI with a Portland Code research interface:
  - Corpus browser by title, chapter, and section.
  - Search page with keyword, vector, and KG-expanded results.
  - Section detail page with citation, source URL, text, related entities, related sections, and proof/formalization metadata.
  - Chat panel for simple corpus-grounded questions with visible citations.

- Add a static corpus build pipeline:
  - Download Hugging Face parquet/json artifacts at build time.
  - Validate row counts, join keys, embedding dimensions, and manifest metadata.
  - Emit optimized static assets under `public/corpus/portland-or/current/`.
  - Keep core assets local: canonical rows, BM25, embeddings, KG entities, KG relationships, KG summary.
  - Include logic proofs as a lazy-loaded optional artifact because they are useful but not required for V1 search.

- Add a browser corpus data layer:
  - Use DuckDB-WASM/parquet-wasm for loading parquet-backed tables where practical.
  - Convert embeddings to a compact `Float32Array` artifact plus `ipfs_cid` lookup during build.
  - Use exact cosine scan for V1 vector search; 3,052 x 384 is small enough for client-side brute force.
  - Build KG adjacency maps from `STATE-OR_knowledge_graph_entities.parquet` and `STATE-OR_knowledge_graph_relationships.parquet`.

- Reuse and generalize browser inference:
  - Keep the existing `clientLLMWorkerService` / `clientLLMWorker` architecture.
  - Refactor prompts away from NPC dialogue and toward legal-corpus GraphRAG answering.
  - Add a client embedding worker using `Xenova/gte-small`, which matches the dataset's `thenlper/gte-small` base model and runs with Transformers.js.
  - Cache loaded generation and embedding pipelines separately, with memory-aware unload controls.

- Implement client-side hybrid search:
  - BM25 search from precomputed term frequencies.
  - Vector search from browser-generated query embedding against static corpus embeddings.
  - KG search by entity label/type and one-hop/two-hop relationship expansion.
  - Hybrid ranking that combines lexical score, vector similarity, KG proximity, and citation/title matches.

- Implement GraphRAG chat:
  - Query -> hybrid retrieval -> KG expansion -> evidence pack -> local LLM answer.
  - Require answers to cite Portland City Code identifiers and source URLs.
  - Add refusal/uncertainty behavior for questions not supported by retrieved evidence.
  - Display "legal information, not legal advice" copy in the UI and keep answer scope limited to the corpus.

- Plan future theorem-prover port:
  - V1 only displays existing proof artifacts from `STATE-OR_logic_proof_artifacts.parquet`.
  - Later phases port small, pure logic primitives from `ipfs_datasets_py/ipfs_datasets_py/logic` to TypeScript/WASM.
  - Treat current ZKP certificates as simulated educational metadata, not cryptographic verification.

## Public Interfaces And Types

- Add corpus types:
  - `CorpusSection`: `ipfs_cid`, `identifier`, `title`, `text`, `source_url`, `bluebook_citation`, `chapter`, `jsonld`.
  - `CorpusEntity`: `id`, `type`, `label`, `properties`.
  - `CorpusRelationship`: `id`, `source`, `target`, `type`, `properties`.
  - `SearchResult`: `ipfs_cid`, `score`, `scoreParts`, `snippet`, `matchedEntities`, `citation`.
  - `GraphRagEvidence`: selected sections, KG entities, KG paths, retrieval scores.

- Add service APIs:
  - `loadPortlandCorpus()`
  - `searchCorpus(query, filters, mode)`
  - `getSection(ipfs_cid)`
  - `getRelatedGraph(ipfs_cid, depth)`
  - `answerWithGraphRag(question, options)`

- Add static configuration:
  - `VITE_CORPUS_BASE_URL=/corpus/portland-or/current`
  - `VITE_DEFAULT_EMBEDDING_MODEL=Xenova/gte-small`
  - `VITE_CLIENT_LLM_MODEL` keeps the existing default override behavior.

## Implementation Phases

- Phase 1: Planning and docs
  - Create this implementation plan.
  - Include milestones, status checkboxes, artifact inventory, architecture decisions, and acceptance criteria.

- Phase 2: Static corpus ingestion
  - Add the build/download script.
  - Generate static metadata, embedding matrix, CID indexes, and KG adjacency artifacts.
  - Add validation output summarizing corpus health.

- Phase 3: Search-first UI
  - Replace the first screen with a dense research interface, not a landing page.
  - Implement corpus browser, section detail, and hybrid search results.
  - Remove or isolate AI Town game-specific UI from the main route.

- Phase 4: GraphRAG chat
  - Add retrieval orchestration and evidence pack formatting.
  - Adapt the LLM worker prompt templates for citation-grounded answers.
  - Stream or progressively display local model responses where supported.

- Phase 5: Proof artifact exploration
  - Lazy-load logic proof parquet.
  - Show FOL, deontic, frame-logic, norm type/operator, and certificate metadata on section pages.
  - Add filters for sections with obligations, permissions, prohibitions, or formalization status.

- Phase 6: Browser theorem-prover research track
  - Identify portable pure-Python logic modules.
  - Define TypeScript/WASM target architecture.
  - Start with deterministic parsers, formula normalization, proof-cache lookup, and simple consistency checks before full theorem proving.

## Test Plan

- Unit tests:
  - Corpus artifact validation.
  - BM25 scoring from precomputed term frequencies.
  - Embedding normalization and cosine ranking.
  - KG adjacency expansion and deduping.
  - Hybrid ranking score composition.
  - GraphRAG prompt evidence formatting.

- Integration tests:
  - Load static corpus assets in a browser-like environment.
  - Search known citations such as `Portland City Code 1.01.010`.
  - Ask a simple supported question and verify answer citations.
  - Ask an unsupported question and verify the answer declines or asks for narrower context.

- Playwright tests:
  - App loads on desktop and mobile.
  - Search results render without overlap.
  - Section detail pages show text, citation, source link, and related graph content.
  - Chat panel remains usable while model or embedding workers are loading.

- Build checks:
  - `npm run build`
  - Existing Jest tests that remain relevant.
  - Artifact script dry-run/validate mode.

## Assumptions

- V1 prioritizes search and corpus browsing over chat polish.
- Corpus artifacts are prebuilt locally and served with the static site.
- Runtime remains fully client-side: no server API, no hosted vector DB, no server LLM.
- Exact vector scan is acceptable for V1 because the Portland corpus has only 3,052 sections.
- `Xenova/gte-small` is the browser query-embedding model because it matches the dataset's embedding base model.
- Chat answers are informational summaries of retrieved code sections, not legal advice.

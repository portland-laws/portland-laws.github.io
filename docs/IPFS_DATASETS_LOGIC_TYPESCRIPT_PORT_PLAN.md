# IPFS Datasets Logic TypeScript Port Improvement Plan

## Executive Summary

This project already contains the Portland City Code corpus, generated search assets, knowledge graph artifacts, and machine-generated logic proof summaries. The improvement track is to port the full `ipfs_datasets_py/ipfs_datasets_py/logic` module into a browser-native TypeScript/WASM logic stack. Heavyweight theorem provers, NLP dependencies, ML confidence scoring, cryptographic proof systems, and chain integrations should be replaced with TypeScript or WebAssembly implementations rather than external server-side calls.

The practical goal is to translate the entire Python logic surface area into TypeScript/WASM in phases. The runtime target is browser-native TypeScript/WebAssembly only. The app must not depend on external server-side services for logic conversion, ML/NLP confidence, proving, or verification.

Update: Python ML confidence scoring and spaCy-style NLP extraction are not optional fallback areas. They must be ported to browser-native equivalents using TypeScript, WebAssembly, Transformers.js, ONNX/WebGPU, or other local browser-compatible packages. Python can only serve as the source implementation and fixture generator during development.

## Current Project Fit

The repository is a Vite/React/TypeScript static app with existing Portland corpus support:

- `src/lib/portlandCorpus.ts` loads sections, BM25 documents, embeddings, entities, relationships, and graph adjacency from `public/corpus/portland-or/current/generated/`.
- `public/corpus/portland-or/current/generated/logic-proof-summaries.json` already exposes per-section formalization data, including `deontic_temporal_fol`, `deontic_cognitive_event_calculus`, `frame_logic_ergo`, `norm_operator`, `norm_type`, `zkp_backend`, `zkp_security_note`, and `zkp_verified`.
- `package.json` already includes browser-oriented foundations that help this port: TypeScript, Jest, Playwright, DuckDB-WASM, parquet-wasm, Transformers.js, hnswlib-wasm, and Vite workers.
- `docs/PORTLAND_LEGAL_CORPUS_IMPLEMENTATION_PLAN.md` already identifies proof artifact exploration and browser theorem-prover research as future phases.

The Python source tree has a broad logic surface:

- Foundation: `logic/types`, `logic/common`, `logic/config.py`, `logic/batch_processing.py`.
- FOL: `logic/fol`, including text-to-FOL conversion, parser utilities, predicate extraction, and output formatters.
- Deontic: `logic/deontic`, including legal-text-to-deontic conversion and normative conflict helpers.
- TDFOL: `logic/TDFOL`, including AST types, parser, converter, prover, inference rules, proof cache, proof visualization, security validator, and performance tooling.
- CEC/DCEC: `logic/CEC`, including event calculus, modal/cognitive inference, native prover machinery, NL policy compilers, and bridges.
- F-logic: `logic/flogic`, including frame/class/query/ontology types and ErgoAI rendering.
- Integration: `logic/integration`, `logic/integrations`, `search/logic_integration`, and GraphRAG-specific bridge code.
- ZKP: `logic/zkp`, including deterministic canonicalization, statement/witness structures, verifier/prover abstractions, Groth16/FFI backends, EVM integration, and simulated backends.
- External provers: `logic/external_provers`, including Z3, CVC5, E Prover, Vampire, Lean, Coq, and routing.
- Operational modules: API server, CLI, security, observability, monitoring, dashboards, benchmarks.

## Guiding Principle

Port behavior first, but account for every file.

The TypeScript target should be a clean client-side domain library that preserves the Python module's semantics without blindly copying Python layout. Browser code should be deterministic, inspectable, offline-capable, and tested against Python parity fixtures. Anything that depends on subprocesses, Python ML packages, prover binaries, secrets, chain RPC, or native dependencies must receive a TypeScript/WASM replacement. Temporary capability reporting is allowed only while a module is mid-port, not as the final state.

## Target Outcomes

1. Add first-class TypeScript types for Portland logic artifacts.
2. Load and index proof summaries alongside existing corpus data.
3. Parse the generated TDFOL, DCEC, and F-logic strings into lightweight ASTs or structured views.
4. Validate formulas and proof metadata deterministically in the browser.
5. Add norm-aware filters and ranking signals to search.
6. Add a proof explorer UI that explains obligations, permissions, prohibitions, temporal operators, supporting code sections, and generated certificate metadata.
7. Add client-side reasoning that grows from bounded forward chaining into full TDFOL/CEC/DCEC parity.
8. Replace Python as the authoritative formalization generator once TypeScript/WASM parity is proven.
9. Port Python ML confidence scoring and spaCy NLP extraction to browser-native ML/NLP.
10. Port external prover bridges and ZKP backends to browser-native WASM or equivalent local packages.

## Portability Matrix

| Python area | TypeScript port recommendation | Why |
| --- | --- | --- |
| `logic/types` | Port directly | Mostly enums, dataclasses, protocol-like shapes. These map well to TypeScript discriminated unions and interfaces. |
| `logic/common/errors.py` | Port directly | Standard error hierarchy improves client diagnostics. |
| `logic/common/bounded_cache.py` | Port directly | Useful for parsed formula caches and proof summary indexes. Browser implementation is straightforward with `Map`, TTL, and LRU bookkeeping. |
| `logic/common/validators.py` | Port selectively | Formula and text validation are useful. Python-specific validation hooks can stay behind. |
| `logic/common/converters.py` | Port as interfaces, not class clone | Browser code should expose composable converter functions and small services rather than inherited Python-style base classes. |
| `logic/TDFOL/tdfol_core.py` | Port directly | AST, operators, terms, formulas, substitution, and free-variable analysis are the best TypeScript core. |
| `logic/TDFOL/tdfol_parser.py` | Port directly, with tests | Recursive descent parsing and tokenization are portable. This unlocks proof explorer and validation. |
| `logic/TDFOL/tdfol_converter.py` | Port selectively | TDFOL-to-display JSON, TDFOL-to-FOL, and TDFOL-to-TPTP rendering are useful. DCEC bridge can be partial. |
| `logic/TDFOL/tdfol_inference_rules.py` | Port a small rule subset | Basic propositional, deontic, and temporal checks are useful; full parity can wait. |
| `logic/TDFOL/tdfol_prover.py` | Port only a lightweight prover | Full theorem proving is a research track. Start with bounded forward chaining and explanation traces. |
| `logic/TDFOL/proof_tree_visualizer.py` | Port concepts | Render proof trees in React rather than export DOT/HTML files from library code. |
| `logic/fol/utils/fol_parser.py` | Port directly | Regex-based quantifier/operator parsing and formatting are browser-friendly. |
| `logic/fol/utils/predicate_extractor.py` | Port selectively | Regex extraction is portable. spaCy/NLP extraction is not. |
| `logic/fol/utils/nlp_predicate_extractor.py` | Browser-native parity track after V1 | Reproduce spaCy extraction behavior where possible via browser NLP substitutes, Transformers.js, or WASM. Python can generate development fixtures only; it must not be a runtime service. |
| `logic/fol/converter.py` | Port as browser converter facade, then add ML/NLP parity | Keep regex fallback, validation, confidence heuristics, and output formatting in V1. Later, match Python `use_ml` and `use_nlp` behavior where feasible. Skip IPFS cache integrations in-browser. |
| `logic/deontic/utils/deontic_parser.py` | Port directly if regex/pattern-based | Norm extraction from legal text is valuable for Portland sections and can be tested against generated artifacts. |
| `logic/deontic/converter.py` | Port selectively, then add browser-native ML/NLP parity | Deontic operator extraction, exceptions, obligations, permissions, prohibitions, and confidence heuristics are high value. Later phases should compare confidence and extraction outputs against Python ML/spaCy-enabled fixtures. |
| `logic/ml_confidence.py` | Browser-native parity track after V1 | Browser V1 uses heuristics. Long-term goal is model-compatible TypeScript/Transformers.js/WASM inference with Python-generated fixtures used only for development comparison. |
| `logic/deontic/knowledge_base.py` | Port selectively | Useful if reduced to in-memory indexed norms by section CID. |
| `logic/flogic/flogic_types.py` | Port directly | Frame, class, query, ontology, and Ergo rendering are simple and valuable for display. |
| `logic/flogic/semantic_normalizer.py` | Port selectively | Helpful for normalizing frame names and relation labels. |
| `logic/zkp/canonicalization.py` | Port directly | Deterministic canonicalization, hashing, and field mapping are useful for verifying generated metadata consistency. Use Web Crypto or a small SHA-256 fallback. |
| `logic/zkp/statement.py` | Port directly | Statement/witness JSON schemas and circuit ref parsing are portable. Witness handling should remain build-time or local-only. |
| `logic/zkp/zkp_verifier.py` | Port simulated verifier only at first | Browser should verify metadata shape and simulated certificates honestly, not claim cryptographic verification. |
| `logic/zkp/groth16*`, EVM files | Do not port in V1 | Native/crypto/chain concerns are too heavy for the current static app. Revisit with WASM/snarkjs only after requirements are clear. |
| `logic/CEC/native` | Research/WASM later | Large inference engine with many rules. Client V1 should parse and display DCEC strings, not implement all CEC reasoning. |
| `logic/CEC/nl` | Do not port in V1 | Natural-language policy compilation is not needed for browsing existing generated artifacts. |
| `logic/external_provers` | Do not call from browser V1 | Depends on external binaries/services. Replace only when a browser-native WASM prover is chosen. No server API dependency. |
| `logic/integration/*bridge*` | Port boundary types and result contracts | Useful to keep API compatibility, but implementation should delegate to TS core or Python build step. |
| `logic/security`, `observability`, `api_server`, `cli` | Do not port, or replace with app-native concerns | Browser app already has its own deployment/runtime model. |

## Proposed TypeScript Architecture

Add a new `src/lib/logic/` package:

```text
src/lib/logic/
  index.ts
  types.ts
  errors.ts
  cache.ts
  proofArtifacts.ts
  tdfol/
    ast.ts
    lexer.ts
    parser.ts
    formatter.ts
    validate.ts
    converter.ts
    reasoner.ts
  fol/
    parser.ts
    predicateExtractor.ts
    formatter.ts
    converter.ts
  deontic/
    types.ts
    parser.ts
    converter.ts
    conflicts.ts
  flogic/
    types.ts
    parser.ts
    formatter.ts
  zkp/
    canonicalization.ts
    statement.ts
    simulatedVerifier.ts
  graph/
    proofGraph.ts
    normIndex.ts
```

The public API should stay small:

```ts
loadLogicProofSummaries(): Promise<LogicProofSummary[]>
getLogicProofForSection(ipfsCid: string): Promise<LogicProofSummary | null>
parseTdfolFormula(source: string): TdfolFormula
validateLogicProofSummary(summary: LogicProofSummary): LogicValidationResult
buildNormIndex(summaries: LogicProofSummary[]): NormIndex
searchByNorm(query: NormQuery): LogicProofSummary[]
explainNorm(summary: LogicProofSummary): LogicExplanation
verifySimulatedCertificate(summary: LogicProofSummary): SimulatedVerificationResult
```

## Data Model Improvements

Add TypeScript contracts for the existing generated artifact:

```ts
export type NormOperator = 'O' | 'P' | 'F' | 'unknown';
export type NormType = 'obligation' | 'permission' | 'prohibition' | 'unknown';
export type FormalizationStatus = 'success' | 'partial' | 'failed' | 'unknown';

export interface LogicProofSummary {
  ipfs_cid: string;
  identifier: string;
  title: string;
  formalization_scope: string;
  fol_status: FormalizationStatus;
  deontic_status: FormalizationStatus;
  deontic_temporal_fol: string;
  deontic_cognitive_event_calculus: string;
  frame_logic_ergo: string;
  norm_operator: NormOperator;
  norm_type: NormType;
  zkp_backend: 'simulated' | 'groth16' | 'unknown';
  zkp_security_note: string;
  zkp_verified: boolean;
}
```

Derived indexes:

- `proofByCid`: map section CID to proof summary.
- `proofByIdentifier`: map Portland citation to proof summary.
- `normByOperator`: `O`, `P`, `F`.
- `formalizationStatusCounts`: success/partial/failed/unknown counts.
- `proofParseStatus`: TDFOL/DCEC/F-logic parse success by section.
- `sectionLogicSignals`: search ranking signals derived from norm type, status, and operator.

## Integration With Existing Corpus Service

Extend `src/lib/portlandCorpus.ts` or add a sibling `src/lib/portlandLogic.ts`.

Recommended split:

- Keep `portlandCorpus.ts` focused on sections, BM25, embeddings, and KG.
- Add `portlandLogic.ts` for proof summaries, norm indexes, and parsed formula caches.
- Add shared ID helpers for `ipfs_cid`, `identifier`, and Portland citation normalization.

New corpus-level APIs:

```ts
getSectionWithLogic(ipfsCid: string): Promise<{
  section: CorpusSection | null;
  proof: LogicProofSummary | null;
  relatedGraph: { entities: CorpusEntity[]; relationships: CorpusRelationship[] };
}>

searchCorpusWithLogic(
  query: string,
  filters: SearchFilters & LogicSearchFilters,
  mode: SearchMode,
  queryEmbedding?: Float32Array | number[],
): Promise<SearchResult[]>
```

Logic-aware search filters:

```ts
export interface LogicSearchFilters {
  normOperators?: NormOperator[];
  normTypes?: NormType[];
  formalizationStatuses?: FormalizationStatus[];
  requireVerifiedCertificate?: boolean;
  requireParseableTdfol?: boolean;
}
```

## UI Improvements Enabled By The Port

1. Proof artifact explorer
   - Section-level panel showing TDFOL, DCEC, F-logic, norm type, operator, status, and certificate note.
   - Parse status badges with precise errors.
   - Toggle between raw source, formatted AST, and plain-English explanation.

2. Norm-aware search
   - Filters for obligations, permissions, prohibitions, formalization status, and certificate metadata.
   - Search result badges for norm type and proof status.
   - Ranking boost when query terms match norm semantics such as "must", "may", "prohibited", "deadline", or "penalty".

3. Logic graph view
   - Start with the existing KG adjacency.
   - Add proof-derived nodes: section, norm, actor, action, condition, temporal operator, certificate.
   - Keep this bounded and inspectable; no force-directed graph is required for V1.

4. Explanation layer
   - Translate `O`, `P`, `F`, `always`, `eventually`, `SubjectTo`, and `ComplyWith` into short user-facing labels.
   - Always label generated formalizations as machine-generated candidates.
   - Always distinguish simulated educational certificates from cryptographic proof verification.

5. GraphRAG improvements
   - Add logic facts to the evidence pack.
   - Prefer citations with successful formalizations when the user asks normative questions.
   - Let the answer cite both code text and logic metadata, with clear caveats.

## Implementation Phases

### Phase 0: Inventory And Baseline

- [x] Add this plan to `docs/`.
- [x] Record the exact generated proof summary schema from `public/corpus/portland-or/current/generated/logic-proof-summaries.json`.
- [ ] Add a small script or test fixture with 10 representative proof summaries: obligation, permission, prohibition, parse success, parse failure, simulated certificate, missing logic, long F-logic, citation match, KG-linked section.
- [x] Decide whether logic code lives in `src/lib/logic/` or a package-style `src/logic/`.

Acceptance criteria:

- There is a typed inventory of all fields consumed by the app.
- No runtime dependency on the Python package is introduced.
- Existing search behavior remains unchanged.

### Phase 1: Proof Summary Loader And Types

- [x] Add `src/lib/portlandLogic.ts`.
- [x] Add `LogicProofSummary` and related enums/unions.
- [x] Implement `loadLogicProofSummaries()`, `getLogicProofForSection()`, and summary count helpers.
- [x] Cache the loaded proof summaries like the existing corpus service does.
- [x] Add Jest tests for loading, indexing, and missing-section behavior.

Acceptance criteria:

- The app can join any section to its proof summary by `ipfs_cid`.
- Tests verify at least one known citation such as `Portland City Code 1.01.010`.
- Logic artifacts remain lazy-loaded.

### Phase 2: TypeScript Logic Foundation

- [x] Port common logic enums and data shapes from `logic/types`.
- [x] Add `LogicError`, `LogicParseError`, `LogicValidationError`, and `LogicVerificationError`.
- [x] Port bounded TTL/LRU cache for parsed formulas.
- [x] Add schema guards for proof summary fields.
- [x] Add normalization helpers for identifiers, predicate names, and citations.

Acceptance criteria:

- Invalid artifact rows fail with actionable validation errors.
- Parsed formula cache has deterministic eviction and no unbounded growth.
- TypeScript exposes discriminated unions instead of loose `Record<string, unknown>` where possible.

### Phase 3: TDFOL AST, Lexer, Parser, Formatter

- [x] Port the TDFOL term/formula model from `tdfol_core.py`.
- [x] Port tokenization and recursive descent parsing from `tdfol_parser.py`.
- [x] Support ASCII and symbolic operator aliases where feasible.
- [x] Format ASTs back to compact source and display-friendly JSON.
- [x] Implement free variable analysis and basic substitution.
- [x] Add fixtures from generated Portland formulas.

Acceptance criteria:

- At least 95 percent of generated `deontic_temporal_fol` strings parse or produce classified parse errors.
- Parsed formulas round-trip to a stable normalized string.
- Parser errors include position, token, and expected token class.

### Phase 4: FOL And Deontic Lightweight Conversion

- [x] Port regex-based quantifier and logical operator parsing from `fol/utils/fol_parser.py`.
- [x] Port predicate-name normalization and simple FOL formatting.
- [x] Port deontic operator extraction for must/shall/required/may/permitted/prohibited/shall not.
- [x] Add a browser deontic converter facade for short clauses.
- [x] Add confidence heuristics but do not port Python ML scoring.
- [ ] Add explicit Python ML confidence and spaCy NLP parity fixtures.
- [x] Decide which parity path to use: browser-native replacement or WASM only for runtime; Python fixtures are development-only.

Acceptance criteria:

- The TypeScript converter can classify simple Portland-style legal clauses as obligation, permission, or prohibition.
- It can explain why an operator was selected using matched phrases.
- It never overwrites the authoritative generated artifact without explicit user action.
- It documents where browser heuristics differ from Python ML/spaCy outputs.

### Phase 4B: Browser-Native Python ML And spaCy Parity Track

- [ ] Capture Python `FOLConverter(use_ml=True, use_nlp=True)` outputs for representative legal clauses as development fixtures only.
- [ ] Capture Python `DeonticConverter(use_ml=True)` confidence outputs for the same fixtures as development fixtures only.
- [ ] Add parity fixtures with raw text, regex-only output, spaCy-enabled output, ML confidence, and expected tolerances.
- [x] Evaluate browser substitutes for spaCy predicate extraction, including Transformers.js token classification or dependency-light NLP packages.
- [x] Decide that ML confidence must run in-browser or from precomputed static artifacts; no runtime Python service is allowed.
- [x] Add a compatibility mode that surfaces `nlpUnavailable` or `mlUnavailable` rather than silently pretending full parity.
- [x] Define acceptance thresholds: exact matches for operator classification, approximate matches for confidence scores, and documented divergences for predicate spans.

Acceptance criteria:

- Python ML/spaCy parity is measurable with fixtures, but runtime execution remains browser-native.
- Browser fallback behavior is explicit in API results and UI copy.
- The TypeScript implementation can run without Python; Python-enhanced outputs may be compared only in development or CI fixture-generation workflows.

### Phase 5: F-Logic Display And Semantic Normalization

- [x] Port `FLogicFrame`, `FLogicClass`, `FLogicQuery`, and `FLogicOntology` concepts.
- [x] Parse the subset of `frame_logic_ergo` currently generated for Portland sections.
- [x] Render frames as structured tables: object, class, attributes, rules.
- [x] Normalize generated object IDs back to Portland citations when possible.

Acceptance criteria:

- F-logic strings in proof summaries can be displayed as structured metadata.
- Unknown or unsupported Ergo syntax remains available as raw source with a parse warning.

### Phase 6: Simulated Certificate And Canonicalization Checks

- [x] Port text normalization and deterministic hashing concepts from `zkp/canonicalization.py`.
- [x] Port `Statement` shape and circuit reference parsing from `zkp/statement.py`.
- [x] Add `verifySimulatedCertificate()` that checks metadata consistency only.
- [x] Rename UI language so `zkp_verified: true` with `zkp_backend: simulated` is shown as "simulated certificate present", not "cryptographically verified".

Acceptance criteria:

- The app cannot accidentally imply real cryptographic verification for simulated artifacts.
- Hash/canonicalization helpers are deterministic across browsers.
- Tests cover whitespace normalization and axiom ordering behavior.

### Phase 7: Lightweight Reasoning

- [x] Add a small in-memory `LogicKnowledgeBase` keyed by section CID.
- [x] Add bounded forward chaining for facts and simple implications.
- [x] Add contradiction hints for obvious norm conflicts: same actor/action/condition with `O` and `F`.
- [x] Add temporal summary helpers for always/eventually/next/until.
- [x] Add proof trace output for any inferred result.

Acceptance criteria:

- Reasoning is bounded by step count and time budget.
- Every inferred hint includes source sections and rule names.
- The UI labels these outputs as heuristic/local reasoning unless backed by generated artifacts.

### Phase 8: Search And GraphRAG Integration

- [x] Add logic filters to the search service layer. UI wiring is deferred to the Portland research screen.
- [x] Add norm-aware score parts to logic-aware search results.
- [x] Add proof facts to GraphRAG evidence packs.
- [x] Add prompts or answer formatting that distinguish code text, KG facts, generated formalization, and local reasoning.
- [x] Add unsupported-question handling for queries not grounded in retrieved code.

Acceptance criteria:

- Search can answer "show prohibitions about retaliation" with norm-aware results.
- GraphRAG evidence includes citations and proof metadata.
- Answers remain grounded in retrieved Portland Code sections.

### Phase 9: Python Parity Harness

- [x] Create a parity test fixture generated from selected Python outputs.
- [x] Compare TypeScript parser/formatter/converter outputs against Python outputs for fixed examples.
- [x] Add a validation command that can be run after corpus regeneration.
- [x] Track intentional divergences in a markdown table.

Acceptance criteria:

- Parity failures are visible in CI or local test output.
- The TypeScript port can evolve without silently drifting from generated artifacts.

### Phase 10: WASM Or Service Research

- [x] Evaluate whether any external prover should run in-browser via WASM.
- [x] Evaluate `z3-solver`/Z3 WASM, cvc5 WASM availability, Tau Prolog, or custom Datalog for limited use cases.
- [x] Evaluate `snarkjs` only if real browser-side proof verification becomes a product requirement.
- [x] Reject serverless/API runtime dependency for V1; use browser-native WASM only when a prover is truly required.

Acceptance criteria:

- A written decision record exists before adding heavy prover dependencies.
- Bundle-size, offline behavior, security, and legal-copy implications are documented.

## What Should Stay Python For Now

Keep these outside the browser V1 runtime until browser-native replacements exist:

- Full CEC and DCEC native prover behavior unless ported to TypeScript/WASM.
- External prover orchestration for Z3, CVC5, E Prover, Vampire, Lean, and Coq unless a browser-native WASM package is selected.
- Groth16 proof generation, FFI backends, EVM harnesses, and chain registry code unless implemented with browser-native libraries.
- spaCy-based NLP extraction and Python ML confidence scoring unless reproduced with browser-native NLP/ML.
- API server, CLI, dashboards, Prometheus/OpenTelemetry integrations.
- IPFS-backed proof cache writes and distributed processing.

## TypeScript Port Estimate

Reasonable V1 TypeScript port:

- 100 percent of shared types needed by the UI.
- 100 percent of proof summary loading, indexing, validation, and display helpers.
- 80-90 percent of TDFOL core AST/parser/formatter behavior needed for generated Portland formulas.
- 60-70 percent of regex FOL/deontic extraction behavior, focused on legal-code clauses.
- 70-80 percent of F-logic data modeling and display rendering for generated frame snippets.
- 50-60 percent of ZKP canonicalization/statement metadata behavior.
- 10-20 percent of prover behavior, intentionally limited to bounded local reasoning and explanation traces.

Not realistic for V1 TypeScript:

- Full CEC native prover parity.
- Full TDFOL prover parity across all inference rules.
- External prover bridge parity.
- Cryptographic proof generation.
- Python NLP/ML parity, now tracked as browser-native Phase 4B rather than omitted entirely.

## Testing Strategy

Unit tests:

- Proof summary schema guards and indexes.
- TDFOL tokenization, parsing, formatting, substitution, and free-variable analysis.
- FOL quantifier/operator parsing and predicate normalization.
- Deontic phrase extraction and norm classification.
- F-logic frame parsing/rendering.
- ZKP canonicalization and simulated verification wording.
- Cache TTL/LRU behavior.

Integration tests:

- Load corpus plus logic proofs and join by CID.
- Search with norm filters.
- Build a GraphRAG evidence pack with logic metadata.
- Validate generated proof summaries and report parse failures.

Playwright tests:

- Proof panel renders on desktop and mobile.
- Search filters do not overlap or resize unexpectedly.
- Raw and structured logic views remain readable for long formulas.
- Simulated certificate copy is visible where relevant.

Parity tests:

- Fixed fixtures from `ipfs_datasets_py` outputs.
- Generated Portland proof summary samples.
- Round-trip normalized formulas.
- Known failures documented instead of ignored.

## Risk Register

| Risk | Mitigation |
| --- | --- |
| Over-porting the Python module creates a large, fragile browser bundle. | Port only UI-serving primitives first; use dynamic imports for logic parsing. |
| Formalization output may be machine-generated and imperfect. | Label all logic artifacts as candidate formalizations and keep original legal text primary. |
| Simulated ZKP metadata may be mistaken for real crypto verification. | Use explicit UI copy and API names such as `verifySimulatedCertificate`. |
| Parser parity may drift from Python. | Add fixture-based parity tests and document intentional differences. |
| TDFOL syntax includes Unicode operators. | Support both symbolic and ASCII aliases; normalize internally. |
| External prover expectations may creep into client code. | Define a `ProverBackend` interface but ship only local bounded reasoning in V1. |
| Licensing may affect reuse. | Review `ipfs_datasets_py/LICENSE` and this repo's `LICENSE` before copying substantive code. Prefer clean-room TypeScript where needed. |

## Documentation Deliverables

- `docs/IPFS_DATASETS_LOGIC_TYPESCRIPT_PORT_PLAN.md`: this plan.
- `docs/LOGIC_ARTIFACT_SCHEMA.md`: generated proof summary schema and examples.
- `docs/LOGIC_PORT_PARITY.md`: Python-to-TypeScript parity matrix and divergences.
- `docs/LOGIC_REASONING_LIMITATIONS.md`: user-facing limitations, safety notes, and certificate wording.
- `docs/LOGIC_WASM_RESEARCH.md`: decision record for any prover or crypto WASM dependency.

## Recommended First Pull Request

The first implementation PR should be intentionally small:

1. Add `src/lib/portlandLogic.ts`.
2. Add TypeScript proof summary types and lazy loader.
3. Add indexes by CID, identifier, norm operator, and norm type.
4. Add validation with warnings for simulated certificates.
5. Add Jest tests using a tiny fixture.
6. Add a minimal proof metadata panel to the existing Portland section detail UI, if that UI is already ready.

That PR gives the project immediate product value without committing to a full theorem prover port.

# Logic Port Parity

## Scope

This document tracks parity between the TypeScript/WASM logic port and the full `ipfs_datasets_py` logic module.

Current parity is focused on deterministic, browser-safe behavior, but the end goal is full Python logic module parity in TypeScript/WASM. The current implemented slice includes:

- FOL regex quantifier/operator parsing.
- FOL regex predicate extraction, logical relation extraction, variable allocation, and formatter helpers.
- Browser-native `logic/ml_confidence.py` feature extraction, deterministic confidence scoring, training-compatible facade, and feature-importance reporting.
- Deontic operator classification and simple formula construction.
- Deontic analyzer and knowledge-base primitives for browser-native norm extraction, grouping, conflict summaries, rule inference, and compliance checks.
- Deontic graph and support-map primitives for browser-native rule/source/authority graphs, conflict detection, reasoning rows, and motion-style support maps.
- Python-style common converter lifecycle for TypeScript converters: statuses, result shape, validation, bounded local cache, batch conversion, async wrapper, and chained converters.
- Common proof cache, feature detection, and utility monitor concepts, mapped to browser-native TypeScript.
- Shared security package for browser-local input validation, sliding-window rate limiting, LLM-style circuit breakers, and structured in-memory audit events.
- Observability package for structured JSON logs, context propagation, Prometheus-style metrics export, and in-memory OpenTelemetry-style traces.
- Initial TDFOL inference rules and bounded forward-chaining prover for deterministic browser proof search.
- Initial TDFOL proof explanation, dependency graph, and proof tree visualization helpers.
- Initial TDFOL security validation, performance metrics, profiler, dashboard, and performance engine helpers.
- TDFOL parsing/formatting for generated Portland formulas.
- F-logic parsing for generated frame snippets.
- ZKP canonicalization and simulated certificate metadata checks.

Python ML confidence scoring and spaCy NLP extraction are explicitly tracked as a browser-native parity target. Python may be used to produce development fixtures, but the production app must not call a Python service or any other server-side NLP/ML endpoint.

## Fixture Location

Parity fixtures live in:

- `src/lib/logic/parity/python-parity-fixtures.json`
- `src/lib/logic/parity/parity.test.ts`

Run them with:

```bash
npm run validate:logic-port
```

## Known Divergences

| Area | Current TypeScript Behavior | Python Behavior / Target | Status |
| --- | --- | --- | --- |
| Common converters | `LogicConverter`, `ConversionResult`, validation result, cache, batch, async wrapper, and `ChainedConverter` ported in browser-native TypeScript. | Full converter lifecycle parity, including monitoring/IPFS-compatible metadata where browser-safe. | Partially ported; no server calls. |
| Common proof cache | Deterministic browser content IDs, local TTL/LRU cache, prover/config-specific lookup, invalidation, global cache, and stats. | Python CID/IPFS-backed proof cache semantics. | Local browser cache ported; IPFS backend parity remains Phase 15. |
| Common feature detection | Browser capability detector plus Python optional dependency facade that does not import server-side modules. | `find_spec` optional dependency probing in Python. | Browser equivalent ported. |
| Shared security | Text/formula/list validation, `RateLimiter`, `LLMCircuitBreaker`, global breaker registry, and structured audit event helpers are ported without filesystem/server dependencies. | `logic/security/input_validation.py`, `rate_limiting.py`, `llm_circuit_breaker.py`, and `audit_log.py`. | Browser-local parity ported; persistent audit sinks remain app-integration work. |
| Observability | Structured logging schema/context helpers, event/error/performance/MCP tool log helpers, JSON-lines parsing/filtering, Prometheus-style metrics collector, and in-memory OTel-style spans/traces/Jaeger export. | `logic/observability/structured_logging.py`, `metrics_prometheus.py`, and `otel_integration.py`. | Browser-local parity ported; external collector/exporter integration remains follow-up work. |
| FOL predicate extraction | Regex noun/verb/adjective extraction, relation extraction, variable allocation, and formula construction from extracted parts. | `fol/utils/predicate_extractor.py` and relation portions of `fol/utils/fol_parser.py`. | Ported for deterministic regex path; NLP path remains Phase 13. |
| FOL formatting | FOL/deontic JSON, Prolog, TPTP, defeasible, text, and aggregate format helpers. | `fol/utils/logic_formatter.py`. | Ported for deterministic formatter path. |
| Deontic analyzer | Corpus statement extraction, entity grouping, statistics, action similarity, and direct/conditional/jurisdictional/temporal conflict detection. | `deontic/analyzer.py`. | Ported for deterministic regex path. |
| Deontic knowledge base | Parties, actions, time intervals, propositions, statements, rule inference, and compliance checks. | `deontic/knowledge_base.py`. | Ported as browser-native TypeScript primitives. |
| Deontic graph and support map | Node/rule graph, modality/node distributions, rule assessment, gap summaries, conflict detection, graph builders from matrix/findings/statements, dictionary/JSON export, and support-map entries with facts/filings. | `deontic/graph.py` and `deontic/support_map.py`. | Ported as browser-native TypeScript primitives. |
| TDFOL inference rules | Rule interface plus initial Modus Ponens, Modus Tollens, hypothetical syllogism, conjunction elimination, double-negation, universal modus ponens, existential instantiation/generalization, universal generalization, temporal K/T, deontic K/D, prohibition equivalence, and obligation weakening. | Full `TDFOL/inference_rules/*` parity. | Initial deterministic propositional, first-order, temporal, and deontic rule subset ported; full rule inventory remains Phase 11. |
| TDFOL converter | Stable TDFOL formatting, FOL projection with explicit temporal/deontic projection warnings, DCEC s-expression conversion, TPTP-style output, JSON output, batch conversion, and metadata. | `tdfol_converter.py`. | Initial browser-native converter ported; exact Python fixture parity for all converter targets remains Phase 11. |
| TDFOL expansion rules | Tableaux expansion context/result/rule interfaces plus AND, OR, IMPLIES, IFF, NOT rule registry and selector. | `expansion_rules.py`. | Browser-native propositional expansion rules ported. |
| TDFOL prover | Bounded forward-chaining prover with proof steps, unknown, and timeout results. | Full `tdfol_prover.py` strategies, modal tableaux, CEC delegation, proof cache, and first-order reasoning. | Initial browser prover ported; full parity remains Phase 11. |
| TDFOL proving strategies | `TdfolProverStrategy`, forward-chaining strategy, backward-chaining implication-goal reduction, bidirectional backward-first/forward-fallback search, local CEC delegate translation/proof subset, modal-tableaux strategy, priority/cost selector, multi-strategy ranking, selected-strategy proof facade, timeout and derived-formula budgets. | `TDFOL/strategies/base.py`, `forward_chaining.py`, `backward_chaining.py`, `bidirectional.py`, `cec_delegate.py`, `modal_tableaux.py`, and `strategy_selector.py`. | Initial browser-native strategy layer ported; deeper CEC native inference and first-order strategy parity remain Phase 11/12. |
| TDFOL optimization | Indexed knowledge base by type/operator/complexity/predicate, automatic strategy heuristics, cache-aware optimized prover, worker/ZKP accounting flags, and optimization stats. | `tdfol_optimization.py`. | Initial browser-native optimization facade ported; real ZKP acceleration and parallel proof search require TS/WASM implementations. |
| TDFOL modal tableaux | World/branch model, K/T/D/S4/S5 accessibility, propositional expansion, temporal/deontic modal expansion, closure checks, validity results, and countermodel-compatible open branches. | `modal_tableaux.py`. | Initial browser-native tableaux core ported; full expansion-rule diagnostics and strategy integration remain Phase 11. |
| TDFOL countermodels | Kripke structures, open-branch countermodel extraction, valuation/accessibility exports, DOT/JSON/ASCII/HTML renderers, and modal property checks. | `countermodels.py` and `countermodel_visualizer.py`. | Initial browser-native countermodel slice ported; modal tableaux integration and richer interactive renderer parity remain Phase 11. |
| TDFOL proof explanation and graphing | Text explanations, reasoning chains, statistics, dependency graph JSON/DOT, topological order, path lookup, ASCII/JSON/DOT/HTML proof tree views. | `proof_explainer.py`, `formula_dependency_graph.py`, and `proof_tree_visualizer.py`. | Initial browser-native slice ported; rich interactive/rendering parity remains Phase 11. |
| TDFOL security validation | Formula size/depth/operator/variable checks, rate limiting, sanitization, resource checks, ZKP proof audit, and security reports. | `security_validator.py`. | Initial browser-native slice ported; complete enterprise parity remains Phase 11. |
| TDFOL performance metrics | Timing samples, memory samples, counters, gauges, histograms, statistical summaries, export, and global collector helpers. | `performance_metrics.py`. | Initial browser-native metrics collector ported. |
| TDFOL performance profiler | Repeated timing profiles, optional browser memory snapshots, bottleneck classification, benchmark suites, baseline regression accounting, and text/JSON/HTML report strings. | `performance_profiler.py`. | Initial browser-native profiler ported; cProfile, flamegraph, and richer timeline parity remain Phase 11. |
| TDFOL performance dashboard | Proof metrics, time-series metrics, aggregated stats, strategy comparisons, JSON export, self-contained HTML dashboard strings, formula complexity/type helpers, and clear/reset. | `performance_dashboard.py`. | Initial browser-native dashboard ported; Chart.js-style rich visualization parity remains Phase 11. |
| TDFOL performance engine | Metrics aggregation, operation profiling, self-contained dashboard HTML strings, JSON/Prometheus-style export, strategy comparison, regression checks, profiler history, and reset. | `tdfol_performance_engine.py`. | Initial browser-native orchestration engine ported; richer browser timeline/flamegraph parity remains Phase 11. |
| FOL NLP extraction | Regex-only extraction plus capability reporting. | Browser-native parity for `FOLConverter(use_nlp=True)`, likely via Transformers.js, ONNX/WebGPU, or WASM NLP. | Planned Phase 13, no server calls. |
| ML confidence core | Python-compatible 22-slot feature extraction, fallback confidence scoring, training facade, and feature-importance reporting are ported in browser-native TypeScript. | `logic/ml_confidence.py` with browser/WASM model artifact loading as the remaining enhancement. | Initial deterministic parity ported; no server calls. |
| FOL confidence | `FOLConverter(use_ml=True)` routes through the browser-native ML confidence scorer. | XGBoost/LightGBM model parity through browser-compatible serialized weights or WASM/ONNX artifact import. | Initial deterministic parity ported; trained model artifact parity remains Phase 13. |
| Deontic confidence | Deontic parser/converter confidence now routes through the browser-native ML confidence scorer with norm-derived predicates/operators. | Python ML confidence behavior for deontic/legal text conversion. | Initial deterministic parity ported; trained model artifact parity remains Phase 13. |
| TDFOL proving | Parser, formatter, substitution, and local helper reasoning only. | Full TDFOL prover/inference-rule parity. | Planned Phase 11. |
| CEC/DCEC | Parser, formatter, analyzer, DCEC cleaning/preprocessing helpers, DCEC parse-token/prefixing helpers, DCEC type/namespace/container helpers, DCEC core term/formula helpers, DCEC string integration pipeline, DCEC prototype namespace, DCEC temporal finite-trace evaluator/state helpers, DCEC natural-language pattern converter, DCEC English grammar facade, syntax tree utilities, grammar loader/engine, enhanced DCEC grammar parser, native inference rules for deterministic propositional, first-order, modal, expanded temporal/deontic, cognitive, resolution, and specialized expressions plus extended prover-core rules for distribution, association, transposition, material implication, Clavius, idempotence, disjunction commutativity, common knowledge, common belief, fixed-point induction, and modal necessitation, including `until`/`since` temporal syntax; ShadowProver problem parser for TPTP `fof`/`cnf` and custom problem files; opt-in generative rules for conjunction/eventuality/generalization, belief/knowledge conjunction, addition/disjunction introduction, obligation conjunction, possibility introduction, and necessity conjunction; initial DCEC advanced modal/temporal/deontic/combined inference layer; initial fluent/event state manager; initial discrete event calculus with `Happens`, `Initiates`, `Terminates`, `Releases`, `ReleasedAt`, `HoldsAt`, and `Clipped`; initial context manager with discourse state, entity tracking, anaphora resolution, CEC expression ingestion, segmentation, and coherence scoring; initial ambiguity resolver with syntax-tree adapters, parse ranking, semantic scoring, and statistical bigram scoring; initial ShadowProver facade over local forward proving, K/T/D/S4/S5 modal tableaux, problem proving, cache/statistics, and cognitive rule subset; modal tableaux; and countermodels for K/T/D/S4/S5 CEC fragments; bounded forward prover with proof steps and budgets; quantified Portland-style DCEC proof support through universal modus ponens; CEC proof cache; CEC lemma generation and reuse cache; CEC native shared type/protocol/statistics helpers; CEC proof optimization; CEC/ZKP hybrid proof integration; proof explainer; proof dependency graph and tree visualizer; performance dashboard, metrics, profiling engine, and profiler reports; CEC native error hierarchy and safe error wrappers; security validator/error-hardening facade; forward/cached-forward/backward/bidirectional/hybrid strategy selector; and initial TDFOL-to-CEC local delegate proof subset for direct facts, implication reduction, and deontic prohibition equivalence. | Native CEC/DCEC reasoning parity. | Expanded browser-native adapter, DCEC cleaning/parsing/type/namespace/core/integration/prototype/temporal-evaluation/NL-pattern/enhanced-grammar/English-grammar helpers, syntax tree utility, grammar loader/engine, problem-parser, propositional/first-order/modal/temporal/deontic/cognitive/resolution/specialized/extended prover-core/common-knowledge rule slices, advanced DCEC inference layer, fluent/event state slice, event-calculus slice, context-manager slice, ambiguity-resolver slice, shadow-prover slice, modal tableaux/countermodel slice, bounded prover, cache, lemma generation/reuse, native type/protocol/stat helpers, proof optimization, CEC/ZKP hybrid integration, explainer, graph/tree visualization, dashboard, metrics/profiling/reporting, CEC native error handling, security validation, and strategy selector and adaptive proof strategies ported; advanced strategies and full prover parity remain Phase 12. |
| ZKP | Deterministic metadata/canonicalization and simulated verification. | Groth16/EVM/backend parity through browser-native crypto/WASM. | Planned Phase 14. |

## Acceptance Rules

- Operator classification should match exactly for deterministic fixtures.
- FOL regex formula strings should match exactly for deterministic fixtures.
- TDFOL generated Portland formulas must parse at or above the threshold in `generatedFixtures.test.ts`.
- ML/spaCy parity may use tolerance bands and documented span differences once development fixtures are captured from Python.

## Runtime Policy

- Runtime logic features must run browser-native.
- No production feature may call a Python service, hosted prover, hosted NLP endpoint, or server-side confidence scorer.
- While browser-native NLP parity is incomplete, APIs must return temporary port-status flags such as `nlpUnavailable`. Browser-native ML confidence now has an initial deterministic TypeScript port, so `mlUnavailable` should remain false unless a caller requires a missing trained artifact.
- Python-generated parity data is allowed only as static development/CI fixture input.
- A capability flag is a temporary port-status signal, not an acceptable final replacement for the Python feature.

# Logic Port Parity

## Scope

This document tracks parity between the TypeScript/WASM logic port and the full `ipfs_datasets_py` logic module.

Current parity is focused on deterministic, browser-safe behavior, but the end goal is full Python logic module parity in TypeScript/WASM. The current implemented slice includes:

- FOL regex quantifier/operator parsing.
- FOL regex predicate extraction, logical relation extraction, variable allocation, and formatter helpers.
- Deontic operator classification and simple formula construction.
- Deontic analyzer and knowledge-base primitives for browser-native norm extraction, grouping, conflict summaries, rule inference, and compliance checks.
- Python-style common converter lifecycle for TypeScript converters: statuses, result shape, validation, bounded local cache, batch conversion, async wrapper, and chained converters.
- Common proof cache, feature detection, and utility monitor concepts, mapped to browser-native TypeScript.
- Initial TDFOL inference rules and bounded forward-chaining prover for deterministic browser proof search.
- Initial TDFOL proof explanation, dependency graph, and proof tree visualization helpers.
- Initial TDFOL security validation and performance metrics helpers.
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
| FOL predicate extraction | Regex noun/verb/adjective extraction, relation extraction, variable allocation, and formula construction from extracted parts. | `fol/utils/predicate_extractor.py` and relation portions of `fol/utils/fol_parser.py`. | Ported for deterministic regex path; NLP path remains Phase 13. |
| FOL formatting | FOL/deontic JSON, Prolog, TPTP, defeasible, text, and aggregate format helpers. | `fol/utils/logic_formatter.py`. | Ported for deterministic formatter path. |
| Deontic analyzer | Corpus statement extraction, entity grouping, statistics, action similarity, and direct/conditional/jurisdictional/temporal conflict detection. | `deontic/analyzer.py`. | Ported for deterministic regex path. |
| Deontic knowledge base | Parties, actions, time intervals, propositions, statements, rule inference, and compliance checks. | `deontic/knowledge_base.py`. | Ported as browser-native TypeScript primitives. |
| TDFOL inference rules | Rule interface plus initial Modus Ponens, Modus Tollens, hypothetical syllogism, conjunction elimination, double-negation, temporal K/T, deontic K/D, prohibition equivalence, and obligation weakening. | Full `TDFOL/inference_rules/*` parity. | Initial deterministic rule subset ported; full rule inventory remains Phase 11. |
| TDFOL prover | Bounded forward-chaining prover with proof steps, unknown, and timeout results. | Full `tdfol_prover.py` strategies, modal tableaux, CEC delegation, proof cache, and first-order reasoning. | Initial browser prover ported; full parity remains Phase 11. |
| TDFOL proving strategies | `TdfolProverStrategy`, forward-chaining strategy, priority/cost selector, multi-strategy ranking, selected-strategy proof facade, timeout and derived-formula budgets. | `TDFOL/strategies/base.py`, `forward_chaining.py`, and `strategy_selector.py`. | Initial browser-native strategy layer ported; backward chaining, modal tableaux, CEC delegate replacement, and bidirectional strategy parity remain Phase 11. |
| TDFOL optimization | Indexed knowledge base by type/operator/complexity/predicate, automatic strategy heuristics, cache-aware optimized prover, worker/ZKP accounting flags, and optimization stats. | `tdfol_optimization.py`. | Initial browser-native optimization facade ported; real ZKP acceleration and parallel proof search require TS/WASM implementations. |
| TDFOL modal tableaux | World/branch model, K/T/D/S4/S5 accessibility, propositional expansion, temporal/deontic modal expansion, closure checks, validity results, and countermodel-compatible open branches. | `modal_tableaux.py`. | Initial browser-native tableaux core ported; full expansion-rule diagnostics and strategy integration remain Phase 11. |
| TDFOL countermodels | Kripke structures, open-branch countermodel extraction, valuation/accessibility exports, DOT/JSON/ASCII/HTML renderers, and modal property checks. | `countermodels.py` and `countermodel_visualizer.py`. | Initial browser-native countermodel slice ported; modal tableaux integration and richer interactive renderer parity remain Phase 11. |
| TDFOL proof explanation and graphing | Text explanations, reasoning chains, statistics, dependency graph JSON/DOT, topological order, path lookup, ASCII/JSON/DOT/HTML proof tree views. | `proof_explainer.py`, `formula_dependency_graph.py`, and `proof_tree_visualizer.py`. | Initial browser-native slice ported; rich interactive/rendering parity remains Phase 11. |
| TDFOL security validation | Formula size/depth/operator/variable checks, rate limiting, sanitization, resource checks, ZKP proof audit, and security reports. | `security_validator.py`. | Initial browser-native slice ported; complete enterprise parity remains Phase 11. |
| TDFOL performance metrics | Timing samples, memory samples, counters, gauges, histograms, statistical summaries, export, and global collector helpers. | `performance_metrics.py`. | Initial browser-native metrics collector ported. |
| FOL NLP extraction | Regex-only extraction plus capability reporting. | Browser-native parity for `FOLConverter(use_nlp=True)`, likely via Transformers.js, ONNX/WebGPU, or WASM NLP. | Planned Phase 13, no server calls. |
| FOL confidence | Validation plus deterministic heuristics only. | Browser-native parity for `FOLConverter(use_ml=True)`. | Planned Phase 13, no server calls. |
| Deontic confidence | Heuristic score from subject/action/condition/temporal extraction. | Browser-native parity for Python ML confidence. | Planned Phase 13, no server calls. |
| TDFOL proving | Parser, formatter, substitution, and local helper reasoning only. | Full TDFOL prover/inference-rule parity. | Planned Phase 11. |
| CEC/DCEC | Display/metadata path only. | Native CEC/DCEC reasoning parity. | Planned Phase 12. |
| ZKP | Deterministic metadata/canonicalization and simulated verification. | Groth16/EVM/backend parity through browser-native crypto/WASM. | Planned Phase 14. |

## Acceptance Rules

- Operator classification should match exactly for deterministic fixtures.
- FOL regex formula strings should match exactly for deterministic fixtures.
- TDFOL generated Portland formulas must parse at or above the threshold in `generatedFixtures.test.ts`.
- ML/spaCy parity may use tolerance bands and documented span differences once development fixtures are captured from Python.

## Runtime Policy

- Runtime logic features must run browser-native.
- No production feature may call a Python service, hosted prover, hosted NLP endpoint, or server-side confidence scorer.
- While browser-native ML/NLP parity is incomplete, APIs must return temporary port-status flags such as `nlpUnavailable` or `mlUnavailable`.
- Python-generated parity data is allowed only as static development/CI fixture input.
- A capability flag is a temporary port-status signal, not an acceptable final replacement for the Python feature.

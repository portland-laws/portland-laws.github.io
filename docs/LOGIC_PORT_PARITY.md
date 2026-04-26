# Logic Port Parity

## Scope

This document tracks parity between the TypeScript logic port and selected `ipfs_datasets_py` logic behavior.

Current parity is focused on deterministic, browser-safe behavior:

- FOL regex quantifier/operator parsing.
- Deontic operator classification and simple formula construction.
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
| FOL NLP extraction | Regex-only extraction plus capability reporting. | Browser-native approximation of `FOLConverter(use_nlp=True)`, likely via Transformers.js or a dependency-light NLP package. | Planned Phase 4B, no server calls. |
| FOL confidence | Validation plus deterministic heuristics only. | Browser-native approximation of `FOLConverter(use_ml=True)`. | Planned Phase 4B, no server calls. |
| Deontic confidence | Heuristic score from subject/action/condition/temporal extraction. | Browser-native approximation of Python ML confidence. | Planned Phase 4B, no server calls. |
| TDFOL proving | Parser, formatter, substitution, and local helper reasoning only. | Python has broader TDFOL prover/inference rules. | V1 intentionally limited. |
| CEC/DCEC | Display/metadata path only. | Python has native CEC/DCEC reasoning. | Keep Python/service for now. |
| ZKP | Deterministic metadata/canonicalization and simulated verification. | Python includes additional Groth16/EVM/backends. | Browser V1 intentionally non-cryptographic. |

## Acceptance Rules

- Operator classification should match exactly for deterministic fixtures.
- FOL regex formula strings should match exactly for deterministic fixtures.
- TDFOL generated Portland formulas must parse at or above the threshold in `generatedFixtures.test.ts`.
- ML/spaCy parity may use tolerance bands and documented span differences once development fixtures are captured from Python.

## Runtime Policy

- Runtime logic features must run browser-native.
- No production feature may call a Python service, hosted prover, hosted NLP endpoint, or server-side confidence scorer.
- If browser-native ML/NLP is unavailable, APIs must return capability flags such as `nlpUnavailable` or `mlUnavailable`.
- Python-generated parity data is allowed only as static development/CI fixture input.

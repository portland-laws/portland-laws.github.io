# Logic Port Parity

## Scope

This document tracks parity between the TypeScript logic port and selected `ipfs_datasets_py` logic behavior.

Current parity is focused on deterministic, browser-safe behavior:

- FOL regex quantifier/operator parsing.
- Deontic operator classification and simple formula construction.
- TDFOL parsing/formatting for generated Portland formulas.
- F-logic parsing for generated frame snippets.
- ZKP canonicalization and simulated certificate metadata checks.

Python ML confidence scoring and spaCy NLP extraction are explicitly tracked as a later parity target.

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
| FOL NLP extraction | Regex-only extraction. | `FOLConverter(use_nlp=True)` can use spaCy when available. | Planned Phase 4B. |
| FOL confidence | Validation plus deterministic heuristics only. | `FOLConverter(use_ml=True)` may use ML confidence scoring. | Planned Phase 4B. |
| Deontic confidence | Heuristic score from subject/action/condition/temporal extraction. | Python can use ML confidence if available. | Planned Phase 4B. |
| TDFOL proving | Parser, formatter, substitution, and local helper reasoning only. | Python has broader TDFOL prover/inference rules. | V1 intentionally limited. |
| CEC/DCEC | Display/metadata path only. | Python has native CEC/DCEC reasoning. | Keep Python/service for now. |
| ZKP | Deterministic metadata/canonicalization and simulated verification. | Python includes additional Groth16/EVM/backends. | Browser V1 intentionally non-cryptographic. |

## Acceptance Rules

- Operator classification should match exactly for deterministic fixtures.
- FOL regex formula strings should match exactly for deterministic fixtures.
- TDFOL generated Portland formulas must parse at or above the threshold in `generatedFixtures.test.ts`.
- ML/spaCy parity may use tolerance bands and documented span differences once fixtures are captured from Python.


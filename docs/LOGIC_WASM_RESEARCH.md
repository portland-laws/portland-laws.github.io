# Logic WASM And Service Research

## Decision

Do not add heavy theorem-prover or cryptographic WASM dependencies casually, but do plan to use TypeScript/WASM/browser-native packages to complete parity with the Python logic module. Do not add server-side prover, NLP, ML, or verification calls. The runtime target is browser-native TypeScript/WebAssembly only.

Use TypeScript for:

- Proof artifact loading and validation.
- TDFOL/FOL/deontic/F-logic parsing and display.
- Lightweight bounded reasoning.
- Deterministic canonicalization and simulated certificate checks.

Port in later phases with browser-native replacements:

- Full CEC/DCEC inference.
- External prover orchestration.
- Full TDFOL theorem proving.
- Groth16 proof generation and EVM/on-chain verification workflows.
- spaCy and Python ML confidence parity until browser substitutes are chosen.

## Evaluated Options

| Option | Fit | Notes |
| --- | --- | --- |
| Z3 WASM / `z3-solver` | Candidate for full external-prover parity | Useful for bounded SMT checks; manage bundle size with dynamic imports/workers. |
| cvc5 WASM | Candidate for full external-prover parity | Similar tradeoffs to Z3; evaluate for formulas Z3 does not cover well. |
| Tau Prolog / Datalog-style engine | Good candidate for local rules | Better fit for forward-chaining and F-logic-like rule demos. |
| `snarkjs` | Candidate for Groth16 parity | Use only with clear circuit/verifier artifact strategy and strong UI wording. |
| Server-side Python prover API | Rejected for runtime | It would violate the browser-native/no external service requirement. |
| Static precomputed artifacts | Acceptable | Keeps runtime offline-friendly as long as the browser does not call an external service. |

## Required Decision Record Before Adding WASM

Before adding a prover or crypto WASM dependency, document:

- Expected user workflow.
- Bundle size and load-time impact.
- Offline behavior.
- Security model.
- Legal copy/caveats.
- Whether outputs are advisory, heuristic, simulated, or cryptographically verified.
- Test fixtures comparing TypeScript/WASM/Python outputs.
- Confirmation that no external server-side runtime call is introduced.

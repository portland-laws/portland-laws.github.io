# Logic WASM And Service Research

## Decision

Do not add heavy theorem-prover or cryptographic WASM dependencies to the browser bundle in V1. Also do not add server-side prover, NLP, ML, or verification calls. The runtime target is browser-native TypeScript/WebAssembly only.

Use TypeScript for:

- Proof artifact loading and validation.
- TDFOL/FOL/deontic/F-logic parsing and display.
- Lightweight bounded reasoning.
- Deterministic canonicalization and simulated certificate checks.

Keep outside browser V1 until browser-native replacements exist:

- Full CEC/DCEC inference.
- External prover orchestration.
- Full TDFOL theorem proving.
- Groth16 proof generation and EVM/on-chain verification workflows.
- spaCy and Python ML confidence parity until browser substitutes are chosen.

## Evaluated Options

| Option | Fit | Notes |
| --- | --- | --- |
| Z3 WASM / `z3-solver` | Possible later | Useful for bounded SMT checks, but bundle size and async initialization need a clear product need. |
| cvc5 WASM | Possible later | Similar tradeoffs to Z3; avoid until proof queries require it. |
| Tau Prolog / Datalog-style engine | Good candidate for local rules | Better fit for small forward-chaining and F-logic-like rule demos than full theorem proving. |
| `snarkjs` | Only if real browser-side verification is required | Do not add while current artifacts are simulated educational certificates. |
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

# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-vector-8h-20260518T072401Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-vector-8h-20260518T072401Z-autoencoder.jsonl`
- TODO count: `3`

## TODOs
- `e7cd1d77bd93cce5`
  action: `add_deterministic_parser_rule`
  role: `program_synthesis`
  target: `modal.compiler`
  scope: `compiler_parser`
  bundle: `{"action":"add_deterministic_parser_rule","family_pairs":[],"program_synthesis_scope":"compiler_parser","target_component":"modal.compiler"}`
  vector_bundle: `e7cd1d77bd93cce5` score `1.0`
  loss: `parser_formula_count` = `1.0`
  objective: Create a golden parser case for legal text that produced no modal formulas.
  samples: `us-code-2-453-868ad5bf81742f35`
- `870116aac0e04789`
  action: `add_deterministic_parser_rule`
  role: `program_synthesis`
  target: `modal.compiler`
  scope: `compiler_parser`
  bundle: `{"action":"add_deterministic_parser_rule","family_pairs":[],"program_synthesis_scope":"compiler_parser","target_component":"modal.compiler"}`
  vector_bundle: `e7cd1d77bd93cce5` score `0.909627`
  loss: `symbolic_validity_penalty` = `0.25`
  objective: Add a deterministic parser rule or fixture for legal text that failed symbolic validation.
  samples: `us-code-9-6-725aa2302c64ab87`
- `8d7bc9cf3e181ce9`
  action: `add_deterministic_parser_rule`
  role: `program_synthesis`
  target: `modal.compiler`
  scope: `compiler_parser`
  bundle: `{"action":"add_deterministic_parser_rule","family_pairs":[],"program_synthesis_scope":"compiler_parser","target_component":"modal.compiler"}`
  vector_bundle: `e7cd1d77bd93cce5` score `0.908484`
  loss: `symbolic_validity_penalty` = `0.25`
  objective: Add a deterministic parser rule or fixture for legal text that failed symbolic validation.
  samples: `us-code-43-1656.-ee86a662b13291c8`

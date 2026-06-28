# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-vector-8h-20260518T072401Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-vector-8h-20260518T072401Z-autoencoder.jsonl`
- TODO count: `3`

## TODOs
- `c2eaf8709a0a07c5`
  action: `add_deterministic_parser_rule`
  role: `program_synthesis`
  target: `modal.compiler`
  scope: `compiler_parser`
  bundle: `{"action":"add_deterministic_parser_rule","family_pairs":[],"program_synthesis_scope":"compiler_parser","target_component":"modal.compiler"}`
  vector_bundle: `c2eaf8709a0a07c5` score `1.0`
  loss: `parser_formula_count` = `1.0`
  objective: Create a golden parser case for legal text that produced no modal formulas.
  samples: `us-code-25-478-1-c2fe462e0462e875`
- `ddcc7a0efc62d6ad`
  action: `add_deterministic_parser_rule`
  role: `program_synthesis`
  target: `modal.compiler`
  scope: `compiler_parser`
  bundle: `{"action":"add_deterministic_parser_rule","family_pairs":[],"program_synthesis_scope":"compiler_parser","target_component":"modal.compiler"}`
  vector_bundle: `c2eaf8709a0a07c5` score `0.906359`
  loss: `symbolic_validity_penalty` = `0.25`
  objective: Add a deterministic parser rule or fixture for legal text that failed symbolic validation.
  samples: `us-code-42-6930.-5842e7569af665c8`
- `4786fc340439dba0`
  action: `add_deterministic_parser_rule`
  role: `program_synthesis`
  target: `modal.compiler`
  scope: `compiler_parser`
  bundle: `{"action":"add_deterministic_parser_rule","family_pairs":[],"program_synthesis_scope":"compiler_parser","target_component":"modal.compiler"}`
  vector_bundle: `c2eaf8709a0a07c5` score `0.905156`
  loss: `symbolic_validity_penalty` = `0.25`
  objective: Add a deterministic parser rule or fixture for legal text that failed symbolic validation.
  samples: `us-code-46-60101.-6bea2346c1c5229c`

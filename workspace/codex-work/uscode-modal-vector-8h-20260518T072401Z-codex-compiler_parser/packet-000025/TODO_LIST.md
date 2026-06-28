# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-vector-8h-20260518T072401Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-vector-8h-20260518T072401Z-autoencoder.jsonl`
- TODO count: `3`

## TODOs
- `664ba16b033deb6b`
  action: `add_deterministic_parser_rule`
  role: `program_synthesis`
  target: `modal.compiler`
  scope: `compiler_parser`
  bundle: `{"action":"add_deterministic_parser_rule","family_pairs":[],"program_synthesis_scope":"compiler_parser","target_component":"modal.compiler"}`
  vector_bundle: `664ba16b033deb6b` score `1.0`
  loss: `parser_formula_count` = `1.0`
  objective: Create a golden parser case for legal text that produced no modal formulas.
  samples: `us-code-7-431-b2d3ec880a4d889f`
- `2e605b586474ff31`
  action: `add_deterministic_parser_rule`
  role: `program_synthesis`
  target: `modal.compiler`
  scope: `compiler_parser`
  bundle: `{"action":"add_deterministic_parser_rule","family_pairs":[],"program_synthesis_scope":"compiler_parser","target_component":"modal.compiler"}`
  vector_bundle: `664ba16b033deb6b` score `0.912653`
  loss: `symbolic_validity_penalty` = `0.25`
  objective: Add a deterministic parser rule or fixture for legal text that failed symbolic validation.
  samples: `us-code-6-257-73184bd2fbf238f5`
- `c174baaf07698e96`
  action: `add_deterministic_parser_rule`
  role: `program_synthesis`
  target: `modal.compiler`
  scope: `compiler_parser`
  bundle: `{"action":"add_deterministic_parser_rule","family_pairs":[],"program_synthesis_scope":"compiler_parser","target_component":"modal.compiler"}`
  vector_bundle: `664ba16b033deb6b` score `0.912072`
  loss: `symbolic_validity_penalty` = `0.25`
  objective: Add a deterministic parser rule or fixture for legal text that failed symbolic validation.
  samples: `us-code-45-81 to 92.-1562d5d82d7f6c80`

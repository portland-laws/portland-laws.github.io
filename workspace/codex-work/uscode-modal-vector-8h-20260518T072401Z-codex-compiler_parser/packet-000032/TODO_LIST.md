# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-vector-8h-20260518T072401Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-vector-8h-20260518T072401Z-autoencoder.jsonl`
- TODO count: `3`

## TODOs
- `c645e00831057d0c`
  action: `add_deterministic_parser_rule`
  role: `program_synthesis`
  target: `modal.compiler`
  scope: `compiler_parser`
  bundle: `{"action":"add_deterministic_parser_rule","family_pairs":[],"program_synthesis_scope":"compiler_parser","target_component":"modal.compiler"}`
  vector_bundle: `c645e00831057d0c` score `1.0`
  loss: `parser_formula_count` = `1.0`
  objective: Create a golden parser case for legal text that produced no modal formulas.
  samples: `us-code-36-110105-c16a1da4a57f02ec`
- `80172c2dc976f3a2`
  action: `add_deterministic_parser_rule`
  role: `program_synthesis`
  target: `modal.compiler`
  scope: `compiler_parser`
  bundle: `{"action":"add_deterministic_parser_rule","family_pairs":[],"program_synthesis_scope":"compiler_parser","target_component":"modal.compiler"}`
  vector_bundle: `c645e00831057d0c` score `0.998138`
  loss: `parser_formula_count` = `1.0`
  objective: Create a golden parser case for legal text that produced no modal formulas.
  samples: `us-code-25-450-c265a65e885d4655`
- `8a8a380c4f010b3f`
  action: `add_deterministic_parser_rule`
  role: `program_synthesis`
  target: `modal.compiler`
  scope: `compiler_parser`
  bundle: `{"action":"add_deterministic_parser_rule","family_pairs":[],"program_synthesis_scope":"compiler_parser","target_component":"modal.compiler"}`
  vector_bundle: `c645e00831057d0c` score `0.915794`
  loss: `symbolic_validity_penalty` = `0.25`
  objective: Add a deterministic parser rule or fixture for legal text that failed symbolic validation.
  samples: `us-code-25-5396-17291bf2fa3ae3f6`

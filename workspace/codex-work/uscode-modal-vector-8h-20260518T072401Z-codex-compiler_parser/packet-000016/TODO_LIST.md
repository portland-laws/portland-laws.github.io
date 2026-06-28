# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-vector-8h-20260518T072401Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-vector-8h-20260518T072401Z-autoencoder.jsonl`
- TODO count: `3`

## TODOs
- `a35a54b31594581e`
  action: `add_deterministic_parser_rule`
  role: `program_synthesis`
  target: `modal.compiler`
  scope: `compiler_parser`
  bundle: `{"action":"add_deterministic_parser_rule","family_pairs":[],"program_synthesis_scope":"compiler_parser","target_component":"modal.compiler"}`
  vector_bundle: `a35a54b31594581e` score `1.0`
  loss: `parser_formula_count` = `1.0`
  objective: Create a golden parser case for legal text that produced no modal formulas.
  samples: `us-code-25-422-f3f166961e45b585`
- `42fd6038fac76d68`
  action: `add_deterministic_parser_rule`
  role: `program_synthesis`
  target: `modal.compiler`
  scope: `compiler_parser`
  bundle: `{"action":"add_deterministic_parser_rule","family_pairs":[],"program_synthesis_scope":"compiler_parser","target_component":"modal.compiler"}`
  vector_bundle: `a35a54b31594581e` score `0.911886`
  loss: `symbolic_validity_penalty` = `0.25`
  objective: Add a deterministic parser rule or fixture for legal text that failed symbolic validation.
  samples: `us-code-48-1572.-8711c64e2d6b256c`
- `bb48ff984ccba439`
  action: `add_deterministic_parser_rule`
  role: `program_synthesis`
  target: `modal.compiler`
  scope: `compiler_parser`
  bundle: `{"action":"add_deterministic_parser_rule","family_pairs":[],"program_synthesis_scope":"compiler_parser","target_component":"modal.compiler"}`
  vector_bundle: `a35a54b31594581e` score `0.911702`
  loss: `symbolic_validity_penalty` = `0.25`
  objective: Add a deterministic parser rule or fixture for legal text that failed symbolic validation.
  samples: `us-code-42-6323.-1c7e7d2f53c36e15`

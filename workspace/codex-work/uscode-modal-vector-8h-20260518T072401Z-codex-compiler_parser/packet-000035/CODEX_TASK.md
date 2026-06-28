# packet-000035

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/packet-000035/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/packet-000035/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000035-20260518_113446

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/compiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/legal_modal_parser.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py`

## TODOs
- `8eae83042efceb73` `add_deterministic_parser_rule`
  target: `modal.compiler`
  scope: `compiler_parser`
  bundle: `{"action":"add_deterministic_parser_rule","family_pairs":[],"program_synthesis_scope":"compiler_parser","target_component":"modal.compiler"}`
  vector_bundle: `8eae83042efceb73` score `1.0`
  objective: Create a golden parser case for legal text that produced no modal formulas.
  support: 
- `4c97a8f50db8b97c` `add_deterministic_parser_rule`
  target: `modal.compiler`
  scope: `compiler_parser`
  bundle: `{"action":"add_deterministic_parser_rule","family_pairs":[],"program_synthesis_scope":"compiler_parser","target_component":"modal.compiler"}`
  vector_bundle: `8eae83042efceb73` score `0.905023`
  objective: Add a deterministic parser rule or fixture for legal text that failed symbolic validation.
  support: 
- `ca0257ae5fd05f14` `add_deterministic_parser_rule`
  target: `modal.compiler`
  scope: `compiler_parser`
  bundle: `{"action":"add_deterministic_parser_rule","family_pairs":[],"program_synthesis_scope":"compiler_parser","target_component":"modal.compiler"}`
  vector_bundle: `8eae83042efceb73` score `0.903179`
  objective: Add a deterministic parser rule or fixture for legal text that failed symbolic validation.
  support: 

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.

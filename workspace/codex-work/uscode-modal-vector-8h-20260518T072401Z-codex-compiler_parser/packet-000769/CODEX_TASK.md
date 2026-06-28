# packet-000769

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/packet-000769/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/packet-000769/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-compiler_parser/worktrees/agent-codex-compiler_parser-packet-000769-20260518_141203

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/compiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/legal_modal_parser.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py`

## TODOs
- `c9beb361ce1d4a9a` `add_deterministic_parser_rule`
  target: `modal.compiler`
  scope: `compiler_parser`
  bundle: `{"action":"add_deterministic_parser_rule","family_pairs":[],"program_synthesis_scope":"compiler_parser","target_component":"modal.compiler"}`
  vector_bundle: `c9beb361ce1d4a9a` score `1.0`
  objective: Create a golden parser case for legal text that produced no modal formulas.
  support: 
- `769971baa6a2c837` `add_deterministic_parser_rule`
  target: `modal.compiler`
  scope: `compiler_parser`
  bundle: `{"action":"add_deterministic_parser_rule","family_pairs":[],"program_synthesis_scope":"compiler_parser","target_component":"modal.compiler"}`
  vector_bundle: `c9beb361ce1d4a9a` score `0.908706`
  objective: Add a deterministic parser rule or fixture for legal text that failed symbolic validation.
  support: 
- `0d2b6ca528398c85` `add_deterministic_parser_rule`
  target: `modal.compiler`
  scope: `compiler_parser`
  bundle: `{"action":"add_deterministic_parser_rule","family_pairs":[],"program_synthesis_scope":"compiler_parser","target_component":"modal.compiler"}`
  vector_bundle: `c9beb361ce1d4a9a` score `0.908374`
  objective: Add a deterministic parser rule or fixture for legal text that failed symbolic validation.
  support: 

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.

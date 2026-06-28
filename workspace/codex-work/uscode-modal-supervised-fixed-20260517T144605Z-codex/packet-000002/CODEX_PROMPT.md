# packet-000002

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-supervised-fixed-20260517T144605Z-codex/packet-000002/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-supervised-fixed-20260517T144605Z-codex/packet-000002/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-supervised-fixed-20260517T144605Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-supervised-fixed-20260517T144605Z-codex-packet-000002-20260517_144813

## Patch
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/legal_modal_parser.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py`
- `ipfs_datasets_py/logic/modal/compiler.py`

## TODOs
- `7b0e6b35b0ea115d` `add_deterministic_parser_rule`
  target: ``
  objective: Create a golden parser case for legal text that produced no modal formulas.
  support: 

## Patch Command
Run this after editing the worktree:

```bash
git diff HEAD > changes.patch
```


## Execution Instructions
Work only inside the packet worktree.
Implement a narrow deterministic parser, IR, decoder, or frame-logic improvement for the claimed TODOs.
Prefer explainable compiler/decompiler code over learned weights when the TODO concerns modal or frame semantics.
Use local repository files and tests only; do not use web search for this packet.
Run the smallest relevant tests you can before finishing.
Leave unrelated files alone.

## Claimed Autoencoder TODO List
# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-supervised-fixed-20260517T144605Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-supervised-fixed-20260517T144605Z-autoencoder.jsonl`
- TODO count: `1`

## TODOs
- `7b0e6b35b0ea115d`
  action: `add_deterministic_parser_rule`
  role: `program_synthesis`
  target: ``
  loss: `parser_formula_count` = `1.0`
  objective: Create a golden parser case for legal text that produced no modal formulas.
  samples: `us-code-22-5957-c0e5d7fd46c2c96b`

# packet-000001

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152839Z-codex/packet-000001/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152839Z-codex/packet-000001/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-e2e-20260517T152839Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-e2e-20260517T152839Z-codex-packet-000001-20260517_152850

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-4c2ad37960848fed` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.488835455246, "hint_id": "modal-synthesis-0d2879665b0866e7", "priority": 0.254298793875, "reconstruction_loss": 0.254298793875, "sample_id": "us-code-29-3006-04f38a86e99a30fc"}`
  evidence: `{"cosine_similarity": -0.575311725768, "hint_id": "modal-synthesis-b0e109524d0019c2", "priority": 0.539460963964, "reconstruction_loss": 0.539460963964, "sample_id": "us-code-42-247b-361c41439e746805"}`
  evidence: `{"cosine_similarity": -0.540687426513, "hint_id": "modal-synthesis-efcc68a5b571e1eb", "priority": 0.725910879126, "reconstruction_loss": 0.725910879126, "sample_id": "us-code-21-346-cbe16eeabb5e6c33"}`
  evidence: `{"cosine_similarity": -0.074181865321, "hint_id": "modal-synthesis-f77f424f1520d17e", "priority": 0.436675998669, "reconstruction_loss": 0.436675998669, "sample_id": "us-code-25-2717-1b98fc55bf9ac07b"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.


## Execution Instructions
Work only inside the packet worktree.
Your worktree edits may be applied back to the source checkout and validated automatically when this packet finishes.
Do not create changes.patch or other patch artifact files; leave source and test edits directly in the worktree.
Implement a narrow deterministic parser, IR, decoder, or frame-logic improvement for the claimed TODOs.
Prefer explainable compiler/decompiler code over learned weights when the TODO concerns modal or frame semantics.
Use local repository files and tests only; do not use web search for this packet.
Run the smallest relevant tests you can before finishing.
Leave unrelated files alone.

## Claimed Autoencoder TODO List
# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-e2e-20260517T152839Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-e2e-20260517T152839Z-autoencoder.jsonl`
- TODO count: `1`

## TODOs
- `program-4c2ad37960848fed`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  loss: `autoencoder_residual_cluster` = `0.489086658909`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-21-346-cbe16eeabb5e6c33, us-code-42-247b-361c41439e746805, us-code-25-2717-1b98fc55bf9ac07b, us-code-29-3006-04f38a86e99a30fc`
  evidence: `{"cosine_similarity": 0.488835455246, "hint_id": "modal-synthesis-0d2879665b0866e7", "priority": 0.254298793875, "reconstruction_loss": 0.254298793875, "sample_id": "us-code-29-3006-04f38a86e99a30fc"}`
  evidence: `{"cosine_similarity": -0.575311725768, "hint_id": "modal-synthesis-b0e109524d0019c2", "priority": 0.539460963964, "reconstruction_loss": 0.539460963964, "sample_id": "us-code-42-247b-361c41439e746805"}`
  evidence: `{"cosine_similarity": -0.540687426513, "hint_id": "modal-synthesis-efcc68a5b571e1eb", "priority": 0.725910879126, "reconstruction_loss": 0.725910879126, "sample_id": "us-code-21-346-cbe16eeabb5e6c33"}`
  evidence: `{"cosine_similarity": -0.074181865321, "hint_id": "modal-synthesis-f77f424f1520d17e", "priority": 0.436675998669, "reconstruction_loss": 0.436675998669, "sample_id": "us-code-25-2717-1b98fc55bf9ac07b"}`

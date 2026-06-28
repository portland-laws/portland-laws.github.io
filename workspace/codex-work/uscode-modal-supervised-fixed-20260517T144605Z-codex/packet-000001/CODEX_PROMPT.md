# packet-000001

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-supervised-fixed-20260517T144605Z-codex/packet-000001/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-supervised-fixed-20260517T144605Z-codex/packet-000001/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-supervised-fixed-20260517T144605Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-supervised-fixed-20260517T144605Z-codex-packet-000001-20260517_144611

## Patch
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/optimizers/logic/flogic_optimizer.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/frame_bm25_selector.py`

## TODOs
- `program-25c3f7865077db77` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 2
  evidence: `{"hint_id": "modal-synthesis-08a2870a8aa334c4", "priority": 0.536654833388, "sample_id": "us-code-12-1261-09ddb07a7e205786"}`
  evidence: `{"hint_id": "modal-synthesis-ba028fa516a1e388", "priority": 0.296090670627, "sample_id": "us-code-42-8286.-dc7a2eb8b0df0830"}`

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
- `program-25c3f7865077db77`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  loss: `autoencoder_residual_cluster` = `0.416372752008`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-12-1261-09ddb07a7e205786, us-code-42-8286.-dc7a2eb8b0df0830`
  evidence: `{"hint_id": "modal-synthesis-08a2870a8aa334c4", "priority": 0.536654833388, "sample_id": "us-code-12-1261-09ddb07a7e205786"}`
  evidence: `{"hint_id": "modal-synthesis-ba028fa516a1e388", "priority": 0.296090670627, "sample_id": "us-code-42-8286.-dc7a2eb8b0df0830"}`

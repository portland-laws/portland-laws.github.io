# packet-000025

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-smoke-20260516T154900Z-codex/packet-000025/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-smoke-20260516T154900Z-codex/packet-000025/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-smoke-20260516T154900Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-smoke-20260516T154900Z-codex-packet-000025-20260516_154926

## Patch
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/compiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_registry.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py`
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/optimizers/logic/flogic_optimizer.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/frame_bm25_selector.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-957c34463225bbb8` `add_or_review_modal_ambiguity_policy`
  target: `modal.compiler.ambiguity`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  support: 2
  evidence: `{"family_margin": -0.654174848239, "hint_id": "modal-synthesis-b0d926c3e310b5ad", "predicted_family": "conditional_normative", "priority": 0.804174848239, "sample_id": "us-code-18-3013-7473c2b440770471", "target_family": "deontic"}`
  evidence: `{"family_margin": -0.990433218902, "hint_id": "modal-synthesis-bbdcb9bb8552f433", "predicted_family": "temporal", "priority": 1.140433218902, "sample_id": "us-code-42-299b-eda60092171769d9", "target_family": "frame"}`
- `program-a109045024d63b07` `refine_modal_family_cue_rules`
  target: `modal.compiler.registry`
  objective: Adaptive family evidence disagrees with, or is weak for, the typed modal family.
  support: 2
  evidence: `{"family_margin": -0.654174848239, "hint_id": "modal-synthesis-586b2a1f928fd38b", "predicted_family": "conditional_normative", "priority": 0.897610094808, "sample_id": "us-code-18-3013-7473c2b440770471", "target_family": "deontic", "target_probability": 0.102389905192}`
  evidence: `{"family_margin": -0.990433218902, "hint_id": "modal-synthesis-97818b52e4c94d64", "predicted_family": "temporal", "priority": 0.999096017484, "sample_id": "us-code-42-299b-eda60092171769d9", "target_family": "frame", "target_probability": 0.000903982516}`
- `program-3b1317be205b7a2c` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 2
  evidence: `{"hint_id": "modal-synthesis-b4f0684f235beec6", "priority": 0.5203984572, "sample_id": "us-code-18-3013-7473c2b440770471"}`
  evidence: `{"hint_id": "modal-synthesis-d4ebf802975a4d94", "priority": 0.203761055357, "sample_id": "us-code-42-299b-eda60092171769d9"}`
- `program-751d235d993c73cc` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 2
  evidence: `{"cosine_similarity": 0.303698358893, "hint_id": "modal-synthesis-92ac8b5b47c4f1c4", "priority": 0.203761055357, "reconstruction_loss": 0.203761055357, "sample_id": "us-code-42-299b-eda60092171769d9"}`
  evidence: `{"cosine_similarity": -0.318405199588, "hint_id": "modal-synthesis-b4b9432aee9f6aae", "priority": 0.5203984572, "reconstruction_loss": 0.5203984572, "sample_id": "us-code-18-3013-7473c2b440770471"}`

## Patch Command
Run this after editing the worktree:

```bash
git diff HEAD > changes.patch
```

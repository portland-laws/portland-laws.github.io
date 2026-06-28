# packet-000024

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-smoke-20260516T154900Z-codex/packet-000024/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-smoke-20260516T154900Z-codex/packet-000024/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-smoke-20260516T154900Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-smoke-20260516T154900Z-codex-packet-000024-20260516_154924

## Patch
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/optimizers/logic/flogic_optimizer.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/frame_bm25_selector.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`
- `ipfs_datasets_py/logic/modal/compiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_registry.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py`

## TODOs
- `program-43a63cf868b34e95` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 2
  evidence: `{"hint_id": "modal-synthesis-577e0e1931503ee9", "priority": 0.483159116907, "sample_id": "us-code-16-709-b9a8bf838e927a34"}`
  evidence: `{"hint_id": "modal-synthesis-7be9fbeb1fd30dab", "priority": 0.927786016819, "sample_id": "us-code-42-300t-165b62726b1ad549"}`
- `program-ce6fe332f1dcf4de` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 2
  evidence: `{"cosine_similarity": -0.389889207147, "hint_id": "modal-synthesis-847681b442bec597", "priority": 0.927786016819, "reconstruction_loss": 0.927786016819, "sample_id": "us-code-42-300t-165b62726b1ad549"}`
  evidence: `{"cosine_similarity": -0.199575532914, "hint_id": "modal-synthesis-f410fe2a97702908", "priority": 0.483159116907, "reconstruction_loss": 0.483159116907, "sample_id": "us-code-16-709-b9a8bf838e927a34"}`
- `program-ab5ec8c5b2ef5b0b` `refine_modal_family_cue_rules`
  target: `modal.compiler.registry`
  objective: Adaptive family evidence disagrees with, or is weak for, the typed modal family.
  support: 2
  evidence: `{"family_margin": 0.0, "hint_id": "modal-synthesis-6d16b50d4cfc3323", "predicted_family": "temporal", "priority": 0.509017538256, "sample_id": "us-code-42-300t-165b62726b1ad549", "target_family": "deontic", "target_probability": 0.490982461744}`
  evidence: `{"family_margin": -0.430679318188, "hint_id": "modal-synthesis-c2136d807a7d433b", "predicted_family": "temporal", "priority": 0.749354668684, "sample_id": "us-code-16-709-b9a8bf838e927a34", "target_family": "deontic", "target_probability": 0.250645331316}`
- `program-235d549eaa201a32` `add_or_review_modal_ambiguity_policy`
  target: `modal.compiler.ambiguity`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  support: 2
  evidence: `{"family_margin": -0.430679318188, "hint_id": "modal-synthesis-c52d2f086d19df72", "predicted_family": "temporal", "priority": 0.580679318188, "sample_id": "us-code-16-709-b9a8bf838e927a34", "target_family": "deontic"}`
  evidence: `{"family_margin": 0.0, "hint_id": "modal-synthesis-eb1b2d584344dda7", "predicted_family": "temporal", "priority": 0.15, "sample_id": "us-code-42-300t-165b62726b1ad549", "target_family": "deontic"}`

## Patch Command
Run this after editing the worktree:

```bash
git diff HEAD > changes.patch
```

# packet-000021

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-smoke-final-20260516T155456Z-codex/packet-000021/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-smoke-final-20260516T155456Z-codex/packet-000021/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-smoke-final-20260516T155456Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-smoke-final-20260516T155456Z-codex-packet-000021-20260516_155519

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
- `program-76d3142c9d1000f3` `add_or_review_modal_ambiguity_policy`
  target: `modal.compiler.ambiguity`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  support: 2
  evidence: `{"family_margin": -0.905148235645, "hint_id": "modal-synthesis-380b61b8340f4861", "predicted_family": "temporal", "priority": 1.055148235645, "sample_id": "us-code-18-2386-91b9795f9b9a4e53", "target_family": "deontic"}`
  evidence: `{"family_margin": -0.896963158598, "hint_id": "modal-synthesis-fe6bc931a113eb26", "predicted_family": "deontic", "priority": 1.046963158598, "sample_id": "us-code-10-2723-3711a965e1107f6a", "target_family": "temporal"}`
- `program-53780f2241b4ac99` `refine_modal_family_cue_rules`
  target: `modal.compiler.registry`
  objective: Adaptive family evidence disagrees with, or is weak for, the typed modal family.
  support: 2
  evidence: `{"family_margin": -0.905148235645, "hint_id": "modal-synthesis-4024a8c3c76d9b16", "predicted_family": "temporal", "priority": 0.952574127766, "sample_id": "us-code-18-2386-91b9795f9b9a4e53", "target_family": "deontic", "target_probability": 0.047425872234}`
  evidence: `{"family_margin": -0.896963158598, "hint_id": "modal-synthesis-adb9239bf957df9e", "predicted_family": "deontic", "priority": 0.953002990578, "sample_id": "us-code-10-2723-3711a965e1107f6a", "target_family": "temporal", "target_probability": 0.046997009422}`
- `program-316fc5445084dbbc` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 2
  evidence: `{"frame_features": ["flogic:candidate_ontology_frame:administrative_notice_hearing", "flogic:candidate_ontology_frame:criminal_penalty_enforcement", "flogic:candidate_ontology_frame:housing_voucher_benefits", "flogic:interpreted_in_frame:administrative_notice_hearing", "flogic:modal_family:deontic", "flogic:modal_operator:O", "flogic:modal_system:D"], "hint_id": "modal-synthesis-0b25aa7f8eac9b84", "priority": 0.378615178487, "sample_id": "us-code-10-2723-3711a965e1107f6a"}`
  evidence: `{"frame_features": ["flogic:candidate_ontology_frame:administrative_notice_hearing", "flogic:candidate_ontology_frame:criminal_penalty_enforcement", "flogic:candidate_ontology_frame:housing_voucher_benefits", "flogic:modal_family:deontic", "flogic:modal_operator:O", "flogic:modal_system:D", "flogic:predicate_role:clause"], "hint_id": "modal-synthesis-f82b93597b008e48", "priority": 0.320475955545, "sample_id": "us-code-18-2386-91b9795f9b9a4e53"}`
- `program-3975dd6339bc7124` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 2
  evidence: `{"cosine_similarity": 0.143039398796, "hint_id": "modal-synthesis-766acd94cee6680a", "priority": 0.320475955545, "reconstruction_loss": 0.320475955545, "sample_id": "us-code-18-2386-91b9795f9b9a4e53", "top_embedding_features": ["cue:deontic:O:shall", "flogic:candidate_ontology_frame:administrative_notice_hearing", "flogic:candidate_ontology_frame:criminal_penalty_enforcement", "flogic:candidate_ontology_frame:housing_voucher_benefits", "flogic:modal_family:deontic", "flogic:modal_operator:O", "flogic:modal_system:D", "flogic:predicate_role:clause"]}`
  evidence: `{"cosine_similarity": -0.201774883902, "hint_id": "modal-synthesis-9d0b30401a2a5de3", "priority": 0.378615178487, "reconstruction_loss": 0.378615178487, "sample_id": "us-code-10-2723-3711a965e1107f6a", "top_embedding_features": ["cue:deontic:O:shall", "flogic:candidate_ontology_frame:administrative_notice_hearing", "flogic:candidate_ontology_frame:criminal_penalty_enforcement", "flogic:candidate_ontology_frame:housing_voucher_benefits", "flogic:interpreted_in_frame:administrative_notice_hearing", "flogic:modal_family:deontic", "flogic:modal_operator:O", "flogic:modal_system:D"]}`

## Patch Command
Run this after editing the worktree:

```bash
git diff HEAD > changes.patch
```

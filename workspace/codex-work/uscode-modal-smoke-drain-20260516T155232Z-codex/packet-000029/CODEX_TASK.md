# packet-000029

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-smoke-drain-20260516T155232Z-codex/packet-000029/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-smoke-drain-20260516T155232Z-codex/packet-000029/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-smoke-drain-20260516T155232Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-smoke-drain-20260516T155232Z-codex-packet-000029-20260516_155302

## Patch
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/compiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_registry.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py`
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`
- `ipfs_datasets_py/optimizers/logic/flogic_optimizer.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/frame_bm25_selector.py`

## TODOs
- `program-3dbe76f3a81d3394` `add_or_review_modal_ambiguity_policy`
  target: `modal.compiler.ambiguity`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  support: 2
  evidence: `{"family_margin": -0.737725781832, "hint_id": "modal-synthesis-d1ce2b0c3c5bd91f", "predicted_family": "temporal", "priority": 0.887725781832, "sample_id": "us-code-2-5146-67710afaeb83f58f", "target_family": "deontic"}`
  evidence: `{"family_margin": -0.892579723708, "hint_id": "modal-synthesis-f2f1117d8a026831", "predicted_family": "temporal", "priority": 1.042579723708, "sample_id": "us-code-7-7611-53e41bebbfcb3009", "target_family": "deontic"}`
- `program-665fd35ad9262e79` `refine_modal_family_cue_rules`
  target: `modal.compiler.registry`
  objective: Adaptive family evidence disagrees with, or is weak for, the typed modal family.
  support: 2
  evidence: `{"family_margin": -0.737725781832, "hint_id": "modal-synthesis-41309f9d0476cfd7", "predicted_family": "temporal", "priority": 0.884532899632, "sample_id": "us-code-2-5146-67710afaeb83f58f", "target_family": "deontic", "target_probability": 0.115467100368}`
  evidence: `{"family_margin": -0.892579723708, "hint_id": "modal-synthesis-d8e8fcc433f6334f", "predicted_family": "temporal", "priority": 0.953232663702, "sample_id": "us-code-7-7611-53e41bebbfcb3009", "target_family": "deontic", "target_probability": 0.046767336298}`
- `program-2a76f3c133a8200b` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 2
  evidence: `{"cosine_similarity": -0.590196691815, "hint_id": "modal-synthesis-65baaa1baa059ca4", "priority": 0.73877214716, "reconstruction_loss": 0.73877214716, "sample_id": "us-code-2-5146-67710afaeb83f58f", "top_embedding_features": ["cue:temporal:F:by", "flogic:candidate_ontology_frame:administrative_notice_hearing", "flogic:candidate_ontology_frame:criminal_penalty_enforcement", "flogic:candidate_ontology_frame:housing_voucher_benefits", "flogic:interpreted_in_frame:administrative_notice_hearing", "flogic:modal_family:deontic", "flogic:modal_family:temporal", "flogic:modal_operator:F"]}`
  evidence: `{"cosine_similarity": 0.137550276758, "hint_id": "modal-synthesis-88619ee42a327081", "priority": 0.37631149861, "reconstruction_loss": 0.37631149861, "sample_id": "us-code-7-7611-53e41bebbfcb3009", "top_embedding_features": ["cue:deontic:O:shall", "cue:temporal:F:by", "family:conditional_normative:1", "flogic:candidate_ontology_frame:administrative_notice_hearing", "flogic:candidate_ontology_frame:criminal_penalty_enforcement", "flogic:candidate_ontology_frame:housing_voucher_benefits", "flogic:interpreted_in_frame:administrative_notice_hearing", "flogic:modal_family:conditional_normative"]}`
- `program-59f6f400fea38ea6` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 2
  evidence: `{"frame_features": ["flogic:candidate_ontology_frame:administrative_notice_hearing", "flogic:candidate_ontology_frame:criminal_penalty_enforcement", "flogic:candidate_ontology_frame:housing_voucher_benefits", "flogic:interpreted_in_frame:administrative_notice_hearing", "flogic:modal_family:deontic", "flogic:modal_family:temporal", "flogic:modal_operator:F"], "hint_id": "modal-synthesis-7e5136b487f77ce9", "priority": 0.73877214716, "sample_id": "us-code-2-5146-67710afaeb83f58f"}`
  evidence: `{"frame_features": ["flogic:candidate_ontology_frame:administrative_notice_hearing", "flogic:candidate_ontology_frame:criminal_penalty_enforcement", "flogic:candidate_ontology_frame:housing_voucher_benefits", "flogic:interpreted_in_frame:administrative_notice_hearing", "flogic:modal_family:conditional_normative"], "hint_id": "modal-synthesis-d7cc9e48a0592456", "priority": 0.37631149861, "sample_id": "us-code-7-7611-53e41bebbfcb3009"}`

## Patch Command
Run this after editing the worktree:

```bash
git diff HEAD > changes.patch
```

# packet-000026

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-smoke-20260516T154900Z-codex/packet-000026/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-smoke-20260516T154900Z-codex/packet-000026/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-smoke-20260516T154900Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-smoke-20260516T154900Z-codex-packet-000026-20260516_154928

## Patch
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`
- `ipfs_datasets_py/optimizers/logic/flogic_optimizer.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/frame_bm25_selector.py`

## TODOs
- `program-2b218e0f33fc0753` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 2
  evidence: `{"cosine_similarity": -0.365412902866, "hint_id": "modal-synthesis-302cb42064cf22e0", "priority": 0.885734924866, "reconstruction_loss": 0.885734924866, "sample_id": "us-code-15-1803-e03f1071c51991cb", "top_embedding_features": ["cue:conditional_normative:O|:except", "cue:deontic:O:shall", "cue:frame:Frame:is a", "cue:temporal:F:by", "family:frame:1", "flogic:candidate_ontology_frame:administrative_notice_hearing", "flogic:candidate_ontology_frame:criminal_penalty_enforcement", "flogic:candidate_ontology_frame:housing_voucher_benefits"]}`
  evidence: `{"cosine_similarity": 0.748425376801, "hint_id": "modal-synthesis-d0e22c88b6b0796d", "priority": 0.06286227354, "reconstruction_loss": 0.06286227354, "sample_id": "us-code-30-934-7dc5c92d73d218b3", "top_embedding_features": ["cue:conditional_normative:O|:except", "cue:deontic:O:shall", "cue:temporal:F:by", "family:frame:1", "flogic:candidate_ontology_frame:administrative_notice_hearing", "flogic:candidate_ontology_frame:criminal_penalty_enforcement", "flogic:candidate_ontology_frame:housing_voucher_benefits", "flogic:interpreted_in_frame:administrative_notice_hearing"]}`
- `program-4a3e9ee43434fc30` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 2
  evidence: `{"frame_features": ["flogic:candidate_ontology_frame:administrative_notice_hearing", "flogic:candidate_ontology_frame:criminal_penalty_enforcement", "flogic:candidate_ontology_frame:housing_voucher_benefits"], "hint_id": "modal-synthesis-5daec858e3d9a936", "priority": 0.885734924866, "sample_id": "us-code-15-1803-e03f1071c51991cb"}`
  evidence: `{"frame_features": ["flogic:candidate_ontology_frame:administrative_notice_hearing", "flogic:candidate_ontology_frame:criminal_penalty_enforcement", "flogic:candidate_ontology_frame:housing_voucher_benefits", "flogic:interpreted_in_frame:administrative_notice_hearing"], "hint_id": "modal-synthesis-829dd7387cd64e64", "priority": 0.06286227354, "sample_id": "us-code-30-934-7dc5c92d73d218b3"}`

## Patch Command
Run this after editing the worktree:

```bash
git diff HEAD > changes.patch
```

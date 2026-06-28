# packet-000023

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-smoke-final-20260516T155456Z-codex/packet-000023/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-smoke-final-20260516T155456Z-codex/packet-000023/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-smoke-final-20260516T155456Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-smoke-final-20260516T155456Z-codex-packet-000023-20260516_155522

## Patch
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/optimizers/logic/flogic_optimizer.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/frame_bm25_selector.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-33bb12221a2e4bc6` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 2
  evidence: `{"frame_features": ["flogic:candidate_ontology_frame:administrative_notice_hearing", "flogic:candidate_ontology_frame:criminal_penalty_enforcement", "flogic:candidate_ontology_frame:housing_voucher_benefits", "flogic:modal_family:deontic", "flogic:modal_operator:O", "flogic:modal_system:D", "flogic:predicate_role:clause"], "hint_id": "modal-synthesis-4a8d2a1bf508a889", "priority": 0.432772191864, "sample_id": "us-code-47-208.-bbe14e3800c522d1"}`
  evidence: `{"hint_id": "modal-synthesis-557a9803eee8dc64", "priority": 0.315995637547, "sample_id": "us-code-26-45E-bd16b29c97210cf4"}`
- `program-503e2be2fe62a3ee` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 2
  evidence: `{"cosine_similarity": 0.167001735891, "hint_id": "modal-synthesis-232eeaf18866bb88", "priority": 0.315995637547, "reconstruction_loss": 0.315995637547, "sample_id": "us-code-26-45E-bd16b29c97210cf4", "top_embedding_features": ["lemma:act", "lemma:date", "lemma:defined", "lemma:effective", "lemma:employees", "lemma:ii", "lemma:member", "lemma:note"]}`
  evidence: `{"cosine_similarity": 0.508660753224, "hint_id": "modal-synthesis-543cb69c8636ef75", "priority": 0.432772191864, "reconstruction_loss": 0.432772191864, "sample_id": "us-code-47-208.-bbe14e3800c522d1", "top_embedding_features": ["cue:deontic:O:shall", "flogic:candidate_ontology_frame:administrative_notice_hearing", "flogic:candidate_ontology_frame:criminal_penalty_enforcement", "flogic:candidate_ontology_frame:housing_voucher_benefits", "flogic:modal_family:deontic", "flogic:modal_operator:O", "flogic:modal_system:D", "flogic:predicate_role:clause"]}`

## Patch Command
Run this after editing the worktree:

```bash
git diff HEAD > changes.patch
```

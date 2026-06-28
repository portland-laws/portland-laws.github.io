# packet-000029

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-smoke-20260516T154900Z-codex/packet-000029/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-smoke-20260516T154900Z-codex/packet-000029/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-smoke-20260516T154900Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-smoke-20260516T154900Z-codex-packet-000029-20260516_154936

## Patch
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/optimizers/logic/flogic_optimizer.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/frame_bm25_selector.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-23f6aa41d991657a` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 2
  evidence: `{"frame_features": ["flogic:candidate_ontology_frame:administrative_notice_hearing", "flogic:candidate_ontology_frame:criminal_penalty_enforcement", "flogic:candidate_ontology_frame:housing_voucher_benefits", "flogic:interpreted_in_frame:administrative_notice_hearing", "flogic:modal_family:conditional_normative", "flogic:modal_family:deontic", "flogic:modal_family:temporal"], "hint_id": "modal-synthesis-a5c60eeaececcf4c", "priority": 0.15759370823, "sample_id": "us-code-6-316-d630144826388409"}`
  evidence: `{"hint_id": "modal-synthesis-b93760d6b3730136", "priority": 0.398353304555, "sample_id": "us-code-28-1346-a5ff9966847c2904"}`
- `program-2f7c17e6b9fb2166` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 2
  evidence: `{"cosine_similarity": 0.049288125528, "hint_id": "modal-synthesis-2dd92cfe76add99d", "priority": 0.398353304555, "reconstruction_loss": 0.398353304555, "sample_id": "us-code-28-1346-a5ff9966847c2904", "top_embedding_features": ["lemma:law", "lemma:prior", "lemma:contained", "lemma:department", "lemma:entered", "lemma:granting", "lemma:party", "lemma:person"]}`
  evidence: `{"cosine_similarity": 0.465167923409, "hint_id": "modal-synthesis-a3a765611889fbdb", "priority": 0.15759370823, "reconstruction_loss": 0.15759370823, "sample_id": "us-code-6-316-d630144826388409", "top_embedding_features": ["cue:deontic:O:shall", "flogic:candidate_ontology_frame:administrative_notice_hearing", "flogic:candidate_ontology_frame:criminal_penalty_enforcement", "flogic:candidate_ontology_frame:housing_voucher_benefits", "flogic:interpreted_in_frame:administrative_notice_hearing", "flogic:modal_family:conditional_normative", "flogic:modal_family:deontic", "flogic:modal_family:temporal"]}`

## Patch Command
Run this after editing the worktree:

```bash
git diff HEAD > changes.patch
```

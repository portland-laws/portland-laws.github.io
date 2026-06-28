# packet-000041

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-smoke-final-20260516T155456Z-codex/packet-000041/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-smoke-final-20260516T155456Z-codex/packet-000041/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-smoke-final-20260516T155456Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-smoke-final-20260516T155456Z-codex-packet-000041-20260516_155548

## Patch
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`
- `ipfs_datasets_py/optimizers/logic/flogic_optimizer.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/frame_bm25_selector.py`

## TODOs
- `program-0a46da1b6c12a2da` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 2
  evidence: `{"cosine_similarity": 0.331299038646, "hint_id": "modal-synthesis-1205591ba504df84", "priority": 0.20875790515, "reconstruction_loss": 0.20875790515, "sample_id": "us-code-34-20144-a1f38c368ce05bfe", "top_embedding_features": ["lemma:set", "lemma:chapter", "lemma:code", "lemma:editorial", "lemma:notes", "lemma:section", "flogic:candidate_ontology_frame:administrative_notice_hearing", "flogic:candidate_ontology_frame:criminal_penalty_enforcement"]}`
  evidence: `{"cosine_similarity": -0.618899958769, "hint_id": "modal-synthesis-ff0277652496ce74", "priority": 0.62716098479, "reconstruction_loss": 0.62716098479, "sample_id": "us-code-48-1807.-2b00a7c8484eaec4", "top_embedding_features": ["lemma:encourage", "lemma:opportunities", "lemma:permanent", "lemma:recruiting", "cue:conditional_normative:O|:provided that", "cue:frame:Frame:part of", "lemma:identify", "lemma:program"]}`
- `program-b300eb260e7d9a18` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 2
  evidence: `{"frame_features": ["flogic:candidate_ontology_frame:administrative_notice_hearing", "flogic:candidate_ontology_frame:criminal_penalty_enforcement"], "hint_id": "modal-synthesis-69d66a8a6010598b", "priority": 0.20875790515, "sample_id": "us-code-34-20144-a1f38c368ce05bfe"}`
  evidence: `{"hint_id": "modal-synthesis-d0ea623a998bb9f8", "priority": 0.62716098479, "sample_id": "us-code-48-1807.-2b00a7c8484eaec4"}`

## Patch Command
Run this after editing the worktree:

```bash
git diff HEAD > changes.patch
```

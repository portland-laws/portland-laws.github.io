# packet-000028

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-smoke-20260516T154900Z-codex/packet-000028/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-smoke-20260516T154900Z-codex/packet-000028/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-smoke-20260516T154900Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-smoke-20260516T154900Z-codex-packet-000028-20260516_154933

## Patch
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-a63ee9ad4a308466` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 2
  evidence: `{"cosine_similarity": 0.047868850145, "hint_id": "modal-synthesis-189b38a5edc1cbad", "priority": 0.592912505891, "reconstruction_loss": 0.592912505891, "sample_id": "us-code-19-3911-46b2d5dc09c76062", "top_embedding_features": ["cue:conditional_normative:O|:if", "lemma:chapter", "lemma:code", "lemma:edition", "lemma:effect", "lemma:government", "lemma:publishing", "lemma:purpose"]}`
  evidence: `{"cosine_similarity": -0.127701115921, "hint_id": "modal-synthesis-dc74e238d7110de5", "priority": 0.414047800905, "reconstruction_loss": 0.414047800905, "sample_id": "us-code-51-20161.-90f4bf0dfa214e7d", "top_embedding_features": ["lemma:iv", "lemma:revised", "lemma:statutes", "lemma:code", "lemma:purpose", "lemma:states", "lemma:united", "flogic:candidate_ontology_frame:administrative_notice_hearing"]}`

## Patch Command
Run this after editing the worktree:

```bash
git diff HEAD > changes.patch
```

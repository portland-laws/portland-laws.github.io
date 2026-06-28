# packet-000030

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-smoke-drain-20260516T155232Z-codex/packet-000030/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-smoke-drain-20260516T155232Z-codex/packet-000030/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-smoke-drain-20260516T155232Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-smoke-drain-20260516T155232Z-codex-packet-000030-20260516_155304

## Patch
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/optimizers/logic/flogic_optimizer.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/frame_bm25_selector.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-b4f19a7abd520b1f` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 2
  evidence: `{"frame_features": ["flogic:modal_operator:X", "flogic:interpreted_in_frame:administrative_notice_hearing", "flogic:selected_ontology_frame:administrative_notice_hearing", "frame:administrative_notice_hearing"], "hint_id": "modal-synthesis-158fa7e5edb19f75", "priority": 0.47693849873, "sample_id": "us-code-25-3741-a5e014ea7f4d1a76"}`
  evidence: `{"frame_features": ["flogic:interpreted_in_frame:administrative_notice_hearing", "flogic:selected_ontology_frame:administrative_notice_hearing", "frame:administrative_notice_hearing"], "hint_id": "modal-synthesis-6ff59f762b2abbd4", "priority": 0.324720800002, "sample_id": "us-code-16-460l-5a-122678c241494e33"}`
- `program-ba3115c84fd35339` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 2
  evidence: `{"cosine_similarity": 0.183050810624, "hint_id": "modal-synthesis-d2e408c862612d0f", "priority": 0.47693849873, "reconstruction_loss": 0.47693849873, "sample_id": "us-code-25-3741-a5e014ea7f4d1a76", "top_embedding_features": ["cue:temporal:X:after", "flogic:modal_operator:X", "family:conditional_normative:1", "lemma:general", "flogic:interpreted_in_frame:administrative_notice_hearing", "flogic:selected_ontology_frame:administrative_notice_hearing", "frame:administrative_notice_hearing", "lemma:chapter"]}`
  evidence: `{"cosine_similarity": -0.109436403253, "hint_id": "modal-synthesis-e83d3367f2216693", "priority": 0.324720800002, "reconstruction_loss": 0.324720800002, "sample_id": "us-code-16-460l-5a-122678c241494e33", "top_embedding_features": ["lemma:available", "lemma:use", "lemma:water", "lemma:b", "flogic:interpreted_in_frame:administrative_notice_hearing", "flogic:selected_ontology_frame:administrative_notice_hearing", "frame:administrative_notice_hearing", "lemma:chapter"]}`
- `program-2004d603274fed93` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 2
  evidence: `{"frame_features": ["flogic:modal_operator:P", "flogic:predicate:pub", "flogic:predicate:section_pub"], "hint_id": "modal-synthesis-3d64aced30c49a8c", "priority": 0.615953834102, "sample_id": "us-code-22-279a-d93c50023668d543"}`
  evidence: `{"frame_features": ["flogic:modal_operator:X"], "hint_id": "modal-synthesis-fc708292d5943582", "priority": 0.143938482524, "sample_id": "us-code-47-925.-235a16e625780e2e"}`
- `program-ddb9d4f3988474d8` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 2
  evidence: `{"cosine_similarity": 0.854732842727, "hint_id": "modal-synthesis-cafd5d1dbdc59fa1", "priority": 0.143938482524, "reconstruction_loss": 0.143938482524, "sample_id": "us-code-47-925.-235a16e625780e2e", "top_embedding_features": ["cue:conditional_normative:O|:provided that", "cue:deontic:O:required", "cue:temporal:X:after", "flogic:modal_operator:X", "lemma:act", "lemma:congress", "lemma:definition", "lemma:e"]}`
  evidence: `{"cosine_similarity": -0.199889005754, "hint_id": "modal-synthesis-fc530cdd7a537d00", "priority": 0.615953834102, "reconstruction_loss": 0.615953834102, "sample_id": "us-code-22-279a-d93c50023668d543", "top_embedding_features": ["cue:conditional_normative:O|:except", "cue:deontic:P:may", "flogic:modal_operator:P", "flogic:predicate:pub", "flogic:predicate:section_pub", "lemma:agriculture", "lemma:amendments", "lemma:code"]}`

## Patch Command
Run this after editing the worktree:

```bash
git diff HEAD > changes.patch
```

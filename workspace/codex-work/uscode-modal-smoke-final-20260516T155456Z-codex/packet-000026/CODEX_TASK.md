# packet-000026

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-smoke-final-20260516T155456Z-codex/packet-000026/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-smoke-final-20260516T155456Z-codex/packet-000026/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-smoke-final-20260516T155456Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-smoke-final-20260516T155456Z-codex-packet-000026-20260516_155528

## Patch
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/optimizers/logic/flogic_optimizer.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/frame_bm25_selector.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-2f2916a70ea31c87` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 2
  evidence: `{"hint_id": "modal-synthesis-0bc5ba5280708b92", "priority": 0.233742460424, "sample_id": "us-code-22-2737-53e3f10c5adf9439"}`
  evidence: `{"frame_features": ["flogic:modal_family:conditional_normative", "flogic:modal_family:temporal", "flogic:modal_operator:F", "flogic:modal_operator:O|"], "hint_id": "modal-synthesis-179abcf0419d66a6", "priority": 0.524316667716, "sample_id": "us-code-46-12113.-237d8a683c3ef740"}`
- `program-942612e48015b882` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 2
  evidence: `{"cosine_similarity": 0.241702482593, "hint_id": "modal-synthesis-048cadb0d242e37d", "priority": 0.233742460424, "reconstruction_loss": 0.233742460424, "sample_id": "us-code-22-2737-53e3f10c5adf9439", "top_embedding_features": ["lemma:effective", "lemma:ii", "lemma:note", "lemma:set", "lemma:statutory", "lemma:subsidiaries", "lemma:editorial", "lemma:notes"]}`
  evidence: `{"cosine_similarity": -0.232661510782, "hint_id": "modal-synthesis-488de262a313e53d", "priority": 0.524316667716, "reconstruction_loss": 0.524316667716, "sample_id": "us-code-46-12113.-237d8a683c3ef740", "top_embedding_features": ["lemma:paragraph", "cue:conditional_normative:O|:if", "cue:deontic:P:may", "cue:temporal:X:after", "flogic:modal_family:conditional_normative", "flogic:modal_family:temporal", "flogic:modal_operator:F", "flogic:modal_operator:O|"]}`

## Patch Command
Run this after editing the worktree:

```bash
git diff HEAD > changes.patch
```

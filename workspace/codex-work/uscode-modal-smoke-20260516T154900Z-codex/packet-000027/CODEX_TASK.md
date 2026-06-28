# packet-000027

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-smoke-20260516T154900Z-codex/packet-000027/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-smoke-20260516T154900Z-codex/packet-000027/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-smoke-20260516T154900Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-smoke-20260516T154900Z-codex-packet-000027-20260516_154931

## Patch
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/legal_modal_parser.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py`
- `ipfs_datasets_py/logic/modal/compiler.py`
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/optimizers/logic/flogic_optimizer.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/frame_bm25_selector.py`

## TODOs
- `55f58a011c9f9564` `add_deterministic_parser_rule`
  target: ``
  objective: Create a golden parser case for legal text that produced no modal formulas.
  support: 
- `5b07b6e9d8a61503` `add_deterministic_parser_rule`
  target: ``
  objective: Add a deterministic parser rule or fixture for legal text that failed symbolic validation.
  support: 
- `f23478c315132c04` `add_deterministic_parser_rule`
  target: ``
  objective: Add a deterministic parser rule or fixture for legal text that failed symbolic validation.
  support: 
- `program-9cc69a60a23817b8` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 2
  evidence: `{"hint_id": "modal-synthesis-ac43939cd52467ca", "priority": 0.592912505891, "sample_id": "us-code-19-3911-46b2d5dc09c76062"}`
  evidence: `{"frame_features": ["flogic:candidate_ontology_frame:administrative_notice_hearing"], "hint_id": "modal-synthesis-adba09b7caf5e452", "priority": 0.414047800905, "sample_id": "us-code-51-20161.-90f4bf0dfa214e7d"}`

## Patch Command
Run this after editing the worktree:

```bash
git diff HEAD > changes.patch
```

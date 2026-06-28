# packet-000028

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-smoke-final-20260516T155456Z-codex/packet-000028/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-smoke-final-20260516T155456Z-codex/packet-000028/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-smoke-final-20260516T155456Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-smoke-final-20260516T155456Z-codex-packet-000028-20260516_155533

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
- `program-429bbec8b81e1287` `refine_modal_family_cue_rules`
  target: `modal.compiler.registry`
  objective: Adaptive family evidence disagrees with, or is weak for, the typed modal family.
  support: 2
  evidence: `{"family_margin": -0.669337638281, "hint_id": "modal-synthesis-84691e1728457dd7", "predicted_family": "conditional_normative", "priority": 0.964929588254, "sample_id": "us-code-18-1864-0895435d80f993be", "target_family": "temporal", "target_probability": 0.035070411746}`
  evidence: `{"family_margin": -0.759550049661, "hint_id": "modal-synthesis-a6e2f4c56a491425", "predicted_family": "temporal", "priority": 0.881117016677, "sample_id": "us-code-46-53713.-35b054d30aa10ddc", "target_family": "deontic", "target_probability": 0.118882983323}`
- `program-454919a69ac82aae` `add_or_review_modal_ambiguity_policy`
  target: `modal.compiler.ambiguity`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  support: 2
  evidence: `{"family_margin": -0.669337638281, "hint_id": "modal-synthesis-4dd428bfef70a93f", "predicted_family": "conditional_normative", "priority": 0.819337638281, "sample_id": "us-code-18-1864-0895435d80f993be", "target_family": "temporal"}`
  evidence: `{"family_margin": -0.759550049661, "hint_id": "modal-synthesis-c5c108c0f9214be6", "predicted_family": "temporal", "priority": 0.909550049661, "sample_id": "us-code-46-53713.-35b054d30aa10ddc", "target_family": "deontic"}`
- `program-569df8edd804df3c` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 2
  evidence: `{"hint_id": "modal-synthesis-243dafec18d9e9a8", "priority": 0.51773843429, "sample_id": "us-code-18-1864-0895435d80f993be"}`
  evidence: `{"hint_id": "modal-synthesis-831df542b5b3f8d1", "priority": 0.300076556014, "sample_id": "us-code-46-53713.-35b054d30aa10ddc"}`
- `program-f631a6967555155a` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 2
  evidence: `{"cosine_similarity": -0.411539146776, "hint_id": "modal-synthesis-6961db96c9131a68", "priority": 0.51773843429, "reconstruction_loss": 0.51773843429, "sample_id": "us-code-18-1864-0895435d80f993be", "top_embedding_features": ["cue:conditional_normative:O|:if", "lemma:civil", "lemma:costs", "lemma:includes", "lemma:regard", "lemma:remains", "lemma:trip", "family:frame:1"]}`
  evidence: `{"cosine_similarity": 0.272661817671, "hint_id": "modal-synthesis-cb34658af9fda078", "priority": 0.300076556014, "reconstruction_loss": 0.300076556014, "sample_id": "us-code-46-53713.-35b054d30aa10ddc", "top_embedding_features": ["lemma:charge", "lemma:investigating", "lemma:administration", "lemma:administrative", "lemma:derived", "lemma:introductory", "lemma:large", "lemma:legislative"]}`

## Patch Command
Run this after editing the worktree:

```bash
git diff HEAD > changes.patch
```

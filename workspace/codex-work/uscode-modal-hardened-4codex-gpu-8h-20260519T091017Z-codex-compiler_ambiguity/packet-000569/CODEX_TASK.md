# packet-000569

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_ambiguity/packet-000569/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_ambiguity/packet-000569/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_ambiguity/worktrees/agent-codex-compiler_ambiguity-packet-000569-20260519_164522

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/compiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_registry.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py`

## TODOs
- `program-cc1244899492db9e` `add_or_review_modal_ambiguity_policy`
  target: `modal.compiler.ambiguity`
  scope: `compiler_ambiguity`
  bundle: `{"action":"add_or_review_modal_ambiguity_policy","family_pairs":["alethic->frame","deontic->epistemic","frame->conditional_normative"],"program_synthesis_scope":"compiler_ambiguity","target_component":"modal.compiler.ambiguity"}`
  vector_bundle: `program-cc1244899492db9e` score `1.0`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  support: 3
  evidence: `{"family_margin": -0.873489298146, "hint_id": "modal-synthesis-369909f52b1c28bc", "predicted_family": "alethic", "priority": 1.023489298146, "sample_id": "us-code-48-1574.-f9081ded4aa34275", "target_family": "frame"}`
  evidence: `{"family_margin": -0.996675378384, "hint_id": "modal-synthesis-7a422ed6786e3304", "predicted_family": "frame", "priority": 1.146675378384, "sample_id": "us-code-33-2716-0a535e176856ddc9", "target_family": "conditional_normative"}`
  evidence: `{"family_margin": -0.422139884017, "hint_id": "modal-synthesis-e74bc2f94c39864f", "predicted_family": "deontic", "priority": 0.572139884017, "sample_id": "us-code-22-262p-4b-03ebeee53c8b50cd", "target_family": "epistemic"}`
- `program-17a05a99670d1ae4` `add_or_review_modal_ambiguity_policy`
  target: `modal.compiler.ambiguity`
  scope: `compiler_ambiguity`
  bundle: `{"action":"add_or_review_modal_ambiguity_policy","family_pairs":["deontic->conditional_normative","deontic->temporal"],"program_synthesis_scope":"compiler_ambiguity","target_component":"modal.compiler.ambiguity"}`
  vector_bundle: `program-cc1244899492db9e` score `0.978664`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  support: 3
  evidence: `{"family_margin": -0.421626693366, "hint_id": "modal-synthesis-103504ece24b2a0c", "predicted_family": "deontic", "priority": 0.571626693366, "sample_id": "us-code-15-6104-8fef2f81532f25c4", "target_family": "temporal"}`
  evidence: `{"family_margin": -0.209360858578, "hint_id": "modal-synthesis-2beb52d6dbab6891", "predicted_family": "deontic", "priority": 0.359360858578, "sample_id": "us-code-7-2158-a09f86abd58a5b26", "target_family": "conditional_normative"}`
  evidence: `{"family_margin": 0.0, "hint_id": "modal-synthesis-9dfdde9030854417", "predicted_family": "deontic", "priority": 0.15, "sample_id": "us-code-22-6592-6a5fd41e31cf2f8d", "target_family": "conditional_normative"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.

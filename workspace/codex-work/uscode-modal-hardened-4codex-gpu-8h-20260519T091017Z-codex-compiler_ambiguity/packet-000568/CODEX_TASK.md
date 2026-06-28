# packet-000568

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_ambiguity/packet-000568/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_ambiguity/packet-000568/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_ambiguity/worktrees/agent-codex-compiler_ambiguity-packet-000568-20260519_163910

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/compiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_registry.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py`

## TODOs
- `program-c51b39bfc0c5043f` `add_or_review_modal_ambiguity_policy`
  target: `modal.compiler.ambiguity`
  scope: `compiler_ambiguity`
  bundle: `{"action":"add_or_review_modal_ambiguity_policy","family_pairs":["alethic->epistemic","deontic->conditional_normative","frame->temporal"],"program_synthesis_scope":"compiler_ambiguity","target_component":"modal.compiler.ambiguity"}`
  vector_bundle: `program-c51b39bfc0c5043f` score `1.0`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  support: 3
  evidence: `{"family_margin": 0.0, "hint_id": "modal-synthesis-72e40a69c4fdd99c", "predicted_family": "deontic", "priority": 0.15, "sample_id": "us-code-7-8203-eef8592beaf3bf27", "target_family": "conditional_normative"}`
  evidence: `{"family_margin": -0.82092512363, "hint_id": "modal-synthesis-a8046d699cc84564", "predicted_family": "alethic", "priority": 0.97092512363, "sample_id": "us-code-12-5018-ece54fe9a514c43c", "target_family": "epistemic"}`
  evidence: `{"family_margin": -0.976122308832, "hint_id": "modal-synthesis-b849570ced4558e1", "predicted_family": "frame", "priority": 1.126122308832, "sample_id": "us-code-10-2650-fc88eeb2517632d4", "target_family": "temporal"}`
- `program-6c7d2601af80f322` `add_or_review_modal_ambiguity_policy`
  target: `modal.compiler.ambiguity`
  scope: `compiler_ambiguity`
  bundle: `{"action":"add_or_review_modal_ambiguity_policy","family_pairs":["deontic->temporal","temporal->temporal"],"program_synthesis_scope":"compiler_ambiguity","target_component":"modal.compiler.ambiguity"}`
  vector_bundle: `program-c51b39bfc0c5043f` score `0.97274`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  support: 2
  evidence: `{"family_margin": 0.0, "hint_id": "modal-synthesis-40f818082492500f", "predicted_family": "temporal", "priority": 0.15, "sample_id": "us-code-16-115a-d0babad0261804a7", "target_family": "temporal"}`
  evidence: `{"family_margin": -0.621470421233, "hint_id": "modal-synthesis-f27a521adb7f4c69", "predicted_family": "deontic", "priority": 0.771470421233, "sample_id": "us-code-42-299b-67436521eac14325", "target_family": "temporal"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.

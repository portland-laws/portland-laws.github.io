# packet-000566

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_ambiguity/packet-000566/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_ambiguity/packet-000566/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_ambiguity/worktrees/agent-codex-compiler_ambiguity-packet-000566-20260519_162452

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/compiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_registry.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py`

## TODOs
- `program-ba549f587ea2d0de` `add_or_review_modal_ambiguity_policy`
  target: `modal.compiler.ambiguity`
  scope: `compiler_ambiguity`
  bundle: `{"action":"add_or_review_modal_ambiguity_policy","family_pairs":["deontic->deontic","frame->conditional_normative","frame->dynamic"],"program_synthesis_scope":"compiler_ambiguity","target_component":"modal.compiler.ambiguity"}`
  vector_bundle: `program-ba549f587ea2d0de` score `1.0`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  support: 3
  evidence: `{"family_margin": -0.494646959627, "hint_id": "modal-synthesis-4d608290aa5a7c45", "predicted_family": "frame", "priority": 0.644646959627, "sample_id": "us-code-15-1693i-c5b32e9682c65bf6", "target_family": "dynamic"}`
  evidence: `{"family_margin": 0.0, "hint_id": "modal-synthesis-a08f820398e26d0f", "predicted_family": "deontic", "priority": 0.15, "sample_id": "us-code-25-2105-2805749f4deed141", "target_family": "deontic"}`
  evidence: `{"family_margin": -0.697957799282, "hint_id": "modal-synthesis-d828f2c604e0ef47", "predicted_family": "frame", "priority": 0.847957799282, "sample_id": "us-code-36-230504-78cb5c6be6527fc3", "target_family": "conditional_normative"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.

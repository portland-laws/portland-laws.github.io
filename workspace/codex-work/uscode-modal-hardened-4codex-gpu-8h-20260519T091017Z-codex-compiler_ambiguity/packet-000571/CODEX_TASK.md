# packet-000571

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_ambiguity/packet-000571/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_ambiguity/packet-000571/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_ambiguity/worktrees/agent-codex-compiler_ambiguity-packet-000571-20260519_170248

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/compiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_registry.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py`

## TODOs
- `program-f5576f3893a4f6b4` `add_or_review_modal_ambiguity_policy`
  target: `modal.compiler.ambiguity`
  scope: `compiler_ambiguity`
  bundle: `{"action":"add_or_review_modal_ambiguity_policy","family_pairs":["conditional_normative->temporal","frame->conditional_normative","frame->temporal","temporal->temporal"],"program_synthesis_scope":"compiler_ambiguity","target_component":"modal.compiler.ambiguity"}`
  vector_bundle: `program-f5576f3893a4f6b4` score `1.0`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  support: 4
  evidence: `{"family_margin": -0.930605805155, "hint_id": "modal-synthesis-04f76ba6709fe14f", "predicted_family": "frame", "priority": 1.080605805155, "sample_id": "us-code-12-5707-a20569681a642369", "target_family": "conditional_normative"}`
  evidence: `{"family_margin": -0.823053456348, "hint_id": "modal-synthesis-349478c77be6c03a", "predicted_family": "frame", "priority": 0.973053456348, "sample_id": "us-code-10-687-62134f1eaa130df9", "target_family": "temporal"}`
  evidence: `{"family_margin": 0.0, "hint_id": "modal-synthesis-585bc3b85d8e591c", "predicted_family": "temporal", "priority": 0.15, "sample_id": "us-code-6-924-46b4e91da16607f0", "target_family": "temporal"}`
  evidence: `{"family_margin": -0.469089453834, "hint_id": "modal-synthesis-b53879e7c4469648", "predicted_family": "conditional_normative", "priority": 0.619089453834, "sample_id": "us-code-42-10225.-8bd3296ec2ba451b", "target_family": "temporal"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.

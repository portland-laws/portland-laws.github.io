# packet-000275

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_registry/packet-000275/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_registry/packet-000275/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_registry/worktrees/agent-codex-compiler_registry-packet-000275-20260519_165700

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/compiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_registry.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py`

## TODOs
- `program-8dcbb5e952521b75` `refine_modal_family_cue_rules`
  target: `modal.compiler.registry`
  scope: `compiler_registry`
  bundle: `{"action":"refine_modal_family_cue_rules","family_pairs":["conditional_normative->temporal","frame->conditional_normative","frame->temporal","temporal->temporal"],"program_synthesis_scope":"compiler_registry","target_component":"modal.compiler.registry"}`
  vector_bundle: `program-8dcbb5e952521b75` score `1.0`
  objective: Adaptive family evidence disagrees with, or is weak for, the typed modal family.
  support: 4
  evidence: `{"family_margin": 0.0, "hint_id": "modal-synthesis-3d67fab112c3707b", "predicted_family": "temporal", "priority": 0.609627680526, "sample_id": "us-code-6-924-46b4e91da16607f0", "target_family": "temporal", "target_probability": 0.390372319474}`
  evidence: `{"family_margin": -0.930605805155, "hint_id": "modal-synthesis-549f9734721b19f7", "predicted_family": "frame", "priority": 0.984317470595, "sample_id": "us-code-12-5707-a20569681a642369", "target_family": "conditional_normative", "target_probability": 0.015682529405}`
  evidence: `{"family_margin": -0.823053456348, "hint_id": "modal-synthesis-7130cd8115875e61", "predicted_family": "frame", "priority": 0.959083302823, "sample_id": "us-code-10-687-62134f1eaa130df9", "target_family": "temporal", "target_probability": 0.040916697177}`
  evidence: `{"family_margin": -0.469089453834, "hint_id": "modal-synthesis-b3c0a3517ef0acde", "predicted_family": "conditional_normative", "priority": 0.952488260414, "sample_id": "us-code-42-10225.-8bd3296ec2ba451b", "target_family": "temporal", "target_probability": 0.047511739586}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.

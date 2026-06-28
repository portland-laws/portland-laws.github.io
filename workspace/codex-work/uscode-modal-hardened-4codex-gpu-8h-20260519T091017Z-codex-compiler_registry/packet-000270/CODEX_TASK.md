# packet-000270

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_registry/packet-000270/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_registry/packet-000270/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_registry/worktrees/agent-codex-compiler_registry-packet-000270-20260519_161027

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/compiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_registry.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py`

## TODOs
- `program-8bec8d1df694ef8b` `refine_modal_family_cue_rules`
  target: `modal.compiler.registry`
  scope: `compiler_registry`
  bundle: `{"action":"refine_modal_family_cue_rules","family_pairs":["frame->deontic","frame->epistemic","frame->temporal"],"program_synthesis_scope":"compiler_registry","target_component":"modal.compiler.registry"}`
  vector_bundle: `program-8bec8d1df694ef8b` score `1.0`
  objective: Adaptive family evidence disagrees with, or is weak for, the typed modal family.
  support: 3
  evidence: `{"family_margin": -0.999908575942, "hint_id": "modal-synthesis-3fba80c5ad03f424", "predicted_family": "frame", "priority": 0.999999998138, "sample_id": "us-code-42-666.-a96cfa64256cae78", "target_family": "deontic", "target_probability": 1.862e-09}`
  evidence: `{"family_margin": -0.631226929562, "hint_id": "modal-synthesis-c1ad3ed87699eb2b", "predicted_family": "frame", "priority": 0.929661901489, "sample_id": "us-code-18-1919-238552e353cd2eec", "target_family": "epistemic", "target_probability": 0.070338098511}`
  evidence: `{"family_margin": -0.998544042424, "hint_id": "modal-synthesis-e7043dd7bd990ab5", "predicted_family": "frame", "priority": 0.999973843971, "sample_id": "us-code-42-16152.-2ce73465f6707341", "target_family": "temporal", "target_probability": 2.6156029e-05}`
- `program-1f464942b3950521` `refine_modal_family_cue_rules`
  target: `modal.compiler.registry`
  scope: `compiler_registry`
  bundle: `{"action":"refine_modal_family_cue_rules","family_pairs":["deontic->deontic","frame->conditional_normative","temporal->temporal"],"program_synthesis_scope":"compiler_registry","target_component":"modal.compiler.registry"}`
  vector_bundle: `program-8bec8d1df694ef8b` score `0.976819`
  objective: Adaptive family evidence disagrees with, or is weak for, the typed modal family.
  support: 3
  evidence: `{"family_margin": 0.0, "hint_id": "modal-synthesis-14e1c7bf48fb611a", "predicted_family": "temporal", "priority": 0.519371197283, "sample_id": "us-code-22-10412-551f5ec597c4dc61", "target_family": "temporal", "target_probability": 0.480628802717}`
  evidence: `{"family_margin": -0.999995600089, "hint_id": "modal-synthesis-c4c7d2fca195502a", "predicted_family": "frame", "priority": 0.999998619881, "sample_id": "us-code-15-80b-2-b829c8e17aa97516", "target_family": "conditional_normative", "target_probability": 1.380119e-06}`
  evidence: `{"family_margin": 0.026492745977, "hint_id": "modal-synthesis-e99f98e981bad29e", "predicted_family": "deontic", "priority": 0.584655674528, "sample_id": "us-code-15-7106-a4e159e8a8f68337", "target_family": "deontic", "target_probability": 0.415344325472}`
- `program-d3ae4c06dba1cca6` `refine_modal_family_cue_rules`
  target: `modal.compiler.registry`
  scope: `compiler_registry`
  bundle: `{"action":"refine_modal_family_cue_rules","family_pairs":["frame->conditional_normative","frame->frame"],"program_synthesis_scope":"compiler_registry","target_component":"modal.compiler.registry"}`
  vector_bundle: `program-8bec8d1df694ef8b` score `0.97396`
  objective: Adaptive family evidence disagrees with, or is weak for, the typed modal family.
  support: 2
  evidence: `{"family_margin": -0.708470320074, "hint_id": "modal-synthesis-0b43976880e5e5e6", "predicted_family": "frame", "priority": 0.900606567433, "sample_id": "us-code-10-8372-d647973d9c9cbccd", "target_family": "conditional_normative", "target_probability": 0.099393432567}`
  evidence: `{"family_margin": 0.230633654258, "hint_id": "modal-synthesis-4478f908aafa5f38", "predicted_family": "frame", "priority": 0.562890382602, "sample_id": "us-code-16-460ss-6-e67f41f2be64b8a8", "target_family": "frame", "target_probability": 0.437109617398}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.

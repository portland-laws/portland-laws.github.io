# packet-000273

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_registry/packet-000273/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_registry/packet-000273/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_registry/worktrees/agent-codex-compiler_registry-packet-000273-20260519_163844

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/compiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_registry.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py`

## TODOs
- `program-12e5deab2816228e` `refine_modal_family_cue_rules`
  target: `modal.compiler.registry`
  scope: `compiler_registry`
  bundle: `{"action":"refine_modal_family_cue_rules","family_pairs":["alethic->epistemic","deontic->conditional_normative","frame->temporal"],"program_synthesis_scope":"compiler_registry","target_component":"modal.compiler.registry"}`
  vector_bundle: `program-12e5deab2816228e` score `1.0`
  objective: Adaptive family evidence disagrees with, or is weak for, the typed modal family.
  support: 3
  evidence: `{"family_margin": -0.82092512363, "hint_id": "modal-synthesis-3792118ee0c768a6", "predicted_family": "alethic", "priority": 0.999724517887, "sample_id": "us-code-12-5018-ece54fe9a514c43c", "target_family": "epistemic", "target_probability": 0.000275482113}`
  evidence: `{"family_margin": -0.976122308832, "hint_id": "modal-synthesis-66231b97c443c29a", "predicted_family": "frame", "priority": 0.998204244387, "sample_id": "us-code-10-2650-fc88eeb2517632d4", "target_family": "temporal", "target_probability": 0.001795755613}`
  evidence: `{"family_margin": 0.0, "hint_id": "modal-synthesis-d75f62bee2c3cbb4", "predicted_family": "deontic", "priority": 0.628450177902, "sample_id": "us-code-7-8203-eef8592beaf3bf27", "target_family": "conditional_normative", "target_probability": 0.371549822098}`
- `program-bb3d590a313f2e1c` `refine_modal_family_cue_rules`
  target: `modal.compiler.registry`
  scope: `compiler_registry`
  bundle: `{"action":"refine_modal_family_cue_rules","family_pairs":["alethic->frame","frame->deontic","temporal->deontic"],"program_synthesis_scope":"compiler_registry","target_component":"modal.compiler.registry"}`
  vector_bundle: `program-12e5deab2816228e` score `0.973529`
  objective: Adaptive family evidence disagrees with, or is weak for, the typed modal family.
  support: 3
  evidence: `{"family_margin": -0.314912979406, "hint_id": "modal-synthesis-27937d5e0e17a829", "predicted_family": "alethic", "priority": 0.689359173016, "sample_id": "us-code-43-390h.-20a339501c1a8236", "target_family": "frame", "target_probability": 0.310640826984}`
  evidence: `{"family_margin": -0.592973972988, "hint_id": "modal-synthesis-e93ec6b21cc452f0", "predicted_family": "frame", "priority": 0.829687843742, "sample_id": "us-code-14-2735-857345e2c5c2a359", "target_family": "deontic", "target_probability": 0.170312156258}`
  evidence: `{"family_margin": -0.332063308249, "hint_id": "modal-synthesis-ee563d0b7cf2523c", "predicted_family": "temporal", "priority": 0.806746889393, "sample_id": "us-code-42-5083.-77b302f9cbe4a1a5", "target_family": "deontic", "target_probability": 0.193253110607}`
- `program-33e47faad4fa245f` `refine_modal_family_cue_rules`
  target: `modal.compiler.registry`
  scope: `compiler_registry`
  bundle: `{"action":"refine_modal_family_cue_rules","family_pairs":["deontic->temporal","temporal->temporal"],"program_synthesis_scope":"compiler_registry","target_component":"modal.compiler.registry"}`
  vector_bundle: `program-12e5deab2816228e` score `0.969799`
  objective: Adaptive family evidence disagrees with, or is weak for, the typed modal family.
  support: 2
  evidence: `{"family_margin": 0.0, "hint_id": "modal-synthesis-6b8d9f47b676117d", "predicted_family": "temporal", "priority": 0.559746660672, "sample_id": "us-code-16-115a-d0babad0261804a7", "target_family": "temporal", "target_probability": 0.440253339328}`
  evidence: `{"family_margin": -0.621470421233, "hint_id": "modal-synthesis-b6f60e97e7b1f1fe", "predicted_family": "deontic", "priority": 0.992911146038, "sample_id": "us-code-42-299b-67436521eac14325", "target_family": "temporal", "target_probability": 0.007088853962}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.

# packet-000272

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_registry/packet-000272/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_registry/packet-000272/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_registry/worktrees/agent-codex-compiler_registry-packet-000272-20260519_162837

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/compiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_registry.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py`

## TODOs
- `program-b8bc98a7d11eeb3d` `refine_modal_family_cue_rules`
  target: `modal.compiler.registry`
  scope: `compiler_registry`
  bundle: `{"action":"refine_modal_family_cue_rules","family_pairs":["deontic->deontic","deontic->temporal","frame->deontic","frame->temporal"],"program_synthesis_scope":"compiler_registry","target_component":"modal.compiler.registry"}`
  vector_bundle: `program-b8bc98a7d11eeb3d` score `1.0`
  objective: Adaptive family evidence disagrees with, or is weak for, the typed modal family.
  support: 4
  evidence: `{"family_margin": -0.926328371836, "hint_id": "modal-synthesis-12cdf77a9057c924", "predicted_family": "frame", "priority": 0.996198772921, "sample_id": "us-code-43-335.-d45612529e6d83ea", "target_family": "temporal", "target_probability": 0.003801227079}`
  evidence: `{"family_margin": 0.219643699714, "hint_id": "modal-synthesis-306a6f237781ff78", "predicted_family": "deontic", "priority": 0.557066586534, "sample_id": "us-code-10-2123-d051400311bbe9ad", "target_family": "deontic", "target_probability": 0.442933413466}`
  evidence: `{"family_margin": -0.391966469637, "hint_id": "modal-synthesis-552c2daeb92496fb", "predicted_family": "deontic", "priority": 0.842605425705, "sample_id": "us-code-12-1772f-ce49c6ebd84349c6", "target_family": "temporal", "target_probability": 0.157394574295}`
  evidence: `{"family_margin": -0.518545682385, "hint_id": "modal-synthesis-da1d81be651af2fb", "predicted_family": "frame", "priority": 0.851064907891, "sample_id": "us-code-12-531-22711fe82760fb04", "target_family": "deontic", "target_probability": 0.148935092109}`
- `program-f33e0f3adaed7d4e` `refine_modal_family_cue_rules`
  target: `modal.compiler.registry`
  scope: `compiler_registry`
  bundle: `{"action":"refine_modal_family_cue_rules","family_pairs":["deontic->deontic","frame->conditional_normative","frame->dynamic"],"program_synthesis_scope":"compiler_registry","target_component":"modal.compiler.registry"}`
  vector_bundle: `program-b8bc98a7d11eeb3d` score `0.970683`
  objective: Adaptive family evidence disagrees with, or is weak for, the typed modal family.
  support: 3
  evidence: `{"family_margin": 0.0, "hint_id": "modal-synthesis-8f4426090b9b810d", "predicted_family": "deontic", "priority": 0.585383129705, "sample_id": "us-code-25-2105-2805749f4deed141", "target_family": "deontic", "target_probability": 0.414616870295}`
  evidence: `{"family_margin": -0.697957799282, "hint_id": "modal-synthesis-a7d7e89502845767", "predicted_family": "frame", "priority": 0.874321204968, "sample_id": "us-code-36-230504-78cb5c6be6527fc3", "target_family": "conditional_normative", "target_probability": 0.125678795032}`
  evidence: `{"family_margin": -0.494646959627, "hint_id": "modal-synthesis-fbb67956257177c8", "predicted_family": "frame", "priority": 0.989569738605, "sample_id": "us-code-15-1693i-c5b32e9682c65bf6", "target_family": "dynamic", "target_probability": 0.010430261395}`
- `program-196031702ee22ff8` `refine_modal_family_cue_rules`
  target: `modal.compiler.registry`
  scope: `compiler_registry`
  bundle: `{"action":"refine_modal_family_cue_rules","family_pairs":["conditional_normative->conditional_normative","frame->temporal"],"program_synthesis_scope":"compiler_registry","target_component":"modal.compiler.registry"}`
  vector_bundle: `program-b8bc98a7d11eeb3d` score `0.911133`
  objective: Adaptive family evidence disagrees with, or is weak for, the typed modal family.
  support: 2
  evidence: `{"family_margin": 0.082281929987, "hint_id": "modal-synthesis-38223766dca02451", "predicted_family": "conditional_normative", "priority": 0.544930762163, "sample_id": "us-code-7-182-b18cb75569dc2d85", "target_family": "conditional_normative", "target_probability": 0.455069237837}`
  evidence: `{"family_margin": -0.98641901285, "hint_id": "modal-synthesis-78f50f32ef802703", "predicted_family": "frame", "priority": 0.995313287566, "sample_id": "us-code-47-555.-f3c0d28d2e6b674d", "target_family": "temporal", "target_probability": 0.004686712434}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.

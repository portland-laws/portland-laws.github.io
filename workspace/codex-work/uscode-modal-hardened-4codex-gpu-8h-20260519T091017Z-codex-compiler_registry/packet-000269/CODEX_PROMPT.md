# packet-000269

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_registry/packet-000269/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_registry/packet-000269/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_registry/worktrees/agent-codex-compiler_registry-packet-000269-20260519_155954

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/compiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_registry.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py`

## TODOs
- `program-54f3a072023a2ab8` `refine_modal_family_cue_rules`
  target: `modal.compiler.registry`
  scope: `compiler_registry`
  bundle: `{"action":"refine_modal_family_cue_rules","family_pairs":["deontic->temporal","frame->epistemic"],"program_synthesis_scope":"compiler_registry","target_component":"modal.compiler.registry"}`
  vector_bundle: `program-54f3a072023a2ab8` score `1.0`
  objective: Adaptive family evidence disagrees with, or is weak for, the typed modal family.
  support: 2
  evidence: `{"family_margin": -0.957919173467, "hint_id": "modal-synthesis-3d5a509e9b8620fa", "predicted_family": "frame", "priority": 0.995194469232, "sample_id": "us-code-15-1644-9e552b71b349501b", "target_family": "epistemic", "target_probability": 0.004805530768}`
  evidence: `{"family_margin": -0.87157850633, "hint_id": "modal-synthesis-ff057548d4e89b20", "predicted_family": "deontic", "priority": 0.958824038525, "sample_id": "us-code-25-139-d7777f253f3394b8", "target_family": "temporal", "target_probability": 0.041175961475}`
- `program-6382a5653079cdc8` `refine_modal_family_cue_rules`
  target: `modal.compiler.registry`
  scope: `compiler_registry`
  bundle: `{"action":"refine_modal_family_cue_rules","family_pairs":["deontic->deontic","deontic->temporal","frame->conditional_normative"],"program_synthesis_scope":"compiler_registry","target_component":"modal.compiler.registry"}`
  vector_bundle: `program-54f3a072023a2ab8` score `0.957551`
  objective: Adaptive family evidence disagrees with, or is weak for, the typed modal family.
  support: 3
  evidence: `{"family_margin": -0.137909020851, "hint_id": "modal-synthesis-3f55bbc49b36c535", "predicted_family": "deontic", "priority": 0.689704703085, "sample_id": "us-code-35-181-f29b71497947aab0", "target_family": "temporal", "target_probability": 0.310295296915}`
  evidence: `{"family_margin": 0.138132227584, "hint_id": "modal-synthesis-4c1d6794ac504d7a", "predicted_family": "deontic", "priority": 0.599209567804, "sample_id": "us-code-12-2153-baf813aee2fd8501", "target_family": "deontic", "target_probability": 0.400790432196}`
  evidence: `{"family_margin": -0.982627491034, "hint_id": "modal-synthesis-d64e847a9dee2ab1", "predicted_family": "frame", "priority": 0.995070516624, "sample_id": "us-code-7-2209j-dd7e2e5d9e16255f", "target_family": "conditional_normative", "target_probability": 0.004929483376}`
- `program-7a502aca45b5c7f9` `refine_modal_family_cue_rules`
  target: `modal.compiler.registry`
  scope: `compiler_registry`
  bundle: `{"action":"refine_modal_family_cue_rules","family_pairs":["conditional_normative->conditional_normative","deontic->temporal","frame->deontic"],"program_synthesis_scope":"compiler_registry","target_component":"modal.compiler.registry"}`
  vector_bundle: `program-54f3a072023a2ab8` score `0.928504`
  objective: Adaptive family evidence disagrees with, or is weak for, the typed modal family.
  support: 4
  evidence: `{"family_margin": -0.487494115977, "hint_id": "modal-synthesis-443c771b7e2a4ce3", "predicted_family": "frame", "priority": 0.859983443056, "sample_id": "us-code-28-1695-5da9389229c48d27", "target_family": "deontic", "target_probability": 0.140016556944}`
  evidence: `{"family_margin": -0.695596453987, "hint_id": "modal-synthesis-61e8c5985ed85e9c", "predicted_family": "deontic", "priority": 0.999086262489, "sample_id": "us-code-42-806.-0f3a967446ef3128", "target_family": "temporal", "target_probability": 0.000913737511}`
  evidence: `{"family_margin": 0.264995459046, "hint_id": "modal-synthesis-930af6e6b1fb15d7", "predicted_family": "conditional_normative", "priority": 0.580783356364, "sample_id": "us-code-18-891-7b57507b76d533ec", "target_family": "conditional_normative", "target_probability": 0.419216643636}`
  evidence: `{"family_margin": -0.999991766738, "hint_id": "modal-synthesis-bd44340d4d134de7", "predicted_family": "frame", "priority": 0.999997638469, "sample_id": "us-code-12-1815-bf9bc9fce970cdfc", "target_family": "deontic", "target_probability": 2.361531e-06}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.


## Execution Instructions
Work only inside the packet worktree.
Your worktree edits may be applied back to the source checkout and validated automatically when this packet finishes.
Do not create changes.patch or other patch artifact files; leave source and test edits directly in the worktree.
Treat the packet's program_synthesis_scope metadata as the AST/write-scope boundary; keep edits inside that lane unless a test requires a small adjacent change.
When multiple TODOs are present, treat their semantic_bundle_key or vector_bundle metadata as evidence for one generalized compiler/decompiler/frame improvement over one-off sample fixes.
Implement a narrow deterministic parser, IR, decoder, or frame-logic improvement for the claimed TODOs.
Prefer explainable compiler/decompiler code over learned weights when the TODO concerns modal or frame semantics.
Use local repository files and tests only; do not use web search for this packet.
Run the smallest relevant tests you can before finishing.
Leave unrelated files alone.

## Claimed Autoencoder TODO List
# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-autoencoder.jsonl`
- TODO count: `3`

## TODOs
- `program-54f3a072023a2ab8`
  action: `refine_modal_family_cue_rules`
  role: `program_synthesis`
  target: `modal.compiler.registry`
  scope: `compiler_registry`
  bundle: `{"action":"refine_modal_family_cue_rules","family_pairs":["deontic->temporal","frame->epistemic"],"program_synthesis_scope":"compiler_registry","target_component":"modal.compiler.registry"}`
  vector_bundle: `program-54f3a072023a2ab8` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.977009253879`
  objective: Adaptive family evidence disagrees with, or is weak for, the typed modal family.
  samples: `us-code-15-1644-9e552b71b349501b, us-code-25-139-d7777f253f3394b8`
  evidence: `{"family_margin": -0.957919173467, "hint_id": "modal-synthesis-3d5a509e9b8620fa", "predicted_family": "frame", "priority": 0.995194469232, "sample_id": "us-code-15-1644-9e552b71b349501b", "target_family": "epistemic", "target_probability": 0.004805530768}`
  evidence: `{"family_margin": -0.87157850633, "hint_id": "modal-synthesis-ff057548d4e89b20", "predicted_family": "deontic", "priority": 0.958824038525, "sample_id": "us-code-25-139-d7777f253f3394b8", "target_family": "temporal", "target_probability": 0.041175961475}`
- `program-6382a5653079cdc8`
  action: `refine_modal_family_cue_rules`
  role: `program_synthesis`
  target: `modal.compiler.registry`
  scope: `compiler_registry`
  bundle: `{"action":"refine_modal_family_cue_rules","family_pairs":["deontic->deontic","deontic->temporal","frame->conditional_normative"],"program_synthesis_scope":"compiler_registry","target_component":"modal.compiler.registry"}`
  vector_bundle: `program-54f3a072023a2ab8` score `0.957551`
  loss: `autoencoder_residual_cluster` = `0.761328262504`
  objective: Adaptive family evidence disagrees with, or is weak for, the typed modal family.
  samples: `us-code-7-2209j-dd7e2e5d9e16255f, us-code-35-181-f29b71497947aab0, us-code-12-2153-baf813aee2fd8501`
  evidence: `{"family_margin": -0.137909020851, "hint_id": "modal-synthesis-3f55bbc49b36c535", "predicted_family": "deontic", "priority": 0.689704703085, "sample_id": "us-code-35-181-f29b71497947aab0", "target_family": "temporal", "target_probability": 0.310295296915}`
  evidence: `{"family_margin": 0.138132227584, "hint_id": "modal-synthesis-4c1d6794ac504d7a", "predicted_family": "deontic", "priority": 0.599209567804, "sample_id": "us-code-12-2153-baf813aee2fd8501", "target_family": "deontic", "target_probability": 0.400790432196}`
  evidence: `{"family_margin": -0.982627491034, "hint_id": "modal-synthesis-d64e847a9dee2ab1", "predicted_family": "frame", "priority": 0.995070516624, "sample_id": "us-code-7-2209j-dd7e2e5d9e16255f", "target_family": "conditional_normative", "target_probability": 0.004929483376}`
- `program-7a502aca45b5c7f9`
  action: `refine_modal_family_cue_rules`
  role: `program_synthesis`
  target: `modal.compiler.registry`
  scope: `compiler_registry`
  bundle: `{"action":"refine_modal_family_cue_rules","family_pairs":["conditional_normative->conditional_normative","deontic->temporal","frame->deontic"],"program_synthesis_scope":"compiler_registry","target_component":"modal.compiler.registry"}`
  vector_bundle: `program-54f3a072023a2ab8` score `0.928504`
  loss: `autoencoder_residual_cluster` = `0.859962675094`
  objective: Adaptive family evidence disagrees with, or is weak for, the typed modal family.
  samples: `us-code-12-1815-bf9bc9fce970cdfc, us-code-42-806.-0f3a967446ef3128, us-code-28-1695-5da9389229c48d27, us-code-18-891-7b57507b76d533ec`
  evidence: `{"family_margin": -0.487494115977, "hint_id": "modal-synthesis-443c771b7e2a4ce3", "predicted_family": "frame", "priority": 0.859983443056, "sample_id": "us-code-28-1695-5da9389229c48d27", "target_family": "deontic", "target_probability": 0.140016556944}`
  evidence: `{"family_margin": -0.695596453987, "hint_id": "modal-synthesis-61e8c5985ed85e9c", "predicted_family": "deontic", "priority": 0.999086262489, "sample_id": "us-code-42-806.-0f3a967446ef3128", "target_family": "temporal", "target_probability": 0.000913737511}`
  evidence: `{"family_margin": 0.264995459046, "hint_id": "modal-synthesis-930af6e6b1fb15d7", "predicted_family": "conditional_normative", "priority": 0.580783356364, "sample_id": "us-code-18-891-7b57507b76d533ec", "target_family": "conditional_normative", "target_probability": 0.419216643636}`
  evidence: `{"family_margin": -0.999991766738, "hint_id": "modal-synthesis-bd44340d4d134de7", "predicted_family": "frame", "priority": 0.999997638469, "sample_id": "us-code-12-1815-bf9bc9fce970cdfc", "target_family": "deontic", "target_probability": 2.361531e-06}`

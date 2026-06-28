# packet-000274

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_registry/packet-000274/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_registry/packet-000274/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_registry/worktrees/agent-codex-compiler_registry-packet-000274-20260519_165114

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/compiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_registry.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py`

## TODOs
- `program-93e0cd75c6a06b7a` `refine_modal_family_cue_rules`
  target: `modal.compiler.registry`
  scope: `compiler_registry`
  bundle: `{"action":"refine_modal_family_cue_rules","family_pairs":["alethic->frame","deontic->epistemic","frame->conditional_normative"],"program_synthesis_scope":"compiler_registry","target_component":"modal.compiler.registry"}`
  vector_bundle: `program-93e0cd75c6a06b7a` score `1.0`
  objective: Adaptive family evidence disagrees with, or is weak for, the typed modal family.
  support: 3
  evidence: `{"family_margin": -0.873489298146, "hint_id": "modal-synthesis-72fd865bdaaa2eb3", "predicted_family": "alethic", "priority": 0.937067277995, "sample_id": "us-code-48-1574.-f9081ded4aa34275", "target_family": "frame", "target_probability": 0.062932722005}`
  evidence: `{"family_margin": -0.422139884017, "hint_id": "modal-synthesis-803bdfbd498a74da", "predicted_family": "deontic", "priority": 0.985217237469, "sample_id": "us-code-22-262p-4b-03ebeee53c8b50cd", "target_family": "epistemic", "target_probability": 0.014782762531}`
  evidence: `{"family_margin": -0.996675378384, "hint_id": "modal-synthesis-f665ce51734877b1", "predicted_family": "frame", "priority": 0.999555857765, "sample_id": "us-code-33-2716-0a535e176856ddc9", "target_family": "conditional_normative", "target_probability": 0.000444142235}`
- `program-2017d1dd4299cf69` `refine_modal_family_cue_rules`
  target: `modal.compiler.registry`
  scope: `compiler_registry`
  bundle: `{"action":"refine_modal_family_cue_rules","family_pairs":["dynamic->dynamic","frame->conditional_normative","frame->deontic"],"program_synthesis_scope":"compiler_registry","target_component":"modal.compiler.registry"}`
  vector_bundle: `program-93e0cd75c6a06b7a` score `0.981934`
  objective: Adaptive family evidence disagrees with, or is weak for, the typed modal family.
  support: 3
  evidence: `{"family_margin": -0.837741879819, "hint_id": "modal-synthesis-08aebd966111ae6e", "predicted_family": "frame", "priority": 0.941865966229, "sample_id": "us-code-36-220522-c5d706908c8f3683", "target_family": "conditional_normative", "target_probability": 0.058134033771}`
  evidence: `{"family_margin": -0.851890543783, "hint_id": "modal-synthesis-5b9c65f32b8f7b13", "predicted_family": "frame", "priority": 0.950507268064, "sample_id": "us-code-12-2091-76d98884a22e0c41", "target_family": "deontic", "target_probability": 0.049492731936}`
  evidence: `{"family_margin": 0.0, "hint_id": "modal-synthesis-f718221c27a91e3e", "predicted_family": "dynamic", "priority": 0.559746660672, "sample_id": "us-code-42-7385s-359864d4338b98ff", "target_family": "dynamic", "target_probability": 0.440253339328}`
- `program-e6c41421aa2cdfa9` `refine_modal_family_cue_rules`
  target: `modal.compiler.registry`
  scope: `compiler_registry`
  bundle: `{"action":"refine_modal_family_cue_rules","family_pairs":["deontic->conditional_normative","deontic->temporal"],"program_synthesis_scope":"compiler_registry","target_component":"modal.compiler.registry"}`
  vector_bundle: `program-93e0cd75c6a06b7a` score `0.978375`
  objective: Adaptive family evidence disagrees with, or is weak for, the typed modal family.
  support: 3
  evidence: `{"family_margin": -0.209360858578, "hint_id": "modal-synthesis-2c620e83ef6fc7d6", "predicted_family": "deontic", "priority": 0.730821753257, "sample_id": "us-code-7-2158-a09f86abd58a5b26", "target_family": "conditional_normative", "target_probability": 0.269178246743}`
  evidence: `{"family_margin": -0.421626693366, "hint_id": "modal-synthesis-80c8141797a1b335", "predicted_family": "deontic", "priority": 0.915674661327, "sample_id": "us-code-15-6104-8fef2f81532f25c4", "target_family": "temporal", "target_probability": 0.084325338673}`
  evidence: `{"family_margin": 0.0, "hint_id": "modal-synthesis-9240d1f0a618d44d", "predicted_family": "deontic", "priority": 0.580222408163, "sample_id": "us-code-22-6592-6a5fd41e31cf2f8d", "target_family": "conditional_normative", "target_probability": 0.419777591837}`
- `program-ba84088348461161` `refine_modal_family_cue_rules`
  target: `modal.compiler.registry`
  scope: `compiler_registry`
  bundle: `{"action":"refine_modal_family_cue_rules","family_pairs":["frame->deontic","frame->epistemic","temporal->temporal"],"program_synthesis_scope":"compiler_registry","target_component":"modal.compiler.registry"}`
  vector_bundle: `program-93e0cd75c6a06b7a` score `0.970331`
  objective: Adaptive family evidence disagrees with, or is weak for, the typed modal family.
  support: 4
  evidence: `{"family_margin": -0.997004445157, "hint_id": "modal-synthesis-0535ee809cb2588d", "predicted_family": "frame", "priority": 0.998759596788, "sample_id": "us-code-28-2674-13d178046c4e836a", "target_family": "deontic", "target_probability": 0.001240403212}`
  evidence: `{"family_margin": 0.168365523136, "hint_id": "modal-synthesis-6229ff63d9f59bf0", "predicted_family": "temporal", "priority": 0.551025271637, "sample_id": "us-code-19-2401-99a60fb0c79f6875", "target_family": "temporal", "target_probability": 0.448974728363}`
  evidence: `{"family_margin": -0.544325473206, "hint_id": "modal-synthesis-7c34a1da22040a90", "predicted_family": "frame", "priority": 0.796079064643, "sample_id": "us-code-25-1-0a08ee6129f682d8", "target_family": "deontic", "target_probability": 0.203920935357}`
  evidence: `{"family_margin": -0.714891687226, "hint_id": "modal-synthesis-7fbb54bb41ee9864", "predicted_family": "frame", "priority": 0.984925597901, "sample_id": "us-code-18-1303-eb206331feb4490b", "target_family": "epistemic", "target_probability": 0.015074402099}`
- `program-e443245fb2b7f45c` `refine_modal_family_cue_rules`
  target: `modal.compiler.registry`
  scope: `compiler_registry`
  bundle: `{"action":"refine_modal_family_cue_rules","family_pairs":["deontic->deontic","deontic->temporal"],"program_synthesis_scope":"compiler_registry","target_component":"modal.compiler.registry"}`
  vector_bundle: `program-93e0cd75c6a06b7a` score `0.956828`
  objective: Adaptive family evidence disagrees with, or is weak for, the typed modal family.
  support: 2
  evidence: `{"family_margin": -0.403296944418, "hint_id": "modal-synthesis-271b1d338a69131c", "predicted_family": "deontic", "priority": 0.994164032444, "sample_id": "us-code-25-2102-27563426a67cc711", "target_family": "temporal", "target_probability": 0.005835967556}`
  evidence: `{"family_margin": 0.249742455922, "hint_id": "modal-synthesis-6e316ff730f31658", "predicted_family": "deontic", "priority": 0.50390312837, "sample_id": "us-code-16-431-715f8a7a6ba4bc2b", "target_family": "deontic", "target_probability": 0.49609687163}`

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
- TODO count: `5`

## TODOs
- `program-93e0cd75c6a06b7a`
  action: `refine_modal_family_cue_rules`
  role: `program_synthesis`
  target: `modal.compiler.registry`
  scope: `compiler_registry`
  bundle: `{"action":"refine_modal_family_cue_rules","family_pairs":["alethic->frame","deontic->epistemic","frame->conditional_normative"],"program_synthesis_scope":"compiler_registry","target_component":"modal.compiler.registry"}`
  vector_bundle: `program-93e0cd75c6a06b7a` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.973946791076`
  objective: Adaptive family evidence disagrees with, or is weak for, the typed modal family.
  samples: `us-code-33-2716-0a535e176856ddc9, us-code-22-262p-4b-03ebeee53c8b50cd, us-code-48-1574.-f9081ded4aa34275`
  evidence: `{"family_margin": -0.873489298146, "hint_id": "modal-synthesis-72fd865bdaaa2eb3", "predicted_family": "alethic", "priority": 0.937067277995, "sample_id": "us-code-48-1574.-f9081ded4aa34275", "target_family": "frame", "target_probability": 0.062932722005}`
  evidence: `{"family_margin": -0.422139884017, "hint_id": "modal-synthesis-803bdfbd498a74da", "predicted_family": "deontic", "priority": 0.985217237469, "sample_id": "us-code-22-262p-4b-03ebeee53c8b50cd", "target_family": "epistemic", "target_probability": 0.014782762531}`
  evidence: `{"family_margin": -0.996675378384, "hint_id": "modal-synthesis-f665ce51734877b1", "predicted_family": "frame", "priority": 0.999555857765, "sample_id": "us-code-33-2716-0a535e176856ddc9", "target_family": "conditional_normative", "target_probability": 0.000444142235}`
- `program-2017d1dd4299cf69`
  action: `refine_modal_family_cue_rules`
  role: `program_synthesis`
  target: `modal.compiler.registry`
  scope: `compiler_registry`
  bundle: `{"action":"refine_modal_family_cue_rules","family_pairs":["dynamic->dynamic","frame->conditional_normative","frame->deontic"],"program_synthesis_scope":"compiler_registry","target_component":"modal.compiler.registry"}`
  vector_bundle: `program-93e0cd75c6a06b7a` score `0.981934`
  loss: `autoencoder_residual_cluster` = `0.817373298322`
  objective: Adaptive family evidence disagrees with, or is weak for, the typed modal family.
  samples: `us-code-12-2091-76d98884a22e0c41, us-code-36-220522-c5d706908c8f3683, us-code-42-7385s-359864d4338b98ff`
  evidence: `{"family_margin": -0.837741879819, "hint_id": "modal-synthesis-08aebd966111ae6e", "predicted_family": "frame", "priority": 0.941865966229, "sample_id": "us-code-36-220522-c5d706908c8f3683", "target_family": "conditional_normative", "target_probability": 0.058134033771}`
  evidence: `{"family_margin": -0.851890543783, "hint_id": "modal-synthesis-5b9c65f32b8f7b13", "predicted_family": "frame", "priority": 0.950507268064, "sample_id": "us-code-12-2091-76d98884a22e0c41", "target_family": "deontic", "target_probability": 0.049492731936}`
  evidence: `{"family_margin": 0.0, "hint_id": "modal-synthesis-f718221c27a91e3e", "predicted_family": "dynamic", "priority": 0.559746660672, "sample_id": "us-code-42-7385s-359864d4338b98ff", "target_family": "dynamic", "target_probability": 0.440253339328}`
- `program-e6c41421aa2cdfa9`
  action: `refine_modal_family_cue_rules`
  role: `program_synthesis`
  target: `modal.compiler.registry`
  scope: `compiler_registry`
  bundle: `{"action":"refine_modal_family_cue_rules","family_pairs":["deontic->conditional_normative","deontic->temporal"],"program_synthesis_scope":"compiler_registry","target_component":"modal.compiler.registry"}`
  vector_bundle: `program-93e0cd75c6a06b7a` score `0.978375`
  loss: `autoencoder_residual_cluster` = `0.742239607582`
  objective: Adaptive family evidence disagrees with, or is weak for, the typed modal family.
  samples: `us-code-15-6104-8fef2f81532f25c4, us-code-7-2158-a09f86abd58a5b26, us-code-22-6592-6a5fd41e31cf2f8d`
  evidence: `{"family_margin": -0.209360858578, "hint_id": "modal-synthesis-2c620e83ef6fc7d6", "predicted_family": "deontic", "priority": 0.730821753257, "sample_id": "us-code-7-2158-a09f86abd58a5b26", "target_family": "conditional_normative", "target_probability": 0.269178246743}`
  evidence: `{"family_margin": -0.421626693366, "hint_id": "modal-synthesis-80c8141797a1b335", "predicted_family": "deontic", "priority": 0.915674661327, "sample_id": "us-code-15-6104-8fef2f81532f25c4", "target_family": "temporal", "target_probability": 0.084325338673}`
  evidence: `{"family_margin": 0.0, "hint_id": "modal-synthesis-9240d1f0a618d44d", "predicted_family": "deontic", "priority": 0.580222408163, "sample_id": "us-code-22-6592-6a5fd41e31cf2f8d", "target_family": "conditional_normative", "target_probability": 0.419777591837}`
- `program-ba84088348461161`
  action: `refine_modal_family_cue_rules`
  role: `program_synthesis`
  target: `modal.compiler.registry`
  scope: `compiler_registry`
  bundle: `{"action":"refine_modal_family_cue_rules","family_pairs":["frame->deontic","frame->epistemic","temporal->temporal"],"program_synthesis_scope":"compiler_registry","target_component":"modal.compiler.registry"}`
  vector_bundle: `program-93e0cd75c6a06b7a` score `0.970331`
  loss: `autoencoder_residual_cluster` = `0.832697382742`
  objective: Adaptive family evidence disagrees with, or is weak for, the typed modal family.
  samples: `us-code-28-2674-13d178046c4e836a, us-code-18-1303-eb206331feb4490b, us-code-25-1-0a08ee6129f682d8, us-code-19-2401-99a60fb0c79f6875`
  evidence: `{"family_margin": -0.997004445157, "hint_id": "modal-synthesis-0535ee809cb2588d", "predicted_family": "frame", "priority": 0.998759596788, "sample_id": "us-code-28-2674-13d178046c4e836a", "target_family": "deontic", "target_probability": 0.001240403212}`
  evidence: `{"family_margin": 0.168365523136, "hint_id": "modal-synthesis-6229ff63d9f59bf0", "predicted_family": "temporal", "priority": 0.551025271637, "sample_id": "us-code-19-2401-99a60fb0c79f6875", "target_family": "temporal", "target_probability": 0.448974728363}`
  evidence: `{"family_margin": -0.544325473206, "hint_id": "modal-synthesis-7c34a1da22040a90", "predicted_family": "frame", "priority": 0.796079064643, "sample_id": "us-code-25-1-0a08ee6129f682d8", "target_family": "deontic", "target_probability": 0.203920935357}`
  evidence: `{"family_margin": -0.714891687226, "hint_id": "modal-synthesis-7fbb54bb41ee9864", "predicted_family": "frame", "priority": 0.984925597901, "sample_id": "us-code-18-1303-eb206331feb4490b", "target_family": "epistemic", "target_probability": 0.015074402099}`
- `program-e443245fb2b7f45c`
  action: `refine_modal_family_cue_rules`
  role: `program_synthesis`
  target: `modal.compiler.registry`
  scope: `compiler_registry`
  bundle: `{"action":"refine_modal_family_cue_rules","family_pairs":["deontic->deontic","deontic->temporal"],"program_synthesis_scope":"compiler_registry","target_component":"modal.compiler.registry"}`
  vector_bundle: `program-93e0cd75c6a06b7a` score `0.956828`
  loss: `autoencoder_residual_cluster` = `0.749033580407`
  objective: Adaptive family evidence disagrees with, or is weak for, the typed modal family.
  samples: `us-code-25-2102-27563426a67cc711, us-code-16-431-715f8a7a6ba4bc2b`
  evidence: `{"family_margin": -0.403296944418, "hint_id": "modal-synthesis-271b1d338a69131c", "predicted_family": "deontic", "priority": 0.994164032444, "sample_id": "us-code-25-2102-27563426a67cc711", "target_family": "temporal", "target_probability": 0.005835967556}`
  evidence: `{"family_margin": 0.249742455922, "hint_id": "modal-synthesis-6e316ff730f31658", "predicted_family": "deontic", "priority": 0.50390312837, "sample_id": "us-code-16-431-715f8a7a6ba4bc2b", "target_family": "deontic", "target_probability": 0.49609687163}`

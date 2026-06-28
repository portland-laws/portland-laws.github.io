# packet-000567

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_ambiguity/packet-000567/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_ambiguity/packet-000567/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_ambiguity/worktrees/agent-codex-compiler_ambiguity-packet-000567-20260519_163406

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/compiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_registry.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py`

## TODOs
- `program-55640050f06dfc39` `add_or_review_modal_ambiguity_policy`
  target: `modal.compiler.ambiguity`
  scope: `compiler_ambiguity`
  bundle: `{"action":"add_or_review_modal_ambiguity_policy","family_pairs":["conditional_normative->conditional_normative","frame->temporal"],"program_synthesis_scope":"compiler_ambiguity","target_component":"modal.compiler.ambiguity"}`
  vector_bundle: `program-55640050f06dfc39` score `1.0`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  support: 2
  evidence: `{"family_margin": -0.98641901285, "hint_id": "modal-synthesis-e865551423ea7cd6", "predicted_family": "frame", "priority": 1.13641901285, "sample_id": "us-code-47-555.-f3c0d28d2e6b674d", "target_family": "temporal"}`
  evidence: `{"family_margin": 0.082281929987, "hint_id": "modal-synthesis-eb1dcda5ac41ee2b", "predicted_family": "conditional_normative", "priority": 0.067718070013, "sample_id": "us-code-7-182-b18cb75569dc2d85", "target_family": "conditional_normative"}`
- `program-3bbcca197991e012` `add_or_review_modal_ambiguity_policy`
  target: `modal.compiler.ambiguity`
  scope: `compiler_ambiguity`
  bundle: `{"action":"add_or_review_modal_ambiguity_policy","family_pairs":["alethic->frame","frame->deontic","temporal->deontic"],"program_synthesis_scope":"compiler_ambiguity","target_component":"modal.compiler.ambiguity"}`
  vector_bundle: `program-55640050f06dfc39` score `0.952677`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  support: 3
  evidence: `{"family_margin": -0.592973972988, "hint_id": "modal-synthesis-0c3258dc13ab613b", "predicted_family": "frame", "priority": 0.742973972988, "sample_id": "us-code-14-2735-857345e2c5c2a359", "target_family": "deontic"}`
  evidence: `{"family_margin": -0.314912979406, "hint_id": "modal-synthesis-7516117f97306f70", "predicted_family": "alethic", "priority": 0.464912979406, "sample_id": "us-code-43-390h.-20a339501c1a8236", "target_family": "frame"}`
  evidence: `{"family_margin": -0.332063308249, "hint_id": "modal-synthesis-c34f852822fee068", "predicted_family": "temporal", "priority": 0.482063308249, "sample_id": "us-code-42-5083.-77b302f9cbe4a1a5", "target_family": "deontic"}`

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
- TODO count: `2`

## TODOs
- `program-55640050f06dfc39`
  action: `add_or_review_modal_ambiguity_policy`
  role: `program_synthesis`
  target: `modal.compiler.ambiguity`
  scope: `compiler_ambiguity`
  bundle: `{"action":"add_or_review_modal_ambiguity_policy","family_pairs":["conditional_normative->conditional_normative","frame->temporal"],"program_synthesis_scope":"compiler_ambiguity","target_component":"modal.compiler.ambiguity"}`
  vector_bundle: `program-55640050f06dfc39` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.602068541432`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  samples: `us-code-47-555.-f3c0d28d2e6b674d, us-code-7-182-b18cb75569dc2d85`
  evidence: `{"family_margin": -0.98641901285, "hint_id": "modal-synthesis-e865551423ea7cd6", "predicted_family": "frame", "priority": 1.13641901285, "sample_id": "us-code-47-555.-f3c0d28d2e6b674d", "target_family": "temporal"}`
  evidence: `{"family_margin": 0.082281929987, "hint_id": "modal-synthesis-eb1dcda5ac41ee2b", "predicted_family": "conditional_normative", "priority": 0.067718070013, "sample_id": "us-code-7-182-b18cb75569dc2d85", "target_family": "conditional_normative"}`
- `program-3bbcca197991e012`
  action: `add_or_review_modal_ambiguity_policy`
  role: `program_synthesis`
  target: `modal.compiler.ambiguity`
  scope: `compiler_ambiguity`
  bundle: `{"action":"add_or_review_modal_ambiguity_policy","family_pairs":["alethic->frame","frame->deontic","temporal->deontic"],"program_synthesis_scope":"compiler_ambiguity","target_component":"modal.compiler.ambiguity"}`
  vector_bundle: `program-55640050f06dfc39` score `0.952677`
  loss: `autoencoder_residual_cluster` = `0.563316753548`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  samples: `us-code-14-2735-857345e2c5c2a359, us-code-42-5083.-77b302f9cbe4a1a5, us-code-43-390h.-20a339501c1a8236`
  evidence: `{"family_margin": -0.592973972988, "hint_id": "modal-synthesis-0c3258dc13ab613b", "predicted_family": "frame", "priority": 0.742973972988, "sample_id": "us-code-14-2735-857345e2c5c2a359", "target_family": "deontic"}`
  evidence: `{"family_margin": -0.314912979406, "hint_id": "modal-synthesis-7516117f97306f70", "predicted_family": "alethic", "priority": 0.464912979406, "sample_id": "us-code-43-390h.-20a339501c1a8236", "target_family": "frame"}`
  evidence: `{"family_margin": -0.332063308249, "hint_id": "modal-synthesis-c34f852822fee068", "predicted_family": "temporal", "priority": 0.482063308249, "sample_id": "us-code-42-5083.-77b302f9cbe4a1a5", "target_family": "deontic"}`

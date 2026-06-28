# packet-000564

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_ambiguity/packet-000564/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_ambiguity/packet-000564/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_ambiguity/worktrees/agent-codex-compiler_ambiguity-packet-000564-20260519_160937

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/compiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_registry.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py`

## TODOs
- `program-be5a2050d0f0af9f` `add_or_review_modal_ambiguity_policy`
  target: `modal.compiler.ambiguity`
  scope: `compiler_ambiguity`
  bundle: `{"action":"add_or_review_modal_ambiguity_policy","family_pairs":["frame->deontic","frame->epistemic","frame->temporal"],"program_synthesis_scope":"compiler_ambiguity","target_component":"modal.compiler.ambiguity"}`
  vector_bundle: `program-be5a2050d0f0af9f` score `1.0`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  support: 3
  evidence: `{"family_margin": -0.998544042424, "hint_id": "modal-synthesis-2053e87132378a96", "predicted_family": "frame", "priority": 1.148544042424, "sample_id": "us-code-42-16152.-2ce73465f6707341", "target_family": "temporal"}`
  evidence: `{"family_margin": -0.631226929562, "hint_id": "modal-synthesis-5d886b2b350f150d", "predicted_family": "frame", "priority": 0.781226929562, "sample_id": "us-code-18-1919-238552e353cd2eec", "target_family": "epistemic"}`
  evidence: `{"family_margin": -0.999908575942, "hint_id": "modal-synthesis-ef20ced44704b3dc", "predicted_family": "frame", "priority": 1.149908575942, "sample_id": "us-code-42-666.-a96cfa64256cae78", "target_family": "deontic"}`

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
- TODO count: `1`

## TODOs
- `program-be5a2050d0f0af9f`
  action: `add_or_review_modal_ambiguity_policy`
  role: `program_synthesis`
  target: `modal.compiler.ambiguity`
  scope: `compiler_ambiguity`
  bundle: `{"action":"add_or_review_modal_ambiguity_policy","family_pairs":["frame->deontic","frame->epistemic","frame->temporal"],"program_synthesis_scope":"compiler_ambiguity","target_component":"modal.compiler.ambiguity"}`
  vector_bundle: `program-be5a2050d0f0af9f` score `1.0`
  loss: `autoencoder_residual_cluster` = `1.026559849309`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  samples: `us-code-42-666.-a96cfa64256cae78, us-code-42-16152.-2ce73465f6707341, us-code-18-1919-238552e353cd2eec`
  evidence: `{"family_margin": -0.998544042424, "hint_id": "modal-synthesis-2053e87132378a96", "predicted_family": "frame", "priority": 1.148544042424, "sample_id": "us-code-42-16152.-2ce73465f6707341", "target_family": "temporal"}`
  evidence: `{"family_margin": -0.631226929562, "hint_id": "modal-synthesis-5d886b2b350f150d", "predicted_family": "frame", "priority": 0.781226929562, "sample_id": "us-code-18-1919-238552e353cd2eec", "target_family": "epistemic"}`
  evidence: `{"family_margin": -0.999908575942, "hint_id": "modal-synthesis-ef20ced44704b3dc", "predicted_family": "frame", "priority": 1.149908575942, "sample_id": "us-code-42-666.-a96cfa64256cae78", "target_family": "deontic"}`

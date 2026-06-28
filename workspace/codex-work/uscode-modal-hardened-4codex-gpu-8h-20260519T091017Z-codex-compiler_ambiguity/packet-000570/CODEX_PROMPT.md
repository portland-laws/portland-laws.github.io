# packet-000570

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_ambiguity/packet-000570/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_ambiguity/packet-000570/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_ambiguity/worktrees/agent-codex-compiler_ambiguity-packet-000570-20260519_165320

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/compiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_registry.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py`

## TODOs
- `program-bfe8ae94d3856e3a` `add_or_review_modal_ambiguity_policy`
  target: `modal.compiler.ambiguity`
  scope: `compiler_ambiguity`
  bundle: `{"action":"add_or_review_modal_ambiguity_policy","family_pairs":["dynamic->dynamic","frame->conditional_normative","frame->deontic"],"program_synthesis_scope":"compiler_ambiguity","target_component":"modal.compiler.ambiguity"}`
  vector_bundle: `program-bfe8ae94d3856e3a` score `1.0`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  support: 3
  evidence: `{"family_margin": 0.0, "hint_id": "modal-synthesis-3f59cdf6d660c8a7", "predicted_family": "dynamic", "priority": 0.15, "sample_id": "us-code-42-7385s-359864d4338b98ff", "target_family": "dynamic"}`
  evidence: `{"family_margin": -0.837741879819, "hint_id": "modal-synthesis-49d645daa86b432e", "predicted_family": "frame", "priority": 0.987741879819, "sample_id": "us-code-36-220522-c5d706908c8f3683", "target_family": "conditional_normative"}`
  evidence: `{"family_margin": -0.851890543783, "hint_id": "modal-synthesis-515f32ba228c133c", "predicted_family": "frame", "priority": 1.001890543783, "sample_id": "us-code-12-2091-76d98884a22e0c41", "target_family": "deontic"}`

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
- `program-bfe8ae94d3856e3a`
  action: `add_or_review_modal_ambiguity_policy`
  role: `program_synthesis`
  target: `modal.compiler.ambiguity`
  scope: `compiler_ambiguity`
  bundle: `{"action":"add_or_review_modal_ambiguity_policy","family_pairs":["dynamic->dynamic","frame->conditional_normative","frame->deontic"],"program_synthesis_scope":"compiler_ambiguity","target_component":"modal.compiler.ambiguity"}`
  vector_bundle: `program-bfe8ae94d3856e3a` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.713210807867`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  samples: `us-code-12-2091-76d98884a22e0c41, us-code-36-220522-c5d706908c8f3683, us-code-42-7385s-359864d4338b98ff`
  evidence: `{"family_margin": 0.0, "hint_id": "modal-synthesis-3f59cdf6d660c8a7", "predicted_family": "dynamic", "priority": 0.15, "sample_id": "us-code-42-7385s-359864d4338b98ff", "target_family": "dynamic"}`
  evidence: `{"family_margin": -0.837741879819, "hint_id": "modal-synthesis-49d645daa86b432e", "predicted_family": "frame", "priority": 0.987741879819, "sample_id": "us-code-36-220522-c5d706908c8f3683", "target_family": "conditional_normative"}`
  evidence: `{"family_margin": -0.851890543783, "hint_id": "modal-synthesis-515f32ba228c133c", "predicted_family": "frame", "priority": 1.001890543783, "sample_id": "us-code-12-2091-76d98884a22e0c41", "target_family": "deontic"}`

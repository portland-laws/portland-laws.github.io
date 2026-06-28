# packet-000015

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/packet-000015/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/packet-000015/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-frame_logic/worktrees/agent-codex-frame_logic-packet-000015-20260518_084129

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/optimizers/logic/flogic_optimizer.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/frame_bm25_selector.py`

## TODOs
- `program-4ebd4e546914c5b9` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-4ebd4e546914c5b9` score `1.0`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 4
  evidence: `{"hint_id": "modal-synthesis-01133415b8ad1321", "priority": 0.409453861987, "sample_id": "us-code-11-555-c1474b1bccd650aa"}`
  evidence: `{"hint_id": "modal-synthesis-0cc77ed04968d1c5", "priority": 0.846460241345, "sample_id": "us-code-23-317-df82896b8ec4432e"}`
  evidence: `{"hint_id": "modal-synthesis-2ba51989fb09aadb", "priority": 0.725779390168, "sample_id": "us-code-15-278g-bfaa6c396a066e31"}`
  evidence: `{"hint_id": "modal-synthesis-8a07a56be2e28e6a", "priority": 0.498936333848, "sample_id": "us-code-10-2683-b289a6ed85956734"}`
- `program-79c604169bc7626b` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-4ebd4e546914c5b9` score `0.993739`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 4
  evidence: `{"hint_id": "modal-synthesis-03d460b8b3938c55", "priority": 0.486195541642, "sample_id": "us-code-33-2236-2d2291391528452f"}`
  evidence: `{"hint_id": "modal-synthesis-1462ef91eb3eb907", "priority": 0.273667490184, "sample_id": "us-code-18-847-388ed160becc8648"}`
  evidence: `{"hint_id": "modal-synthesis-42e169e5a5ea76b2", "priority": 0.287409479261, "sample_id": "us-code-22-1156-20d188d5c341c511"}`
  evidence: `{"hint_id": "modal-synthesis-6fee865dc11aa4a9", "priority": 0.561860385952, "sample_id": "us-code-7-492-4174ea46ee10e623"}`
- `program-d3d4b6f853785a79` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-4ebd4e546914c5b9` score `0.993368`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 4
  evidence: `{"hint_id": "modal-synthesis-4da760d148561ef5", "priority": 0.576251032019, "sample_id": "us-code-7-1421c-82918530eda35172"}`
  evidence: `{"hint_id": "modal-synthesis-5eb91f45fe5d00bf", "priority": 0.338255731335, "sample_id": "us-code-25-201-359bc39e3fbde5c1"}`
  evidence: `{"hint_id": "modal-synthesis-8a07a56be2e28e6a", "priority": 0.498936333848, "sample_id": "us-code-10-2683-b289a6ed85956734"}`
  evidence: `{"hint_id": "modal-synthesis-8c21d3643ab4b7e6", "priority": 0.109517878796, "sample_id": "us-code-15-1508-311f3665421d344f"}`

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

- Queue run: `uscode-modal-vector-8h-20260518T072401Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-vector-8h-20260518T072401Z-autoencoder.jsonl`
- TODO count: `3`

## TODOs
- `program-4ebd4e546914c5b9`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-4ebd4e546914c5b9` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.620157456837`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-23-317-df82896b8ec4432e, us-code-15-278g-bfaa6c396a066e31, us-code-10-2683-b289a6ed85956734, us-code-11-555-c1474b1bccd650aa`
  evidence: `{"hint_id": "modal-synthesis-01133415b8ad1321", "priority": 0.409453861987, "sample_id": "us-code-11-555-c1474b1bccd650aa"}`
  evidence: `{"hint_id": "modal-synthesis-0cc77ed04968d1c5", "priority": 0.846460241345, "sample_id": "us-code-23-317-df82896b8ec4432e"}`
  evidence: `{"hint_id": "modal-synthesis-2ba51989fb09aadb", "priority": 0.725779390168, "sample_id": "us-code-15-278g-bfaa6c396a066e31"}`
  evidence: `{"hint_id": "modal-synthesis-8a07a56be2e28e6a", "priority": 0.498936333848, "sample_id": "us-code-10-2683-b289a6ed85956734"}`
- `program-79c604169bc7626b`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-4ebd4e546914c5b9` score `0.993739`
  loss: `autoencoder_residual_cluster` = `0.40228322426`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-7-492-4174ea46ee10e623, us-code-33-2236-2d2291391528452f, us-code-22-1156-20d188d5c341c511, us-code-18-847-388ed160becc8648`
  evidence: `{"hint_id": "modal-synthesis-03d460b8b3938c55", "priority": 0.486195541642, "sample_id": "us-code-33-2236-2d2291391528452f"}`
  evidence: `{"hint_id": "modal-synthesis-1462ef91eb3eb907", "priority": 0.273667490184, "sample_id": "us-code-18-847-388ed160becc8648"}`
  evidence: `{"hint_id": "modal-synthesis-42e169e5a5ea76b2", "priority": 0.287409479261, "sample_id": "us-code-22-1156-20d188d5c341c511"}`
  evidence: `{"hint_id": "modal-synthesis-6fee865dc11aa4a9", "priority": 0.561860385952, "sample_id": "us-code-7-492-4174ea46ee10e623"}`
- `program-d3d4b6f853785a79`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  scope: `frame_logic`
  bundle: `{"action":"audit_frame_logic_terms","family_pairs":[],"program_synthesis_scope":"frame_logic","target_component":"modal.frame_logic"}`
  vector_bundle: `program-4ebd4e546914c5b9` score `0.993368`
  loss: `autoencoder_residual_cluster` = `0.380740244`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-7-1421c-82918530eda35172, us-code-10-2683-b289a6ed85956734, us-code-25-201-359bc39e3fbde5c1, us-code-15-1508-311f3665421d344f`
  evidence: `{"hint_id": "modal-synthesis-4da760d148561ef5", "priority": 0.576251032019, "sample_id": "us-code-7-1421c-82918530eda35172"}`
  evidence: `{"hint_id": "modal-synthesis-5eb91f45fe5d00bf", "priority": 0.338255731335, "sample_id": "us-code-25-201-359bc39e3fbde5c1"}`
  evidence: `{"hint_id": "modal-synthesis-8a07a56be2e28e6a", "priority": 0.498936333848, "sample_id": "us-code-10-2683-b289a6ed85956734"}`
  evidence: `{"hint_id": "modal-synthesis-8c21d3643ab4b7e6", "priority": 0.109517878796, "sample_id": "us-code-15-1508-311f3665421d344f"}`

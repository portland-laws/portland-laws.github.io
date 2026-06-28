# packet-000015

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000015/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000015/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000015-20260518_084118

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-ba37f3f28356ecca` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-ba37f3f28356ecca` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.121694592989, "hint_id": "modal-synthesis-3e1cbf8ecab4501a", "priority": 0.498936333848, "reconstruction_loss": 0.498936333848, "sample_id": "us-code-10-2683-b289a6ed85956734"}`
  evidence: `{"cosine_similarity": 0.238392752827, "hint_id": "modal-synthesis-c3d4d293110c058b", "priority": 0.409453861987, "reconstruction_loss": 0.409453861987, "sample_id": "us-code-11-555-c1474b1bccd650aa"}`
  evidence: `{"cosine_similarity": -0.271449765706, "hint_id": "modal-synthesis-ca31e3468c1991ac", "priority": 0.725779390168, "reconstruction_loss": 0.725779390168, "sample_id": "us-code-15-278g-bfaa6c396a066e31"}`
  evidence: `{"cosine_similarity": -0.427487253378, "hint_id": "modal-synthesis-fe1d840cbf72550a", "priority": 0.846460241345, "reconstruction_loss": 0.846460241345, "sample_id": "us-code-23-317-df82896b8ec4432e"}`
- `program-6204dc1efeedf5f3` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-ba37f3f28356ecca` score `0.994473`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.715448308068, "hint_id": "modal-synthesis-162e6c34dc62bfc3", "priority": 0.143718032412, "reconstruction_loss": 0.143718032412, "sample_id": "us-code-42-300mm-238d8a2ba206bb92"}`
  evidence: `{"cosine_similarity": -0.398215743415, "hint_id": "modal-synthesis-be817ef3ea572957", "priority": 0.46921692286, "reconstruction_loss": 0.46921692286, "sample_id": "us-code-28-44-64d56278ffc8b5ad"}`
  evidence: `{"cosine_similarity": -0.261770390068, "hint_id": "modal-synthesis-ddda53c5129e6f7c", "priority": 0.467283032106, "reconstruction_loss": 0.467283032106, "sample_id": "us-code-50-4022.-0c42665eac8ff501"}`
  evidence: `{"cosine_similarity": 0.325463293556, "hint_id": "modal-synthesis-df28407922fe01f2", "priority": 0.326151351037, "reconstruction_loss": 0.326151351037, "sample_id": "us-code-19-4345-aa35dc5acdf4616c"}`
- `program-c39507627506c5a2` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-ba37f3f28356ecca` score `0.994062`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.16395831021, "hint_id": "modal-synthesis-1a8327abe6e3285a", "priority": 0.405229087047, "reconstruction_loss": 0.405229087047, "sample_id": "us-code-21-1711-adac5c30d3aba8aa"}`
  evidence: `{"cosine_similarity": 0.338610074304, "hint_id": "modal-synthesis-582a2033f49a7a8e", "priority": 0.297902926036, "reconstruction_loss": 0.297902926036, "sample_id": "us-code-42-19221.-bcfcf066cb704bdf"}`
  evidence: `{"cosine_similarity": 0.438858647177, "hint_id": "modal-synthesis-8950f26d272a4947", "priority": 0.363114640747, "reconstruction_loss": 0.363114640747, "sample_id": "us-code-10-14311-d99c284777d18b1d"}`
  evidence: `{"cosine_similarity": 0.249140479491, "hint_id": "modal-synthesis-b1ccc54e5bdf0c8c", "priority": 0.38782770057, "reconstruction_loss": 0.38782770057, "sample_id": "us-code-46-70105.-511479ded7538ce3"}`

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
- `program-ba37f3f28356ecca`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-ba37f3f28356ecca` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.620157456837`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-23-317-df82896b8ec4432e, us-code-15-278g-bfaa6c396a066e31, us-code-10-2683-b289a6ed85956734, us-code-11-555-c1474b1bccd650aa`
  evidence: `{"cosine_similarity": 0.121694592989, "hint_id": "modal-synthesis-3e1cbf8ecab4501a", "priority": 0.498936333848, "reconstruction_loss": 0.498936333848, "sample_id": "us-code-10-2683-b289a6ed85956734"}`
  evidence: `{"cosine_similarity": 0.238392752827, "hint_id": "modal-synthesis-c3d4d293110c058b", "priority": 0.409453861987, "reconstruction_loss": 0.409453861987, "sample_id": "us-code-11-555-c1474b1bccd650aa"}`
  evidence: `{"cosine_similarity": -0.271449765706, "hint_id": "modal-synthesis-ca31e3468c1991ac", "priority": 0.725779390168, "reconstruction_loss": 0.725779390168, "sample_id": "us-code-15-278g-bfaa6c396a066e31"}`
  evidence: `{"cosine_similarity": -0.427487253378, "hint_id": "modal-synthesis-fe1d840cbf72550a", "priority": 0.846460241345, "reconstruction_loss": 0.846460241345, "sample_id": "us-code-23-317-df82896b8ec4432e"}`
- `program-6204dc1efeedf5f3`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-ba37f3f28356ecca` score `0.994473`
  loss: `autoencoder_residual_cluster` = `0.351592334604`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-28-44-64d56278ffc8b5ad, us-code-50-4022.-0c42665eac8ff501, us-code-19-4345-aa35dc5acdf4616c, us-code-42-300mm-238d8a2ba206bb92`
  evidence: `{"cosine_similarity": 0.715448308068, "hint_id": "modal-synthesis-162e6c34dc62bfc3", "priority": 0.143718032412, "reconstruction_loss": 0.143718032412, "sample_id": "us-code-42-300mm-238d8a2ba206bb92"}`
  evidence: `{"cosine_similarity": -0.398215743415, "hint_id": "modal-synthesis-be817ef3ea572957", "priority": 0.46921692286, "reconstruction_loss": 0.46921692286, "sample_id": "us-code-28-44-64d56278ffc8b5ad"}`
  evidence: `{"cosine_similarity": -0.261770390068, "hint_id": "modal-synthesis-ddda53c5129e6f7c", "priority": 0.467283032106, "reconstruction_loss": 0.467283032106, "sample_id": "us-code-50-4022.-0c42665eac8ff501"}`
  evidence: `{"cosine_similarity": 0.325463293556, "hint_id": "modal-synthesis-df28407922fe01f2", "priority": 0.326151351037, "reconstruction_loss": 0.326151351037, "sample_id": "us-code-19-4345-aa35dc5acdf4616c"}`
- `program-c39507627506c5a2`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-ba37f3f28356ecca` score `0.994062`
  loss: `autoencoder_residual_cluster` = `0.3635185886`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-21-1711-adac5c30d3aba8aa, us-code-46-70105.-511479ded7538ce3, us-code-10-14311-d99c284777d18b1d, us-code-42-19221.-bcfcf066cb704bdf`
  evidence: `{"cosine_similarity": 0.16395831021, "hint_id": "modal-synthesis-1a8327abe6e3285a", "priority": 0.405229087047, "reconstruction_loss": 0.405229087047, "sample_id": "us-code-21-1711-adac5c30d3aba8aa"}`
  evidence: `{"cosine_similarity": 0.338610074304, "hint_id": "modal-synthesis-582a2033f49a7a8e", "priority": 0.297902926036, "reconstruction_loss": 0.297902926036, "sample_id": "us-code-42-19221.-bcfcf066cb704bdf"}`
  evidence: `{"cosine_similarity": 0.438858647177, "hint_id": "modal-synthesis-8950f26d272a4947", "priority": 0.363114640747, "reconstruction_loss": 0.363114640747, "sample_id": "us-code-10-14311-d99c284777d18b1d"}`
  evidence: `{"cosine_similarity": 0.249140479491, "hint_id": "modal-synthesis-b1ccc54e5bdf0c8c", "priority": 0.38782770057, "reconstruction_loss": 0.38782770057, "sample_id": "us-code-46-70105.-511479ded7538ce3"}`

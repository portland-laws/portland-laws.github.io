# packet-000048

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000048/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000048/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000048-20260518_115943

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-36541352f6ca4fb0` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-36541352f6ca4fb0` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.312648574661, "hint_id": "modal-synthesis-7ca60c58f21e6997", "priority": 0.336595637015, "reconstruction_loss": 0.336595637015, "sample_id": "us-code-18-952-99b724458d84f0af"}`
  evidence: `{"cosine_similarity": 0.063620447297, "hint_id": "modal-synthesis-97735438235a2f0b", "priority": 0.64531256303, "reconstruction_loss": 0.64531256303, "sample_id": "us-code-12-2121-2f87de947818271b"}`
  evidence: `{"cosine_similarity": -0.222956597383, "hint_id": "modal-synthesis-c30a94e2c3fda434", "priority": 0.633646696412, "reconstruction_loss": 0.633646696412, "sample_id": "us-code-10-7841-1869ba046c4879f6"}`
  evidence: `{"cosine_similarity": -0.424036786678, "hint_id": "modal-synthesis-eb1c06b9e682922c", "priority": 0.472074372882, "reconstruction_loss": 0.472074372882, "sample_id": "us-code-42-12655k.-03c6ac8f40f3b866"}`
- `program-fbaabcdbb6e811c7` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-36541352f6ca4fb0` score `0.99491`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.191409211814, "hint_id": "modal-synthesis-090bd1f1c2c417f1", "priority": 0.542893144259, "reconstruction_loss": 0.542893144259, "sample_id": "us-code-40-8908-1132d2ce8b9f2856"}`
  evidence: `{"cosine_similarity": 0.304926223908, "hint_id": "modal-synthesis-240ad99921ed3e0c", "priority": 0.314933763652, "reconstruction_loss": 0.314933763652, "sample_id": "us-code-50-2675.-8dbd5e2eb6c364c8"}`
  evidence: `{"cosine_similarity": -0.304117001253, "hint_id": "modal-synthesis-c7aa88f0bf9a2e22", "priority": 0.344686077451, "reconstruction_loss": 0.344686077451, "sample_id": "us-code-16-1305-52deab0121bcfa56"}`
  evidence: `{"cosine_similarity": 0.141007096928, "hint_id": "modal-synthesis-e59f05c74f24b024", "priority": 0.452905484216, "reconstruction_loss": 0.452905484216, "sample_id": "us-code-10-2694c-6c9a3275768273e9"}`
- `program-ce045275b2b2dd14` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-36541352f6ca4fb0` score `0.994673`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.019911316572, "hint_id": "modal-synthesis-03778112886a71b3", "priority": 0.422901652001, "reconstruction_loss": 0.422901652001, "sample_id": "us-code-16-408-a7e62f6961e17dee"}`
  evidence: `{"cosine_similarity": 0.514178586798, "hint_id": "modal-synthesis-8eab28510fe09de4", "priority": 0.300566969526, "reconstruction_loss": 0.300566969526, "sample_id": "us-code-51-70703.-06aa964c887c382b"}`
  evidence: `{"cosine_similarity": -0.539996210637, "hint_id": "modal-synthesis-b4cdcef5f533d557", "priority": 0.752424584555, "reconstruction_loss": 0.752424584555, "sample_id": "us-code-2-5301-9cf0c794269555f7"}`
  evidence: `{"cosine_similarity": 0.375354115772, "hint_id": "modal-synthesis-e66a3ea2dc3b7a9a", "priority": 0.285084927086, "reconstruction_loss": 0.285084927086, "sample_id": "us-code-20-741-d9743e9c6ae8213e"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.

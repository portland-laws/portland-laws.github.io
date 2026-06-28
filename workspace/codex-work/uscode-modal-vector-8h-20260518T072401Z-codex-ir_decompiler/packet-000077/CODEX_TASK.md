# packet-000077

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000077/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000077/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000077-20260518_151617

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-dd17bb3eda92a5bc` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-dd17bb3eda92a5bc` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.699691828399, "hint_id": "modal-synthesis-74b72b7ecc3898e3", "priority": 0.743686188379, "reconstruction_loss": 0.743686188379, "sample_id": "us-code-42-300i-0102d16fb9d986ee"}`
  evidence: `{"cosine_similarity": 0.193987360589, "hint_id": "modal-synthesis-c59dad8112de2544", "priority": 0.289028254313, "reconstruction_loss": 0.289028254313, "sample_id": "us-code-29-1861-70ebe58703e28711"}`
  evidence: `{"cosine_similarity": 0.011199603808, "hint_id": "modal-synthesis-dba3d53a06093d4d", "priority": 0.499472959965, "reconstruction_loss": 0.499472959965, "sample_id": "us-code-11-1201-861fe19213adc1fd"}`
  evidence: `{"cosine_similarity": -0.391198407005, "hint_id": "modal-synthesis-ff4c50955b2e6123", "priority": 0.795075535022, "reconstruction_loss": 0.795075535022, "sample_id": "us-code-26-307-c04b9c0813def639"}`
- `program-3e19b9a8f806da27` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-dd17bb3eda92a5bc` score `0.993865`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.014531460078, "hint_id": "modal-synthesis-394f62024590372b", "priority": 0.459543004816, "reconstruction_loss": 0.459543004816, "sample_id": "us-code-40-503-8a3140ba873e991d"}`
  evidence: `{"cosine_similarity": 0.093170192574, "hint_id": "modal-synthesis-3f5982f30e548aaa", "priority": 0.329648975897, "reconstruction_loss": 0.329648975897, "sample_id": "us-code-37-308i-95ee3d764155e44d"}`
  evidence: `{"cosine_similarity": -0.097228745834, "hint_id": "modal-synthesis-52c724e04adc1ef8", "priority": 0.325002066926, "reconstruction_loss": 0.325002066926, "sample_id": "us-code-26-1400L-f8d163d7baa2349b"}`
  evidence: `{"cosine_similarity": 0.162772334811, "hint_id": "modal-synthesis-dcc855bb2aa57df9", "priority": 0.431284091724, "reconstruction_loss": 0.431284091724, "sample_id": "us-code-16-695i-77e5280fbfc218f6"}`
- `program-106d6b726a04d422` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-dd17bb3eda92a5bc` score `0.993591`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.675797574743, "hint_id": "modal-synthesis-8ab06820fbb8bbc6", "priority": 0.106821554805, "reconstruction_loss": 0.106821554805, "sample_id": "us-code-10-1414-f4ba273cfbf0af99"}`
  evidence: `{"cosine_similarity": 0.564259296523, "hint_id": "modal-synthesis-9479ab0103533770", "priority": 0.20234817471, "reconstruction_loss": 0.20234817471, "sample_id": "us-code-22-6001-0d612f0c24406f5e"}`
  evidence: `{"cosine_similarity": 0.324516518803, "hint_id": "modal-synthesis-dd095a4b737cf056", "priority": 0.266804060802, "reconstruction_loss": 0.266804060802, "sample_id": "us-code-50-1828.-d3a2921302190f6c"}`
  evidence: `{"cosine_similarity": -0.000930340959, "hint_id": "modal-synthesis-e1fe3117a67a1d3d", "priority": 0.313503015589, "reconstruction_loss": 0.313503015589, "sample_id": "us-code-33-2351b-2fc05983ad47e2c5"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.

# packet-000016

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000016/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000016/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000016-20260518_084645

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-b57279718017be56` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-b57279718017be56` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.493412420017, "hint_id": "modal-synthesis-19bb96426ca4d61b", "priority": 0.687538193387, "reconstruction_loss": 0.687538193387, "sample_id": "us-code-30-1735-640a78b78367a81a"}`
  evidence: `{"cosine_similarity": -0.494954292803, "hint_id": "modal-synthesis-1d462c0faccfcb43", "priority": 0.818044501994, "reconstruction_loss": 0.818044501994, "sample_id": "us-code-42-10145.-cdf17e327d28e2de"}`
  evidence: `{"cosine_similarity": 0.133184692572, "hint_id": "modal-synthesis-53c8a59875d90f04", "priority": 0.480995576101, "reconstruction_loss": 0.480995576101, "sample_id": "us-code-19-2295a-baf69bb4242cfb98"}`
  evidence: `{"cosine_similarity": -0.657999300243, "hint_id": "modal-synthesis-6ab9441c0b6ce77e", "priority": 0.481023932854, "reconstruction_loss": 0.481023932854, "sample_id": "us-code-19-3910-60fa256ef71dcf49"}`
- `program-13449b038ebef17b` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-b57279718017be56` score `0.995616`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.077082554509, "hint_id": "modal-synthesis-402d6195a213004b", "priority": 0.425729181541, "reconstruction_loss": 0.425729181541, "sample_id": "us-code-10-2410h-e08bf2fac5d3dfc6"}`
  evidence: `{"cosine_similarity": 0.573491494334, "hint_id": "modal-synthesis-72cdbac3ff927d9f", "priority": 0.167044996625, "reconstruction_loss": 0.167044996625, "sample_id": "us-code-12-1451-62da0e1325fc7b20"}`
  evidence: `{"cosine_similarity": -0.017800905452, "hint_id": "modal-synthesis-8b966bdc9e07b69f", "priority": 0.506354635467, "reconstruction_loss": 0.506354635467, "sample_id": "us-code-42-300u-f870772ac24eb534"}`
  evidence: `{"cosine_similarity": -0.240189733889, "hint_id": "modal-synthesis-aaf287d4f784cac3", "priority": 0.574114600405, "reconstruction_loss": 0.574114600405, "sample_id": "us-code-5-579-97aa5a2961f00da7"}`
- `program-0e8e38f84faede76` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-b57279718017be56` score `0.995552`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.505703242657, "hint_id": "modal-synthesis-75deb0a4ddad1424", "priority": 0.174625415867, "reconstruction_loss": 0.174625415867, "sample_id": "us-code-42-2000e-87b0a223ec2f555f"}`
  evidence: `{"cosine_similarity": 0.13401329759, "hint_id": "modal-synthesis-87e79e73457dffd9", "priority": 0.556894111119, "reconstruction_loss": 0.556894111119, "sample_id": "us-code-10-853-371a22478ec3fdb1"}`
  evidence: `{"cosine_similarity": -0.183850258153, "hint_id": "modal-synthesis-b6f44a1924b32c77", "priority": 0.589877799395, "reconstruction_loss": 0.589877799395, "sample_id": "us-code-25-573-b9b5106ce77b7f27"}`
  evidence: `{"cosine_similarity": 0.111584314278, "hint_id": "modal-synthesis-ba8d7b0b41f031a8", "priority": 0.457821978579, "reconstruction_loss": 0.457821978579, "sample_id": "us-code-29-2635-77f495668196ac4e"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.

# packet-000040

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000040/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/packet-000040/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-vector-8h-20260518T072401Z-codex-ir_decompiler/worktrees/agent-codex-ir_decompiler-packet-000040-20260518_112130

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`

## TODOs
- `program-0ea99b69e758c4f4` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-0ea99b69e758c4f4` score `1.0`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.027799470879, "hint_id": "modal-synthesis-557f99c67998f091", "priority": 0.399546040227, "reconstruction_loss": 0.399546040227, "sample_id": "us-code-6-488d-1401e9f1b262033a"}`
  evidence: `{"cosine_similarity": -0.640562415326, "hint_id": "modal-synthesis-e34b67dab3679c3a", "priority": 0.725318979612, "reconstruction_loss": 0.725318979612, "sample_id": "us-code-42-10803.-d12c4e07d891530b"}`
  evidence: `{"cosine_similarity": -0.146897343126, "hint_id": "modal-synthesis-e4d890efdc9e990b", "priority": 0.435433949165, "reconstruction_loss": 0.435433949165, "sample_id": "us-code-19-2439-673af9a078a1ab94"}`
  evidence: `{"cosine_similarity": -0.192707758228, "hint_id": "modal-synthesis-ee3b1df636fdceb9", "priority": 0.730045628325, "reconstruction_loss": 0.730045628325, "sample_id": "us-code-16-582a-8-edd7f9ae525f622d"}`
- `program-a5bfc34db4e65ba1` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-0ea99b69e758c4f4` score `0.995371`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": 0.328259761159, "hint_id": "modal-synthesis-2b5deb9286102e0c", "priority": 0.364320800261, "reconstruction_loss": 0.364320800261, "sample_id": "us-code-43-1471i.-46d37d0d20b434f1"}`
  evidence: `{"cosine_similarity": -0.273831619758, "hint_id": "modal-synthesis-5ac7221988b6a9ed", "priority": 0.483755523451, "reconstruction_loss": 0.483755523451, "sample_id": "us-code-7-2204j-f79b0f532e34c176"}`
  evidence: `{"cosine_similarity": -0.175692259494, "hint_id": "modal-synthesis-ee011c5b7cbfa8ad", "priority": 0.481640214533, "reconstruction_loss": 0.481640214533, "sample_id": "us-code-34-12514-e47ffcaa5d0f29a0"}`
  evidence: `{"cosine_similarity": -0.378100496837, "hint_id": "modal-synthesis-f5732f95ce2dc83c", "priority": 0.739908581754, "reconstruction_loss": 0.739908581754, "sample_id": "us-code-10-3863-81a531d729ac08e5"}`
- `program-3ca6f6fef951c758` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-0ea99b69e758c4f4` score `0.994969`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 4
  evidence: `{"cosine_similarity": -0.250990184738, "hint_id": "modal-synthesis-464209c80cf2c042", "priority": 0.410423145133, "reconstruction_loss": 0.410423145133, "sample_id": "us-code-7-8784-e97982b17d0c912e"}`
  evidence: `{"cosine_similarity": 0.050080790337, "hint_id": "modal-synthesis-6a895faed42098e0", "priority": 0.485242473842, "reconstruction_loss": 0.485242473842, "sample_id": "us-code-10-8462-d8d574c61d00a0e7"}`
  evidence: `{"cosine_similarity": -0.312237771261, "hint_id": "modal-synthesis-c8c9686d158bde91", "priority": 0.712858213193, "reconstruction_loss": 0.712858213193, "sample_id": "us-code-7-8107a-bd10e243e426fef7"}`
  evidence: `{"cosine_similarity": -0.133578569129, "hint_id": "modal-synthesis-e37c986eb6b42ef1", "priority": 0.485757594205, "reconstruction_loss": 0.485757594205, "sample_id": "us-code-10-4067-a0844f1327727f88"}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.

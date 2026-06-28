# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-vector-8h-20260518T072401Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-vector-8h-20260518T072401Z-autoencoder.jsonl`
- TODO count: `3`

## TODOs
- `program-11fb1bd50073a48b`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-11fb1bd50073a48b` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.669603422463`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-43-37.-3a7baac185a1d8ae, us-code-7-323-5f06bf8223062016, us-code-20-6011-75175afa871b5d2d, us-code-16-3861-0140b49d9866524d`
  evidence: `{"cosine_similarity": -0.644611027928, "hint_id": "modal-synthesis-573121755f8a5c4d", "priority": 0.629349421056, "reconstruction_loss": 0.629349421056, "sample_id": "us-code-16-3861-0140b49d9866524d"}`
  evidence: `{"cosine_similarity": -0.627962183466, "hint_id": "modal-synthesis-70a9332a9b81540a", "priority": 0.690243402403, "reconstruction_loss": 0.690243402403, "sample_id": "us-code-7-323-5f06bf8223062016"}`
  evidence: `{"cosine_similarity": -0.398087811086, "hint_id": "modal-synthesis-c82c8e6dcaac6ea3", "priority": 0.704702661059, "reconstruction_loss": 0.704702661059, "sample_id": "us-code-43-37.-3a7baac185a1d8ae"}`
  evidence: `{"cosine_similarity": -0.31469021382, "hint_id": "modal-synthesis-f39c85bb560ff88a", "priority": 0.654118205333, "reconstruction_loss": 0.654118205333, "sample_id": "us-code-20-6011-75175afa871b5d2d"}`
- `program-ffd969eefcf2c227`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-11fb1bd50073a48b` score `0.99493`
  loss: `autoencoder_residual_cluster` = `0.560433358861`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-49-44718.-e33d4fe6efe48835, us-code-14-323-84bfe15bba62b796, us-code-5-408-4c3f3a9c1e2ec77d, us-code-12-359-79de307df5a44e1a`
  evidence: `{"cosine_similarity": -0.373717651493, "hint_id": "modal-synthesis-28f40f437ffe4e58", "priority": 0.638803195267, "reconstruction_loss": 0.638803195267, "sample_id": "us-code-14-323-84bfe15bba62b796"}`
  evidence: `{"cosine_similarity": 0.379039830081, "hint_id": "modal-synthesis-b8faafbbe459409a", "priority": 0.259677014082, "reconstruction_loss": 0.259677014082, "sample_id": "us-code-12-359-79de307df5a44e1a"}`
  evidence: `{"cosine_similarity": -0.043577795537, "hint_id": "modal-synthesis-cb937b8d5712bd6e", "priority": 0.544191436109, "reconstruction_loss": 0.544191436109, "sample_id": "us-code-5-408-4c3f3a9c1e2ec77d"}`
  evidence: `{"cosine_similarity": -0.543541062743, "hint_id": "modal-synthesis-d5d58110b4b9a1ed", "priority": 0.799061789987, "reconstruction_loss": 0.799061789987, "sample_id": "us-code-49-44718.-e33d4fe6efe48835"}`
- `program-b02e821fe44bf571`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-11fb1bd50073a48b` score `0.9949`
  loss: `autoencoder_residual_cluster` = `0.377818137233`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-12-336-f031869ab767b893, us-code-33-1302-dc3c0f2c4b6da7dc, us-code-22-9622-5fb0c2ff8811f943, us-code-28-1338-51eca7d74ce13dba`
  evidence: `{"cosine_similarity": -0.43937749217, "hint_id": "modal-synthesis-2cfc80b631a049b1", "priority": 0.727553369914, "reconstruction_loss": 0.727553369914, "sample_id": "us-code-12-336-f031869ab767b893"}`
  evidence: `{"cosine_similarity": 0.506702901361, "hint_id": "modal-synthesis-6633b1b7f57b997d", "priority": 0.261276778387, "reconstruction_loss": 0.261276778387, "sample_id": "us-code-22-9622-5fb0c2ff8811f943"}`
  evidence: `{"cosine_similarity": 0.687612923784, "hint_id": "modal-synthesis-8544442c8a24d686", "priority": 0.093643399381, "reconstruction_loss": 0.093643399381, "sample_id": "us-code-28-1338-51eca7d74ce13dba"}`
  evidence: `{"cosine_similarity": 0.233660360892, "hint_id": "modal-synthesis-f5320f25e27d405b", "priority": 0.428799001248, "reconstruction_loss": 0.428799001248, "sample_id": "us-code-33-1302-dc3c0f2c4b6da7dc"}`

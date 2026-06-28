# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-vector-8h-20260518T072401Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-vector-8h-20260518T072401Z-autoencoder.jsonl`
- TODO count: `3`

## TODOs
- `program-2f13a15c39737e55`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-2f13a15c39737e55` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.587044945407`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-15-8563-3b998304c368f8a4, us-code-15-1693l-62b207bc138a3216, us-code-29-1169-02398831eb6558ee, us-code-16-6410-7cc9d1ff88340f35`
  evidence: `{"cosine_similarity": -0.341476323478, "hint_id": "modal-synthesis-3a129e6578aabc50", "priority": 0.584563515822, "reconstruction_loss": 0.584563515822, "sample_id": "us-code-15-1693l-62b207bc138a3216"}`
  evidence: `{"cosine_similarity": -0.095199770173, "hint_id": "modal-synthesis-3abdcf9a25825df2", "priority": 0.572915792228, "reconstruction_loss": 0.572915792228, "sample_id": "us-code-29-1169-02398831eb6558ee"}`
  evidence: `{"cosine_similarity": -0.221982793063, "hint_id": "modal-synthesis-54322f75266d76fb", "priority": 0.637180749754, "reconstruction_loss": 0.637180749754, "sample_id": "us-code-15-8563-3b998304c368f8a4"}`
  evidence: `{"cosine_similarity": 0.249672960891, "hint_id": "modal-synthesis-d6bce96877318836", "priority": 0.553519723823, "reconstruction_loss": 0.553519723823, "sample_id": "us-code-16-6410-7cc9d1ff88340f35"}`
- `program-7f15fb215988c86b`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-2f13a15c39737e55` score `0.995496`
  loss: `autoencoder_residual_cluster` = `0.377479114085`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-26-6688-faa4a47aed02ba86, us-code-42-1500c-3cf28446a4418c3b, us-code-42-3797aa-a1bd6223a0df015d, us-code-2-1341-0953371178320b06`
  evidence: `{"cosine_similarity": 0.217315055666, "hint_id": "modal-synthesis-79063054c633f925", "priority": 0.313993343963, "reconstruction_loss": 0.313993343963, "sample_id": "us-code-42-1500c-3cf28446a4418c3b"}`
  evidence: `{"cosine_similarity": -0.249569120576, "hint_id": "modal-synthesis-a6c646b96063f3f7", "priority": 0.605454270093, "reconstruction_loss": 0.605454270093, "sample_id": "us-code-26-6688-faa4a47aed02ba86"}`
  evidence: `{"cosine_similarity": 0.246326308152, "hint_id": "modal-synthesis-df16032d91f92821", "priority": 0.304307755491, "reconstruction_loss": 0.304307755491, "sample_id": "us-code-42-3797aa-a1bd6223a0df015d"}`
  evidence: `{"cosine_similarity": 0.10958085498, "hint_id": "modal-synthesis-eb89156ef7b40cfe", "priority": 0.286161086793, "reconstruction_loss": 0.286161086793, "sample_id": "us-code-2-1341-0953371178320b06"}`
- `program-19491af0ebd9d446`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-2f13a15c39737e55` score `0.995492`
  loss: `autoencoder_residual_cluster` = `0.549836579766`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-46-60506.-4f83586b5bbf6f54, us-code-36-220527-4a929d8a32d82694, us-code-40-584-1c47d69e5d25d899, us-code-33-1208-d233029bac220eb2`
  evidence: `{"cosine_similarity": -0.045161836825, "hint_id": "modal-synthesis-0cb8413a797eb3ee", "priority": 0.544048514044, "reconstruction_loss": 0.544048514044, "sample_id": "us-code-36-220527-4a929d8a32d82694"}`
  evidence: `{"cosine_similarity": -0.771342573519, "hint_id": "modal-synthesis-11ed59677e1703db", "priority": 0.823044925592, "reconstruction_loss": 0.823044925592, "sample_id": "us-code-46-60506.-4f83586b5bbf6f54"}`
  evidence: `{"cosine_similarity": 0.171318643154, "hint_id": "modal-synthesis-c1461e5ad059016c", "priority": 0.434163378515, "reconstruction_loss": 0.434163378515, "sample_id": "us-code-40-584-1c47d69e5d25d899"}`
  evidence: `{"cosine_similarity": 0.174630679383, "hint_id": "modal-synthesis-c6426e76ff36db97", "priority": 0.398089500911, "reconstruction_loss": 0.398089500911, "sample_id": "us-code-33-1208-d233029bac220eb2"}`

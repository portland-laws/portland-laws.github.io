# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-vector-8h-20260518T072401Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-vector-8h-20260518T072401Z-autoencoder.jsonl`
- TODO count: `3`

## TODOs
- `program-e189fec5a0264aca`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-e189fec5a0264aca` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.49630978684`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-48-1422a.-f2723a282421b5ac, us-code-42-17031.-d2421167a1dd890c, us-code-49-44732.-e52d78d208d231fd, us-code-7-1983a-13c7ecbbb5dee0f5`
  evidence: `{"cosine_similarity": -0.095809278064, "hint_id": "modal-synthesis-c180a93fa900a69e", "priority": 0.546466114701, "reconstruction_loss": 0.546466114701, "sample_id": "us-code-42-17031.-d2421167a1dd890c"}`
  evidence: `{"cosine_similarity": -0.245254324377, "hint_id": "modal-synthesis-c86144aa221387fb", "priority": 0.668867382778, "reconstruction_loss": 0.668867382778, "sample_id": "us-code-48-1422a.-f2723a282421b5ac"}`
  evidence: `{"cosine_similarity": -0.276600904174, "hint_id": "modal-synthesis-c89856f995a0ed9d", "priority": 0.5154658367, "reconstruction_loss": 0.5154658367, "sample_id": "us-code-49-44732.-e52d78d208d231fd"}`
  evidence: `{"cosine_similarity": 0.4394779846, "hint_id": "modal-synthesis-ed3cc7682504c935", "priority": 0.254439813182, "reconstruction_loss": 0.254439813182, "sample_id": "us-code-7-1983a-13c7ecbbb5dee0f5"}`
- `program-1061c97c27a49811`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-e189fec5a0264aca` score `0.994268`
  loss: `autoencoder_residual_cluster` = `0.405017058873`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-33-591-7ac145167fbe4c62, us-code-12-5221-fbc1ebcd76d8075c, us-code-10-2349-ea0086bf31d7610c, us-code-16-410ggg-3553c335e4a01eae`
  evidence: `{"cosine_similarity": 0.713472496457, "hint_id": "modal-synthesis-03e4cccf1d51a4dc", "priority": 0.205177989367, "reconstruction_loss": 0.205177989367, "sample_id": "us-code-10-2349-ea0086bf31d7610c"}`
  evidence: `{"cosine_similarity": 0.501429919338, "hint_id": "modal-synthesis-35df11d9d77bb6a6", "priority": 0.183241559881, "reconstruction_loss": 0.183241559881, "sample_id": "us-code-16-410ggg-3553c335e4a01eae"}`
  evidence: `{"cosine_similarity": -0.039038565511, "hint_id": "modal-synthesis-8dc8b49030735156", "priority": 0.514528990314, "reconstruction_loss": 0.514528990314, "sample_id": "us-code-12-5221-fbc1ebcd76d8075c"}`
  evidence: `{"cosine_similarity": -0.436535057262, "hint_id": "modal-synthesis-d6349b8b56469846", "priority": 0.71711969593, "reconstruction_loss": 0.71711969593, "sample_id": "us-code-33-591-7ac145167fbe4c62"}`
- `program-0701c4e5c17a459a`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-e189fec5a0264aca` score `0.994195`
  loss: `autoencoder_residual_cluster` = `0.348034439003`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-42-13921.-00331d9b996254c9, us-code-19-4586-d9e19a964f3f3b00, us-code-42-6250a.-c0024f70ec1986ca, us-code-46-10318.-fce306c016fdd990`
  evidence: `{"cosine_similarity": -0.308488432872, "hint_id": "modal-synthesis-129750affd4a5d1b", "priority": 0.599405561369, "reconstruction_loss": 0.599405561369, "sample_id": "us-code-42-13921.-00331d9b996254c9"}`
  evidence: `{"cosine_similarity": 0.442824033776, "hint_id": "modal-synthesis-728f5fca76a0a1f3", "priority": 0.151353749328, "reconstruction_loss": 0.151353749328, "sample_id": "us-code-46-10318.-fce306c016fdd990"}`
  evidence: `{"cosine_similarity": 0.246369884621, "hint_id": "modal-synthesis-d6951a6ef9ea9c34", "priority": 0.319727071781, "reconstruction_loss": 0.319727071781, "sample_id": "us-code-42-6250a.-c0024f70ec1986ca"}`
  evidence: `{"cosine_similarity": 0.287618867515, "hint_id": "modal-synthesis-f671336255804ad3", "priority": 0.321651373533, "reconstruction_loss": 0.321651373533, "sample_id": "us-code-19-4586-d9e19a964f3f3b00"}`

# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-vector-packet-smoke-20260518T071033Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-vector-packet-smoke-20260518T071033Z-autoencoder.jsonl`
- TODO count: `1`

## TODOs
- `program-9bff8b67a346b324`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-9bff8b67a346b324` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.365590871595`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-26-455-1a66a843f76c6812, us-code-49-332.-7864dd8cea9c0675, us-code-45-797k.-3992b88eab5a40c3, us-code-49-15301.-22006f67889073a7`
  evidence: `{"cosine_similarity": -0.507209600604, "hint_id": "modal-synthesis-183b379b34bcbf82", "priority": 0.625943748255, "reconstruction_loss": 0.625943748255, "sample_id": "us-code-26-455-1a66a843f76c6812"}`
  evidence: `{"cosine_similarity": 0.351264734793, "hint_id": "modal-synthesis-26f4f1ce4a9e1c7f", "priority": 0.412779504645, "reconstruction_loss": 0.412779504645, "sample_id": "us-code-49-332.-7864dd8cea9c0675"}`
  evidence: `{"cosine_similarity": 0.359276846921, "hint_id": "modal-synthesis-5e793b4ea2de912b", "priority": 0.271956069227, "reconstruction_loss": 0.271956069227, "sample_id": "us-code-45-797k.-3992b88eab5a40c3"}`
  evidence: `{"cosine_similarity": 0.476897657104, "hint_id": "modal-synthesis-a468e0ff825f89cc", "priority": 0.151684164252, "reconstruction_loss": 0.151684164252, "sample_id": "us-code-49-15301.-22006f67889073a7"}`

# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-vector-packet-smoke-20260518T071033Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-vector-packet-smoke-20260518T071033Z-autoencoder.jsonl`
- TODO count: `1`

## TODOs
- `program-b774b7c887b55d56`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-b774b7c887b55d56` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.616896131965`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-42-16928a.-51cc2f6b0ac5ca81, us-code-33-549-6f82e0c7217912c5, us-code-7-2032-e45599d1c3b7a334, us-code-35-313-0cdecd0367a5f7c3`
  evidence: `{"cosine_similarity": 0.169670105411, "hint_id": "modal-synthesis-2d981f77e6feac7b", "priority": 0.551847934098, "reconstruction_loss": 0.551847934098, "sample_id": "us-code-7-2032-e45599d1c3b7a334"}`
  evidence: `{"cosine_similarity": -0.395176577456, "hint_id": "modal-synthesis-2de74ab6c8461df8", "priority": 0.714468989682, "reconstruction_loss": 0.714468989682, "sample_id": "us-code-33-549-6f82e0c7217912c5"}`
  evidence: `{"cosine_similarity": 0.138427528331, "hint_id": "modal-synthesis-a2b1026615cd1b7e", "priority": 0.374759681351, "reconstruction_loss": 0.374759681351, "sample_id": "us-code-35-313-0cdecd0367a5f7c3"}`
  evidence: `{"cosine_similarity": -0.395249364059, "hint_id": "modal-synthesis-c8c0813489c93587", "priority": 0.826507922731, "reconstruction_loss": 0.826507922731, "sample_id": "us-code-42-16928a.-51cc2f6b0ac5ca81"}`

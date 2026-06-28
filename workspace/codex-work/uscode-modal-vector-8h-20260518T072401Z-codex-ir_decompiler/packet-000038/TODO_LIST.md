# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-vector-8h-20260518T072401Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-vector-8h-20260518T072401Z-autoencoder.jsonl`
- TODO count: `3`

## TODOs
- `program-f9f5348f3699127e`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-f9f5348f3699127e` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.625134623966`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-34-20505-b8e4325ca129b142, us-code-48-1469d.-4c9a69a32ed8020e, us-code-10-7038-c3782e6a14360ca2, us-code-42-7384w-0d7c6d4971248c5e`
  evidence: `{"cosine_similarity": 0.193256241858, "hint_id": "modal-synthesis-2743e7913c0c9bdf", "priority": 0.415077902938, "reconstruction_loss": 0.415077902938, "sample_id": "us-code-42-7384w-0d7c6d4971248c5e"}`
  evidence: `{"cosine_similarity": -0.792973737371, "hint_id": "modal-synthesis-37b64ff69b893ac7", "priority": 0.841723720906, "reconstruction_loss": 0.841723720906, "sample_id": "us-code-34-20505-b8e4325ca129b142"}`
  evidence: `{"cosine_similarity": -0.271857180973, "hint_id": "modal-synthesis-457f03573a2f8ba0", "priority": 0.697358242843, "reconstruction_loss": 0.697358242843, "sample_id": "us-code-48-1469d.-4c9a69a32ed8020e"}`
  evidence: `{"cosine_similarity": -0.068522362199, "hint_id": "modal-synthesis-e89881aff1f1c744", "priority": 0.546378629176, "reconstruction_loss": 0.546378629176, "sample_id": "us-code-10-7038-c3782e6a14360ca2"}`
- `program-d373b831ba18d0df`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-f9f5348f3699127e` score `0.995958`
  loss: `autoencoder_residual_cluster` = `0.474170026378`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-46-8906.-ebe08e6d737c3c40, us-code-35-4-50bdd346f6009649, us-code-16-467b-4168eef88d7e96d0, us-code-42-3796ff-59f170d1c742e9af`
  evidence: `{"cosine_similarity": -0.649482359439, "hint_id": "modal-synthesis-2f535a0e57828121", "priority": 0.789548359551, "reconstruction_loss": 0.789548359551, "sample_id": "us-code-46-8906.-ebe08e6d737c3c40"}`
  evidence: `{"cosine_similarity": 0.343120163473, "hint_id": "modal-synthesis-6490bf4f9c94f677", "priority": 0.321006764248, "reconstruction_loss": 0.321006764248, "sample_id": "us-code-42-3796ff-59f170d1c742e9af"}`
  evidence: `{"cosine_similarity": -0.10800861151, "hint_id": "modal-synthesis-a874b7e5d376f966", "priority": 0.321520895473, "reconstruction_loss": 0.321520895473, "sample_id": "us-code-16-467b-4168eef88d7e96d0"}`
  evidence: `{"cosine_similarity": -0.105476715994, "hint_id": "modal-synthesis-c63aa68daa292c14", "priority": 0.464604086239, "reconstruction_loss": 0.464604086239, "sample_id": "us-code-35-4-50bdd346f6009649"}`
- `program-7d9d7a64e3e55392`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-f9f5348f3699127e` score `0.995685`
  loss: `autoencoder_residual_cluster` = `0.34586592899`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-48-1664.-5d3e74a2d04b3d3c, us-code-16-3471-5fee68b480ee46f0, us-code-54-304101.-92e1c25b121cd946, us-code-16-430g-4-0245d2dc387f18dd`
  evidence: `{"cosine_similarity": 0.446751533568, "hint_id": "modal-synthesis-17db7e37f698d201", "priority": 0.192769985344, "reconstruction_loss": 0.192769985344, "sample_id": "us-code-16-430g-4-0245d2dc387f18dd"}`
  evidence: `{"cosine_similarity": -0.584048624796, "hint_id": "modal-synthesis-2c48d4d86461d96a", "priority": 0.467532130311, "reconstruction_loss": 0.467532130311, "sample_id": "us-code-48-1664.-5d3e74a2d04b3d3c"}`
  evidence: `{"cosine_similarity": -0.146117518426, "hint_id": "modal-synthesis-5c73cd39c2e538c4", "priority": 0.420623661818, "reconstruction_loss": 0.420623661818, "sample_id": "us-code-16-3471-5fee68b480ee46f0"}`
  evidence: `{"cosine_similarity": 0.019437025204, "hint_id": "modal-synthesis-62483cc53665558e", "priority": 0.302537938486, "reconstruction_loss": 0.302537938486, "sample_id": "us-code-54-304101.-92e1c25b121cd946"}`

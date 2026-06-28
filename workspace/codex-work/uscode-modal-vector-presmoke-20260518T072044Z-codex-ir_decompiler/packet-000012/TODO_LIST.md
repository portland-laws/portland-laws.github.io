# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-vector-presmoke-20260518T072044Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-vector-presmoke-20260518T072044Z-autoencoder.jsonl`
- TODO count: `1`

## TODOs
- `program-326070d1a8d6fcbe`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-326070d1a8d6fcbe` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.685252825033`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-25-313-bf7627b91b7f3810, us-code-20-1703-d96d239b54afbdf8, us-code-7-2563-691a5826001c99d0, us-code-18-796-a1562639a021acf9`
  evidence: `{"cosine_similarity": -0.576871750268, "hint_id": "modal-synthesis-1846e5841ea06232", "priority": 0.65469988386, "reconstruction_loss": 0.65469988386, "sample_id": "us-code-7-2563-691a5826001c99d0"}`
  evidence: `{"cosine_similarity": 0.060668859399, "hint_id": "modal-synthesis-3bd0ab799a6bc6bd", "priority": 0.407851775836, "reconstruction_loss": 0.407851775836, "sample_id": "us-code-18-796-a1562639a021acf9"}`
  evidence: `{"cosine_similarity": -0.284125646631, "hint_id": "modal-synthesis-e5949d069b7e9f56", "priority": 0.74901868596, "reconstruction_loss": 0.74901868596, "sample_id": "us-code-20-1703-d96d239b54afbdf8"}`
  evidence: `{"cosine_similarity": -0.622630657712, "hint_id": "modal-synthesis-fc57f8c8c9264b05", "priority": 0.929440954476, "reconstruction_loss": 0.929440954476, "sample_id": "us-code-25-313-bf7627b91b7f3810"}`

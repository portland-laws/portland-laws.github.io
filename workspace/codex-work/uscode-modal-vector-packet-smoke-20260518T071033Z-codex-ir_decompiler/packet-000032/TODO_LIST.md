# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-vector-packet-smoke-20260518T071033Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-vector-packet-smoke-20260518T071033Z-autoencoder.jsonl`
- TODO count: `1`

## TODOs
- `program-3693c93fdfac4d5e`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-3693c93fdfac4d5e` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.251240657173`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-36-70106-73278ae51e89d117, us-code-15-30-0373429453f33a93, us-code-10-866-8b98b809e95dea95, us-code-18-2074-b9a9a415f557f92e`
  evidence: `{"cosine_similarity": -0.165918050931, "hint_id": "modal-synthesis-18db4255fa3ca890", "priority": 0.407830054743, "reconstruction_loss": 0.407830054743, "sample_id": "us-code-36-70106-73278ae51e89d117"}`
  evidence: `{"cosine_similarity": 0.917165526962, "hint_id": "modal-synthesis-5e8cb698a3a652e5", "priority": 0.055481214822, "reconstruction_loss": 0.055481214822, "sample_id": "us-code-18-2074-b9a9a415f557f92e"}`
  evidence: `{"cosine_similarity": 0.666504861949, "hint_id": "modal-synthesis-a094585b459cd8fc", "priority": 0.16834282508, "reconstruction_loss": 0.16834282508, "sample_id": "us-code-10-866-8b98b809e95dea95"}`
  evidence: `{"cosine_similarity": 0.031947337369, "hint_id": "modal-synthesis-c591cd170621b2c7", "priority": 0.373308534046, "reconstruction_loss": 0.373308534046, "sample_id": "us-code-15-30-0373429453f33a93"}`

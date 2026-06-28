# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-vector-8h-20260518T072401Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-vector-8h-20260518T072401Z-autoencoder.jsonl`
- TODO count: `3`

## TODOs
- `program-80b6894ed97e25f4`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-80b6894ed97e25f4` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.532275485157`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-28-2322-25d8930c51b5f4f8, us-code-15-649b-8dfcb3fb05dd4cea, us-code-42-3797cc-445d9bb6c7d68792, us-code-7-285-dc4b831efb3052da`
  evidence: `{"cosine_similarity": 0.09777035824, "hint_id": "modal-synthesis-253a7d8bda88b677", "priority": 0.496569795265, "reconstruction_loss": 0.496569795265, "sample_id": "us-code-42-3797cc-445d9bb6c7d68792"}`
  evidence: `{"cosine_similarity": 0.219748051273, "hint_id": "modal-synthesis-6ffff1931f3f6de0", "priority": 0.3542224818, "reconstruction_loss": 0.3542224818, "sample_id": "us-code-7-285-dc4b831efb3052da"}`
  evidence: `{"cosine_similarity": -0.245968259541, "hint_id": "modal-synthesis-7aaf7115283d184d", "priority": 0.760404438052, "reconstruction_loss": 0.760404438052, "sample_id": "us-code-28-2322-25d8930c51b5f4f8"}`
  evidence: `{"cosine_similarity": 0.031698938522, "hint_id": "modal-synthesis-e39cbb3ab59fa76f", "priority": 0.51790522551, "reconstruction_loss": 0.51790522551, "sample_id": "us-code-15-649b-8dfcb3fb05dd4cea"}`
- `program-661ebbbcc1446a46`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-80b6894ed97e25f4` score `0.9943`
  loss: `autoencoder_residual_cluster` = `0.370205922167`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-26-741-bddc56288e87db29, us-code-36-230307-9b4115dfe3f6ee62, us-code-48-338 to 338g.-c2b1aeb76673fe26, us-code-18-492-dda4957e0939c34f`
  evidence: `{"cosine_similarity": 0.22960545871, "hint_id": "modal-synthesis-8a846177709e2b1f", "priority": 0.303356486104, "reconstruction_loss": 0.303356486104, "sample_id": "us-code-48-338 to 338g.-c2b1aeb76673fe26"}`
  evidence: `{"cosine_similarity": 0.658603428402, "hint_id": "modal-synthesis-93d7cae4c4bd1b0b", "priority": 0.193427509167, "reconstruction_loss": 0.193427509167, "sample_id": "us-code-18-492-dda4957e0939c34f"}`
  evidence: `{"cosine_similarity": 0.34129868906, "hint_id": "modal-synthesis-be7094952b6ce314", "priority": 0.345840653586, "reconstruction_loss": 0.345840653586, "sample_id": "us-code-36-230307-9b4115dfe3f6ee62"}`
  evidence: `{"cosine_similarity": -0.239260016105, "hint_id": "modal-synthesis-d2dee340c306ce7c", "priority": 0.638199039813, "reconstruction_loss": 0.638199039813, "sample_id": "us-code-26-741-bddc56288e87db29"}`
- `program-f701644b8b542a24`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-80b6894ed97e25f4` score `0.994177`
  loss: `autoencoder_residual_cluster` = `0.441137477301`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-42-6932.-4c8798ac1bdcb191, us-code-26-6671-0699b447cf6fa07d, us-code-25-51-b0f49682f9dfa228, us-code-25-564m-dee77e626d5d85a3`
  evidence: `{"cosine_similarity": 0.329262755337, "hint_id": "modal-synthesis-51e1e2dba3e6cc3e", "priority": 0.197844854345, "reconstruction_loss": 0.197844854345, "sample_id": "us-code-25-564m-dee77e626d5d85a3"}`
  evidence: `{"cosine_similarity": -0.635744023742, "hint_id": "modal-synthesis-7b3eb260a93627f8", "priority": 0.776976462585, "reconstruction_loss": 0.776976462585, "sample_id": "us-code-42-6932.-4c8798ac1bdcb191"}`
  evidence: `{"cosine_similarity": -0.093410327162, "hint_id": "modal-synthesis-92ab6e1b46ec87e6", "priority": 0.355006179563, "reconstruction_loss": 0.355006179563, "sample_id": "us-code-25-51-b0f49682f9dfa228"}`
  evidence: `{"cosine_similarity": -0.22914181215, "hint_id": "modal-synthesis-df7ec9d5850255b9", "priority": 0.434722412709, "reconstruction_loss": 0.434722412709, "sample_id": "us-code-26-6671-0699b447cf6fa07d"}`

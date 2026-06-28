# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-vector-8h-20260518T072401Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-vector-8h-20260518T072401Z-autoencoder.jsonl`
- TODO count: `3`

## TODOs
- `program-8344057bac0f7f62`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-8344057bac0f7f62` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.672329288694`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-16-670k-17bc84bc0384b851, us-code-46-53704.-cb881a4cf0490cd8, us-code-46-53207.-71916fbaac27cc8b, us-code-42-2296b-efbe30fae94a572c`
  evidence: `{"cosine_similarity": -0.420987509816, "hint_id": "modal-synthesis-1e7caa5efae2e6aa", "priority": 0.573149629914, "reconstruction_loss": 0.573149629914, "sample_id": "us-code-42-2296b-efbe30fae94a572c"}`
  evidence: `{"cosine_similarity": -0.682676571059, "hint_id": "modal-synthesis-29561acc6c39f2b5", "priority": 0.820316128577, "reconstruction_loss": 0.820316128577, "sample_id": "us-code-16-670k-17bc84bc0384b851"}`
  evidence: `{"cosine_similarity": -0.027962950274, "hint_id": "modal-synthesis-31527f35d95b152b", "priority": 0.691607958048, "reconstruction_loss": 0.691607958048, "sample_id": "us-code-46-53704.-cb881a4cf0490cd8"}`
  evidence: `{"cosine_similarity": -0.112870838255, "hint_id": "modal-synthesis-e4dd0ad3f6f567e9", "priority": 0.604243438237, "reconstruction_loss": 0.604243438237, "sample_id": "us-code-46-53207.-71916fbaac27cc8b"}`
- `program-60d6e73516be48c9`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-8344057bac0f7f62` score `0.993421`
  loss: `autoencoder_residual_cluster` = `0.380581998351`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-25-1041d-c3e0074a42836f20, us-code-42-8013.-3827148a37e8f294, us-code-54-100507.-1d61356e95e05c6f, us-code-16-3605-012f7f1a16380c5e`
  evidence: `{"cosine_similarity": 0.695959102078, "hint_id": "modal-synthesis-693d668c7b488ce6", "priority": 0.187673286805, "reconstruction_loss": 0.187673286805, "sample_id": "us-code-16-3605-012f7f1a16380c5e"}`
  evidence: `{"cosine_similarity": -0.349754245424, "hint_id": "modal-synthesis-b1c6b57cd1c7ada9", "priority": 0.565395891658, "reconstruction_loss": 0.565395891658, "sample_id": "us-code-25-1041d-c3e0074a42836f20"}`
  evidence: `{"cosine_similarity": 0.577888800848, "hint_id": "modal-synthesis-e9abf81aa17991ca", "priority": 0.339786598051, "reconstruction_loss": 0.339786598051, "sample_id": "us-code-54-100507.-1d61356e95e05c6f"}`
  evidence: `{"cosine_similarity": 0.423173748077, "hint_id": "modal-synthesis-f6b686fea82bea18", "priority": 0.429472216889, "reconstruction_loss": 0.429472216889, "sample_id": "us-code-42-8013.-3827148a37e8f294"}`
- `program-f4f38c14738e8baa`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-8344057bac0f7f62` score `0.993198`
  loss: `autoencoder_residual_cluster` = `0.480826499127`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-5-1203-c9451c6b0e587874, us-code-29-3222-cd9982a1ebd83367, us-code-26-4972-1f4aeead9cb8d7a4, us-code-16-460eee-2-151f071e709ab648`
  evidence: `{"cosine_similarity": 0.398931035299, "hint_id": "modal-synthesis-1e9f89c3046fb507", "priority": 0.248122808396, "reconstruction_loss": 0.248122808396, "sample_id": "us-code-16-460eee-2-151f071e709ab648"}`
  evidence: `{"cosine_similarity": 0.034585861686, "hint_id": "modal-synthesis-646e3f277c151ca9", "priority": 0.585431913016, "reconstruction_loss": 0.585431913016, "sample_id": "us-code-29-3222-cd9982a1ebd83367"}`
  evidence: `{"cosine_similarity": -0.346904462296, "hint_id": "modal-synthesis-6c6fe83cc616edbc", "priority": 0.627443526617, "reconstruction_loss": 0.627443526617, "sample_id": "us-code-5-1203-c9451c6b0e587874"}`
  evidence: `{"cosine_similarity": -0.078513892093, "hint_id": "modal-synthesis-da845b0a4583870e", "priority": 0.462307748481, "reconstruction_loss": 0.462307748481, "sample_id": "us-code-26-4972-1f4aeead9cb8d7a4"}`

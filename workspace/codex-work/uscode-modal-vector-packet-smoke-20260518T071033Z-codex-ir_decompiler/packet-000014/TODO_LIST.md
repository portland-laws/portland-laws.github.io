# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-vector-packet-smoke-20260518T071033Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-vector-packet-smoke-20260518T071033Z-autoencoder.jsonl`
- TODO count: `2`

## TODOs
- `program-5779fe0d92060c37`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-5779fe0d92060c37` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.48333485376`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-7-2153-deb8e23300430df9, us-code-26-6403-ec645fcbda259907, us-code-42-1395w-745a0a8249ece403, us-code-38-5319-5304ffaedccf083f`
  evidence: `{"cosine_similarity": 0.623260157897, "hint_id": "modal-synthesis-a56c8d09f1b5a478", "priority": 0.291857326462, "reconstruction_loss": 0.291857326462, "sample_id": "us-code-38-5319-5304ffaedccf083f"}`
  evidence: `{"cosine_similarity": -0.002577020317, "hint_id": "modal-synthesis-d96d65af1264c82d", "priority": 0.475018200831, "reconstruction_loss": 0.475018200831, "sample_id": "us-code-26-6403-ec645fcbda259907"}`
  evidence: `{"cosine_similarity": 0.099422186577, "hint_id": "modal-synthesis-f06296368efcaecb", "priority": 0.400672918879, "reconstruction_loss": 0.400672918879, "sample_id": "us-code-42-1395w-745a0a8249ece403"}`
  evidence: `{"cosine_similarity": -0.630119112778, "hint_id": "modal-synthesis-fb719110f2b0502f", "priority": 0.765790968868, "reconstruction_loss": 0.765790968868, "sample_id": "us-code-7-2153-deb8e23300430df9"}`
- `program-d6d88d8df413137b`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-5779fe0d92060c37` score `0.73261`
  loss: `autoencoder_residual_cluster` = `0.38128250526`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-19-1522-c9f523c29b6f60ec, us-code-42-3789p.-e9f782ad4a060674, us-code-20-1070a-31-a5557d79e0f05fab, us-code-2-149a-fb43ab8a1db5b475`
  evidence: `{"cosine_similarity": 0.544911213566, "hint_id": "modal-synthesis-bbf5eb00535eb366", "priority": 0.282904350197, "reconstruction_loss": 0.282904350197, "sample_id": "us-code-2-149a-fb43ab8a1db5b475"}`
  evidence: `{"cosine_similarity": 0.414772919162, "hint_id": "modal-synthesis-e3f2128b47c88ae1", "priority": 0.379192046405, "reconstruction_loss": 0.379192046405, "sample_id": "us-code-20-1070a-31-a5557d79e0f05fab"}`
  evidence: `{"cosine_similarity": 0.141739533857, "hint_id": "modal-synthesis-f132acfd5b28289e", "priority": 0.471645178796, "reconstruction_loss": 0.471645178796, "sample_id": "us-code-19-1522-c9f523c29b6f60ec"}`
  evidence: `{"cosine_similarity": -0.020851807248, "hint_id": "modal-synthesis-fcf0d795be63a4f6", "priority": 0.391388445642, "reconstruction_loss": 0.391388445642, "sample_id": "us-code-42-3789p.-e9f782ad4a060674"}`

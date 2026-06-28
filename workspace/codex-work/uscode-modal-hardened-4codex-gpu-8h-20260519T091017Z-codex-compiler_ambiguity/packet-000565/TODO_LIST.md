# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-autoencoder.jsonl`
- TODO count: `3`

## TODOs
- `program-2855240214eada2e`
  action: `add_or_review_modal_ambiguity_policy`
  role: `program_synthesis`
  target: `modal.compiler.ambiguity`
  scope: `compiler_ambiguity`
  bundle: `{"action":"add_or_review_modal_ambiguity_policy","family_pairs":["alethic->deontic","frame->conditional_normative","frame->temporal","temporal->deontic"],"program_synthesis_scope":"compiler_ambiguity","target_component":"modal.compiler.ambiguity"}`
  vector_bundle: `program-2855240214eada2e` score `1.0`
  loss: `autoencoder_residual_cluster` = `1.001310702258`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  samples: `us-code-25-3652-ba56d9096e1a4b44, us-code-42-5101.-ba8d782ceb25bd14, us-code-26-6700-5ffa6d152d81c4b5, us-code-19-1450-aea5c8a1932fb39d`
  evidence: `{"family_margin": -0.819447023251, "hint_id": "modal-synthesis-20c54707e901a305", "predicted_family": "frame", "priority": 0.969447023251, "sample_id": "us-code-26-6700-5ffa6d152d81c4b5", "target_family": "conditional_normative"}`
  evidence: `{"family_margin": -0.999129026364, "hint_id": "modal-synthesis-6694c7e47ad00138", "predicted_family": "frame", "priority": 1.149129026364, "sample_id": "us-code-25-3652-ba56d9096e1a4b44", "target_family": "temporal"}`
  evidence: `{"family_margin": -0.587963597647, "hint_id": "modal-synthesis-69b0da0a95a3e8d9", "predicted_family": "temporal", "priority": 0.737963597647, "sample_id": "us-code-19-1450-aea5c8a1932fb39d", "target_family": "deontic"}`
  evidence: `{"family_margin": -0.998703161772, "hint_id": "modal-synthesis-d29c621e2338e916", "predicted_family": "alethic", "priority": 1.148703161772, "sample_id": "us-code-42-5101.-ba8d782ceb25bd14", "target_family": "deontic"}`
- `program-3876ef231e0c2d93`
  action: `add_or_review_modal_ambiguity_policy`
  role: `program_synthesis`
  target: `modal.compiler.ambiguity`
  scope: `compiler_ambiguity`
  bundle: `{"action":"add_or_review_modal_ambiguity_policy","family_pairs":["deontic->deontic","frame->conditional_normative","temporal->temporal"],"program_synthesis_scope":"compiler_ambiguity","target_component":"modal.compiler.ambiguity"}`
  vector_bundle: `program-2855240214eada2e` score `0.976381`
  loss: `autoencoder_residual_cluster` = `0.474500951371`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  samples: `us-code-15-80b-2-b829c8e17aa97516, us-code-22-10412-551f5ec597c4dc61, us-code-15-7106-a4e159e8a8f68337`
  evidence: `{"family_margin": 0.0, "hint_id": "modal-synthesis-2e9ea24a449cbd90", "predicted_family": "temporal", "priority": 0.15, "sample_id": "us-code-22-10412-551f5ec597c4dc61", "target_family": "temporal"}`
  evidence: `{"family_margin": 0.026492745977, "hint_id": "modal-synthesis-400a312648a4bb5f", "predicted_family": "deontic", "priority": 0.123507254023, "sample_id": "us-code-15-7106-a4e159e8a8f68337", "target_family": "deontic"}`
  evidence: `{"family_margin": -0.999995600089, "hint_id": "modal-synthesis-6089d3aab0c3b9ab", "predicted_family": "frame", "priority": 1.149995600089, "sample_id": "us-code-15-80b-2-b829c8e17aa97516", "target_family": "conditional_normative"}`
- `program-3233fd4612879e72`
  action: `add_or_review_modal_ambiguity_policy`
  role: `program_synthesis`
  target: `modal.compiler.ambiguity`
  scope: `compiler_ambiguity`
  bundle: `{"action":"add_or_review_modal_ambiguity_policy","family_pairs":["deontic->temporal","frame->deontic","temporal->temporal"],"program_synthesis_scope":"compiler_ambiguity","target_component":"modal.compiler.ambiguity"}`
  vector_bundle: `program-2855240214eada2e` score `0.969538`
  loss: `autoencoder_residual_cluster` = `0.56505178328`
  objective: The adaptive family margin is small, so the compiler should expose an explicit ambiguity.
  samples: `us-code-51-60146.-259c98a1d437a478, us-code-42-2039.-0d1fc5eb235a096d, us-code-38-1831-0790b56af17a6963`
  evidence: `{"family_margin": 0.07230802082, "hint_id": "modal-synthesis-07b75b9305febe12", "predicted_family": "temporal", "priority": 0.07769197918, "sample_id": "us-code-38-1831-0790b56af17a6963", "target_family": "temporal"}`
  evidence: `{"family_margin": -0.373163839572, "hint_id": "modal-synthesis-b245f9ade3f23b0c", "predicted_family": "deontic", "priority": 0.523163839572, "sample_id": "us-code-42-2039.-0d1fc5eb235a096d", "target_family": "temporal"}`
  evidence: `{"family_margin": -0.944299531087, "hint_id": "modal-synthesis-f8fd1e4d0009a74c", "predicted_family": "frame", "priority": 1.094299531087, "sample_id": "us-code-51-60146.-259c98a1d437a478", "target_family": "deontic"}`

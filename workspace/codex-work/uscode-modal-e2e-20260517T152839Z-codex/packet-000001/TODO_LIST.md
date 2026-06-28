# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-e2e-20260517T152839Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-e2e-20260517T152839Z-autoencoder.jsonl`
- TODO count: `1`

## TODOs
- `program-4c2ad37960848fed`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  loss: `autoencoder_residual_cluster` = `0.489086658909`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-21-346-cbe16eeabb5e6c33, us-code-42-247b-361c41439e746805, us-code-25-2717-1b98fc55bf9ac07b, us-code-29-3006-04f38a86e99a30fc`
  evidence: `{"cosine_similarity": 0.488835455246, "hint_id": "modal-synthesis-0d2879665b0866e7", "priority": 0.254298793875, "reconstruction_loss": 0.254298793875, "sample_id": "us-code-29-3006-04f38a86e99a30fc"}`
  evidence: `{"cosine_similarity": -0.575311725768, "hint_id": "modal-synthesis-b0e109524d0019c2", "priority": 0.539460963964, "reconstruction_loss": 0.539460963964, "sample_id": "us-code-42-247b-361c41439e746805"}`
  evidence: `{"cosine_similarity": -0.540687426513, "hint_id": "modal-synthesis-efcc68a5b571e1eb", "priority": 0.725910879126, "reconstruction_loss": 0.725910879126, "sample_id": "us-code-21-346-cbe16eeabb5e6c33"}`
  evidence: `{"cosine_similarity": -0.074181865321, "hint_id": "modal-synthesis-f77f424f1520d17e", "priority": 0.436675998669, "reconstruction_loss": 0.436675998669, "sample_id": "us-code-25-2717-1b98fc55bf9ac07b"}`

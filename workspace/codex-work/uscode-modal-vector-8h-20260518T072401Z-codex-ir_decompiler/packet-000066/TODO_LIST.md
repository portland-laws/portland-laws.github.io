# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-vector-8h-20260518T072401Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-vector-8h-20260518T072401Z-autoencoder.jsonl`
- TODO count: `3`

## TODOs
- `program-22a338b7e0c8dd6e`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-22a338b7e0c8dd6e` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.483046536801`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-6-314-afaf3a4084d6428b, us-code-16-410iii-4-0c9d2d4fb65dc095, us-code-12-5216-52f223ae468c3154, us-code-42-18654.-cc134e58e70d774d`
  evidence: `{"cosine_similarity": -0.187675455237, "hint_id": "modal-synthesis-18f4c9c9f631248b", "priority": 0.247345147214, "reconstruction_loss": 0.247345147214, "sample_id": "us-code-42-18654.-cc134e58e70d774d"}`
  evidence: `{"cosine_similarity": 0.049648407944, "hint_id": "modal-synthesis-23152dab221387f8", "priority": 0.338196064846, "reconstruction_loss": 0.338196064846, "sample_id": "us-code-12-5216-52f223ae468c3154"}`
  evidence: `{"cosine_similarity": -0.652427373845, "hint_id": "modal-synthesis-50bbb15c85e72372", "priority": 0.868089587226, "reconstruction_loss": 0.868089587226, "sample_id": "us-code-6-314-afaf3a4084d6428b"}`
  evidence: `{"cosine_similarity": -0.546496969011, "hint_id": "modal-synthesis-edc2b755d66007fb", "priority": 0.478555347918, "reconstruction_loss": 0.478555347918, "sample_id": "us-code-16-410iii-4-0c9d2d4fb65dc095"}`
- `program-2c7f3a9c23d867ea`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-22a338b7e0c8dd6e` score `0.992837`
  loss: `autoencoder_residual_cluster` = `0.481075343898`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-52-10314.-f756f2d8ac6ce0a3, us-code-5-8992-5f974d5c7be457ea, us-code-42-16502.-29bf576eaa911553, us-code-48-1711.-fe46b6a75dd51e41`
  evidence: `{"cosine_similarity": 0.27710588905, "hint_id": "modal-synthesis-045c5d033ffe93e2", "priority": 0.301106636535, "reconstruction_loss": 0.301106636535, "sample_id": "us-code-48-1711.-fe46b6a75dd51e41"}`
  evidence: `{"cosine_similarity": -0.099415948822, "hint_id": "modal-synthesis-42c4277a84d082ad", "priority": 0.348540307875, "reconstruction_loss": 0.348540307875, "sample_id": "us-code-42-16502.-29bf576eaa911553"}`
  evidence: `{"cosine_similarity": -0.25023480019, "hint_id": "modal-synthesis-6ae7d18cfc6d611a", "priority": 0.644961581489, "reconstruction_loss": 0.644961581489, "sample_id": "us-code-52-10314.-f756f2d8ac6ce0a3"}`
  evidence: `{"cosine_similarity": -0.183924340227, "hint_id": "modal-synthesis-9d4ac7d26bd127e2", "priority": 0.629692849694, "reconstruction_loss": 0.629692849694, "sample_id": "us-code-5-8992-5f974d5c7be457ea"}`
- `program-ba33d2e6e72c4d66`
  action: `refine_typed_ir_or_decompiler_slots`
  role: `program_synthesis`
  target: `modal.ir_decompiler`
  scope: `ir_decompiler`
  bundle: `{"action":"refine_typed_ir_or_decompiler_slots","family_pairs":[],"program_synthesis_scope":"ir_decompiler","target_component":"modal.ir_decompiler"}`
  vector_bundle: `program-22a338b7e0c8dd6e` score `0.992558`
  loss: `autoencoder_residual_cluster` = `0.44208747618`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  samples: `us-code-14-1942-500ca0c5b02a01bb, us-code-16-715d-3-6cfb243e9cba29a2, us-code-33-1951-865446e0c07d8ee8, us-code-43-1634.-c7f76ec94bc02b88`
  evidence: `{"cosine_similarity": 0.196536543792, "hint_id": "modal-synthesis-0cf25fdcda884013", "priority": 0.53640500037, "reconstruction_loss": 0.53640500037, "sample_id": "us-code-16-715d-3-6cfb243e9cba29a2"}`
  evidence: `{"cosine_similarity": -0.200178870031, "hint_id": "modal-synthesis-5ba78da7df413358", "priority": 0.542472700711, "reconstruction_loss": 0.542472700711, "sample_id": "us-code-14-1942-500ca0c5b02a01bb"}`
  evidence: `{"cosine_similarity": 0.512910054329, "hint_id": "modal-synthesis-69d7877f1bea063c", "priority": 0.260841829857, "reconstruction_loss": 0.260841829857, "sample_id": "us-code-43-1634.-c7f76ec94bc02b88"}`
  evidence: `{"cosine_similarity": -0.325162290583, "hint_id": "modal-synthesis-879323f571b87775", "priority": 0.428630373783, "reconstruction_loss": 0.428630373783, "sample_id": "us-code-33-1951-865446e0c07d8ee8"}`

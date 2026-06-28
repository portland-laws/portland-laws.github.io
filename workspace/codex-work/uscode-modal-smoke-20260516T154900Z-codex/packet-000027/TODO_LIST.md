# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-smoke-20260516T154900Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-smoke-20260516T154900Z-autoencoder.jsonl`
- TODO count: `4`

## TODOs
- `55f58a011c9f9564`
  action: `add_deterministic_parser_rule`
  role: `program_synthesis`
  target: ``
  loss: `parser_formula_count` = `1.0`
  objective: Create a golden parser case for legal text that produced no modal formulas.
  samples: `us-code-51-20161.-90f4bf0dfa214e7d`
- `5b07b6e9d8a61503`
  action: `add_deterministic_parser_rule`
  role: `program_synthesis`
  target: ``
  loss: `symbolic_validity_penalty` = `0.5`
  objective: Add a deterministic parser rule or fixture for legal text that failed symbolic validation.
  samples: `us-code-51-20161.-90f4bf0dfa214e7d`
- `f23478c315132c04`
  action: `add_deterministic_parser_rule`
  role: `program_synthesis`
  target: ``
  loss: `symbolic_validity_penalty` = `0.5`
  objective: Add a deterministic parser rule or fixture for legal text that failed symbolic validation.
  samples: `us-code-19-3911-46b2d5dc09c76062`
- `program-9cc69a60a23817b8`
  action: `audit_frame_logic_terms`
  role: `program_synthesis`
  target: `modal.frame_logic`
  loss: `autoencoder_residual_cluster` = `0.503480153398`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  samples: `us-code-19-3911-46b2d5dc09c76062, us-code-51-20161.-90f4bf0dfa214e7d`
  evidence: `{"hint_id": "modal-synthesis-ac43939cd52467ca", "priority": 0.592912505891, "sample_id": "us-code-19-3911-46b2d5dc09c76062"}`
  evidence: `{"frame_features": ["flogic:candidate_ontology_frame:administrative_notice_hearing"], "hint_id": "modal-synthesis-adba09b7caf5e452", "priority": 0.414047800905, "sample_id": "us-code-51-20161.-90f4bf0dfa214e7d"}`

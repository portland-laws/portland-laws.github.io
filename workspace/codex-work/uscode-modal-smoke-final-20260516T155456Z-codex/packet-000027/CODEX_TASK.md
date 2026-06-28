# packet-000027

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-smoke-final-20260516T155456Z-codex/packet-000027/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-smoke-final-20260516T155456Z-codex/packet-000027/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-smoke-final-20260516T155456Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-smoke-final-20260516T155456Z-codex-packet-000027-20260516_155531

## Patch
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/codec.py`
- `ipfs_datasets_py/logic/modal/decompiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_ir.py`
- `ipfs_datasets_py/optimizers/logic/flogic_optimizer.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/frame_bm25_selector.py`

## TODOs
- `program-3d6533e87a953fe9` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 2
  evidence: `{"cosine_similarity": 0.116707523278, "hint_id": "modal-synthesis-7708e523060d0a60", "priority": 0.425972123547, "reconstruction_loss": 0.425972123547, "sample_id": "us-code-16-1882-7162f921f0a7085c", "top_embedding_features": ["family:alethic:2", "lemma:later", "lemma:state", "lemma:iv", "lemma:known", "lemma:existing", "lemma:june", "lemma:added"]}`
  evidence: `{"cosine_similarity": -0.228023584524, "hint_id": "modal-synthesis-7bee6236f345e5b5", "priority": 0.621882730049, "reconstruction_loss": 0.621882730049, "sample_id": "us-code-42-300t.-aaed07240d8c050d", "top_embedding_features": ["lemma:application", "lemma:appropriations", "lemma:eligible", "lemma:establish", "lemma:iii", "lemma:secretary", "lemma:june", "lemma:determination"]}`
- `program-ef6db7f780ba4b90` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 2
  evidence: `{"hint_id": "modal-synthesis-a16fec0fa73bfedd", "priority": 0.425972123547, "sample_id": "us-code-16-1882-7162f921f0a7085c"}`
  evidence: `{"hint_id": "modal-synthesis-bf1b170a3037e565", "priority": 0.621882730049, "sample_id": "us-code-42-300t.-aaed07240d8c050d"}`
- `program-3c8c635e7b37eed0` `audit_frame_logic_terms`
  target: `modal.frame_logic`
  objective: Frame-linked features influenced reconstruction or family scoring and should be audited as ontology terms.
  support: 2
  evidence: `{"hint_id": "modal-synthesis-419359f2759e28e8", "priority": 0.396669988652, "sample_id": "us-code-12-3205-dfa0e74737439e95"}`
  evidence: `{"frame_features": ["flogic:predicate:pub"], "hint_id": "modal-synthesis-578461b17b5f05fb", "priority": 0.2257743056, "sample_id": "us-code-9-307-174540ee55e7b56f"}`
- `program-d468a646026b5726` `refine_typed_ir_or_decompiler_slots`
  target: `modal.ir_decompiler`
  objective: Embedding residuals point to information not well represented by the typed IR/decompiler.
  support: 2
  evidence: `{"cosine_similarity": 0.38554548742, "hint_id": "modal-synthesis-9728d4b9778b28fe", "priority": 0.2257743056, "reconstruction_loss": 0.2257743056, "sample_id": "us-code-9-307-174540ee55e7b56f", "top_embedding_features": ["lemma:substituted", "lemma:conflict", "cue:temporal:F:by", "lemma:amendments", "lemma:inserted", "lemma:application", "flogic:predicate:pub", "lemma:amended"]}`
  evidence: `{"cosine_similarity": 0.105902970905, "hint_id": "modal-synthesis-d80982983fa22ec6", "priority": 0.396669988652, "reconstruction_loss": 0.396669988652, "sample_id": "us-code-12-3205-dfa0e74737439e95", "top_embedding_features": ["lemma:assets", "lemma:expiration", "lemma:makes", "lemma:establishment", "lemma:days", "lemma:preceding", "lemma:changes", "cue:deontic:F:prohibited"]}`

## Patch Command
Run this after editing the worktree:

```bash
git diff HEAD > changes.patch
```

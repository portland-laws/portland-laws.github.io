# packet-000271

## Source
The TODO batch is autoencoder/supervisor output; this file is the Codex-facing work order.
- Raw TODO JSONL: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_registry/packet-000271/TODO_LIST.jsonl`
- TODO markdown: `/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_registry/packet-000271/TODO_LIST.md`

## Worktree
/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-codex-compiler_registry/worktrees/agent-codex-compiler_registry-packet-000271-20260519_162140

## Change Capture
pending: awaiting_codex_changes

## Suggested Files
- `ipfs_datasets_py/logic/modal/compiler.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/modal_registry.py`
- `ipfs_datasets_py/optimizers/logic_theorem_optimizer/spacy_modal_codec.py`

## TODOs
- `program-4dc6c791a3882279` `refine_modal_family_cue_rules`
  target: `modal.compiler.registry`
  scope: `compiler_registry`
  bundle: `{"action":"refine_modal_family_cue_rules","family_pairs":["alethic->deontic","frame->conditional_normative","frame->temporal","temporal->deontic"],"program_synthesis_scope":"compiler_registry","target_component":"modal.compiler.registry"}`
  vector_bundle: `program-4dc6c791a3882279` score `1.0`
  objective: Adaptive family evidence disagrees with, or is weak for, the typed modal family.
  support: 4
  evidence: `{"family_margin": -0.998703161772, "hint_id": "modal-synthesis-024f2c3a6342e3c0", "predicted_family": "alethic", "priority": 0.999982560238, "sample_id": "us-code-42-5101.-ba8d782ceb25bd14", "target_family": "deontic", "target_probability": 1.7439762e-05}`
  evidence: `{"family_margin": -0.587963597647, "hint_id": "modal-synthesis-1a2d231d10ca4d30", "predicted_family": "temporal", "priority": 0.979656013254, "sample_id": "us-code-19-1450-aea5c8a1932fb39d", "target_family": "deontic", "target_probability": 0.020343986746}`
  evidence: `{"family_margin": -0.819447023251, "hint_id": "modal-synthesis-4686a96042b15a2d", "predicted_family": "frame", "priority": 0.94266893352, "sample_id": "us-code-26-6700-5ffa6d152d81c4b5", "target_family": "conditional_normative", "target_probability": 0.05733106648}`
  evidence: `{"family_margin": -0.999129026364, "hint_id": "modal-synthesis-73585b612cc3befd", "predicted_family": "frame", "priority": 0.999973828647, "sample_id": "us-code-25-3652-ba56d9096e1a4b44", "target_family": "temporal", "target_probability": 2.6171353e-05}`
- `program-667d6ab61eb8f7de` `refine_modal_family_cue_rules`
  target: `modal.compiler.registry`
  scope: `compiler_registry`
  bundle: `{"action":"refine_modal_family_cue_rules","family_pairs":["deontic->temporal","frame->frame","frame->temporal","temporal->deontic"],"program_synthesis_scope":"compiler_registry","target_component":"modal.compiler.registry"}`
  vector_bundle: `program-4dc6c791a3882279` score `0.984859`
  objective: Adaptive family evidence disagrees with, or is weak for, the typed modal family.
  support: 4
  evidence: `{"family_margin": -0.478966698068, "hint_id": "modal-synthesis-2ad492c41d07f7e6", "predicted_family": "deontic", "priority": 0.925033261463, "sample_id": "us-code-15-80a-40-7182504490ffc287", "target_family": "temporal", "target_probability": 0.074966738537}`
  evidence: `{"family_margin": 0.0, "hint_id": "modal-synthesis-4d9cfe6fd4b3c12f", "predicted_family": "temporal", "priority": 0.633596363007, "sample_id": "us-code-48-1470.-20dd186a1c515410", "target_family": "deontic", "target_probability": 0.366403636993}`
  evidence: `{"family_margin": -0.189640912447, "hint_id": "modal-synthesis-79ade1fc0affd1f5", "predicted_family": "frame", "priority": 0.598507425648, "sample_id": "us-code-10-7591-1d9c7f85c1418d0b", "target_family": "temporal", "target_probability": 0.401492574352}`
  evidence: `{"family_margin": 0.199221055742, "hint_id": "modal-synthesis-fdea4ff52cb96b4f", "predicted_family": "frame", "priority": 0.529084111933, "sample_id": "us-code-16-14c-2d71ab3683bdda91", "target_family": "frame", "target_probability": 0.470915888067}`
- `program-eca30389dc431bfd` `refine_modal_family_cue_rules`
  target: `modal.compiler.registry`
  scope: `compiler_registry`
  bundle: `{"action":"refine_modal_family_cue_rules","family_pairs":["deontic->temporal","frame->deontic","temporal->temporal"],"program_synthesis_scope":"compiler_registry","target_component":"modal.compiler.registry"}`
  vector_bundle: `program-4dc6c791a3882279` score `0.968365`
  objective: Adaptive family evidence disagrees with, or is weak for, the typed modal family.
  support: 3
  evidence: `{"family_margin": -0.373163839572, "hint_id": "modal-synthesis-b07c3af93eb2951b", "predicted_family": "deontic", "priority": 0.893381760122, "sample_id": "us-code-42-2039.-0d1fc5eb235a096d", "target_family": "temporal", "target_probability": 0.106618239878}`
  evidence: `{"family_margin": -0.944299531087, "hint_id": "modal-synthesis-d3bc5f66f2ae90ba", "predicted_family": "frame", "priority": 0.975828940505, "sample_id": "us-code-51-60146.-259c98a1d437a478", "target_family": "deontic", "target_probability": 0.024171059495}`
  evidence: `{"family_margin": 0.07230802082, "hint_id": "modal-synthesis-dbd3fe0883227293", "predicted_family": "temporal", "priority": 0.600092560674, "sample_id": "us-code-38-1831-0790b56af17a6963", "target_family": "temporal", "target_probability": 0.399907439326}`

## Finish
Leave the completed edits in the worktree; the daemon captures, applies, and validates the diff.


## Execution Instructions
Work only inside the packet worktree.
Your worktree edits may be applied back to the source checkout and validated automatically when this packet finishes.
Do not create changes.patch or other patch artifact files; leave source and test edits directly in the worktree.
Treat the packet's program_synthesis_scope metadata as the AST/write-scope boundary; keep edits inside that lane unless a test requires a small adjacent change.
When multiple TODOs are present, treat their semantic_bundle_key or vector_bundle metadata as evidence for one generalized compiler/decompiler/frame improvement over one-off sample fixes.
Implement a narrow deterministic parser, IR, decoder, or frame-logic improvement for the claimed TODOs.
Prefer explainable compiler/decompiler code over learned weights when the TODO concerns modal or frame semantics.
Use local repository files and tests only; do not use web search for this packet.
Run the smallest relevant tests you can before finishing.
Leave unrelated files alone.

## Claimed Autoencoder TODO List
# Autoencoder TODO List

These TODOs were generated from autoencoder introspection and claimed from the supervisor queue.

- Queue run: `uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-autoencoder`
- Queue path: `/home/barberb/portland-laws.github.io/workspace/todo-queues/uscode-modal-hardened-4codex-gpu-8h-20260519T091017Z-autoencoder.jsonl`
- TODO count: `3`

## TODOs
- `program-4dc6c791a3882279`
  action: `refine_modal_family_cue_rules`
  role: `program_synthesis`
  target: `modal.compiler.registry`
  scope: `compiler_registry`
  bundle: `{"action":"refine_modal_family_cue_rules","family_pairs":["alethic->deontic","frame->conditional_normative","frame->temporal","temporal->deontic"],"program_synthesis_scope":"compiler_registry","target_component":"modal.compiler.registry"}`
  vector_bundle: `program-4dc6c791a3882279` score `1.0`
  loss: `autoencoder_residual_cluster` = `0.980570333915`
  objective: Adaptive family evidence disagrees with, or is weak for, the typed modal family.
  samples: `us-code-42-5101.-ba8d782ceb25bd14, us-code-25-3652-ba56d9096e1a4b44, us-code-19-1450-aea5c8a1932fb39d, us-code-26-6700-5ffa6d152d81c4b5`
  evidence: `{"family_margin": -0.998703161772, "hint_id": "modal-synthesis-024f2c3a6342e3c0", "predicted_family": "alethic", "priority": 0.999982560238, "sample_id": "us-code-42-5101.-ba8d782ceb25bd14", "target_family": "deontic", "target_probability": 1.7439762e-05}`
  evidence: `{"family_margin": -0.587963597647, "hint_id": "modal-synthesis-1a2d231d10ca4d30", "predicted_family": "temporal", "priority": 0.979656013254, "sample_id": "us-code-19-1450-aea5c8a1932fb39d", "target_family": "deontic", "target_probability": 0.020343986746}`
  evidence: `{"family_margin": -0.819447023251, "hint_id": "modal-synthesis-4686a96042b15a2d", "predicted_family": "frame", "priority": 0.94266893352, "sample_id": "us-code-26-6700-5ffa6d152d81c4b5", "target_family": "conditional_normative", "target_probability": 0.05733106648}`
  evidence: `{"family_margin": -0.999129026364, "hint_id": "modal-synthesis-73585b612cc3befd", "predicted_family": "frame", "priority": 0.999973828647, "sample_id": "us-code-25-3652-ba56d9096e1a4b44", "target_family": "temporal", "target_probability": 2.6171353e-05}`
- `program-667d6ab61eb8f7de`
  action: `refine_modal_family_cue_rules`
  role: `program_synthesis`
  target: `modal.compiler.registry`
  scope: `compiler_registry`
  bundle: `{"action":"refine_modal_family_cue_rules","family_pairs":["deontic->temporal","frame->frame","frame->temporal","temporal->deontic"],"program_synthesis_scope":"compiler_registry","target_component":"modal.compiler.registry"}`
  vector_bundle: `program-4dc6c791a3882279` score `0.984859`
  loss: `autoencoder_residual_cluster` = `0.671555290513`
  objective: Adaptive family evidence disagrees with, or is weak for, the typed modal family.
  samples: `us-code-15-80a-40-7182504490ffc287, us-code-48-1470.-20dd186a1c515410, us-code-10-7591-1d9c7f85c1418d0b, us-code-16-14c-2d71ab3683bdda91`
  evidence: `{"family_margin": -0.478966698068, "hint_id": "modal-synthesis-2ad492c41d07f7e6", "predicted_family": "deontic", "priority": 0.925033261463, "sample_id": "us-code-15-80a-40-7182504490ffc287", "target_family": "temporal", "target_probability": 0.074966738537}`
  evidence: `{"family_margin": 0.0, "hint_id": "modal-synthesis-4d9cfe6fd4b3c12f", "predicted_family": "temporal", "priority": 0.633596363007, "sample_id": "us-code-48-1470.-20dd186a1c515410", "target_family": "deontic", "target_probability": 0.366403636993}`
  evidence: `{"family_margin": -0.189640912447, "hint_id": "modal-synthesis-79ade1fc0affd1f5", "predicted_family": "frame", "priority": 0.598507425648, "sample_id": "us-code-10-7591-1d9c7f85c1418d0b", "target_family": "temporal", "target_probability": 0.401492574352}`
  evidence: `{"family_margin": 0.199221055742, "hint_id": "modal-synthesis-fdea4ff52cb96b4f", "predicted_family": "frame", "priority": 0.529084111933, "sample_id": "us-code-16-14c-2d71ab3683bdda91", "target_family": "frame", "target_probability": 0.470915888067}`
- `program-eca30389dc431bfd`
  action: `refine_modal_family_cue_rules`
  role: `program_synthesis`
  target: `modal.compiler.registry`
  scope: `compiler_registry`
  bundle: `{"action":"refine_modal_family_cue_rules","family_pairs":["deontic->temporal","frame->deontic","temporal->temporal"],"program_synthesis_scope":"compiler_registry","target_component":"modal.compiler.registry"}`
  vector_bundle: `program-4dc6c791a3882279` score `0.968365`
  loss: `autoencoder_residual_cluster` = `0.8231010871`
  objective: Adaptive family evidence disagrees with, or is weak for, the typed modal family.
  samples: `us-code-51-60146.-259c98a1d437a478, us-code-42-2039.-0d1fc5eb235a096d, us-code-38-1831-0790b56af17a6963`
  evidence: `{"family_margin": -0.373163839572, "hint_id": "modal-synthesis-b07c3af93eb2951b", "predicted_family": "deontic", "priority": 0.893381760122, "sample_id": "us-code-42-2039.-0d1fc5eb235a096d", "target_family": "temporal", "target_probability": 0.106618239878}`
  evidence: `{"family_margin": -0.944299531087, "hint_id": "modal-synthesis-d3bc5f66f2ae90ba", "predicted_family": "frame", "priority": 0.975828940505, "sample_id": "us-code-51-60146.-259c98a1d437a478", "target_family": "deontic", "target_probability": 0.024171059495}`
  evidence: `{"family_margin": 0.07230802082, "hint_id": "modal-synthesis-dbd3fe0883227293", "predicted_family": "temporal", "priority": 0.600092560674, "sample_id": "us-code-38-1831-0790b56af17a6963", "target_family": "temporal", "target_probability": 0.399907439326}`

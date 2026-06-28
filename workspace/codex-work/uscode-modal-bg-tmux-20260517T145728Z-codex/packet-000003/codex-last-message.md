Implemented the `modal.compiler.ambiguity` TODO with a deterministic family-margin ambiguity rule.

- Added `modal_family_count_margin` to compiler config and a new ambiguity detector in [compiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-bg-tmux-20260517T145728Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-bg-tmux-20260517T145728Z-codex-packet-000003-20260517_150843/ipfs_datasets_py/logic/modal/compiler.py#L37).
- Compiler now emits `close_modal_family_counts` when top two cue-family counts are too close (default normalized margin `<= 0.15`), with explicit metadata (`family_counts`, `margin`, top/runner-up counts).
- Wired this into the main ambiguity list in `compile()` in [compiler.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-bg-tmux-20260517T145728Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-bg-tmux-20260517T145728Z-codex-packet-000003-20260517_150843/ipfs_datasets_py/logic/modal/compiler.py#L144).

Added focused coverage in [test_modal_codec.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-bg-tmux-20260517T145728Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-bg-tmux-20260517T145728Z-codex-packet-000003-20260517_150843/tests/unit_tests/logic/modal/test_modal_codec.py#L146):

- New test verifies a deontic/frame tie produces `close_modal_family_counts`.
- Confirms this family ambiguity is distinct from BM25 frame-score ambiguity.

Validation run:
- `pytest` targeted run is currently blocked by an existing repo issue: root [__init__.py](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-bg-tmux-20260517T145728Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-bg-tmux-20260517T145728Z-codex-packet-000003-20260517_150843/__init__.py#L11) raises `NameError: __path__ is not defined`.
- Performed direct `python3` runtime assertions for:
  - new family ambiguity path (`manual_check_ok`)
  - existing close-frame ambiguity path (`legacy_check_ok`)

Generated patch file as requested: [changes.patch](/home/barberb/portland-laws.github.io/workspace/codex-work/uscode-modal-bg-tmux-20260517T145728Z-codex/worktrees/agent-codex-program-synthesis-uscode-modal-bg-tmux-20260517T145728Z-codex-packet-000003-20260517_150843/changes.patch).
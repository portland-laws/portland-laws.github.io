from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CONTROL_SCRIPT = REPO_ROOT / "ppd" / "daemon" / "control.sh"


class DaemonControlProcessFamilyShutdownTest(unittest.TestCase):
    def test_control_script_is_syntax_valid(self) -> None:
        result = subprocess.run(
            ["bash", "-n", str(CONTROL_SCRIPT)],
            cwd=REPO_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual("", result.stderr)
        self.assertEqual(0, result.returncode)

    def test_stop_paths_terminate_captured_descendant_process_groups(self) -> None:
        source = CONTROL_SCRIPT.read_text(encoding="utf-8")

        self.assertIn("collect_descendant_pids", source)
        self.assertIn("process_group_for_pid", source)
        self.assertIn("terminate_process_family", source)
        self.assertIn("sweep_orphaned_ppd_llm_children", source)
        self.assertIn('kill -TERM -- "-$pgid"', source)
        self.assertIn('kill -KILL -- "-$pgid"', source)
        self.assertIn('[[ "$ppid" == "1" ]]', source)
        self.assertIn("/PPD_LLM_PROMPT_FILE/", source)
        self.assertIn("--repair-validation-failures", source)
        self.assertIn("--crash-backoff 5", source)
        self.assertIn("--exception-backoff 5", source)
        self.assertIn('terminate_process_family "$pid" "PP&D daemon"', source)
        self.assertIn('terminate_process_family "$pid" "PP&D supervisor"', source)


if __name__ == "__main__":
    unittest.main()

from ppd.daemon.syntax_preflight_diagnostics import (
    SMALLER_NEXT_ATTEMPT_GUIDANCE,
    SyntaxPreflightFailure,
    repeated_syntax_preflight_diagnostics,
)


def test_repeated_syntax_preflight_diagnostic_records_required_context():
    failures = [
        SyntaxPreflightFailure(
            target_task="checkbox-40",
            failing_file="ppd/daemon/syntax_preflight_diagnostics.py",
            validation_command=(
                "python3",
                "-m",
                "py_compile",
                "ppd/daemon/syntax_preflight_diagnostics.py",
            ),
            summary="line 80: malformed Python expression",
        ),
        SyntaxPreflightFailure(
            target_task="checkbox-40",
            failing_file="ppd/daemon/syntax_preflight_diagnostics.py",
            validation_command=(
                "python3",
                "-m",
                "py_compile",
                "ppd/daemon/syntax_preflight_diagnostics.py",
            ),
            summary="line 81: malformed Python expression",
        ),
    ]

    diagnostics = repeated_syntax_preflight_diagnostics(failures)

    assert diagnostics == [
        {
            "kind": "repeated_syntax_preflight_failure",
            "target_task": "checkbox-40",
            "failing_file": "ppd/daemon/syntax_preflight_diagnostics.py",
            "validation_command": [
                "python3",
                "-m",
                "py_compile",
                "ppd/daemon/syntax_preflight_diagnostics.py",
            ],
            "failure_count": 2,
            "latest_summary": "line 81: malformed Python expression",
            "guidance": SMALLER_NEXT_ATTEMPT_GUIDANCE,
        }
    ]


def test_single_syntax_preflight_failure_is_not_reported_as_repeated():
    failures = [
        SyntaxPreflightFailure(
            target_task="checkbox-40",
            failing_file="ppd/daemon/syntax_preflight_diagnostics.py",
            validation_command=(
                "python3",
                "-m",
                "py_compile",
                "ppd/daemon/syntax_preflight_diagnostics.py",
            ),
            summary="line 80: malformed Python expression",
        )
    ]

    assert repeated_syntax_preflight_diagnostics(failures) == []


def test_diagnostics_do_not_include_worker_selection_fields():
    failures = [
        SyntaxPreflightFailure(
            target_task="checkbox-40",
            failing_file="ppd/daemon/syntax_preflight_diagnostics.py",
            validation_command=("python3", "-m", "py_compile", "ppd/daemon/syntax_preflight_diagnostics.py"),
        ),
        SyntaxPreflightFailure(
            target_task="checkbox-40",
            failing_file="ppd/daemon/syntax_preflight_diagnostics.py",
            validation_command=("python3", "-m", "py_compile", "ppd/daemon/syntax_preflight_diagnostics.py"),
        ),
    ]

    diagnostic = repeated_syntax_preflight_diagnostics(failures)[0]

    assert "selected_task" not in diagnostic
    assert "worker" not in diagnostic
    assert "priority" not in diagnostic
    assert "score" not in diagnostic

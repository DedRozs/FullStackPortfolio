"""
End-to-end tests for ticket-cli.py.
Tests full user workflows spanning multiple subcommands in sequence.
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess

import pytest

WORKSPACE = pathlib.Path(__file__).resolve().parents[3]
PYTHON = WORKSPACE / ".venv" / "Scripts" / "python.exe"
SCRIPT = WORKSPACE / "knowledge-base" / "scripts" / "ticket-cli.py"
QA_PARITY_SCRIPT = WORKSPACE / "knowledge-base" / "scripts" / "qa-field-parity-check.py"


def run_cli(args: list, cwd: pathlib.Path, env_extra: dict | None = None) -> subprocess.CompletedProcess:
    env = {**os.environ, "TICKET_BACKEND": "internal"}
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [str(PYTHON), str(SCRIPT)] + [str(a) for a in args],
        capture_output=True,
        text=True,
        cwd=str(cwd),
        env=env,
    )


def init_project(cwd: pathlib.Path, project_key: str = "QATEST") -> None:
    result = run_cli(
        ["init-project", "--project-key", project_key, "--display-name", "QA Test"],
        cwd=cwd,
    )
    assert result.returncode == 0, f"init-project failed: {result.stderr}"


def create_issue(
    cwd: pathlib.Path,
    project_key: str = "QATEST",
    issue_type: str = "Story",
    summary: str = "Test issue",
) -> dict:
    result = run_cli(
        ["create", "--project-key", project_key, "--type", issue_type, "--summary", summary],
        cwd=cwd,
    )
    assert result.returncode == 0, f"create failed: {result.stderr}"
    return json.loads(result.stdout)


# ---------------------------------------------------------------------------
# E2E: Full story lifecycle
# ---------------------------------------------------------------------------


class TestStoryLifecycle:
    """
    Full story lifecycle: create -> start progress -> close -> search for closed.
    Verifies that the state machine, persistence, and search all work end-to-end.
    """

    def test_story_lifecycle_create_to_close(self, tmp_path):
        # 1. Init project
        init_project(tmp_path)

        # 2. Create story
        story = create_issue(tmp_path, issue_type="Story", summary="Implement feature X")
        assert story["status"] == "Open"
        key = story["key"]

        # 3. Start progress
        result = run_cli(["transition", key, "Start Progress"], cwd=tmp_path)
        assert result.returncode == 0
        in_progress = json.loads(result.stdout)
        assert in_progress["status"] == "In Progress"

        # 4. Submit for review
        result = run_cli(["transition", key, "Submit for Review"], cwd=tmp_path)
        assert result.returncode == 0
        in_review = json.loads(result.stdout)
        assert in_review["status"] == "In Review"

        # 5. Approve (Done)
        result = run_cli(["transition", key, "Approve"], cwd=tmp_path)
        assert result.returncode == 0
        done = json.loads(result.stdout)
        assert done["status"] == "Done"

        # 6. Close
        result = run_cli(["transition", key, "Close"], cwd=tmp_path)
        assert result.returncode == 0
        closed = json.loads(result.stdout)
        assert closed["status"] == "Closed"

        # 7. Verify transition history has all steps
        get_result = run_cli(["get", key], cwd=tmp_path)
        final = json.loads(get_result.stdout)
        assert len(final["transition_history"]) == 4

        # 8. Search for closed issues
        search_result = run_cli(["search", "--jql", "status = Closed"], cwd=tmp_path)
        assert search_result.returncode == 0
        closed_issues = json.loads(search_result.stdout)
        closed_keys = [i["key"] for i in closed_issues]
        assert key in closed_keys

    def test_search_for_closed_excludes_open(self, tmp_path):
        init_project(tmp_path)
        create_issue(tmp_path, summary="Open story")
        story2 = create_issue(tmp_path, summary="Will be closed")

        # Close story2
        key2 = story2["key"]
        run_cli(["transition", key2, "Start Progress"], cwd=tmp_path)
        run_cli(["transition", key2, "Submit for Review"], cwd=tmp_path)
        run_cli(["transition", key2, "Approve"], cwd=tmp_path)
        run_cli(["transition", key2, "Close"], cwd=tmp_path)

        # Search for closed - should only return QATEST-2
        result = run_cli(["search", "--jql", "status = Closed"], cwd=tmp_path)
        closed = json.loads(result.stdout)
        closed_keys = [i["key"] for i in closed]
        assert key2 in closed_keys
        assert "QATEST-1" not in closed_keys


# ---------------------------------------------------------------------------
# E2E: Epic linking workflow
# ---------------------------------------------------------------------------


class TestEpicLinking:
    """
    Epic linking: create epic -> create story -> set-epic-link -> list-epic-children.
    Verifies the full epic-child relationship lifecycle.
    """

    def test_epic_link_workflow(self, tmp_path):
        init_project(tmp_path)

        # 1. Create an epic
        epic = create_issue(tmp_path, issue_type="Epic", summary="Q2 Release Epic")
        epic_key = epic["key"]
        assert epic["issue_type"] == "Epic"

        # 2. Create two stories
        story1 = create_issue(tmp_path, issue_type="Story", summary="Feature A")
        story2 = create_issue(tmp_path, issue_type="Story", summary="Feature B")
        story1_key = story1["key"]
        story2_key = story2["key"]

        # 3. Link both stories to the epic
        link1 = run_cli(["set-epic-link", story1_key, epic_key], cwd=tmp_path)
        assert link1.returncode == 0
        updated1 = json.loads(link1.stdout)
        assert updated1["epic_link"] == epic_key

        link2 = run_cli(["set-epic-link", story2_key, epic_key], cwd=tmp_path)
        assert link2.returncode == 0

        # 4. list-epic-children should return both stories
        children_result = run_cli(["list-epic-children", epic_key], cwd=tmp_path)
        assert children_result.returncode == 0
        children = json.loads(children_result.stdout)
        child_keys = [c["key"] for c in children]
        assert story1_key in child_keys
        assert story2_key in child_keys
        # Epic itself should NOT be in children
        assert epic_key not in child_keys

    def test_set_epic_link_on_non_epic_fails(self, tmp_path):
        init_project(tmp_path)
        story1 = create_issue(tmp_path, issue_type="Story", summary="Story 1")
        story2 = create_issue(tmp_path, issue_type="Story", summary="Story 2")

        # Attempt to link story1 as an "epic" of story2 - should fail
        result = run_cli(["set-epic-link", story2["key"], story1["key"]], cwd=tmp_path)
        assert result.returncode == 1

    def test_list_epic_children_empty_when_none_linked(self, tmp_path):
        init_project(tmp_path)
        epic = create_issue(tmp_path, issue_type="Epic", summary="Empty epic")
        children_result = run_cli(["list-epic-children", epic["key"]], cwd=tmp_path)
        assert children_result.returncode == 0
        children = json.loads(children_result.stdout)
        assert children == []


# ---------------------------------------------------------------------------
# E2E: Field parity check script
# ---------------------------------------------------------------------------


class TestFieldParityCheck:
    """
    Verify that the qa-field-parity-check.py script exits 0 on the real manifest.
    """

    def test_field_parity_script_exits_0(self):
        result = subprocess.run(
            [str(PYTHON), str(QA_PARITY_SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(WORKSPACE),
        )
        assert result.returncode == 0, (
            f"qa-field-parity-check.py exited {result.returncode}.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_field_parity_script_prints_table(self):
        result = subprocess.run(
            [str(PYTHON), str(QA_PARITY_SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(WORKSPACE),
        )
        assert result.returncode == 0
        # Should print the header line
        assert "internal_field" in result.stdout
        assert "parity" in result.stdout
        # Should print a summary line
        assert "Total:" in result.stdout


# ---------------------------------------------------------------------------
# E2E: Reopen workflow (Closed -> Open)
# ---------------------------------------------------------------------------


class TestReopenWorkflow:
    def test_closed_issue_can_be_reopened(self, tmp_path):
        init_project(tmp_path)
        story = create_issue(tmp_path, summary="Reopen me")
        key = story["key"]

        # Close directly (Open -> Closed is a valid transition)
        close_result = run_cli(["transition", key, "Close"], cwd=tmp_path)
        assert close_result.returncode == 0
        closed_issue = json.loads(close_result.stdout)
        assert closed_issue["status"] == "Closed"

        # Reopen
        reopen_result = run_cli(["transition", key, "Reopen"], cwd=tmp_path)
        assert reopen_result.returncode == 0
        reopened = json.loads(reopen_result.stdout)
        assert reopened["status"] == "Open"

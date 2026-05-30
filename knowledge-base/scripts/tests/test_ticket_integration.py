"""
Integration tests for ticket-cli.py.
All tests invoke the CLI via subprocess with a temporary cwd so file I/O
is fully isolated from the real ticket store.
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
        [
            "create",
            "--project-key", project_key,
            "--type", issue_type,
            "--summary", summary,
        ],
        cwd=cwd,
    )
    assert result.returncode == 0, f"create failed: {result.stderr}"
    return json.loads(result.stdout)


# ---------------------------------------------------------------------------
# Test: init-project
# ---------------------------------------------------------------------------


class TestInitProject:
    def test_creates_project_and_workflow_files(self, tmp_path):
        result = run_cli(
            ["init-project", "--project-key", "QATEST", "--display-name", "QA Test"],
            cwd=tmp_path,
        )
        assert result.returncode == 0
        project_file = tmp_path / "knowledge-base" / "plans" / "tickets" / "QATEST" / "project.json"
        workflow_file = tmp_path / "knowledge-base" / "plans" / "tickets" / "QATEST" / "workflow.json"
        assert project_file.exists(), "project.json not created"
        assert workflow_file.exists(), "workflow.json not created"

    def test_output_contains_project_key(self, tmp_path):
        result = run_cli(
            ["init-project", "--project-key", "QATEST", "--display-name", "QA Test"],
            cwd=tmp_path,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["project_key"] == "QATEST"
        assert data["status"] == "initialized"

    def test_duplicate_init_returns_exit_1(self, tmp_path):
        init_project(tmp_path)
        result = run_cli(
            ["init-project", "--project-key", "QATEST", "--display-name", "QA Test"],
            cwd=tmp_path,
        )
        assert result.returncode == 1

    def test_invalid_project_key_returns_exit_1(self, tmp_path):
        result = run_cli(
            ["init-project", "--project-key", "qatest", "--display-name", "lowercase"],
            cwd=tmp_path,
        )
        assert result.returncode == 1


# ---------------------------------------------------------------------------
# Test: create
# ---------------------------------------------------------------------------


class TestCreate:
    def test_first_issue_gets_key_1(self, tmp_path):
        init_project(tmp_path)
        issue = create_issue(tmp_path, summary="First issue")
        assert issue["key"] == "QATEST-1"
        assert issue["status"] == "Open"

    def test_sequential_keys(self, tmp_path):
        init_project(tmp_path)
        i1 = create_issue(tmp_path, summary="First")
        i2 = create_issue(tmp_path, summary="Second")
        assert i1["key"] == "QATEST-1"
        assert i2["key"] == "QATEST-2"

    def test_issue_has_correct_fields(self, tmp_path):
        init_project(tmp_path)
        issue = create_issue(tmp_path, issue_type="Bug", summary="A bug")
        assert issue["issue_type"] == "Bug"
        assert issue["summary"] == "A bug"
        assert issue["project_key"] == "QATEST"
        assert "created_at" in issue
        assert "updated_at" in issue
        assert issue["comments"] == []
        assert issue["worklogs"] == []
        assert issue["labels"] == []
        assert issue["links"] == []
        assert issue["transition_history"] == []

    def test_create_without_init_returns_exit_1(self, tmp_path):
        result = run_cli(
            ["create", "--project-key", "QATEST", "--type", "Story", "--summary", "Orphan"],
            cwd=tmp_path,
        )
        assert result.returncode == 1


# ---------------------------------------------------------------------------
# Test: get
# ---------------------------------------------------------------------------


class TestGet:
    def test_get_returns_issue(self, tmp_path):
        init_project(tmp_path)
        create_issue(tmp_path, summary="Findable issue")
        result = run_cli(["get", "QATEST-1"], cwd=tmp_path)
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["key"] == "QATEST-1"
        assert data["summary"] == "Findable issue"

    def test_get_nonexistent_returns_exit_1(self, tmp_path):
        init_project(tmp_path)
        result = run_cli(["get", "QATEST-999"], cwd=tmp_path)
        assert result.returncode == 1

    def test_get_invalid_key_returns_exit_1(self, tmp_path):
        result = run_cli(["get", "../../../../etc/passwd"], cwd=tmp_path)
        assert result.returncode == 1


# ---------------------------------------------------------------------------
# Test: update
# ---------------------------------------------------------------------------


class TestUpdate:
    def test_update_summary(self, tmp_path):
        init_project(tmp_path)
        create_issue(tmp_path, summary="Original")
        result = run_cli(
            ["update", "QATEST-1", "--summary", "Updated Summary"],
            cwd=tmp_path,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["summary"] == "Updated Summary"

    def test_update_priority(self, tmp_path):
        init_project(tmp_path)
        create_issue(tmp_path, summary="Priority test")
        result = run_cli(
            ["update", "QATEST-1", "--priority", "High"],
            cwd=tmp_path,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["priority"] == "High"

    def test_update_no_fields_returns_exit_1(self, tmp_path):
        init_project(tmp_path)
        create_issue(tmp_path, summary="No update")
        result = run_cli(["update", "QATEST-1"], cwd=tmp_path)
        assert result.returncode == 1


# ---------------------------------------------------------------------------
# Test: transition
# ---------------------------------------------------------------------------


class TestTransition:
    def test_valid_transition_updates_status(self, tmp_path):
        init_project(tmp_path)
        create_issue(tmp_path, summary="Transition test")
        result = run_cli(["transition", "QATEST-1", "Start Progress"], cwd=tmp_path)
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["status"] == "In Progress"

    def test_transition_appends_history(self, tmp_path):
        init_project(tmp_path)
        create_issue(tmp_path, summary="History test")
        run_cli(["transition", "QATEST-1", "Start Progress"], cwd=tmp_path)
        result = run_cli(["get", "QATEST-1"], cwd=tmp_path)
        data = json.loads(result.stdout)
        assert len(data["transition_history"]) == 1
        assert data["transition_history"][0]["from_status"] == "Open"
        assert data["transition_history"][0]["to_status"] == "In Progress"
        assert data["transition_history"][0]["transition_name"] == "Start Progress"

    def test_invalid_transition_returns_exit_1(self, tmp_path):
        init_project(tmp_path)
        create_issue(tmp_path, summary="Invalid transition")
        result = run_cli(["transition", "QATEST-1", "Approve"], cwd=tmp_path)
        assert result.returncode == 1


# ---------------------------------------------------------------------------
# Test: add-comment / list-comments
# ---------------------------------------------------------------------------


class TestComments:
    def test_add_and_list_comments(self, tmp_path):
        init_project(tmp_path)
        create_issue(tmp_path, summary="Comment test")
        add_result = run_cli(
            ["add-comment", "QATEST-1", "--author", "alice", "--body", "Hello world"],
            cwd=tmp_path,
        )
        assert add_result.returncode == 0

        list_result = run_cli(["list-comments", "QATEST-1"], cwd=tmp_path)
        assert list_result.returncode == 0
        comments = json.loads(list_result.stdout)
        assert len(comments) == 1
        assert comments[0]["author"] == "alice"
        assert comments[0]["body"] == "Hello world"

    def test_multiple_comments_appended(self, tmp_path):
        init_project(tmp_path)
        create_issue(tmp_path, summary="Multi-comment")
        run_cli(["add-comment", "QATEST-1", "--author", "alice", "--body", "First"], cwd=tmp_path)
        run_cli(["add-comment", "QATEST-1", "--author", "bob", "--body", "Second"], cwd=tmp_path)
        list_result = run_cli(["list-comments", "QATEST-1"], cwd=tmp_path)
        comments = json.loads(list_result.stdout)
        assert len(comments) == 2


# ---------------------------------------------------------------------------
# Test: add-worklog / list-worklogs
# ---------------------------------------------------------------------------


class TestWorklogs:
    def test_add_and_list_worklogs(self, tmp_path):
        init_project(tmp_path)
        create_issue(tmp_path, summary="Worklog test")
        add_result = run_cli(
            ["add-worklog", "QATEST-1", "--author", "bob", "--time-spent", "2h"],
            cwd=tmp_path,
        )
        assert add_result.returncode == 0

        list_result = run_cli(["list-worklogs", "QATEST-1"], cwd=tmp_path)
        assert list_result.returncode == 0
        worklogs = json.loads(list_result.stdout)
        assert len(worklogs) == 1
        assert worklogs[0]["author"] == "bob"
        assert worklogs[0]["time_spent"] == "2h"


# ---------------------------------------------------------------------------
# Test: create-link / list-links
# ---------------------------------------------------------------------------


class TestLinks:
    def test_create_and_list_links(self, tmp_path):
        init_project(tmp_path)
        create_issue(tmp_path, summary="Source issue")
        create_issue(tmp_path, summary="Target issue")

        link_result = run_cli(
            ["create-link", "QATEST-1", "QATEST-2", "--link-type", "relates-to"],
            cwd=tmp_path,
        )
        assert link_result.returncode == 0

        list_result = run_cli(["list-links", "QATEST-1"], cwd=tmp_path)
        assert list_result.returncode == 0
        links = json.loads(list_result.stdout)
        assert len(links) == 1
        assert links[0]["target_key"] == "QATEST-2"
        assert links[0]["link_type"] == "relates-to"

    def test_link_to_nonexistent_target_returns_exit_1(self, tmp_path):
        init_project(tmp_path)
        create_issue(tmp_path, summary="Source only")
        result = run_cli(
            ["create-link", "QATEST-1", "QATEST-999", "--link-type", "blocks"],
            cwd=tmp_path,
        )
        assert result.returncode == 1


# ---------------------------------------------------------------------------
# Test: search
# ---------------------------------------------------------------------------


class TestSearch:
    def test_search_by_status(self, tmp_path):
        init_project(tmp_path)
        create_issue(tmp_path, summary="Open issue")
        create_issue(tmp_path, summary="In progress issue")
        run_cli(["transition", "QATEST-2", "Start Progress"], cwd=tmp_path)

        result = run_cli(["search", "--jql", "status = Open"], cwd=tmp_path)
        assert result.returncode == 0
        issues = json.loads(result.stdout)
        keys = [i["key"] for i in issues]
        assert "QATEST-1" in keys
        assert "QATEST-2" not in keys

    def test_search_order_by_key_asc(self, tmp_path):
        init_project(tmp_path)
        create_issue(tmp_path, summary="First")
        create_issue(tmp_path, summary="Second")
        create_issue(tmp_path, summary="Third")

        result = run_cli(["search", "--jql", "project = QATEST ORDER BY key ASC"], cwd=tmp_path)
        assert result.returncode == 0
        issues = json.loads(result.stdout)
        keys = [i["key"] for i in issues]
        assert keys == sorted(keys)

    def test_search_no_match_returns_empty_list(self, tmp_path):
        init_project(tmp_path)
        create_issue(tmp_path, summary="Open issue")
        result = run_cli(["search", "--jql", "status = Closed"], cwd=tmp_path)
        assert result.returncode == 0
        issues = json.loads(result.stdout)
        assert issues == []


# ---------------------------------------------------------------------------
# Test: list-issues
# ---------------------------------------------------------------------------


class TestListIssues:
    def test_list_issues_with_project_filter(self, tmp_path):
        init_project(tmp_path)
        create_issue(tmp_path, summary="Issue one")
        create_issue(tmp_path, summary="Issue two")

        result = run_cli(["list-issues", "--project", "QATEST"], cwd=tmp_path)
        assert result.returncode == 0
        issues = json.loads(result.stdout)
        assert len(issues) == 2
        # Verify sorted by key
        keys = [i["key"] for i in issues]
        assert keys == ["QATEST-1", "QATEST-2"]

    def test_list_issues_with_status_filter(self, tmp_path):
        init_project(tmp_path)
        create_issue(tmp_path, summary="Open issue")
        create_issue(tmp_path, summary="In progress issue")
        run_cli(["transition", "QATEST-2", "Start Progress"], cwd=tmp_path)

        result = run_cli(
            ["list-issues", "--project", "QATEST", "--status", "Open"],
            cwd=tmp_path,
        )
        assert result.returncode == 0
        issues = json.loads(result.stdout)
        assert len(issues) == 1
        assert issues[0]["key"] == "QATEST-1"


# ---------------------------------------------------------------------------
# Test: add-label / remove-label / list-labels
# ---------------------------------------------------------------------------


class TestLabels:
    def test_add_list_remove_labels_round_trip(self, tmp_path):
        init_project(tmp_path)
        create_issue(tmp_path, summary="Label test")

        # add
        add_result = run_cli(["add-label", "QATEST-1", "urgent"], cwd=tmp_path)
        assert add_result.returncode == 0

        # list - should contain "urgent"
        list_result = run_cli(["list-labels", "QATEST-1"], cwd=tmp_path)
        assert list_result.returncode == 0
        labels = json.loads(list_result.stdout)
        assert "urgent" in labels

        # remove
        remove_result = run_cli(["remove-label", "QATEST-1", "urgent"], cwd=tmp_path)
        assert remove_result.returncode == 0

        # list - should be empty
        list_result2 = run_cli(["list-labels", "QATEST-1"], cwd=tmp_path)
        labels2 = json.loads(list_result2.stdout)
        assert labels2 == []

    def test_add_label_idempotent(self, tmp_path):
        init_project(tmp_path)
        create_issue(tmp_path, summary="Idempotent label test")
        run_cli(["add-label", "QATEST-1", "urgent"], cwd=tmp_path)
        run_cli(["add-label", "QATEST-1", "urgent"], cwd=tmp_path)
        list_result = run_cli(["list-labels", "QATEST-1"], cwd=tmp_path)
        labels = json.loads(list_result.stdout)
        assert labels.count("urgent") == 1

    def test_remove_nonexistent_label_returns_exit_1(self, tmp_path):
        init_project(tmp_path)
        create_issue(tmp_path, summary="No label")
        result = run_cli(["remove-label", "QATEST-1", "nonexistent"], cwd=tmp_path)
        assert result.returncode == 1


# ---------------------------------------------------------------------------
# Test: invalid input guards (OWASP A03)
# ---------------------------------------------------------------------------


class TestInputGuards:
    def test_path_traversal_issue_key_rejected(self, tmp_path):
        result = run_cli(["get", "../../../../etc/passwd"], cwd=tmp_path)
        assert result.returncode == 1

    def test_shell_metachar_issue_key_rejected(self, tmp_path):
        result = run_cli(["get", "PROJ-1; rm -rf /"], cwd=tmp_path)
        assert result.returncode == 1

    def test_lowercase_project_key_rejected(self, tmp_path):
        result = run_cli(
            ["init-project", "--project-key", "lowercase", "--display-name", "Bad"],
            cwd=tmp_path,
        )
        assert result.returncode == 1

    def test_path_traversal_project_key_rejected(self, tmp_path):
        result = run_cli(
            ["init-project", "--project-key", "../../etc", "--display-name", "Bad"],
            cwd=tmp_path,
        )
        assert result.returncode == 1

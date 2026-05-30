"""Unit tests for ticket-cli.py - domain logic in isolation."""
from __future__ import annotations

import importlib.util
import pathlib
import re
import sys
import unittest.mock

import pytest

# ---------------------------------------------------------------------------
# Module import via importlib (hyphenated filename)
# ---------------------------------------------------------------------------

_CLI_PATH = pathlib.Path(__file__).parent.parent / "ticket-cli.py"
spec = importlib.util.spec_from_file_location("ticket_cli", _CLI_PATH)
ticket_cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ticket_cli)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def _make_issue(
    key: str = "QATEST-1",
    project_key: str = "QATEST",
    status: str = "Open",
    issue_type: str = "Story",
    assignee: str = "alice",
    labels: list = None,
    created_at: str = "2026-01-01T00:00:00Z",
    updated_at: str = "2026-01-02T00:00:00Z",
) -> dict:
    return {
        "key": key,
        "project_key": project_key,
        "status": status,
        "issue_type": issue_type,
        "assignee": assignee,
        "labels": labels if labels is not None else [],
        "created_at": created_at,
        "updated_at": updated_at,
        "transition_history": [],
        "summary": "Test issue",
        "description": "",
        "comments": [],
        "links": [],
        "worklogs": [],
        "priority": "Medium",
        "epic_link": "",
        "import_source": "",
    }


# ---------------------------------------------------------------------------
# 1. validate_issue_key
# ---------------------------------------------------------------------------


class TestValidateIssueKey:
    def test_valid_standard_key(self):
        assert ticket_cli.validate_issue_key("PROJ-1") == "PROJ-1"

    def test_valid_long_project_key(self):
        assert ticket_cli.validate_issue_key("QATEST-123") == "QATEST-123"

    def test_valid_two_char_project_key(self):
        assert ticket_cli.validate_issue_key("AB-1") == "AB-1"

    def test_valid_zero_sequence(self):
        # PROJ-0 is valid: regex is ^[A-Z][A-Z0-9]+-[0-9]+$ and 0 is a digit
        assert ticket_cli.validate_issue_key("PROJ-0") == "PROJ-0"

    def test_valid_alphanumeric_project_part(self):
        assert ticket_cli.validate_issue_key("A1B-42") == "A1B-42"

    def test_invalid_empty_string(self):
        with pytest.raises(SystemExit) as exc_info:
            ticket_cli.validate_issue_key("")
        assert exc_info.value.code == 1

    def test_invalid_lowercase_project(self):
        with pytest.raises(SystemExit) as exc_info:
            ticket_cli.validate_issue_key("proj-1")
        assert exc_info.value.code == 1

    def test_invalid_no_number(self):
        with pytest.raises(SystemExit) as exc_info:
            ticket_cli.validate_issue_key("PROJ")
        assert exc_info.value.code == 1

    def test_invalid_trailing_hyphen_no_number(self):
        with pytest.raises(SystemExit) as exc_info:
            ticket_cli.validate_issue_key("PROJ-")
        assert exc_info.value.code == 1

    def test_invalid_starts_with_digit(self):
        with pytest.raises(SystemExit) as exc_info:
            ticket_cli.validate_issue_key("1PROJ-1")
        assert exc_info.value.code == 1

    def test_invalid_double_hyphen(self):
        with pytest.raises(SystemExit) as exc_info:
            ticket_cli.validate_issue_key("PROJ--1")
        assert exc_info.value.code == 1

    def test_invalid_path_traversal(self):
        with pytest.raises(SystemExit) as exc_info:
            ticket_cli.validate_issue_key("../../../../etc/passwd")
        assert exc_info.value.code == 1

    def test_invalid_shell_injection(self):
        with pytest.raises(SystemExit) as exc_info:
            ticket_cli.validate_issue_key("PROJ-1; rm -rf")
        assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# 2. validate_project_key
# ---------------------------------------------------------------------------


class TestValidateProjectKey:
    def test_valid_simple(self):
        assert ticket_cli.validate_project_key("PROJ") == "PROJ"

    def test_valid_long(self):
        assert ticket_cli.validate_project_key("QATEST") == "QATEST"

    def test_valid_two_char_minimum(self):
        # Regex is ^[A-Z][A-Z0-9]+$ - requires at least 2 chars
        assert ticket_cli.validate_project_key("AB") == "AB"

    def test_valid_alphanumeric(self):
        assert ticket_cli.validate_project_key("ABC123") == "ABC123"

    def test_invalid_single_char(self):
        # Regex requires [A-Z][A-Z0-9]+ - at least 2 characters
        with pytest.raises(SystemExit) as exc_info:
            ticket_cli.validate_project_key("A")
        assert exc_info.value.code == 1

    def test_invalid_empty(self):
        with pytest.raises(SystemExit) as exc_info:
            ticket_cli.validate_project_key("")
        assert exc_info.value.code == 1

    def test_invalid_lowercase(self):
        with pytest.raises(SystemExit) as exc_info:
            ticket_cli.validate_project_key("proj")
        assert exc_info.value.code == 1

    def test_invalid_starts_with_digit(self):
        with pytest.raises(SystemExit) as exc_info:
            ticket_cli.validate_project_key("1PROJ")
        assert exc_info.value.code == 1

    def test_invalid_contains_hyphen(self):
        with pytest.raises(SystemExit) as exc_info:
            ticket_cli.validate_project_key("PROJ-1")
        assert exc_info.value.code == 1

    def test_invalid_path_traversal(self):
        with pytest.raises(SystemExit) as exc_info:
            ticket_cli.validate_project_key("../../../../etc")
        assert exc_info.value.code == 1

    def test_invalid_contains_space(self):
        with pytest.raises(SystemExit) as exc_info:
            ticket_cli.validate_project_key("PROJ KEY")
        assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# 3. JqlParser.parse_and_evaluate
# ---------------------------------------------------------------------------


class TestJqlParser:
    def setup_method(self):
        self.parser = ticket_cli.JqlParser()
        self.issues = [
            _make_issue(
                key="QATEST-1",
                project_key="QATEST",
                status="Open",
                issue_type="Bug",
                assignee="alice",
                labels=["bug", "urgent"],
                created_at="2026-01-01T00:00:00Z",
                updated_at="2026-01-02T00:00:00Z",
            ),
            _make_issue(
                key="QATEST-2",
                project_key="QATEST",
                status="In Progress",
                issue_type="Story",
                assignee="bob",
                labels=["feature"],
                created_at="2026-01-03T00:00:00Z",
                updated_at="2026-01-04T00:00:00Z",
            ),
            _make_issue(
                key="OTHER-1",
                project_key="OTHER",
                status="Open",
                issue_type="Story",
                assignee="carol",
                labels=["bug"],
                created_at="2026-01-05T00:00:00Z",
                updated_at="2026-01-06T00:00:00Z",
            ),
        ]

    def test_simple_equality_project(self):
        result = self.parser.parse_and_evaluate("project = QATEST", self.issues)
        assert len(result) == 2
        keys = {i["key"] for i in result}
        assert keys == {"QATEST-1", "QATEST-2"}

    def test_and_combination(self):
        result = self.parser.parse_and_evaluate(
            "project = QATEST AND status = Open", self.issues
        )
        assert len(result) == 1
        assert result[0]["key"] == "QATEST-1"

    def test_order_by_asc(self):
        result = self.parser.parse_and_evaluate(
            "project = QATEST ORDER BY created ASC", self.issues
        )
        assert len(result) == 2
        assert result[0]["key"] == "QATEST-1"
        assert result[1]["key"] == "QATEST-2"

    def test_order_by_desc(self):
        result = self.parser.parse_and_evaluate(
            "project = QATEST ORDER BY created DESC", self.issues
        )
        assert len(result) == 2
        assert result[0]["key"] == "QATEST-2"
        assert result[1]["key"] == "QATEST-1"

    def test_quoted_value(self):
        result = self.parser.parse_and_evaluate(
            'status = "In Progress"', self.issues
        )
        assert len(result) == 1
        assert result[0]["key"] == "QATEST-2"

    def test_label_field_mapping(self):
        # "label" maps to the "labels" list field
        result = self.parser.parse_and_evaluate("label = bug", self.issues)
        assert len(result) == 2
        keys = {i["key"] for i in result}
        assert keys == {"QATEST-1", "OTHER-1"}

    def test_empty_results_when_no_match(self):
        result = self.parser.parse_and_evaluate(
            "project = NONEXISTENT", self.issues
        )
        assert result == []


# ---------------------------------------------------------------------------
# 4. TransitionService.transition
# ---------------------------------------------------------------------------


class TestTransitionService:
    def _open_issue(self) -> dict:
        return _make_issue(
            key="QATEST-10",
            project_key="QATEST",
            status="Open",
        )

    def test_valid_transition_sets_status(self):
        issue = self._open_issue()
        with unittest.mock.patch.object(
            ticket_cli.JsonWorkflowRepository,
            "load",
            return_value=ticket_cli.DEFAULT_WORKFLOW,
        ):
            updated = ticket_cli.TransitionService.transition(issue, "Start Progress")
        assert updated["status"] == "In Progress"

    def test_valid_transition_appends_history(self):
        issue = self._open_issue()
        with unittest.mock.patch.object(
            ticket_cli.JsonWorkflowRepository,
            "load",
            return_value=ticket_cli.DEFAULT_WORKFLOW,
        ):
            updated = ticket_cli.TransitionService.transition(issue, "Start Progress")
        assert len(updated["transition_history"]) == 1
        entry = updated["transition_history"][0]
        assert entry["from_status"] == "Open"
        assert entry["to_status"] == "In Progress"
        assert entry["transition_name"] == "Start Progress"

    def test_valid_transition_returns_same_dict(self):
        issue = self._open_issue()
        with unittest.mock.patch.object(
            ticket_cli.JsonWorkflowRepository,
            "load",
            return_value=ticket_cli.DEFAULT_WORKFLOW,
        ):
            result = ticket_cli.TransitionService.transition(issue, "Start Progress")
        assert result is issue

    def test_invalid_transition_exits_1(self):
        issue = self._open_issue()
        with unittest.mock.patch.object(
            ticket_cli.JsonWorkflowRepository,
            "load",
            return_value=ticket_cli.DEFAULT_WORKFLOW,
        ):
            with pytest.raises(SystemExit) as exc_info:
                ticket_cli.TransitionService.transition(issue, "Approve")
        assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# 5. utcnow_iso
# ---------------------------------------------------------------------------


class TestUtcnowIso:
    def test_returns_string(self):
        result = ticket_cli.utcnow_iso()
        assert isinstance(result, str)

    def test_ends_with_z(self):
        result = ticket_cli.utcnow_iso()
        assert result.endswith("Z")

    def test_matches_iso8601_pattern(self):
        result = ticket_cli.utcnow_iso()
        assert _ISO_RE.match(result), f"Unexpected format: {result!r}"

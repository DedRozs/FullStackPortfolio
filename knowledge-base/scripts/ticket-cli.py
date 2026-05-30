#!/usr/bin/env python3
"""
ticket-cli.py - Internal Ticketing System CLI

Single entry point for the internal ticket backend.
Invocation: .venv/Scripts/python.exe knowledge-base/scripts/ticket-cli.py <subcommand> [args]

IMPORTANT - Single writer only:
  Concurrent writes to the same ProjectKey directory will corrupt the
  TicketStore. At most one process may write to a given ProjectKey at a time.

Exit codes: 0=success, 1=user error, 2=internal error.
stdout: JSON only. stderr: human-readable text only.
TICKET_BACKEND is read from the environment; never passed as a CLI argument.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import pathlib
import re
import sys

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TICKETS_ROOT: pathlib.Path = pathlib.Path("knowledge-base") / "plans" / "tickets"

ISSUE_KEY_RE = re.compile(r"^[A-Z][A-Z0-9]+-[0-9]+$")
PROJECT_KEY_RE = re.compile(r"^[A-Z][A-Z0-9]+$")

VALID_ISSUE_TYPES = frozenset({"Bug", "Chore", "Epic", "Spike", "Story"})
VALID_PRIORITIES = frozenset({"High", "Highest", "Low", "Lowest", "Medium"})
VALID_LINK_TYPES = frozenset(
    {"blocks", "clones", "duplicates", "is-child-of", "relates-to"}
)
IMMUTABLE_FIELDS = frozenset(
    {"created_at", "import_source", "issue_type", "key", "project_key", "status"}
)

DEFAULT_WORKFLOW: dict = {
    "initial_status": "Open",
    "statuses": ["Open", "In Progress", "In Review", "Done", "Closed"],
    "transitions": {
        "Closed": [{"name": "Reopen", "target": "Open"}],
        "Done": [
            {"name": "Close", "target": "Closed"},
            {"name": "Reopen", "target": "Open"},
        ],
        "In Progress": [
            {"name": "Done", "target": "Done"},
            {"name": "Reopen", "target": "Open"},
            {"name": "Submit for Review", "target": "In Review"},
        ],
        "In Review": [
            {"name": "Approve", "target": "Done"},
            {"name": "Done", "target": "Done"},
            {"name": "Request Changes", "target": "In Progress"},
        ],
        "Open": [
            {"name": "Close", "target": "Closed"},
            {"name": "Done", "target": "Done"},
            {"name": "Start Progress", "target": "In Progress"},
        ],
    },
}

# ---------------------------------------------------------------------------
# OWASP A03:2021 - path validation
# ---------------------------------------------------------------------------


def validate_issue_key(key: str) -> str:
    if not ISSUE_KEY_RE.match(key):
        print(f"Invalid issue key: {key}", file=sys.stderr)
        sys.exit(1)
    return key


def validate_project_key(key: str) -> str:
    if not PROJECT_KEY_RE.match(key):
        print(f"Invalid project key: {key}", file=sys.stderr)
        sys.exit(1)
    return key


# ---------------------------------------------------------------------------
# Atomic write
# ---------------------------------------------------------------------------


def atomic_write_json(path: pathlib.Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
    os.replace(tmp, path)


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------


def project_dir(project_key: str) -> pathlib.Path:
    return TICKETS_ROOT / project_key


def project_config_path(project_key: str) -> pathlib.Path:
    return project_dir(project_key) / "project.json"


def workflow_config_path(project_key: str) -> pathlib.Path:
    return project_dir(project_key) / "workflow.json"


def issue_file_path(issue_key: str) -> pathlib.Path:
    project_key = issue_key.split("-")[0]
    return project_dir(project_key) / f"{issue_key}.json"


# ---------------------------------------------------------------------------
# Timestamp helper
# ---------------------------------------------------------------------------


def utcnow_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Repository: JsonProjectRepository
# ---------------------------------------------------------------------------


class JsonProjectRepository:
    @staticmethod
    def load(project_key: str) -> dict:
        path = project_config_path(project_key)
        if not path.exists():
            print(
                f"Project not found: {project_key}. Run init-project first.",
                file=sys.stderr,
            )
            sys.exit(1)
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def save(config: dict, project_key: str) -> None:
        atomic_write_json(project_config_path(project_key), config)

    @staticmethod
    def exists(project_key: str) -> bool:
        return project_config_path(project_key).exists()

    @staticmethod
    def next_key(project_key: str) -> str:
        """Read current_sequence, increment, write back atomically, return new key."""
        config = JsonProjectRepository.load(project_key)
        seq = config["current_sequence"] + 1
        config["current_sequence"] = seq
        atomic_write_json(project_config_path(project_key), config)
        return f"{project_key}-{seq}"


# ---------------------------------------------------------------------------
# Repository: JsonWorkflowRepository
# ---------------------------------------------------------------------------


class JsonWorkflowRepository:
    @staticmethod
    def load(project_key: str) -> dict:
        path = workflow_config_path(project_key)
        if not path.exists():
            print(
                f"Workflow config not found for project: {project_key}", file=sys.stderr
            )
            sys.exit(2)
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def validate(config: dict) -> list:
        errors = []
        if "statuses" not in config or not isinstance(config["statuses"], list):
            errors.append("Missing or invalid 'statuses' list")
        if "initial_status" not in config or not isinstance(
            config["initial_status"], str
        ):
            errors.append("Missing or invalid 'initial_status' string")
        if "transitions" not in config or not isinstance(config["transitions"], dict):
            errors.append("Missing or invalid 'transitions' dict")
        return errors


# ---------------------------------------------------------------------------
# Repository: JsonIssueRepository
# ---------------------------------------------------------------------------


class JsonIssueRepository:
    @staticmethod
    def load(issue_key: str) -> dict:
        path = issue_file_path(issue_key)
        if not path.exists():
            print(f"Issue not found: {issue_key}", file=sys.stderr)
            sys.exit(1)
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def save(issue: dict) -> None:
        atomic_write_json(issue_file_path(issue["key"]), issue)

    @staticmethod
    def exists(issue_key: str) -> bool:
        return issue_file_path(issue_key).exists()

    @staticmethod
    def search(project_key: str, filters: dict = None) -> list:
        pdir = project_dir(project_key)
        if not pdir.exists():
            return []
        issues = []
        for f in pdir.iterdir():
            if f.suffix == ".json" and ISSUE_KEY_RE.match(f.stem):
                with open(f, encoding="utf-8") as fh:
                    issue = json.load(fh)
                if filters:
                    if all(issue.get(field) == val for field, val in filters.items()):
                        issues.append(issue)
                else:
                    issues.append(issue)
        return issues

    @staticmethod
    def all_issues() -> list:
        result = []
        if not TICKETS_ROOT.exists():
            return result
        for pdir in TICKETS_ROOT.iterdir():
            if pdir.is_dir() and PROJECT_KEY_RE.match(pdir.name):
                for f in pdir.iterdir():
                    if f.suffix == ".json" and ISSUE_KEY_RE.match(f.stem):
                        with open(f, encoding="utf-8") as fh:
                            result.append(json.load(fh))
        return result


# ---------------------------------------------------------------------------
# Domain service: TransitionService
# ---------------------------------------------------------------------------


class TransitionService:
    @staticmethod
    def transition(issue: dict, transition_name: str) -> dict:
        workflow = JsonWorkflowRepository.load(issue["project_key"])
        current_status = issue["status"]
        allowed = workflow["transitions"].get(current_status, [])

        target = None
        for t in allowed:
            if t["name"] == transition_name:
                target = t["target"]
                break

        if target is None:
            available = [t["name"] for t in allowed]
            print(
                f"Transition '{transition_name}' not allowed from status "
                f"'{current_status}'. Available: {available}",
                file=sys.stderr,
            )
            sys.exit(1)

        now = utcnow_iso()
        issue["transition_history"].append(
            {
                "actor": "system",
                "from_status": current_status,
                "timestamp": now,
                "to_status": target,
                "transition_name": transition_name,
            }
        )
        issue["status"] = target
        issue["updated_at"] = now
        return issue


# ---------------------------------------------------------------------------
# Domain service: JqlParser
# ---------------------------------------------------------------------------

_JQL_FIELD_MAP: dict = {
    "assignee": "assignee",
    "created": "created_at",
    "issuetype": "issue_type",
    "label": "labels",
    "project": "project_key",
    "status": "status",
    "updated": "updated_at",
}

_ORDER_FIELD_MAP: dict = {
    "created": "created_at",
    "issuetype": "issue_type",
    "status": "status",
    "updated": "updated_at",
}


class JqlParser:
    """Parse and evaluate a JQL subset query against a list of issue dicts.

    Supported grammar:
        query      ::= predicates [ORDER BY field (ASC|DESC)]
        predicates ::= predicate (AND predicate)*
        predicate  ::= field = value
                     | field in (value, ...)
                     | field >= date_value
                     | field > date_value
                     | field <= date_value
                     | field < date_value
        field      ::= project | status | issuetype | assignee | label
                     | created | updated
        value      ::= "quoted string" | unquoted_token
    """

    def parse_and_evaluate(self, jql_string: str, issues: list) -> list:
        jql_clean = jql_string.strip()

        order_by = None
        order_match = re.search(
            r"\bORDER\s+BY\s+(\w+)\s+(ASC|DESC)\s*$", jql_clean, re.IGNORECASE
        )
        if order_match:
            raw_field = order_match.group(1).lower()
            direction = order_match.group(2).upper()
            jql_clean = jql_clean[: order_match.start()].strip()
            mapped = _ORDER_FIELD_MAP.get(raw_field, raw_field)
            order_by = (mapped, direction)

        predicates = self._parse_predicates(jql_clean)
        result = [i for i in issues if self._evaluate(predicates, i)]

        if order_by:
            field, direction = order_by
            result.sort(key=lambda i: i.get(field, ""), reverse=(direction == "DESC"))

        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _parse_predicates(self, text: str) -> list:
        parts = re.split(r"\bAND\b", text, flags=re.IGNORECASE)
        predicates = []
        for part in parts:
            part = part.strip()
            if part:
                predicates.append(self._parse_predicate(part))
        return predicates

    def _parse_predicate(self, text: str) -> dict:
        # in operator: field in ("v1", "v2")
        in_match = re.match(
            r"^(\w+)\s+in\s*\(\s*(.*?)\s*\)\s*$", text, re.IGNORECASE
        )
        if in_match:
            raw_field = in_match.group(1).lower()
            values = self._parse_value_list(in_match.group(2))
            return {"field": raw_field, "op": "in", "values": values}

        # comparison operators: >=, >, <=, <
        cmp_match = re.match(r"^(\w+)\s*(>=|>|<=|<)\s*(.+)$", text)
        if cmp_match:
            raw_field = cmp_match.group(1).lower()
            op = cmp_match.group(2)
            value = self._strip_quotes(cmp_match.group(3).strip())
            return {"field": raw_field, "op": op, "value": value}

        # equality: field = value
        eq_match = re.match(r"^(\w+)\s*=\s*(.+)$", text)
        if eq_match:
            raw_field = eq_match.group(1).lower()
            value = self._strip_quotes(eq_match.group(2).strip())
            return {"field": raw_field, "op": "=", "value": value}

        print(f"Unsupported JQL predicate: {text!r}", file=sys.stderr)
        sys.exit(1)

    def _parse_value_list(self, text: str) -> list:
        values = []
        for token in re.findall(r'"([^"]*?)"|\'([^\']*?)\'|([^,\s]+)', text):
            val = token[0] or token[1] or token[2]
            if val:
                values.append(val)
        return values

    def _strip_quotes(self, value: str) -> str:
        if len(value) >= 2 and (
            (value[0] == '"' and value[-1] == '"')
            or (value[0] == "'" and value[-1] == "'")
        ):
            return value[1:-1]
        return value

    def _evaluate(self, predicates: list, issue: dict) -> bool:
        return all(self._eval_predicate(p, issue) for p in predicates)

    def _eval_predicate(self, pred: dict, issue: dict) -> bool:
        raw_field = pred["field"]
        mapped = _JQL_FIELD_MAP.get(raw_field, raw_field)
        op = pred["op"]
        issue_val = issue.get(mapped)

        if op == "=":
            value = pred["value"]
            if mapped == "labels":
                return value in (issue_val or [])
            return str(issue_val) == value

        if op == "in":
            values = pred["values"]
            if mapped == "labels":
                return any(v in (issue_val or []) for v in values)
            return str(issue_val) in values

        if op in (">=", ">", "<=", "<"):
            value = pred["value"]
            iv = issue_val or ""
            if op == ">=":
                return iv >= value
            if op == ">":
                return iv > value
            if op == "<=":
                return iv <= value
            if op == "<":
                return iv < value

        print(f"Unsupported JQL operator: {op}", file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Issue factory
# ---------------------------------------------------------------------------


def _new_issue(
    key: str,
    project_key: str,
    issue_type: str,
    summary: str,
    description: str = "",
    assignee: str = "",
    import_source: str = "",
) -> dict:
    now = utcnow_iso()
    return {
        "assignee": assignee,
        "comments": [],
        "created_at": now,
        "description": description,
        "epic_link": "",
        "import_source": import_source,
        "issue_type": issue_type,
        "key": key,
        "labels": [],
        "links": [],
        "priority": "Medium",
        "project_key": project_key,
        "status": "",
        "summary": summary,
        "transition_history": [],
        "updated_at": now,
        "worklogs": [],
    }


# ---------------------------------------------------------------------------
# Issue sort key helper
# ---------------------------------------------------------------------------


def _issue_sort_key(issue: dict) -> tuple:
    key = issue.get("key", "")
    parts = key.split("-", 1)
    if len(parts) == 2 and parts[1].isdigit():
        return (parts[0], int(parts[1]))
    return (key, 0)


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------


def cmd_init_project(args: argparse.Namespace) -> None:
    project_key = validate_project_key(args.project_key)
    if JsonProjectRepository.exists(project_key):
        print(f"Project already exists: {project_key}", file=sys.stderr)
        sys.exit(1)

    project_dir(project_key).mkdir(parents=True, exist_ok=True)
    config = {
        "current_sequence": 0,
        "display_name": args.display_name,
        "project_key": project_key,
    }
    atomic_write_json(project_config_path(project_key), config)
    atomic_write_json(workflow_config_path(project_key), DEFAULT_WORKFLOW)

    result = {
        "display_name": args.display_name,
        "project_key": project_key,
        "status": "initialized",
        "workflow": "default",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_create(args: argparse.Namespace) -> None:
    project_key = validate_project_key(args.project_key)

    if args.type not in VALID_ISSUE_TYPES:
        print(
            f"Invalid issue type: {args.type}. Valid: {sorted(VALID_ISSUE_TYPES)}",
            file=sys.stderr,
        )
        sys.exit(1)

    if not JsonProjectRepository.exists(project_key):
        print(
            f"Project not found: {project_key}. Run init-project first.",
            file=sys.stderr,
        )
        sys.exit(1)

    import_source = ""
    if args.import_key:
        import_key = validate_issue_key(args.import_key)
        if import_key.split("-")[0] != project_key:
            print(
                f"import-key project prefix '{import_key.split('-')[0]}' "
                f"does not match project-key '{project_key}'",
                file=sys.stderr,
            )
            sys.exit(1)
        if JsonIssueRepository.exists(import_key):
            print(f"Issue already exists: {import_key}", file=sys.stderr)
            sys.exit(1)
        imported_seq = int(import_key.split("-")[1])
        config = JsonProjectRepository.load(project_key)
        if imported_seq > config["current_sequence"]:
            config["current_sequence"] = imported_seq
            atomic_write_json(project_config_path(project_key), config)
        issue_key = import_key
        import_source = import_key
    else:
        issue_key = JsonProjectRepository.next_key(project_key)

    workflow = JsonWorkflowRepository.load(project_key)
    issue = _new_issue(
        key=issue_key,
        project_key=project_key,
        issue_type=args.type,
        summary=args.summary,
        description=args.description or "",
        assignee=args.assignee or "",
        import_source=import_source,
    )
    issue["status"] = workflow["initial_status"]

    JsonIssueRepository.save(issue)
    print(json.dumps(issue, ensure_ascii=False, indent=2))


def cmd_get(args: argparse.Namespace) -> None:
    issue_key = validate_issue_key(args.issue_key)
    issue = JsonIssueRepository.load(issue_key)
    print(json.dumps(issue, ensure_ascii=False, indent=2))


def cmd_update(args: argparse.Namespace) -> None:
    issue_key = validate_issue_key(args.issue_key)
    issue = JsonIssueRepository.load(issue_key)

    updates = {}
    if args.summary is not None:
        updates["summary"] = args.summary
    if args.description is not None:
        updates["description"] = args.description
    if args.assignee is not None:
        updates["assignee"] = args.assignee
    if args.priority is not None:
        if args.priority not in VALID_PRIORITIES:
            print(
                f"Invalid priority: {args.priority}. Valid: {sorted(VALID_PRIORITIES)}",
                file=sys.stderr,
            )
            sys.exit(1)
        updates["priority"] = args.priority

    if not updates:
        print("No updatable fields provided.", file=sys.stderr)
        sys.exit(1)

    for field, value in updates.items():
        issue[field] = value
    issue["updated_at"] = utcnow_iso()

    JsonIssueRepository.save(issue)
    print(json.dumps(issue, ensure_ascii=False, indent=2))


def cmd_transition(args: argparse.Namespace) -> None:
    issue_key = validate_issue_key(args.issue_key)
    issue = JsonIssueRepository.load(issue_key)
    issue = TransitionService.transition(issue, args.transition_name)
    JsonIssueRepository.save(issue)
    print(json.dumps(issue, ensure_ascii=False, indent=2))


def cmd_add_comment(args: argparse.Namespace) -> None:
    issue_key = validate_issue_key(args.issue_key)
    issue = JsonIssueRepository.load(issue_key)

    comment = {
        "author": args.author,
        "body": args.body,
        "created_at": utcnow_iso(),
    }
    issue["comments"].append(comment)
    issue["updated_at"] = utcnow_iso()

    JsonIssueRepository.save(issue)
    print(json.dumps(issue, ensure_ascii=False, indent=2))


def cmd_list_comments(args: argparse.Namespace) -> None:
    issue_key = validate_issue_key(args.issue_key)
    issue = JsonIssueRepository.load(issue_key)
    print(json.dumps(issue["comments"], ensure_ascii=False, indent=2))


def cmd_add_worklog(args: argparse.Namespace) -> None:
    issue_key = validate_issue_key(args.issue_key)
    issue = JsonIssueRepository.load(issue_key)

    worklog = {
        "author": args.author,
        "comment": args.comment or "",
        "started_at": utcnow_iso(),
        "time_spent": args.time_spent,
    }
    issue["worklogs"].append(worklog)
    issue["updated_at"] = utcnow_iso()

    JsonIssueRepository.save(issue)
    print(json.dumps(issue, ensure_ascii=False, indent=2))


def cmd_list_worklogs(args: argparse.Namespace) -> None:
    issue_key = validate_issue_key(args.issue_key)
    issue = JsonIssueRepository.load(issue_key)
    print(json.dumps(issue["worklogs"], ensure_ascii=False, indent=2))


def cmd_create_link(args: argparse.Namespace) -> None:
    source_key = validate_issue_key(args.source_key)
    target_key = validate_issue_key(args.target_key)

    if args.link_type not in VALID_LINK_TYPES:
        print(
            f"Invalid link type: {args.link_type}. Valid: {sorted(VALID_LINK_TYPES)}",
            file=sys.stderr,
        )
        sys.exit(1)

    if not JsonIssueRepository.exists(source_key):
        print(f"Source issue not found: {source_key}", file=sys.stderr)
        sys.exit(1)
    if not JsonIssueRepository.exists(target_key):
        print(f"Target issue not found: {target_key}", file=sys.stderr)
        sys.exit(1)

    issue = JsonIssueRepository.load(source_key)
    issue["links"].append(
        {
            "direction": "outward",
            "link_type": args.link_type,
            "target_key": target_key,
        }
    )
    issue["updated_at"] = utcnow_iso()

    JsonIssueRepository.save(issue)
    print(json.dumps(issue, ensure_ascii=False, indent=2))


def cmd_list_links(args: argparse.Namespace) -> None:
    issue_key = validate_issue_key(args.issue_key)
    issue = JsonIssueRepository.load(issue_key)
    print(json.dumps(issue["links"], ensure_ascii=False, indent=2))


def cmd_search(args: argparse.Namespace) -> None:
    all_issues = JsonIssueRepository.all_issues()
    result = JqlParser().parse_and_evaluate(args.jql, all_issues)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_list_issues(args: argparse.Namespace) -> None:
    if args.project:
        project_key = validate_project_key(args.project)
        filters: dict = {}
        if args.status:
            filters["status"] = args.status
        if args.type:
            filters["issue_type"] = args.type
        issues = JsonIssueRepository.search(project_key, filters or None)
    else:
        issues = JsonIssueRepository.all_issues()
        if args.status:
            issues = [i for i in issues if i.get("status") == args.status]
        if args.type:
            issues = [i for i in issues if i.get("issue_type") == args.type]

    issues.sort(key=_issue_sort_key)
    print(json.dumps(issues, ensure_ascii=False, indent=2))


def cmd_set_epic_link(args: argparse.Namespace) -> None:
    issue_key = validate_issue_key(args.issue_key)
    epic_key = validate_issue_key(args.epic_key)

    if not JsonIssueRepository.exists(epic_key):
        print(f"Epic issue not found: {epic_key}", file=sys.stderr)
        sys.exit(1)

    epic = JsonIssueRepository.load(epic_key)
    if epic.get("issue_type") != "Epic":
        print(
            f"Issue {epic_key} is not an Epic (type: {epic.get('issue_type')})",
            file=sys.stderr,
        )
        sys.exit(1)

    issue = JsonIssueRepository.load(issue_key)
    issue["epic_link"] = epic_key
    issue["updated_at"] = utcnow_iso()

    JsonIssueRepository.save(issue)
    print(json.dumps(issue, ensure_ascii=False, indent=2))


def cmd_list_epic_children(args: argparse.Namespace) -> None:
    epic_key = validate_issue_key(args.epic_key)

    if not JsonIssueRepository.exists(epic_key):
        print(f"Epic issue not found: {epic_key}", file=sys.stderr)
        sys.exit(1)

    epic = JsonIssueRepository.load(epic_key)
    if epic.get("issue_type") != "Epic":
        print(
            f"Issue {epic_key} is not an Epic (type: {epic.get('issue_type')})",
            file=sys.stderr,
        )
        sys.exit(1)

    project_key = epic_key.split("-")[0]
    children = [
        i
        for i in JsonIssueRepository.search(project_key)
        if i.get("epic_link") == epic_key
    ]
    children.sort(key=_issue_sort_key)
    print(json.dumps(children, ensure_ascii=False, indent=2))


def cmd_add_label(args: argparse.Namespace) -> None:
    issue_key = validate_issue_key(args.issue_key)
    issue = JsonIssueRepository.load(issue_key)

    if args.label not in issue["labels"]:
        issue["labels"].append(args.label)
        issue["updated_at"] = utcnow_iso()
        JsonIssueRepository.save(issue)

    print(json.dumps(issue, ensure_ascii=False, indent=2))


def cmd_remove_label(args: argparse.Namespace) -> None:
    issue_key = validate_issue_key(args.issue_key)
    issue = JsonIssueRepository.load(issue_key)

    if args.label not in issue["labels"]:
        print(f"Label '{args.label}' not present on {issue_key}", file=sys.stderr)
        sys.exit(1)

    issue["labels"].remove(args.label)
    issue["updated_at"] = utcnow_iso()
    JsonIssueRepository.save(issue)
    print(json.dumps(issue, ensure_ascii=False, indent=2))


def cmd_list_labels(args: argparse.Namespace) -> None:
    issue_key = validate_issue_key(args.issue_key)
    issue = JsonIssueRepository.load(issue_key)
    print(json.dumps(issue["labels"], ensure_ascii=False, indent=2))


# ---------------------------------------------------------------------------
# TICKET_BACKEND dispatch
# ---------------------------------------------------------------------------

_SUBCOMMAND_DISPATCH: dict = {
    "add-comment": cmd_add_comment,
    "add-label": cmd_add_label,
    "add-worklog": cmd_add_worklog,
    "create": cmd_create,
    "create-link": cmd_create_link,
    "get": cmd_get,
    "init-project": cmd_init_project,
    "list-comments": cmd_list_comments,
    "list-epic-children": cmd_list_epic_children,
    "list-issues": cmd_list_issues,
    "list-labels": cmd_list_labels,
    "list-links": cmd_list_links,
    "list-worklogs": cmd_list_worklogs,
    "remove-label": cmd_remove_label,
    "search": cmd_search,
    "set-epic-link": cmd_set_epic_link,
    "transition": cmd_transition,
    "update": cmd_update,
}


def _route_internal(subcommand: str, args: argparse.Namespace) -> None:
    handler = _SUBCOMMAND_DISPATCH.get(subcommand)
    if handler is None:
        print(f"Unknown subcommand: {subcommand}", file=sys.stderr)
        sys.exit(1)
    handler(args)


def _dispatch(subcommand: str, args: argparse.Namespace) -> None:
    backend = os.environ.get("TICKET_BACKEND", "jira").lower()
    if backend == "internal":
        _route_internal(subcommand, args)
    elif backend == "jira":
        print(
            "TICKET_BACKEND=jira: use the mcp_com_atlassian_* tools directly",
            file=sys.stderr,
        )
        sys.exit(0)
    else:
        print(
            f"Unknown TICKET_BACKEND value: {backend!r}. Valid values: internal, jira",
            file=sys.stderr,
        )
        sys.exit(1)


# ---------------------------------------------------------------------------
# CLI parser
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ticket-cli.py",
        description=(
            "Internal Ticketing System CLI. "
            "Single writer only. "
            "Set TICKET_BACKEND=internal to enable the local backend."
        ),
    )
    sub = parser.add_subparsers(dest="subcommand", required=True)

    # init-project
    p = sub.add_parser(
        "init-project",
        help="Create project directory, project.json, and default workflow.json",
    )
    p.add_argument("--project-key", required=True, dest="project_key")
    p.add_argument("--display-name", required=True, dest="display_name")

    # create
    p = sub.add_parser("create", help="Create a new issue")
    p.add_argument("--project-key", required=True, dest="project_key")
    p.add_argument(
        "--type", required=True, choices=sorted(VALID_ISSUE_TYPES), dest="type"
    )
    p.add_argument("--summary", required=True)
    p.add_argument("--description", default="")
    p.add_argument("--assignee", default="")
    p.add_argument("--import-key", default="", dest="import_key")

    # get
    p = sub.add_parser("get", help="Retrieve an issue by key")
    p.add_argument("issue_key")

    # update
    p = sub.add_parser(
        "update",
        help="Update mutable fields: summary, description, assignee, priority",
    )
    p.add_argument("issue_key")
    p.add_argument("--summary", default=None)
    p.add_argument("--description", default=None)
    p.add_argument("--assignee", default=None)
    p.add_argument("--priority", default=None, choices=sorted(VALID_PRIORITIES))

    # transition
    p = sub.add_parser("transition", help="Apply a named workflow transition")
    p.add_argument("issue_key")
    p.add_argument("transition_name")

    # add-comment
    p = sub.add_parser("add-comment", help="Append a comment to an issue")
    p.add_argument("issue_key")
    p.add_argument("--author", required=True)
    p.add_argument("--body", required=True)

    # list-comments
    p = sub.add_parser("list-comments", help="List comments on an issue")
    p.add_argument("issue_key")

    # add-worklog
    p = sub.add_parser("add-worklog", help="Append a worklog entry to an issue")
    p.add_argument("issue_key")
    p.add_argument("--author", required=True)
    p.add_argument("--time-spent", required=True, dest="time_spent")
    p.add_argument("--comment", default="")

    # list-worklogs
    p = sub.add_parser("list-worklogs", help="List worklog entries on an issue")
    p.add_argument("issue_key")

    # create-link
    p = sub.add_parser("create-link", help="Create a typed link between two issues")
    p.add_argument("source_key")
    p.add_argument("target_key")
    p.add_argument(
        "--link-type",
        required=True,
        dest="link_type",
        choices=sorted(VALID_LINK_TYPES),
    )

    # list-links
    p = sub.add_parser("list-links", help="List links on an issue")
    p.add_argument("issue_key")

    # search
    p = sub.add_parser("search", help="Search issues using JQL subset")
    p.add_argument("--jql", required=True)

    # list-issues
    p = sub.add_parser(
        "list-issues",
        help="List issues with optional filters, sorted by IssueKey",
    )
    p.add_argument("--project", default="")
    p.add_argument("--status", default="")
    p.add_argument("--type", default="", dest="type")

    # set-epic-link
    p = sub.add_parser(
        "set-epic-link", help="Set the epic link on an issue to a given Epic key"
    )
    p.add_argument("issue_key")
    p.add_argument("epic_key")

    # list-epic-children
    p = sub.add_parser(
        "list-epic-children", help="List all issues whose epic_link equals epic_key"
    )
    p.add_argument("epic_key")

    # add-label
    p = sub.add_parser(
        "add-label", help="Add a label to an issue (idempotent; silently deduplicates)"
    )
    p.add_argument("issue_key")
    p.add_argument("label")

    # remove-label
    p = sub.add_parser("remove-label", help="Remove a label from an issue")
    p.add_argument("issue_key")
    p.add_argument("label")

    # list-labels
    p = sub.add_parser("list-labels", help="List labels on an issue")
    p.add_argument("issue_key")

    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    try:
        _dispatch(args.subcommand, args)
    except SystemExit:
        raise
    except Exception as exc:
        print(f"Internal error: {exc}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()

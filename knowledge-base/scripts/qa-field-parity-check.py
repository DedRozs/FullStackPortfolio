#!/usr/bin/env python3
"""
qa-field-parity-check.py - FieldParity manifest QA check

Loads knowledge-base/plans/tickets/field-parity.json, validates its structure,
and prints a tabular summary of every IssueField's parity status against the
Jira REST API.

Exit codes:
  0 - Manifest is well-formed (missing-parity entries are acceptable when documented)
  1 - Manifest is malformed, missing required fields, or unreadable

Usage:
  .venv/Scripts/python.exe knowledge-base/scripts/qa-field-parity-check.py
  (run from repository root)
"""

import json
import pathlib
import sys

MANIFEST_PATH = pathlib.Path("knowledge-base") / "plans" / "tickets" / "field-parity.json"

REQUIRED_FIELDS = frozenset({"internal_field", "jira_field", "notes", "parity_status"})
VALID_PARITY_STATUSES = frozenset({"full", "missing", "partial"})


def _load_manifest() -> list:
    if not MANIFEST_PATH.exists():
        print(f"ERROR: Manifest not found: {MANIFEST_PATH}", file=sys.stderr)
        sys.exit(1)
    try:
        with open(MANIFEST_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"ERROR: Failed to read manifest: {exc}", file=sys.stderr)
        sys.exit(1)
    if not isinstance(data, list):
        print("ERROR: Manifest root must be a JSON array", file=sys.stderr)
        sys.exit(1)
    return data


def _validate_entries(manifest: list) -> list:
    errors = []
    for i, entry in enumerate(manifest):
        if not isinstance(entry, dict):
            errors.append(f"Entry {i}: not a JSON object")
            continue
        missing = REQUIRED_FIELDS - set(entry.keys())
        if missing:
            errors.append(f"Entry {i}: missing required fields {sorted(missing)}")
            continue
        if entry["parity_status"] not in VALID_PARITY_STATUSES:
            errors.append(
                f"Entry {i} ({entry.get('internal_field', '?')}): "
                f"invalid parity_status '{entry['parity_status']}'. "
                f"Valid: {sorted(VALID_PARITY_STATUSES)}"
            )
    return errors


def _print_table(manifest: list) -> None:
    col_f = 22
    col_j = 36
    col_p = 10
    header = (
        f"{'internal_field':<{col_f}} {'jira_field':<{col_j}} "
        f"{'parity':<{col_p}} notes"
    )
    separator = "-" * (col_f + col_j + col_p + 3 + 60)
    print(header)
    print(separator)
    for entry in manifest:
        jira = entry["jira_field"] if entry["jira_field"] is not None else "null"
        notes = entry.get("notes", "")
        print(
            f"{entry['internal_field']:<{col_f}} {jira:<{col_j}} "
            f"{entry['parity_status']:<{col_p}} {notes}"
        )


def _print_summary(manifest: list) -> None:
    total = len(manifest)
    full_count = sum(1 for e in manifest if e["parity_status"] == "full")
    partial_count = sum(1 for e in manifest if e["parity_status"] == "partial")
    missing_count = sum(1 for e in manifest if e["parity_status"] == "missing")

    print()
    print(
        f"Total: {total}  |  full: {full_count}  |  "
        f"partial: {partial_count}  |  missing: {missing_count}"
    )

    if missing_count > 0:
        print()
        print(
            f"NOTE: {missing_count} field(s) have parity_status=missing. "
            "These are internal-only fields documented intentionally with no Jira equivalent."
        )
        missing_fields = [
            e["internal_field"] for e in manifest if e["parity_status"] == "missing"
        ]
        for field in missing_fields:
            print(f"  - {field}")


def main() -> None:
    manifest = _load_manifest()
    errors = _validate_entries(manifest)

    if errors:
        print("ERROR: Manifest is malformed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        sys.exit(1)

    _print_table(manifest)
    _print_summary(manifest)
    print()
    print("Manifest OK - field-parity.json is well-formed.", file=sys.stderr)
    sys.exit(0)


if __name__ == "__main__":
    main()

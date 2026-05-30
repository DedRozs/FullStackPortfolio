# qa-e2e-test.py
# Purpose: First-time user simulation E2E test for implement-ticket.prompt.md.
# Usage: .venv\Scripts\python.exe knowledge-base/scripts/qa-e2e-test.py
# Checks:
#   1. All 7 phase orchestrator agent names are present
#   2. Required input fields (TICKET_ID, TARGET_LANGUAGE, FRAMEWORK_NAME) are present
#   3. TICKET_ID validation regex is present
#   4. Coordinator constraint is stated clearly
#   5. workflow-gate.prompt.md delegation is present

import re
import sys

TARGET_FILE = ".github/prompts/implement-ticket.prompt.md"

REQUIRED_ORCHESTRATORS = [
    "discovery-orchestrator",
    "architecture-orchestrator",
    "domain-modeling-orchestrator",
    "development-orchestrator",
    "qa-orchestrator",
    "documentation-orchestrator",
    "deployment-orchestrator",
]

REQUIRED_INPUT_FIELDS = [
    "TICKET_ID",
    "TARGET_LANGUAGE",
    "FRAMEWORK_NAME",
]

COORDINATOR_CONSTRAINT_MARKERS = [
    "do not perform any work yourself",
    "delegate",
]

TICKET_ID_REGEX = r"^[A-Z]"


def main():
    with open(TARGET_FILE, encoding="utf-8") as f:
        body = f.read()

    defects = []

    # E2E Check 1: All 7 phase orchestrators present
    print("=== E2E Check 1: All 7 phase orchestrators present ===")
    for agent in REQUIRED_ORCHESTRATORS:
        if agent in body:
            print(f"  PASS: '{agent}' present")
        else:
            msg = f"MISSING orchestrator reference: '{agent}'"
            defects.append(msg)
            print(f"  FAIL: {msg}")

    # E2E Check 2: Required input fields present
    print("\n=== E2E Check 2: Required input fields present ===")
    for field in REQUIRED_INPUT_FIELDS:
        if field in body:
            print(f"  PASS: '{field}' present")
        else:
            msg = f"MISSING required input field: '{field}'"
            defects.append(msg)
            print(f"  FAIL: {msg}")

    # E2E Check 3: TICKET_ID validation regex present
    print("\n=== E2E Check 3: TICKET_ID validation regex present ===")
    if TICKET_ID_REGEX in body:
        print("  PASS: TICKET_ID validation regex found")
    else:
        msg = "MISSING: TICKET_ID validation regex pattern"
        defects.append(msg)
        print(f"  FAIL: {msg}")

    # E2E Check 4: Coordinator constraint stated clearly
    print("\n=== E2E Check 4: Coordinator constraint ===")
    for marker in COORDINATOR_CONSTRAINT_MARKERS:
        if marker.lower() in body.lower():
            print(f"  PASS: marker '{marker}' found")
        else:
            msg = f"MISSING coordinator constraint marker: '{marker}'"
            defects.append(msg)
            print(f"  FAIL: {msg}")

    # E2E Check 5: workflow-gate.prompt.md delegation present
    print("\n=== E2E Check 5: workflow-gate.prompt.md delegation present ===")
    if "workflow-gate.prompt.md" in body:
        print("  PASS: workflow-gate.prompt.md delegation found")
    else:
        msg = "MISSING: workflow-gate.prompt.md delegation"
        defects.append(msg)
        print(f"  FAIL: {msg}")

    print()
    if defects:
        print(f"E2E TEST FAILED - {len(defects)} defect(s):")
        for d in defects:
            print(f"  {d}")
        sys.exit(1)
    else:
        print("ALL E2E CHECKS PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()

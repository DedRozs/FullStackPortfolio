#!/usr/bin/env bash
# validate-schemas.sh
#
# Purpose:
#   Validates that every JSON file in contracts/schemas/ is well-formed JSON.
#   Exits with status 0 if all files pass; exits with status 1 if any file
#   fails, printing the name of each failing file.
#
# Usage:
#   bash knowledge-base/scripts/validate-schemas.sh
#
# Example output (all pass):
#   PASS  contracts/schemas/architecture-to-domain-modeling.schema.json
#   PASS  contracts/schemas/defect-report.schema.json
#   PASS  contracts/schemas/deployment-record.schema.json
#   PASS  contracts/schemas/development-to-qa.schema.json
#   PASS  contracts/schemas/discovery-to-architecture.schema.json
#   PASS  contracts/schemas/documentation-to-deployment.schema.json
#   PASS  contracts/schemas/domain-modeling-to-development.schema.json
#   PASS  contracts/schemas/mini-discovery.schema.json
#   PASS  contracts/schemas/qa-to-documentation.schema.json
#   All 9 schema file(s) passed validation.
#
# Example output (one fail):
#   PASS  contracts/schemas/architecture-to-domain-modeling.schema.json
#   FAIL  contracts/schemas/defect-report.schema.json
#   ...
#   1 schema file(s) failed validation. Fix before proceeding.
#
# Dependencies:
#   python3 (standard library only - no third-party packages required)
#
# Notes:
#   - Run from the repository root.
#   - Referenced by ADR-008: Schema Validation Runtime Mechanism Is a Shell Script.
#   - Used as a pre-release check step in knowledge-base/content/deployment/release-process.md.

set -euo pipefail

SCHEMA_DIR="contracts/schemas"
PASS=0
FAIL=0

if [ ! -d "$SCHEMA_DIR" ]; then
  echo "ERROR: Schema directory not found: $SCHEMA_DIR"
  echo "Run this script from the repository root."
  exit 1
fi

for file in "$SCHEMA_DIR"/*.json; do
  if [ ! -f "$file" ]; then
    echo "WARNING: No JSON files found in $SCHEMA_DIR"
    break
  fi

  if python3 -c "
import json, sys
try:
    with open(sys.argv[1]) as f:
        json.load(f)
    sys.exit(0)
except json.JSONDecodeError as e:
    print(f'  JSON error: {e}', file=sys.stderr)
    sys.exit(1)
" "$file" 2>/dev/null; then
    echo "PASS  $file"
    PASS=$((PASS + 1))
  else
    # Run again to capture the error message
    python3 -c "
import json, sys
try:
    with open(sys.argv[1]) as f:
        json.load(f)
except json.JSONDecodeError as e:
    print(f'  JSON error: {e}')
" "$file" 2>&1 | while IFS= read -r line; do
      echo "FAIL  $file"
      echo "      $line"
    done
    FAIL=$((FAIL + 1))
  fi
done

TOTAL=$((PASS + FAIL))
echo ""
if [ "$FAIL" -eq 0 ]; then
  echo "All $TOTAL schema file(s) passed validation."
  exit 0
else
  echo "$FAIL schema file(s) failed validation. Fix before proceeding."
  exit 1
fi

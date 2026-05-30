# qa-integration-tests.py
# Purpose: Cross-file consistency checks for the prompt library.
# Usage: .venv\Scripts\python.exe knowledge-base/scripts/qa-integration-tests.py
# Checks:
#   1. No two files share the same name: value
#   2. All instruction file paths in constraint prompt bodies are resolvable

import os
import re
import sys

import yaml

PROMPTS_DIR = ".github/prompts"
AGENTS_DIR = ".github/agents"


def parse_fm(path):
    """Return (frontmatter_dict, body_text)."""
    with open(path, encoding="utf-8") as f:
        content = f.read()
    if not content.startswith("---"):
        return None, content
    end = content.find("\n---", 3)
    if end == -1:
        return None, content
    try:
        data = yaml.safe_load(content[3:end].strip())
    except yaml.YAMLError:
        return None, content
    return data, content[end + 4:]


def main():
    defects = []

    # --- Integration Test 1: No duplicate name values ---
    print("=== Integration Test 1: No duplicate name values ===")
    names = {}
    for fname in sorted(os.listdir(PROMPTS_DIR)):
        if not fname.endswith(".prompt.md"):
            continue
        data, _ = parse_fm(os.path.join(PROMPTS_DIR, fname))
        name_val = data.get("name") if data else None
        if name_val in names:
            msg = f"DUPLICATE name: '{name_val}' in {fname} and {names[name_val]}"
            defects.append(msg)
            print(f"  FAIL: {msg}")
        else:
            names[name_val] = fname
    print(f"  {len(names)} unique names found - PASS\n")

    # --- Integration Test 2: Instruction file paths in constraint prompts are resolvable ---
    print("=== Integration Test 2: Instruction file paths resolvable ===")
    path_re = re.compile(r"\(path:\s*`?([^`\)]+\.instructions\.md)`?\)")
    for fname in sorted(os.listdir(PROMPTS_DIR)):
        if not fname.startswith("constraint-"):
            continue
        fpath = os.path.join(PROMPTS_DIR, fname)
        _, body = parse_fm(fpath)
        for match in path_re.finditer(body):
            ref_path = match.group(1).strip()
            if os.path.isfile(ref_path):
                print(f"  PASS: {ref_path}")
            else:
                msg = f"UNRESOLVABLE path: {ref_path!r} in {fname}"
                defects.append(msg)
                print(f"  FAIL: {msg}")
    print()

    if defects:
        print(f"INTEGRATION TESTS FAILED - {len(defects)} defect(s):")
        for d in defects:
            print(f"  {d}")
        sys.exit(1)
    else:
        print("ALL INTEGRATION TESTS PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()

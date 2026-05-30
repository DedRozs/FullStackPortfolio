# health-check-prompts.py
# Purpose: Health check for all .prompt.md files in .github/prompts/
# Usage: .venv\Scripts\python.exe knowledge-base/scripts/health-check-prompts.py
# Checks:
#   - YAML frontmatter parses without errors for all .prompt.md files
#   - No unresolved {{PLACEHOLDER}} tokens remain in frontmatter fields
# Exit 0 if healthy, 1 if any check fails.

import os
import re
import sys

import yaml

PROMPTS_DIR = ".github/prompts"

# Uppercase-only tokens are configuration placeholders that must be resolved.
# Mixed-case or lowercase tokens are intentional runtime placeholders - skip them.
CONFIG_PLACEHOLDER_RE = re.compile(r"\{\{[A-Z][A-Z0-9_]+\}\}")


def parse_frontmatter(filepath):
    """Return (data_dict, error_str). error_str is None on success."""
    with open(filepath, encoding="utf-8") as f:
        content = f.read()

    if not content.startswith("---"):
        return None, "no frontmatter delimiter found"

    end = content.find("\n---", 3)
    if end == -1:
        return None, "frontmatter closing delimiter not found"

    raw_yaml = content[3:end].strip()
    try:
        data = yaml.safe_load(raw_yaml)
    except yaml.YAMLError as exc:
        return None, f"YAML parse error: {exc}"

    if not isinstance(data, dict):
        return None, f"frontmatter did not parse to a mapping (got {type(data).__name__})"

    return data, None


def check_file(filepath):
    """Return list of defect strings. Empty list means healthy."""
    defects = []
    data, error = parse_frontmatter(filepath)

    if error is not None:
        defects.append(f"PARSE ERROR: {error}")
        return defects

    # Check each string-valued frontmatter field for unresolved config placeholders.
    for key, value in data.items():
        if isinstance(value, str):
            matches = CONFIG_PLACEHOLDER_RE.findall(value)
            if matches:
                defects.append(
                    f"UNRESOLVED PLACEHOLDER in '{key}': {matches}"
                )
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    matches = CONFIG_PLACEHOLDER_RE.findall(item)
                    if matches:
                        defects.append(
                            f"UNRESOLVED PLACEHOLDER in '{key}' list item '{item}': {matches}"
                        )

    return defects


def main():
    files = sorted(
        f for f in os.listdir(PROMPTS_DIR) if f.endswith(".prompt.md")
    )
    print(f"Health check: {len(files)} prompt files in {PROMPTS_DIR}\n")

    total_failures = 0
    for filename in files:
        filepath = os.path.join(PROMPTS_DIR, filename)
        defects = check_file(filepath)
        if defects:
            print(f"FAIL  {filename}")
            for d in defects:
                print(f"      {d}")
            total_failures += len(defects)
        else:
            print(f"OK    {filename}")

    print(f"\n--- Health Check Summary ---")
    print(f"Files checked: {len(files)}")
    if total_failures == 0:
        print("Status: HEALTHY - all files pass")
        sys.exit(0)
    else:
        print(f"Status: UNHEALTHY - {total_failures} issue(s) found")
        sys.exit(1)


if __name__ == "__main__":
    main()

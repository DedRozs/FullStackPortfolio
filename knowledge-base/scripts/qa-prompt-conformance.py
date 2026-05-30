# qa-prompt-conformance.py
# Purpose: Per-file conformance checks for all .prompt.md files in .github/prompts/
# Usage: .venv\Scripts\python.exe knowledge-base/scripts/qa-prompt-conformance.py
# Checks: frontmatter field order, name matches filename, mode value,
#         no unresolved config placeholders in frontmatter.

import os
import re
import sys

import yaml

PROMPTS_DIR = ".github/prompts"
COMMANDS_DIR = ".github/prompts/commands"

# Section headings permitted in a ThinLauncher command file body
PERMITTED_COMMAND_SECTIONS = {"## Required Input Fields", "## Phase Invocation Order"}

CANONICAL_ORDER = ["name", "description", "mode"]
VALID_MODE = "agent"

# Unresolved config placeholder - captures {{UPPER_CASE}} only (uppercase = config placeholder)
CONFIG_PLACEHOLDER_RE = re.compile(r"\{\{[A-Z][A-Z0-9_]+\}\}")


def parse_frontmatter(filepath):
    """Parse YAML frontmatter from a .prompt.md file. Returns (dict, raw_yaml_str)."""
    with open(filepath, encoding="utf-8") as f:
        content = f.read()

    if not content.startswith("---"):
        return None, None, content

    end = content.find("\n---", 3)
    if end == -1:
        return None, None, content

    raw_yaml = content[3:end].strip()
    try:
        data = yaml.safe_load(raw_yaml)
    except yaml.YAMLError as e:
        return None, str(e), content

    return data, raw_yaml, content


def check_file(filepath):
    filename = os.path.basename(filepath)
    stem = filename.replace(".prompt.md", "")
    defects = []

    data, raw_yaml, full_content = parse_frontmatter(filepath)

    if data is None:
        defects.append(f"  FAIL: No valid YAML frontmatter found")
        return defects
    if isinstance(data, str):
        defects.append(f"  FAIL: YAML parse error: {raw_yaml}")
        return defects

    # 1. Canonical field order
    actual_keys = list(data.keys())
    expected_keys = [k for k in CANONICAL_ORDER if k in data]
    extra_keys = [k for k in actual_keys if k not in CANONICAL_ORDER]
    if actual_keys != expected_keys + extra_keys:
        defects.append(
            f"  FAIL [order]: frontmatter keys {actual_keys} not in canonical order {CANONICAL_ORDER}"
        )

    # 2. name matches filename
    name_val = data.get("name", "")
    if name_val != stem:
        defects.append(
            f"  FAIL [name]: name '{name_val}' does not match filename stem '{stem}'"
        )

    # 3. mode value
    mode_val = data.get("mode", "")
    if mode_val != VALID_MODE:
        defects.append(
            f"  FAIL [mode]: mode is '{mode_val}', expected '{VALID_MODE}'"
        )

    # 4. No unresolved config placeholders in frontmatter (check raw YAML)
    if raw_yaml:
        matches = CONFIG_PLACEHOLDER_RE.findall(raw_yaml)
        if matches:
            defects.append(
                f"  FAIL [placeholders]: unresolved config placeholder(s) in frontmatter: {matches}"
            )

    # 5. Forbidden keys must not appear in frontmatter
    forbidden_keys = [k for k in data if k in ("model", "tools")]
    if forbidden_keys:
        defects.append(
            f"  FAIL [forbidden-keys]: frontmatter must not contain: {forbidden_keys}"
        )

    return defects


def extract_body(content):
    """Return the body text after the closing frontmatter delimiter."""
    if content.startswith("---"):
        end = content.find("\n---", 3)
        if end != -1:
            return content[end + 4:].strip()
    return content.strip()


def check_command_file(filepath):
    """ThinLauncher constraint checks for command files in commands/ directory."""
    defects = check_file(filepath)  # run standard frontmatter checks first

    with open(filepath, encoding="utf-8") as f:
        content = f.read()

    body = extract_body(content)

    # ThinLauncher: required body sections must be present
    if "## Required Input Fields" not in body:
        defects.append("  FAIL [thin-launcher]: missing '## Required Input Fields' section")
    if "## Phase Invocation Order" not in body:
        defects.append("  FAIL [thin-launcher]: missing '## Phase Invocation Order' section")

    # ThinLauncher: delegation instruction must reference workflow-gate
    if "workflow-gate.prompt.md" not in body:
        defects.append(
            "  FAIL [thin-launcher]: delegation instruction must reference workflow-gate.prompt.md"
        )

    # ThinLauncher: no extra section headings permitted beyond the two required
    section_headings = [
        line.strip() for line in body.splitlines() if line.startswith("## ")
    ]
    extra_sections = [s for s in section_headings if s not in PERMITTED_COMMAND_SECTIONS]
    if extra_sections:
        defects.append(
            f"  FAIL [thin-launcher]: forbidden extra section(s): {extra_sections}"
        )

    return defects


def main():
    if not os.path.isdir(PROMPTS_DIR):
        print(f"ERROR: prompts directory not found: {PROMPTS_DIR}")
        sys.exit(1)

    files = sorted(
        f for f in os.listdir(PROMPTS_DIR) if f.endswith(".prompt.md")
    )

    if not files:
        print("ERROR: no .prompt.md files found")
        sys.exit(1)

    total = len(files)
    passed = 0
    failed_files = []

    print(f"Checking {total} prompt files in {PROMPTS_DIR}/\n")

    for fname in files:
        fpath = os.path.join(PROMPTS_DIR, fname)
        defects = check_file(fpath)
        if defects:
            print(f"FAIL  {fname}")
            for d in defects:
                print(d)
            failed_files.append(fname)
        else:
            print(f"PASS  {fname}")
            passed += 1

    # --- Commands directory: ThinLauncher checks ---
    cmd_total = 0
    cmd_passed = 0
    cmd_failed_files = []

    if os.path.isdir(COMMANDS_DIR):
        cmd_files = sorted(
            f for f in os.listdir(COMMANDS_DIR) if f.endswith(".prompt.md")
        )
        cmd_total = len(cmd_files)
        print(f"\nChecking {cmd_total} command files in {COMMANDS_DIR}/\n")
        for fname in cmd_files:
            fpath = os.path.join(COMMANDS_DIR, fname)
            defects = check_command_file(fpath)
            if defects:
                print(f"FAIL  commands/{fname}")
                for d in defects:
                    print(d)
                cmd_failed_files.append(f"commands/{fname}")
            else:
                print(f"PASS  commands/{fname}")
                cmd_passed += 1
    else:
        print(f"\nINFO: commands directory not found at {COMMANDS_DIR} - skipping ThinLauncher checks")

    # --- Combined summary ---
    all_total = total + cmd_total
    all_passed = passed + cmd_passed
    all_failed = failed_files + cmd_failed_files

    print(f"\n--- Summary ---")
    print(f"Total: {all_total}  Passed: {all_passed}  Failed: {len(all_failed)}")

    if all_failed:
        print("\nFailed files:")
        for f in all_failed:
            print(f"  {f}")
        sys.exit(1)
    else:
        print("All files passed conformance checks.")
        sys.exit(0)


if __name__ == "__main__":
    main()

---
name: audit-all-documents
description: "Runs a single-pass quality audit on every .md file in the project. Uses Python to enumerate all markdown files, delegates one audit-document subagent call per file, writes each report to a temp file to preserve context, then consolidates all reports at the end. Usage: /audit-all-documents"
mode: agent
---

Run a full-project markdown audit by delegating one `audit-document` subagent call per
`.md` file discovered in the workspace. Each subagent report is written to a temporary
file immediately after receipt so that accumulated findings do not exhaust context
before the audit is complete.

## Process

Execute all steps in strict serial order. Do not skip any step.

---

### Step 0 - Verify the virtual environment

Before running any Python command, check whether `.venv\Scripts\python.exe` exists at
the workspace root. If it does not exist, create the virtual environment using the
system Python launcher:

```
python -m venv .venv
```

Then install project dependencies:

```
.venv\Scripts\pip install -r requirements.txt
```

If `requirements-dev.txt` exists, install it too:

```
.venv\Scripts\pip install -r requirements-dev.txt
```

Do not proceed to Step 1 until `.venv\Scripts\python.exe` is confirmed present.

---

### Step 1 - Prepare the temp directory

Create the directory `knowledge-base/temp/audit-reports/` if it does not already exist.
Delete any files already present inside it from a prior run so the directory starts
clean.

Run this Python command in the terminal to set up the directory:

```python
.venv\Scripts\python.exe -c "
import pathlib, shutil
report_dir = pathlib.Path('knowledge-base/temp/audit-reports')
if report_dir.exists():
    shutil.rmtree(report_dir)
report_dir.mkdir(parents=True)
print('Temp directory ready:', report_dir)
"
```

---

### Step 2 - Enumerate all markdown files

Run the following Python command in the terminal from the workspace root to list every
`.md` file in the project, excluding `.git/`, `node_modules/`, and
`knowledge-base/temp/`:

```python
.venv\Scripts\python.exe -c "
import pathlib, sys
root = pathlib.Path('.')
files = sorted(
    str(p) for p in root.rglob('*.md')
    if '.git' not in p.parts
    and 'node_modules' not in p.parts
    and 'temp' not in p.parts
)
for f in files:
    print(f)
print(f'Total: {len(files)} files', file=sys.stderr)
"
```

Capture every line of standard output. Each line is a workspace-relative path to one
`.md` file to audit.

Report the total file count to the user before proceeding:

```
Found <n> markdown files. Beginning audit - writing each report to
knowledge-base/temp/audit-reports/. This may take several minutes.
```

---

### Step 3 - Audit each file

For **each** file path collected in Step 2, in order, execute these two sub-steps:

**3a. Invoke the subagent.**

Delegate to the `audit-document` subagent with one input field:

- `documentPath` - the workspace-relative path from Step 2 (exact string, no
  modification).

**3b. Write the report to a temp file.**

Immediately after the subagent returns its report, derive a safe filename by replacing
every path separator and special character with an underscore, then appending
`.audit.md`. For example:

- `knowledge-base\content\decisions\0001-foo.md`
  becomes `knowledge-base_content_decisions_0001-foo.md.audit.md`

Write the full verbatim report to:

```
knowledge-base/temp/audit-reports/<safe-filename>
```

Use `create_file` to write the file. Do not store the report in memory beyond extracting
the three summary fields below (needed for the progress counter).

Extract from the report before discarding it from context:

- `verdict` - `Pass`, `Pass with Warnings`, or `Fail`
- `findingCount` - integer
- `gateDecision` - `PASS` or `FAIL`

After writing the file, print a one-line progress update to the user:

```
[<n>/<total>] <documentPath> - <verdict>
```

Then continue immediately to the next file. Do not halt on a `Fail` verdict.

---

### Step 4 - Consolidate all reports

After every file has been audited and its temp file written, run this Python command to
list all generated report files in alphabetical order:

```python
.venv\Scripts\python.exe -c "
import pathlib
reports = sorted(pathlib.Path('knowledge-base/temp/audit-reports').glob('*.audit.md'))
for r in reports:
    print(r)
print(f'Total report files: {len(reports)}', file=sys.stderr)
"
```

Read each report file in the order listed. From each file extract:

- The `File:` line (audited document path)
- The `Type:` line (document type)
- The `Verdict:` line
- The `Finding count:` line
- The `Gate decision:` line
- Every row in the findings table where Severity is `Critical` or `Major`

Using the extracted data, produce the consolidated summary using this exact format:

```
Audit Complete - Full Project Markdown Audit
============================================
Total files audited : <n>
Pass                : <n>
Pass with Warnings  : <n>
Fail                : <n>

Results by File
---------------
| File | Type | Verdict | Findings |
|---|---|---|---|
<one row per audited file>

Critical and Major Findings
---------------------------
| File | Severity | Dim | Description | Recommendation |
|---|---|---|---|---|
<one row per Critical or Major finding across all files,
 or "(none)" if all files passed clean>

Overall Assessment
------------------
<PASS | PASS WITH WARNINGS | FAIL>

Verdict rules applied:
- PASS              : zero Fail verdicts, zero Critical findings
- PASS WITH WARNINGS: zero Fail verdicts, one or more Minor findings only
- FAIL              : one or more Fail verdicts or Critical findings

Individual reports: knowledge-base/temp/audit-reports/
```

Present the consolidated report to the user. Do not propose fixes inline; the user
decides which findings to act on.

The individual report files in `knowledge-base/temp/audit-reports/` are left in place
so the user can inspect the full per-file detail. Inform the user they can delete the
directory when no longer needed.

---

## Constraints

- Write each report to `knowledge-base/temp/audit-reports/` immediately after the
  subagent returns it. Do not accumulate reports in memory.
- Never skip a file from the Python-enumerated list.
- Never halt the audit loop because a single file's verdict is `Fail`; always complete
  all files before reporting.
- Always report the total file count discovered before beginning the per-file loop.
- The Python enumeration command must run in the terminal; do not substitute a manual
  file listing.
- Exclude `knowledge-base/temp/` from the enumeration in Step 2 to prevent auditing
  reports from previous runs.
- Never modify any source file during the audit. Writing to `knowledge-base/temp/` is
  the only permitted write operation.

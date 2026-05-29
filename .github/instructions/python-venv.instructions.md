---
applyTo: "**/*.{py,agent.md}"
description: "Use when executing any Python command in a terminal - test runners, package installers, linting tools, migration runners, or any other Python CLI invocation. Enforces mandatory virtual environment activation rules for all Python command execution to prevent system Python pollution and dependency conflicts."
---
<!-- v1.0 | Created: 2026-05-02 | Pattern: Python Virtual Environment -->

# Python Virtual Environment Rules

## Rule: All Python Commands Must Use the Virtual Environment

A `.venv/` virtual environment must exist at the workspace root before any Python
command is executed. Never invoke the system Python (`python`, `python3`) directly
for project commands.

---

## Step 1: Verify the Virtual Environment Exists

Before running any Python command, check whether `.venv/` exists at the workspace root.

**If `.venv/` is absent**, create it using the system Python launcher:

```
python -m venv .venv
```

---

## Step 2: Install Dependencies

After confirming `.venv/` exists, install project dependencies into the virtual
environment.

| Platform   | Command                                                  |
|------------|----------------------------------------------------------|
| Windows    | `.venv\Scripts\pip install -r requirements.txt`          |
| Unix/macOS | `.venv/bin/pip install -r requirements.txt`              |

If a `requirements-dev.txt` or `requirements-test.txt` file exists, install it too:

| Platform   | Command                                                      |
|------------|--------------------------------------------------------------|
| Windows    | `.venv\Scripts\pip install -r requirements-dev.txt`          |
| Unix/macOS | `.venv/bin/pip install -r requirements-dev.txt`              |

---

## Step 3: Run Commands via the Virtual Environment

Always invoke Python using the virtual environment executable. Never use bare `python`
or `python3` for project commands.

| Action                  | Windows                                                                      | Unix/macOS                                                       |
|-------------------------|------------------------------------------------------------------------------|------------------------------------------------------------------|
| Run a Python script     | `.venv\Scripts\python.exe script.py`                                         | `.venv/bin/python script.py`                                     |
| Run pytest              | `.venv\Scripts\python.exe -m pytest`                                         | `.venv/bin/python -m pytest`                                     |
| Run pytest with coverage| `.venv\Scripts\python.exe -m pytest --cov=src --cov-report=term-missing`     | `.venv/bin/python -m pytest --cov=src --cov-report=term-missing` |
| Install a package       | `.venv\Scripts\pip install <package>`                                        | `.venv/bin/pip install <package>`                                |
| Run a module            | `.venv\Scripts\python.exe -m <module>`                                       | `.venv/bin/python -m <module>`                                   |

---

## Anti-Patterns to Avoid

- Never run `python script.py` without either activating the virtual environment or
  using the full venv-relative executable path.
- Never run `pip install` without targeting the virtual environment pip executable.
- Never commit `.venv/` to source control; it must always be recreated from
  `requirements.txt`.
- Never assume the virtual environment is already activated; always invoke Python via
  the full venv-relative path or activate explicitly within the same shell session.
- Never use `sudo pip install` or `pip install --user` for project dependencies.

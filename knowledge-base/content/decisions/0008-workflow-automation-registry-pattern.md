# ADR 0008: Decorator-Based Registry Pattern for Trigger/Condition/Action Extensibility

**Status:** Accepted
**Date:** 2026-05-30
**Bounded context:** workflow_automation
**Decided by:** Joseph Prince

---

## Context

The workflow_automation engine needs to support multiple trigger types, condition
operators, and action handlers. The immediate requirements include four trigger types,
five condition operators, and four action types. The design constraint is that the engine
must remain closed to modification as new handlers are added over time - the portfolio
roadmap anticipates webhook triggers, conditional branching, and additional notification
channels as future extensions.

The engine also dispatches all actions as Django-Q2 tasks, which means action handler
implementations need to import ORM models and external SDK clients (SendGrid, Twilio).
These imports must be deferred to avoid circular imports when the engine module is loaded
at Django startup.

A class-based approach (a registry class with `register()` methods) was ruled out early
because it would require every caller to hold a reference to a registry instance,
complicating dependency injection across three bounded contexts and the Q2 task worker.

---

## Decision

Use a module-level dictionary plus a decorator factory pattern in a single
`registry.py` file. Two dictionaries are defined at module scope:

```python
_action_handlers: dict[str, Callable] = {}
_condition_evaluators: dict[str, Callable] = {}
```

Two public decorator factories allow any function to self-register at import time:

```python
def register_action_handler(action_type: ActionType) -> Callable:
    def decorator(fn: Callable) -> Callable:
        _action_handlers[action_type.value] = fn
        return fn
    return decorator

def register_condition_evaluator(operator: ConditionOperator) -> Callable:
    def decorator(fn: Callable) -> Callable:
        _condition_evaluators[operator.value] = fn
        return fn
    return decorator
```

All default handlers are defined in the same `registry.py` file, directly below the
registry infrastructure, and decorated at definition time. Lookups use two public
retrieval functions:

```python
def get_action_handler(action_type: str) -> Callable | None: ...
def get_condition_evaluator(operator: str) -> Callable | None: ...
```

The engine calls only `get_action_handler` and `get_condition_evaluator`; it has no
knowledge of which handlers are registered.

---

## Alternatives Considered

### Class-based handler map

A `HandlerRegistry` class with `register()` instance methods and a shared singleton
(`registry = HandlerRegistry()`). Rejected because it requires every caller to import
and reference the singleton. The decorator-factory pattern with module-level dicts
achieves the same result with less boilerplate and no singleton management.

### Django signals

Use `post_save` or custom signals to wire actions to trigger events. Rejected because
signals couple the sender and receiver through Django's signal dispatcher, making the
execution path opaque and harder to test. Signals also do not support the ordered
condition evaluation or the dry-run execution mode that the engine requires.

### Celery signals / task routing

Route actions to Celery tasks by action type using Celery's `task_prerun` signal or
routing keys. Rejected because the project uses Django-Q2 (already installed and
configured) and does not require Celery's distributed routing capabilities at this scale.
Switching task backends to support a registry abstraction would add unnecessary
complexity.

---

## Consequences

### Positive

- New action handlers and condition evaluators are added by writing a function and
  applying a decorator. Zero changes to `engine.py`, `tasks.py`, or any use case.
- Handlers load lazily: the decorator registers the function reference; expensive SDK
  imports (SendGrid, Twilio) happen inside the handler body, not at registration time.
  This keeps Django startup fast and avoids circular imports.
- The registry is trivially testable: register a mock handler in a test, run the engine,
  assert the mock was called.
- Adding a handler in a future app (e.g. a `payments` bounded context) requires only
  importing `register_action_handler` and adding a decorated function. The engine
  discovers it automatically on the next request after the module is imported.

### Negative

- The registry state is global (module-level dict). In tests that modify the registry,
  teardown must deregister the test handler to avoid bleeding state between test cases.
- There is no compile-time guarantee that a handler exists for every `ActionType` value.
  Unregistered action types produce a logged warning and a skipped action, not a hard
  failure. This trade-off was accepted: a missing handler on a new action type is a
  developer error surfaced immediately in the first dry-run test, not a silent data
  corruption.
- Handler discovery is implicit (import-order dependent). All default handlers live in
  `registry.py` and are imported by `engine.py`, so the default set is always available.
  Third-party or app-specific handlers must ensure their module is imported before the
  engine runs.

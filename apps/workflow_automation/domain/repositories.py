from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence
from uuid import UUID

from apps.workflow_automation.domain.model import (
    AutomationAction,
    AutomationCondition,
    AutomationRule,
    AutomationRun,
    AutomationRunLog,
)
from apps.workflow_automation.domain.value_objects import TriggerType


class AutomationRuleRepository(ABC):
    @abstractmethod
    def get_by_id(self, rule_id: UUID) -> AutomationRule | None: ...

    @abstractmethod
    def find_by_trigger_type(self, trigger_type: TriggerType) -> Sequence[AutomationRule]: ...

    @abstractmethod
    def find_all_enabled(self) -> Sequence[AutomationRule]: ...

    @abstractmethod
    def list_all(self) -> Sequence[AutomationRule]: ...

    @abstractmethod
    def save(self, rule: AutomationRule) -> None: ...

    @abstractmethod
    def delete(self, rule_id: UUID) -> None: ...


class AutomationConditionRepository(ABC):
    @abstractmethod
    def find_by_rule_id(self, rule_id: UUID) -> Sequence[AutomationCondition]: ...

    @abstractmethod
    def save(self, condition: AutomationCondition) -> None: ...

    @abstractmethod
    def delete_by_rule_id(self, rule_id: UUID) -> None: ...


class AutomationActionRepository(ABC):
    @abstractmethod
    def find_by_rule_id(self, rule_id: UUID) -> Sequence[AutomationAction]: ...

    @abstractmethod
    def save(self, action: AutomationAction) -> None: ...

    @abstractmethod
    def delete_by_rule_id(self, rule_id: UUID) -> None: ...


class AutomationRunRepository(ABC):
    @abstractmethod
    def get_by_id(self, run_id: UUID) -> AutomationRun | None: ...

    @abstractmethod
    def find_by_rule_id(self, rule_id: UUID) -> Sequence[AutomationRun]: ...

    @abstractmethod
    def save(self, run: AutomationRun) -> None: ...


class AutomationRunLogRepository(ABC):
    @abstractmethod
    def find_by_run_id(self, run_id: UUID) -> Sequence[AutomationRunLog]: ...

    @abstractmethod
    def save(self, log: AutomationRunLog) -> None: ...

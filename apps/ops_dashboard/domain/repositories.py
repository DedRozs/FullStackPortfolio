from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Sequence
from uuid import UUID

from apps.ops_dashboard.domain.model import (
    AlertRule,
    AuditLogEntry,
    CompanyMetric,
    CustomerGrowthSnapshot,
    DashboardAlert,
    RevenueSnapshot,
)
from apps.ops_dashboard.domain.value_objects import DateRange


class MetricRepository(ABC):
    @abstractmethod
    def get_by_id(self, metric_id: UUID) -> CompanyMetric | None: ...

    @abstractmethod
    def list_all(self) -> Sequence[CompanyMetric]: ...

    @abstractmethod
    def save(self, metric: CompanyMetric) -> None: ...

    @abstractmethod
    def get_revenue_snapshots(
        self, metric_id: UUID, date_range: DateRange
    ) -> list[RevenueSnapshot]: ...

    @abstractmethod
    def get_growth_snapshots(
        self, metric_id: UUID, date_range: DateRange
    ) -> list[CustomerGrowthSnapshot]: ...

    @abstractmethod
    def save_revenue_snapshot(self, snapshot: RevenueSnapshot) -> None: ...

    @abstractmethod
    def save_growth_snapshot(self, snapshot: CustomerGrowthSnapshot) -> None: ...


class AlertRuleRepository(ABC):
    @abstractmethod
    def get_by_id(self, rule_id: UUID) -> AlertRule | None: ...

    @abstractmethod
    def list_active(self) -> Sequence[AlertRule]: ...

    @abstractmethod
    def list_all(self) -> Sequence[AlertRule]: ...

    @abstractmethod
    def save(self, rule: AlertRule) -> None: ...

    @abstractmethod
    def delete(self, rule_id: UUID) -> None: ...


class DashboardAlertRepository(ABC):
    @abstractmethod
    def get_by_id(self, alert_id: UUID) -> DashboardAlert | None: ...

    @abstractmethod
    def list_active(self) -> Sequence[DashboardAlert]: ...

    @abstractmethod
    def list_by_rule(self, rule_id: UUID) -> Sequence[DashboardAlert]: ...

    @abstractmethod
    def save(self, alert: DashboardAlert) -> None: ...


class AuditLogRepository(ABC):
    @abstractmethod
    def append(self, entry: AuditLogEntry) -> None: ...

    @abstractmethod
    def list_recent(self, limit: int) -> Sequence[AuditLogEntry]: ...

    @abstractmethod
    def list_by_resource(
        self, resource_id: UUID, limit: int
    ) -> Sequence[AuditLogEntry]: ...

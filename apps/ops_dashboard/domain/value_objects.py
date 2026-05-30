from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional


class MetricType(str, Enum):
    REVENUE = "revenue"
    CUSTOMER_GROWTH = "customer_growth"
    CUSTOM = "custom"


class ThresholdOperator(str, Enum):
    GT = "gt"
    LT = "lt"
    GTE = "gte"
    LTE = "lte"
    EQ = "eq"


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class AlertRuleStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"


class ImportStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETE = "complete"
    FAILED = "failed"


class AuditAction(str, Enum):
    METRIC_CREATED = "metric_created"
    METRIC_UPDATED = "metric_updated"
    ALERT_ACKNOWLEDGED = "alert_acknowledged"
    ALERT_RESOLVED = "alert_resolved"
    RULE_CREATED = "rule_created"
    RULE_PAUSED = "rule_paused"
    RULE_ACTIVATED = "rule_activated"
    IMPORT_STARTED = "import_started"
    IMPORT_COMPLETED = "import_completed"
    IMPORT_FAILED = "import_failed"


@dataclass(frozen=True)
class DateRange:
    start_date: date
    end_date: date

    def __post_init__(self) -> None:
        if self.end_date < self.start_date:
            raise ValueError("DateRange.end_date must be >= start_date")

    def contains(self, d: date) -> bool:
        return self.start_date <= d <= self.end_date


@dataclass(frozen=True)
class PeriodDelta:
    current_value: Decimal
    prior_value: Decimal

    @property
    def delta(self) -> Decimal:
        return self.current_value - self.prior_value

    @property
    def percentage_change(self) -> Optional[float]:
        if self.prior_value == Decimal("0"):
            return None
        return float((self.delta / self.prior_value) * Decimal("100"))

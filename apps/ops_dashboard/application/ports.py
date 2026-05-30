from __future__ import annotations

from abc import ABC, abstractmethod

from apps.ops_dashboard.domain.model import DashboardAlert


class AlertNotificationPort(ABC):
    @abstractmethod
    def notify_alert_triggered(self, alert: DashboardAlert) -> None: ...

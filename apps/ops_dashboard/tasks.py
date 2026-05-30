"""
Background tasks for the ops_dashboard app.

Tasks are executed asynchronously by Django-Q2.

Usage (from Django code):
    from django_q.tasks import async_task
    async_task('apps.ops_dashboard.tasks.evaluate_alert_rules')
    async_task('apps.ops_dashboard.tasks.process_metric_import', import_id)
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def evaluate_alert_rules() -> None:
    """Evaluate all active AlertRules against latest metric snapshots.

    Called by the Q2 scheduler every 15 minutes.
    """
    from apps.ops_dashboard import models as orm
    from apps.ops_dashboard.domain.services import AlertEvaluationService
    from apps.ops_dashboard.infrastructure.repositories import (
        DjangoAlertRuleRepository,
        DjangoDashboardAlertRepository,
        DjangoMetricRepository,
    )

    service = AlertEvaluationService(
        metric_repo=DjangoMetricRepository(),
        rule_repo=DjangoAlertRuleRepository(),
        alert_repo=DjangoDashboardAlertRepository(),
    )
    triggered = service.evaluate_all_rules()
    if triggered:
        logger.info(
            'evaluate_alert_rules: triggered %d new alert(s)', len(triggered)
        )
    else:
        logger.debug('evaluate_alert_rules: no new alerts triggered')

    for alert in (triggered or []):
        try:
            from apps.workflow_automation.engine import fire_trigger
            fire_trigger(
                'metric.threshold_crossed',
                {
                    'trigger_type': 'metric.threshold_crossed',
                    'source_id': str(getattr(alert, 'id', '')),
                    'source_type': 'DashboardAlert',
                    'payload': {
                        'rule_id': str(getattr(alert, 'rule_id', '')),
                    },
                },
            )
        except Exception:
            logger.exception('fire_trigger failed for metric.threshold_crossed')


def process_metric_import(import_id: str) -> None:
    """Process a CSV metric import job in the background.

    Args:
        import_id: Identifier for the import job (used for status tracking and
                   locating the CSV data in temporary storage).
    """
    import csv
    import io
    import uuid
    from datetime import datetime, timezone
    from decimal import Decimal

    from django.core.cache import cache

    from apps.ops_dashboard.application.dtos import (
        RecordGrowthSnapshotCommand,
        RecordRevenueSnapshotCommand,
    )
    from apps.ops_dashboard.application.use_cases import (
        RecordGrowthSnapshot,
        RecordRevenueSnapshot,
    )
    from apps.ops_dashboard.infrastructure.repositories import (
        DjangoAuditLogRepository,
        DjangoMetricRepository,
    )

    _UTC = timezone.utc
    cache_key = f'ops_import_{import_id}'
    csv_text = cache.get(cache_key)
    if csv_text is None:
        logger.error('process_metric_import: no CSV data found for import_id=%s', import_id)
        return

    metric_repo = DjangoMetricRepository()
    audit_repo = DjangoAuditLogRepository()
    rows_ok = 0
    rows_failed = 0

    reader = csv.DictReader(io.StringIO(csv_text))
    for row in reader:
        try:
            row_type = row.get('type', '').strip()
            metric_id = uuid.UUID(row['metric_id'].strip())
            period_start = datetime.fromisoformat(row['period_start'].strip()).date()
            period_end = datetime.fromisoformat(row['period_end'].strip()).date()

            if row_type == 'revenue':
                use_case = RecordRevenueSnapshot(
                    metric_repo=metric_repo,
                    audit_repo=audit_repo,
                )
                use_case.execute(
                    RecordRevenueSnapshotCommand(
                        metric_id=metric_id,
                        amount=Decimal(row['amount'].strip()),
                        currency=row.get('currency', 'USD').strip(),
                        period_start=period_start,
                        period_end=period_end,
                        recorded_by_id=uuid.UUID(int=0),
                    )
                )
            elif row_type == 'growth':
                use_case = RecordGrowthSnapshot(
                    metric_repo=metric_repo,
                    audit_repo=audit_repo,
                )
                new_customers = int(row['new_customers'].strip())
                churned_customers = int(row['churned_customers'].strip())
                use_case.execute(
                    RecordGrowthSnapshotCommand(
                        metric_id=metric_id,
                        new_customers=new_customers,
                        churned_customers=churned_customers,
                        period_start=period_start,
                        period_end=period_end,
                        recorded_by_id=uuid.UUID(int=0),
                    )
                )
            rows_ok += 1
        except Exception:
            rows_failed += 1
            logger.exception(
                'process_metric_import: failed to process row for import_id=%s', import_id
            )

    logger.info(
        'process_metric_import: import_id=%s completed. ok=%d failed=%d',
        import_id,
        rows_ok,
        rows_failed,
    )
    cache.delete(cache_key)

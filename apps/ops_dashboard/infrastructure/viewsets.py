from __future__ import annotations

import csv
import logging
from datetime import date
from uuid import UUID

from django.http import StreamingHttpResponse
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet, ReadOnlyModelViewSet

from apps.ops_dashboard import models as orm
from apps.ops_dashboard.application.dtos import (
    AcknowledgeAlertCommand,
    ActivateAlertRuleCommand,
    CreateAlertRuleCommand,
    CreateCompanyMetricCommand,
    DeleteAlertRuleCommand,
    GetMetricSeriesQuery,
    ListActiveAlertsQuery,
    ListAlertRulesQuery,
    ListAuditLogQuery,
    ListMetricsQuery,
    PauseAlertRuleCommand,
    RecordGrowthSnapshotCommand,
    RecordRevenueSnapshotCommand,
    ResolveAlertCommand,
    UpdateAlertRuleCommand,
    UpdateCompanyMetricCommand,
)
from apps.ops_dashboard.application.use_cases import (
    AcknowledgeAlert,
    ActivateAlertRule,
    CreateAlertRule,
    CreateCompanyMetric,
    DeleteAlertRule,
    GetMetricSeries,
    ListActiveAlerts,
    ListAlertRules,
    ListAuditLog,
    ListMetrics,
    PauseAlertRule,
    RecordGrowthSnapshot,
    RecordRevenueSnapshot,
    ResolveAlert,
    UpdateAlertRule,
    UpdateCompanyMetric,
)
from apps.ops_dashboard.domain.services import MetricAggregationService
from apps.ops_dashboard.infrastructure.permissions import IsStaffUser
from core.demo_guard import DemoReadOnlyMixin
from apps.ops_dashboard.infrastructure.repositories import (
    DjangoAlertRuleRepository,
    DjangoDashboardAlertRepository,
    DjangoAuditLogRepository,
    DjangoMetricRepository,
)
from apps.ops_dashboard.infrastructure.serializers import (
    AlertRuleSerializer,
    AuditLogEntrySerializer,
    CompanyMetricSerializer,
    CustomerGrowthSnapshotSerializer,
    DashboardAlertSerializer,
    RevenueSnapshotSerializer,
)

logger = logging.getLogger(__name__)


class _EchoWriter:
    """Pseudo-buffer for StreamingHttpResponse CSV export."""

    def write(self, value: str) -> str:
        return value


class CompanyMetricViewSet(DemoReadOnlyMixin, ModelViewSet):
    serializer_class = CompanyMetricSerializer
    permission_classes = [IsStaffUser]

    def get_queryset(self):
        return orm.CompanyMetric.objects.all()

    def create(self, request: Request, *args, **kwargs) -> Response:
        if (block := self._demo_block()) is not None:
            return block
        try:
            use_case = CreateCompanyMetric(
                metric_repo=DjangoMetricRepository(),
                audit_repo=DjangoAuditLogRepository(),
            )
            dto = use_case.execute(
                CreateCompanyMetricCommand(
                    name=request.data['name'],
                    metric_type=request.data['metric_type'],
                    description=request.data.get('description'),
                    created_by_id=request.user.pk,
                )
            )
        except (ValueError, KeyError) as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'id': str(dto.id)}, status=status.HTTP_201_CREATED)

    def update(self, request: Request, pk: str = None, *args, **kwargs) -> Response:
        if (block := self._demo_block()) is not None:
            return block
        try:
            use_case = UpdateCompanyMetric(
                metric_repo=DjangoMetricRepository(),
                audit_repo=DjangoAuditLogRepository(),
            )
            dto = use_case.execute(
                UpdateCompanyMetricCommand(
                    metric_id=UUID(str(pk)),
                    name=request.data['name'],
                    description=request.data.get('description'),
                    updated_by_id=request.user.pk,
                )
            )
        except (ValueError, KeyError) as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'id': str(dto.id)})

    @action(detail=True, methods=['get'], url_path='series')
    def series(self, request: Request, pk: str = None) -> Response:
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        if not start_date_str or not end_date_str:
            return Response(
                {'detail': 'start_date and end_date query params are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            start_date = date.fromisoformat(start_date_str)
            end_date = date.fromisoformat(end_date_str)
        except ValueError:
            return Response(
                {'detail': 'Invalid date format. Use YYYY-MM-DD.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        use_case = GetMetricSeries(
            metric_repo=DjangoMetricRepository(),
            aggregation_service=MetricAggregationService(DjangoMetricRepository()),
        )
        try:
            dto = use_case.execute(
                GetMetricSeriesQuery(
                    metric_id=UUID(str(pk)),
                    start_date=start_date,
                    end_date=end_date,
                )
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'metric': {
                'id': str(dto.metric.id),
                'name': dto.metric.name,
                'metric_type': dto.metric.metric_type,
            },
            'revenue_snapshots': [
                {
                    'id': str(s.id),
                    'amount': str(s.amount),
                    'currency': s.currency,
                    'period_start': s.period_start.isoformat(),
                    'period_end': s.period_end.isoformat(),
                    'recorded_at': s.recorded_at.isoformat(),
                }
                for s in dto.revenue_snapshots
            ],
            'growth_snapshots': [
                {
                    'id': str(s.id),
                    'new_customers': s.new_customers,
                    'churned_customers': s.churned_customers,
                    'net_customers': s.net_customers,
                    'period_start': s.period_start.isoformat(),
                    'period_end': s.period_end.isoformat(),
                    'recorded_at': s.recorded_at.isoformat(),
                }
                for s in dto.growth_snapshots
            ],
        })

    @action(detail=True, methods=['get'], url_path='export')
    def export(self, request: Request, pk: str = None) -> StreamingHttpResponse:
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        try:
            start_date = date.fromisoformat(start_date_str) if start_date_str else date(2000, 1, 1)
            end_date = date.fromisoformat(end_date_str) if end_date_str else date.today()
        except ValueError:
            return Response(
                {'detail': 'Invalid date format. Use YYYY-MM-DD.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            metric_id = UUID(str(pk))
        except ValueError:
            return Response(
                {'detail': 'Invalid metric ID.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        revenue_qs = orm.RevenueSnapshot.objects.filter(
            metric_id=metric_id,
            period_start__lte=end_date,
            period_end__gte=start_date,
        ).order_by('period_start')

        def generate_rows():
            writer = csv.writer(_EchoWriter())
            yield writer.writerow(['type', 'period_start', 'period_end', 'amount', 'currency'])
            for snap in revenue_qs.iterator():
                yield writer.writerow([
                    'revenue',
                    snap.period_start.isoformat(),
                    snap.period_end.isoformat(),
                    str(snap.amount),
                    snap.currency,
                ])

        response = StreamingHttpResponse(generate_rows(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="metric-{pk}-export.csv"'
        return response


class RevenueSnapshotViewSet(
    DemoReadOnlyMixin, ListModelMixin, RetrieveModelMixin, CreateModelMixin, GenericViewSet
):
    serializer_class = RevenueSnapshotSerializer
    permission_classes = [IsStaffUser]

    def get_queryset(self):
        qs = orm.RevenueSnapshot.objects.all()
        metric_id = self.request.query_params.get('metric')
        if metric_id:
            qs = qs.filter(metric_id=metric_id)
        return qs

    def create(self, request: Request, *args, **kwargs) -> Response:
        if (block := self._demo_block()) is not None:
            return block
        try:
            use_case = RecordRevenueSnapshot(
                metric_repo=DjangoMetricRepository(),
                audit_repo=DjangoAuditLogRepository(),
            )
            dto = use_case.execute(
                RecordRevenueSnapshotCommand(
                    metric_id=UUID(str(request.data['metric'])),
                    amount=request.data['amount'],
                    currency=request.data.get('currency', 'USD'),
                    period_start=date.fromisoformat(request.data['period_start']),
                    period_end=date.fromisoformat(request.data['period_end']),
                    recorded_by_id=request.user.pk,
                )
            )
        except (ValueError, KeyError) as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'id': str(dto.id)}, status=status.HTTP_201_CREATED)


class CustomerGrowthSnapshotViewSet(
    DemoReadOnlyMixin, ListModelMixin, RetrieveModelMixin, CreateModelMixin, GenericViewSet
):
    serializer_class = CustomerGrowthSnapshotSerializer
    permission_classes = [IsStaffUser]

    def get_queryset(self):
        qs = orm.CustomerGrowthSnapshot.objects.all()
        metric_id = self.request.query_params.get('metric')
        if metric_id:
            qs = qs.filter(metric_id=metric_id)
        return qs

    def create(self, request: Request, *args, **kwargs) -> Response:
        if (block := self._demo_block()) is not None:
            return block
        try:
            new_customers = int(request.data['new_customers'])
            churned_customers = int(request.data['churned_customers'])
            use_case = RecordGrowthSnapshot(
                metric_repo=DjangoMetricRepository(),
                audit_repo=DjangoAuditLogRepository(),
            )
            dto = use_case.execute(
                RecordGrowthSnapshotCommand(
                    metric_id=UUID(str(request.data['metric'])),
                    new_customers=new_customers,
                    churned_customers=churned_customers,
                    period_start=date.fromisoformat(request.data['period_start']),
                    period_end=date.fromisoformat(request.data['period_end']),
                    recorded_by_id=request.user.pk,
                )
            )
        except (ValueError, KeyError) as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'id': str(dto.id)}, status=status.HTTP_201_CREATED)


class AlertRuleViewSet(DemoReadOnlyMixin, ModelViewSet):
    serializer_class = AlertRuleSerializer
    permission_classes = [IsStaffUser]

    def get_queryset(self):
        return orm.AlertRule.objects.all()

    def create(self, request: Request, *args, **kwargs) -> Response:
        if (block := self._demo_block()) is not None:
            return block
        try:
            use_case = CreateAlertRule(
                rule_repo=DjangoAlertRuleRepository(),
                audit_repo=DjangoAuditLogRepository(),
            )
            dto = use_case.execute(
                CreateAlertRuleCommand(
                    name=request.data['name'],
                    metric_id=UUID(str(request.data['metric'])),
                    threshold_value=request.data['threshold_value'],
                    operator=request.data['operator'],
                    severity=request.data['severity'],
                    created_by_id=request.user.pk,
                )
            )
        except (ValueError, KeyError) as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'id': str(dto.id)}, status=status.HTTP_201_CREATED)

    def update(self, request: Request, pk: str = None, *args, **kwargs) -> Response:
        if (block := self._demo_block()) is not None:
            return block
        try:
            use_case = UpdateAlertRule(
                rule_repo=DjangoAlertRuleRepository(),
                audit_repo=DjangoAuditLogRepository(),
            )
            dto = use_case.execute(
                UpdateAlertRuleCommand(
                    rule_id=UUID(str(pk)),
                    name=request.data['name'],
                    threshold_value=request.data['threshold_value'],
                    operator=request.data['operator'],
                    severity=request.data['severity'],
                    updated_by_id=request.user.pk,
                )
            )
        except (ValueError, KeyError) as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'id': str(dto.id)})

    def destroy(self, request: Request, pk: str = None, *args, **kwargs) -> Response:
        if (block := self._demo_block()) is not None:
            return block
        try:
            use_case = DeleteAlertRule(
                rule_repo=DjangoAlertRuleRepository(),
                audit_repo=DjangoAuditLogRepository(),
            )
            use_case.execute(
                DeleteAlertRuleCommand(
                    rule_id=UUID(str(pk)),
                    deleted_by_id=request.user.pk,
                )
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'], url_path='pause')
    def pause(self, request: Request, pk: str = None) -> Response:
        if (block := self._demo_block()) is not None:
            return block
        try:
            use_case = PauseAlertRule(
                rule_repo=DjangoAlertRuleRepository(),
                audit_repo=DjangoAuditLogRepository(),
            )
            dto = use_case.execute(
                PauseAlertRuleCommand(
                    rule_id=UUID(str(pk)),
                    paused_by_id=request.user.pk,
                )
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'status': dto.status})

    @action(detail=True, methods=['post'], url_path='activate')
    def activate(self, request: Request, pk: str = None) -> Response:
        if (block := self._demo_block()) is not None:
            return block
        try:
            use_case = ActivateAlertRule(
                rule_repo=DjangoAlertRuleRepository(),
                audit_repo=DjangoAuditLogRepository(),
            )
            dto = use_case.execute(
                ActivateAlertRuleCommand(
                    rule_id=UUID(str(pk)),
                    activated_by_id=request.user.pk,
                )
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'status': dto.status})


class DashboardAlertViewSet(
    DemoReadOnlyMixin, ListModelMixin, RetrieveModelMixin, GenericViewSet
):
    serializer_class = DashboardAlertSerializer
    permission_classes = [IsStaffUser]

    def get_queryset(self):
        return orm.DashboardAlert.objects.all()

    @action(detail=True, methods=['post'], url_path='acknowledge')
    def acknowledge(self, request: Request, pk: str = None) -> Response:
        if (block := self._demo_block()) is not None:
            return block
        try:
            use_case = AcknowledgeAlert(
                alert_repo=DjangoDashboardAlertRepository(),
                audit_repo=DjangoAuditLogRepository(),
            )
            dto = use_case.execute(
                AcknowledgeAlertCommand(
                    alert_id=UUID(str(pk)),
                    acknowledged_by_id=request.user.pk,
                )
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'status': dto.status})

    @action(detail=True, methods=['post'], url_path='resolve')
    def resolve(self, request: Request, pk: str = None) -> Response:
        if (block := self._demo_block()) is not None:
            return block
        try:
            use_case = ResolveAlert(
                alert_repo=DjangoDashboardAlertRepository(),
                audit_repo=DjangoAuditLogRepository(),
            )
            dto = use_case.execute(
                ResolveAlertCommand(
                    alert_id=UUID(str(pk)),
                    resolved_by_id=request.user.pk,
                )
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'status': dto.status})


class AuditLogEntryViewSet(ReadOnlyModelViewSet):
    serializer_class = AuditLogEntrySerializer
    permission_classes = [IsStaffUser]

    def get_queryset(self):
        qs = orm.AuditLogEntry.objects.all()
        resource_id = self.request.query_params.get('resource_id')
        if resource_id:
            qs = qs.filter(resource_id=resource_id)
        return qs

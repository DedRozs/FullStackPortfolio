from rest_framework.routers import DefaultRouter

from apps.ops_dashboard.infrastructure.viewsets import (
    AlertRuleViewSet,
    AuditLogEntryViewSet,
    CompanyMetricViewSet,
    CustomerGrowthSnapshotViewSet,
    DashboardAlertViewSet,
    RevenueSnapshotViewSet,
)

router = DefaultRouter()
router.register('metrics', CompanyMetricViewSet, basename='companymetric')
router.register('revenue-snapshots', RevenueSnapshotViewSet, basename='revenuesnapshot')
router.register('growth-snapshots', CustomerGrowthSnapshotViewSet, basename='customergrowthsnapshot')
router.register('alert-rules', AlertRuleViewSet, basename='alertrule')
router.register('alerts', DashboardAlertViewSet, basename='dashboardalert')
router.register('audit-log', AuditLogEntryViewSet, basename='auditlogentry')

urlpatterns = router.urls

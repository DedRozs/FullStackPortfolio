from rest_framework.routers import DefaultRouter

from apps.workflow_automation.infrastructure.viewsets import (
    AutomationActionViewSet,
    AutomationConditionViewSet,
    AutomationRunLogViewSet,
    AutomationRunViewSet,
    AutomationRuleViewSet,
)

router = DefaultRouter()
router.register('rules', AutomationRuleViewSet, basename='automationrule')
router.register('conditions', AutomationConditionViewSet, basename='automationcondition')
router.register('actions', AutomationActionViewSet, basename='automationaction')
router.register('runs', AutomationRunViewSet, basename='automationrun')
router.register('logs', AutomationRunLogViewSet, basename='automationrunlog')

urlpatterns = router.urls

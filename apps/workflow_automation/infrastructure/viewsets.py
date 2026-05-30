from __future__ import annotations

import logging

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.workflow_automation import models as orm
from apps.workflow_automation.application.dtos import (
    DisableRuleCommand,
    DryRunRuleCommand,
    EnableRuleCommand,
)
from apps.workflow_automation.application.use_cases import (
    DisableRule,
    DryRunRule,
    EnableRule,
)
from apps.workflow_automation.domain.value_objects import ConditionOperator
from apps.workflow_automation.infrastructure.permissions import IsStaffUser
from apps.workflow_automation.infrastructure.repositories import (
    DjangoAutomationActionRepository,
    DjangoAutomationConditionRepository,
    DjangoAutomationRuleRepository,
    DjangoAutomationRunLogRepository,
    DjangoAutomationRunRepository,
)
from apps.workflow_automation.infrastructure.serializers import (
    AutomationActionSerializer,
    AutomationConditionSerializer,
    AutomationRunLogSerializer,
    AutomationRunSerializer,
    AutomationRuleSerializer,
)
from apps.workflow_automation.registry import get_condition_evaluator

logger = logging.getLogger(__name__)


class AutomationRuleViewSet(ModelViewSet):
    queryset = orm.AutomationRule.objects.all()
    serializer_class = AutomationRuleSerializer
    permission_classes = [IsStaffUser]

    @action(detail=True, methods=['post'])
    def enable(self, request, pk=None):
        instance = get_object_or_404(orm.AutomationRule, pk=pk)
        rule_repo = DjangoAutomationRuleRepository()
        use_case = EnableRule(rule_repo=rule_repo)
        use_case.execute(EnableRuleCommand(rule_id=instance.id))
        instance.refresh_from_db()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def disable(self, request, pk=None):
        instance = get_object_or_404(orm.AutomationRule, pk=pk)
        rule_repo = DjangoAutomationRuleRepository()
        use_case = DisableRule(rule_repo=rule_repo)
        use_case.execute(DisableRuleCommand(rule_id=instance.id))
        instance.refresh_from_db()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def dry_run(self, request, pk=None):
        instance = get_object_or_404(orm.AutomationRule, pk=pk)
        context = request.data.get('context', {})

        rule_repo = DjangoAutomationRuleRepository()
        condition_repo = DjangoAutomationConditionRepository()
        action_repo = DjangoAutomationActionRepository()
        run_repo = DjangoAutomationRunRepository()
        run_log_repo = DjangoAutomationRunLogRepository()

        use_case = DryRunRule(
            rule_repo=rule_repo,
            condition_repo=condition_repo,
            action_repo=action_repo,
            run_repo=run_repo,
            run_log_repo=run_log_repo,
        )

        evaluators = {}
        for op in ConditionOperator:
            fn = get_condition_evaluator(op.value)
            if fn:
                evaluators[op.value] = fn
        use_case.set_condition_evaluators(evaluators)

        result = use_case.execute(DryRunRuleCommand(rule_id=instance.id, context_payload=context))
        return Response({
            'rule_id': str(result.rule_id),
            'conditions_passed': result.conditions_passed,
            'log_messages': result.log_messages,
            'would_execute_actions': result.would_execute_actions,
        })


class AutomationConditionViewSet(ModelViewSet):
    queryset = orm.AutomationCondition.objects.all()
    serializer_class = AutomationConditionSerializer
    permission_classes = [IsStaffUser]

    def get_queryset(self):
        rule_id = self.request.query_params.get('rule_id')
        if rule_id:
            return orm.AutomationCondition.objects.filter(rule_id=rule_id)
        return orm.AutomationCondition.objects.all()


class AutomationActionViewSet(ModelViewSet):
    queryset = orm.AutomationAction.objects.all()
    serializer_class = AutomationActionSerializer
    permission_classes = [IsStaffUser]

    def get_queryset(self):
        rule_id = self.request.query_params.get('rule_id')
        if rule_id:
            return orm.AutomationAction.objects.filter(rule_id=rule_id)
        return orm.AutomationAction.objects.all()


class AutomationRunViewSet(ModelViewSet):
    queryset = orm.AutomationRun.objects.all()
    serializer_class = AutomationRunSerializer
    permission_classes = [IsStaffUser]
    http_method_names = ['get', 'head', 'options']

    def get_queryset(self):
        rule_id = self.request.query_params.get('rule_id')
        if rule_id:
            return orm.AutomationRun.objects.filter(rule_id=rule_id)
        return orm.AutomationRun.objects.all()


class AutomationRunLogViewSet(ModelViewSet):
    queryset = orm.AutomationRunLog.objects.all()
    serializer_class = AutomationRunLogSerializer
    permission_classes = [IsStaffUser]
    http_method_names = ['get', 'head', 'options']

    def get_queryset(self):
        run_id = self.request.query_params.get('run_id')
        if run_id:
            return orm.AutomationRunLog.objects.filter(run_id=run_id)
        return orm.AutomationRunLog.objects.all()

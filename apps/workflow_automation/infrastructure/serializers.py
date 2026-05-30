from __future__ import annotations

from rest_framework import serializers

from apps.workflow_automation import models as orm


class AutomationRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = orm.AutomationRule
        fields = ['id', 'name', 'description', 'trigger_type', 'is_enabled', 'created_at']
        read_only_fields = ['id', 'created_at']


class AutomationConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = orm.AutomationCondition
        fields = ['id', 'rule', 'field_name', 'operator', 'expected_value', 'position']
        read_only_fields = ['id']


class AutomationActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = orm.AutomationAction
        fields = ['id', 'rule', 'action_type', 'parameters', 'position']
        read_only_fields = ['id']


class AutomationRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = orm.AutomationRun
        fields = [
            'id', 'rule', 'trigger_type', 'context_payload',
            'status', 'is_dry_run', 'started_at', 'completed_at', 'created_at',
        ]
        read_only_fields = [
            'id', 'rule', 'trigger_type', 'context_payload',
            'status', 'is_dry_run', 'started_at', 'completed_at', 'created_at',
        ]


class AutomationRunLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = orm.AutomationRunLog
        fields = ['id', 'run', 'level', 'message', 'logged_at']
        read_only_fields = ['id', 'run', 'level', 'message', 'logged_at']

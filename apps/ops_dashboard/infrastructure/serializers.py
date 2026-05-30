from __future__ import annotations

from rest_framework import serializers

from apps.ops_dashboard import models as orm


class CompanyMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = orm.CompanyMetric
        fields = ['id', 'name', 'metric_type', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class RevenueSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = orm.RevenueSnapshot
        fields = [
            'id', 'metric', 'amount', 'currency',
            'period_start', 'period_end', 'recorded_at',
        ]
        read_only_fields = ['id']


class CustomerGrowthSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = orm.CustomerGrowthSnapshot
        fields = [
            'id', 'metric', 'new_customers', 'churned_customers', 'net_customers',
            'period_start', 'period_end', 'recorded_at',
        ]
        read_only_fields = ['id', 'net_customers']


class AlertRuleSerializer(serializers.ModelSerializer):
    metric_name = serializers.CharField(source='metric.name', read_only=True)

    class Meta:
        model = orm.AlertRule
        fields = [
            'id', 'name', 'metric', 'metric_name', 'threshold_value', 'operator',
            'severity', 'status', 'last_evaluated_at', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'metric_name', 'created_at', 'updated_at']


class DashboardAlertSerializer(serializers.ModelSerializer):
    metric_name = serializers.CharField(source='metric.name', read_only=True)
    rule_name = serializers.CharField(source='rule.name', read_only=True)

    class Meta:
        model = orm.DashboardAlert
        fields = [
            'id', 'rule', 'rule_name', 'metric', 'metric_name', 'triggered_value',
            'threshold_value', 'operator', 'severity', 'status', 'acknowledged_at',
            'acknowledged_by', 'resolved_at', 'resolved_by', 'created_at',
        ]
        read_only_fields = [
            'id', 'rule', 'rule_name', 'metric', 'metric_name', 'triggered_value',
            'threshold_value', 'operator', 'severity', 'created_at',
        ]


class AuditLogEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = orm.AuditLogEntry
        fields = [
            'id', 'action', 'actor', 'resource_id', 'resource_type',
            'detail', 'created_at',
        ]
        read_only_fields = [
            'id', 'action', 'actor', 'resource_id', 'resource_type',
            'detail', 'created_at',
        ]

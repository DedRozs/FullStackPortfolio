from __future__ import annotations

from rest_framework import serializers

from apps.client_portal import models as orm


class ClientOrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = orm.ClientOrganization
        fields = ['id', 'name', 'slug', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = orm.UserProfile
        fields = ['id', 'user', 'email', 'is_client', 'organization', 'created_at']
        read_only_fields = ['id', 'created_at']


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = orm.Project
        fields = [
            'id', 'name', 'organization', 'status', 'description',
            'target_date', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class MilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = orm.Milestone
        fields = ['id', 'name', 'project', 'status', 'target_date', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class DeliverableSerializer(serializers.ModelSerializer):
    class Meta:
        model = orm.Deliverable
        fields = [
            'id', 'name', 'milestone', 'description',
            'current_version_number', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'current_version_number', 'created_at', 'updated_at']


class DeliverableVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = orm.DeliverableVersion
        fields = ['id', 'deliverable', 'version_number', 'notes', 'created_at']
        read_only_fields = ['id', 'version_number', 'created_at']


class ApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = orm.Approval
        fields = [
            'id', 'deliverable_version', 'reviewer', 'status',
            'comment', 'decided_at', 'created_at',
        ]
        read_only_fields = ['id', 'decided_at', 'created_at']


class MessageThreadSerializer(serializers.ModelSerializer):
    class Meta:
        model = orm.MessageThread
        fields = ['id', 'subject', 'project', 'created_at']
        read_only_fields = ['id', 'created_at']


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = orm.Message
        fields = ['id', 'thread', 'sender', 'body', 'created_at']
        read_only_fields = ['id', 'created_at']


class FileRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = orm.FileRecord
        fields = [
            'id', 'filename', 'storage_path', 'mime_type', 'file_size_bytes',
            'deliverable_version', 'message', 'uploaded_by', 'created_at',
        ]
        read_only_fields = ['id', 'storage_path', 'created_at']


class InvoiceRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = orm.InvoiceRecord
        fields = [
            'id', 'organization', 'project', 'status', 'amount',
            'due_date', 'issued_at', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'issued_at', 'created_at', 'updated_at']


class ActivityEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = orm.ActivityEvent
        fields = [
            'id', 'event_type', 'actor', 'project', 'organization',
            'payload', 'occurred_at',
        ]
        read_only_fields = ['id', 'occurred_at']

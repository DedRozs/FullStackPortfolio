from __future__ import annotations

from dj_rest_auth.serializers import UserDetailsSerializer as BaseUserDetailsSerializer


class UserDetailsSerializer(BaseUserDetailsSerializer):
    """Extends the default dj-rest-auth user serializer to include is_staff."""

    class Meta(BaseUserDetailsSerializer.Meta):
        fields = (*BaseUserDetailsSerializer.Meta.fields, 'is_staff')
        read_only_fields = (*BaseUserDetailsSerializer.Meta.read_only_fields, 'is_staff')

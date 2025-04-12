# serializers.py
from rest_framework import serializers
from .models import ApiStatus


class ApiStatusSerializer(serializers.ModelSerializer):
    alternate_api_id = serializers.IntegerField(
        source="alternate_api.id", read_only=True
    )
    alternate_api_name = serializers.CharField(
        source="alternate_api.api_name", read_only=True
    )

    class Meta:
        model = ApiStatus
        fields = [
            "id",
            "api_name",
            "is_enabled",
            "api_provider",
            "description",
            "alternate_api_id",
            "alternate_api_name",
        ]


class ApiStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiStatus
        fields = ["is_enabled"]

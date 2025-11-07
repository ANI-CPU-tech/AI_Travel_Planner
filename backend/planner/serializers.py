from rest_framework import serializers
from .models import Plan
from Location.serializers import LocationSerializer, HomesSerializer
from Location.models import Location, Homes


class PlanSerializer(serializers.ModelSerializer):
    locations = LocationSerializer(many=True, read_only=True)
    homes = HomesSerializer(many=True, read_only=True)

    class Meta:
        model = Plan
        fields = [
            "id",
            "user",
            "title",
            "start_date",
            "end_date",
            "num_days",
            "summary",
            "itinerary",
            "locations",
            "homes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["user", "created_at", "updated_at"]


class PlanCreateSerializer(serializers.ModelSerializer):
    """Used for creating plans: accepts raw itinerary JSON produced by Gemini."""
    class Meta:
        model = Plan
        fields = ["title", "start_date", "end_date", "num_days", "summary", "itinerary"]
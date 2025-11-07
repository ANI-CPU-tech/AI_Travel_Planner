from django.db import models
from django.conf import settings
from Location.models import Location, Homes


class Plan(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="plans")
    title = models.CharField(max_length=255, blank=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    num_days = models.IntegerField(blank=True, null=True)
    summary = models.TextField(blank=True, null=True)
    # Raw itinerary as produced by Gemini (JSON blob)
    itinerary = models.JSONField(blank=True, null=True)
    # Link to Location and Homes objects referenced in the plan
    locations = models.ManyToManyField(Location, blank=True, related_name="plans")
    homes = models.ManyToManyField(Homes, blank=True, related_name="plans")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Plan: {self.title or self.user.email or self.user.username} ({self.created_at.date()})"
from django.db import models

# Create your models here.

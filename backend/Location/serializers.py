from rest_framework import serializers
from django.conf import settings
from .models import Location, Homes


class LocationSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Location
        # include model fields plus `image_url`
        fields = '__all__'

    def get_image_url(self, obj):
        """Return an absolute URL for the location image when possible."""
        img = getattr(obj, 'location_image', None)
        if not img:
            return None
        try:
            url = img.url
        except Exception:
            # sometimes the field already contains a URL string
            url = img

        request = self.context.get('request') if hasattr(self, 'context') else None
        if request:
            return request.build_absolute_uri(url)
        # fallback: if MEDIA_URL is configured and url is relative, try to join
        if isinstance(url, str) and url.startswith('/'):
            base = getattr(settings, 'SITE_BASE', '') or ''
            return base + url
        return url


class HomesSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Homes
        fields = '__all__'

    def get_image_url(self, obj):
        img = getattr(obj, 'location_image', None)
        if not img:
            return None
        try:
            url = img.url
        except Exception:
            url = img
        request = self.context.get('request') if hasattr(self, 'context') else None
        if request:
            return request.build_absolute_uri(url)
        if isinstance(url, str) and url.startswith('/'):
            base = getattr(settings, 'SITE_BASE', '') or ''
            return base + url
        return url

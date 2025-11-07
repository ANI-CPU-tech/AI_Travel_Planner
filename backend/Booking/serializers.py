from rest_framework import serializers
from .models import BookingLocation,BookingHome

class BookingLocationSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    location_name = serializers.ReadOnlyField(source='location.location_name')

    class Meta:
        model = BookingLocation
        fields = '__all__'

class BookingHomeSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.email')
    home_name = serializers.ReadOnlyField(source='home.location_name')

    class Meta:
        model = BookingHome
        fields = '__all__'

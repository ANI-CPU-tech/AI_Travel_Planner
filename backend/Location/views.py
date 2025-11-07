from rest_framework import viewsets, permissions
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import Location,Homes
from .serializers import LocationSerializer,HomesSerializer

class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

class HomesViewSet(viewsets.ModelViewSet):
    queryset = Homes.objects.all()
    serializer_class = HomesSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


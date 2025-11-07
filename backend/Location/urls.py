# location/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LocationViewSet,HomesViewSet

# Create a router and register the Location viewset
router = DefaultRouter()
router.register(r'locations', LocationViewSet, basename='location')
router.register(r'homes', HomesViewSet, basename='homes')
urlpatterns = [
    path('', include(router.urls)),
]

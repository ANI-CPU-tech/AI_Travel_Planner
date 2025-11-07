from rest_framework.routers import DefaultRouter
from .views import PlanViewSet
from django.urls import path, include

router = DefaultRouter()
router.register(r'plans', PlanViewSet, basename='plan')

urlpatterns = [
    path('', include(router.urls)),
]

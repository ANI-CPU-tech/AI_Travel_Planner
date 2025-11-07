from rest_framework.routers import DefaultRouter
from .views import BookingViewSet,BookingHomeViewSet

router = DefaultRouter()
router.register(r'locations', BookingViewSet, basename='booking')
router.register(r'homes', BookingHomeViewSet, basename='bookinghome')
urlpatterns = router.urls

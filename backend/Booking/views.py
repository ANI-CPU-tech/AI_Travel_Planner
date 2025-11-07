from rest_framework import viewsets, permissions
from .models import BookingLocation,BookingHome
from .serializers import BookingLocationSerializer,BookingHomeSerializer

class BookingViewSet(viewsets.ModelViewSet):
    queryset = BookingLocation.objects.all()
    serializer_class = BookingLocationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Users only see their own bookings
        return BookingLocation.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        location = serializer.validated_data.get('location')

        
        average_cost = location.average_cost if location else None

        serializer.save(
            user=self.request.user,
            average_cost=average_cost
        )

class BookingHomeViewSet(viewsets.ModelViewSet):
    queryset = BookingHome.objects.all()
    serializer_class = BookingHomeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Users only see their own bookings
        return BookingHome.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        home = serializer.validated_data.get('home')

        
        average_cost = home.average_cost if home else None

        serializer.save(
            user=self.request.user,
            average_cost=average_cost
        )


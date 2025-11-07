from django.db import models
from django.conf import settings
from Location.models import Location,Homes

class BookingLocation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    booking_date = models.DateTimeField(auto_now_add=True)
    travel_date = models.DateField()
    average_cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    number_of_people = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.user.username} → {self.location.location_name}"

class BookingHome(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='home_bookings'
    )
    home = models.ForeignKey(
        Homes,
        on_delete=models.CASCADE,
        related_name='home_bookings'
    )
    booking_date = models.DateTimeField(auto_now_add=True)
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    average_cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    number_of_guests = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.user.email} → {self.home.location_name}"

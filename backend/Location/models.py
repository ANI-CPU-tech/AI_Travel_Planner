from django.db import models

class Location(models.Model):
    CATEGORY_CHOICES = [
        ('nature', 'Nature'),
        ('city', 'City'),
        ('adventure', 'Adventure'),
        ('beach', 'Beach'),
        ('historical', 'Historical'),
        ('romantic', 'Romantic'),
        ('wildlife', 'Wildlife'),
    ]

    location_name = models.CharField(max_length=255)
    country = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='nature')
    location_image = models.ImageField(upload_to='locations/', blank=True, null=True)
    best_time_to_visit = models.CharField(max_length=100, blank=True, null=True)
    average_cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.location_name

class Homes(models.Model):
    CATEGORY_CHOICES = [
        ('nature', 'Nature'),
        ('city', 'City'),
        ('adventure', 'Adventure'),
        ('beach', 'Beach'),
        ('historical', 'Historical'),
        ('romantic', 'Romantic'),
        ('wildlife', 'Wildlife'),
    ]

    location_name = models.CharField(max_length=255)
    country = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='nature')
    location_image = models.ImageField(upload_to='locations/', blank=True, null=True)
    best_time_to_visit = models.CharField(max_length=100, blank=True, null=True)
    average_cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.location_name
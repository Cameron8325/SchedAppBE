from django.db import models
from django.contrib.auth.models import User

class AvailableDay(models.Model):
    DAY_TYPES = [
        ("tea_tasting", "Tea Tasting"),
        ("intro_gongfu", "Intro to Gongfu"),
        ("guided_meditation", "Guided Meditation"),
    ]
    date = models.DateField(unique=True)
    type = models.CharField(max_length=20, choices=DAY_TYPES, default='tea_tasting')

    def __str__(self):
        return f"{self.date} - {self.get_type_display() if self.type else 'Available'}"

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('denied', 'Denied'),
        ('flagged', 'Flagged'),
        ('to_completion', 'To Completion'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # Allow null for walk-ins
    date = models.DateField()
    day_type = models.CharField(max_length=20, choices=AvailableDay.DAY_TYPES, default='tea_tasting')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    spots_left = models.IntegerField(default=4)
    reason = models.CharField(max_length=255, blank=True, null=True)

    # Walk-in specific fields
    walk_in_first_name = models.CharField(max_length=255, blank=True, null=True)
    walk_in_last_name = models.CharField(max_length=255, blank=True, null=True)
    walk_in_email = models.EmailField(max_length=255, blank=True, null=True)
    walk_in_phone = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        if self.user:
            return f"{self.user.username} - {self.date} - {self.status}"
        return f"Walk-in {self.walk_in_first_name} {self.walk_in_last_name} - {self.date} - {self.status}"
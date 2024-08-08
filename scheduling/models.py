from django.db import models
from django.contrib.auth.models import User

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('denied', 'Denied'),
        ('flagged', 'Flagged'),
        ('to_completion', 'To Completion'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    spots_left = models.IntegerField(default=4)

    def __str__(self):
        return f"{self.user.username} - {self.date} - {self.status}"

from django.db import models

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


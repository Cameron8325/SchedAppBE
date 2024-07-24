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


class UnavailableDay(models.Model):
    date = models.DateField(unique=True)
    reason = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.date} - {self.reason if self.reason else 'Unavailable'}"

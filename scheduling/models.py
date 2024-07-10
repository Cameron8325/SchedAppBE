from django.db import models
from django.contrib.auth.models import User

class Appointment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=10, choices=[('pending', 'Pending'), ('confirmed', 'Confirmed')])
    spots_left = models.IntegerField(default=4)

    def __str__(self):
        return f"{self.user.username} - {self.date} - {self.status}"

class UnavailableDay(models.Model):
    date = models.DateField(unique=True)
    reason = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.date} - {self.reason if self.reason else 'Unavailable'}"

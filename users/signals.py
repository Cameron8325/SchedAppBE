from django.db.models.signals import pre_save, post_save
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.dispatch import receiver
from django.utils import timezone
from .models import Profile

@receiver(pre_save, sender=User)
def store_old_password(sender, instance, **kwargs):
    if instance.pk:
        # Retrieve the existing user from the database
        try:
            existing_user = User.objects.get(pk=instance.pk)
            instance._old_password = existing_user.password
        except User.DoesNotExist:
            instance._old_password = None
    else:
        instance._old_password = None

@receiver(post_save, sender=User)
def invalidate_sessions_on_password_change(sender, instance, **kwargs):
    if hasattr(instance, '_old_password') and instance._old_password != instance.password:
        # The password has changed
        # Invalidate all active sessions for this user
        sessions = Session.objects.filter(expire_date__gte=timezone.now())
        for session in sessions:
            data = session.get_decoded()
            if data.get('_auth_user_id') == str(instance.id):
                session.delete()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

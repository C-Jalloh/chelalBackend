from django.db.models.signals import post_save, post_delete
from django.contrib.auth.signals import user_logged_in, user_logged_out # Corrected import path
from django.dispatch import receiver
from django.forms.models import model_to_dict
from django.utils import timezone
from django.conf import settings
from datetime import date # Import date from datetime

from .models import AuditLog, Patient, Prescription, InventoryItem, User, LabOrder, LabOrderItem, LabResultValue

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    AuditLog.objects.create(
        user=user,
        action="login",
        description=f'User {user.username} logged in.'
    )

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    if user:
        AuditLog.objects.create(
            user=user,
            action="logout",
            description=f'User {user.username} logged out.'
        )

@receiver(post_save, sender=Patient)
@receiver(post_save, sender=Prescription)
@receiver(post_save, sender=InventoryItem)
@receiver(post_save, sender=LabOrder)
@receiver(post_save, sender=LabOrderItem)
@receiver(post_save, sender=LabResultValue)
def log_model_save(sender, instance, created, **kwargs):
    action = "create" if created else "edit"
    description = f'{sender.__name__} {action}d: {instance}'
    details = model_to_dict(instance)

    # Convert date objects to strings for JSON serialization
    for key, value in details.items():
        if isinstance(value, timezone.datetime):
            details[key] = value.isoformat()
        elif isinstance(value, date): # Use the imported date class
            details[key] = value.strftime('%Y-%m-%d')

    # Attempt to get the user from kwargs or request context if available
    user = kwargs.get('user', None)
    # If user is not in kwargs, try to get it from the current request (requires middleware)
    # This part might need a custom middleware to attach user to the request object
    # For now, we'll rely on the signal sender or kwargs

    AuditLog.objects.create(
        user=user,
        action=action,
        object_type=sender.__name__,
        object_id=instance.pk,
        description=description,
        details=details
    )

@receiver(post_delete, sender=Patient)
@receiver(post_delete, sender=Prescription)
@receiver(post_delete, sender=InventoryItem)
@receiver(post_delete, sender=LabOrder)
@receiver(post_delete, sender=LabOrderItem)
@receiver(post_delete, sender=LabResultValue)
def log_model_delete(sender, instance, **kwargs):
    description = f'{sender.__name__} deleted: {instance}'
    details = model_to_dict(instance)

    # Convert date objects to strings for JSON serialization
    for key, value in details.items():
        if isinstance(value, timezone.datetime):
            details[key] = value.isoformat()
        elif isinstance(value, date): # Use the imported date class
            details[key] = value.strftime('%Y-%m-%d')

    # Attempt to get the user from kwargs or request context if available
    user = kwargs.get('user', None)

    AuditLog.objects.create(
        user=user,
        action="delete",
        object_type=sender.__name__,
        object_id=instance.pk,
        description=description,
        details=details
    )

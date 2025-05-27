from celery import shared_task
from .views import schedule_upcoming_appointment_reminders
from .tasks import send_appointment_followup_task
from .models import Appointment
from django.utils import timezone

@shared_task
def periodic_appointment_reminder():
    # Schedule reminders for appointments 24 hours in advance
    schedule_upcoming_appointment_reminders(hours_before=24)

@shared_task
def periodic_appointment_followup():
    # Send follow-ups for appointments completed 1 hour ago
    now = timezone.now()
    one_hour_ago = now - timezone.timedelta(hours=1)
    appointments = Appointment.objects.filter(
        status="completed",
        updated_at__gte=one_hour_ago,
        updated_at__lt=now
    )
    for appointment in appointments:
        send_appointment_followup_task.delay(appointment.id)

from celery import shared_task
from .models import Appointment
from django.utils import timezone

@shared_task
def send_appointment_reminder_task(appointment_id, notification_type="reminder"):
    try:
        appointment = Appointment.objects.get(id=appointment_id)
        from .views import send_appointment_sms_reminder
        success, result = send_appointment_sms_reminder(appointment, notification_type)
        return {'success': success, 'result': result}
    except Appointment.DoesNotExist:
        return {'success': False, 'result': 'Appointment not found'}

@shared_task
def send_appointment_email_reminder_task(appointment_id, notification_type="reminder"):
    from .models import Appointment
    try:
        appointment = Appointment.objects.get(id=appointment_id)
        from .views import send_appointment_email_reminder
        success, result = send_appointment_email_reminder(appointment, notification_type)
        return {'success': success, 'result': result}
    except Appointment.DoesNotExist:
        return {'success': False, 'result': 'Appointment not found'}

@shared_task
def send_appointment_followup_task(appointment_id):
    from .models import Appointment
    try:
        appointment = Appointment.objects.get(id=appointment_id)
        from .views import send_appointment_sms_reminder, send_appointment_email_reminder
        # Send SMS follow-up
        send_appointment_sms_reminder(appointment, notification_type="followup")
        # Send Email follow-up
        send_appointment_email_reminder(appointment, notification_type="followup")
        return {'success': True, 'result': 'Follow-up sent'}
    except Appointment.DoesNotExist:
        return {'success': False, 'result': 'Appointment not found'}

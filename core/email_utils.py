from django.core.mail import send_mail
from django.conf import settings

def send_appointment_email(to_email, subject, message):
    """
    Send an appointment-related email.
    :param to_email: Recipient email address
    :param subject: Email subject
    :param message: Email body
    :return: (success, error_message)
    """
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [to_email],
            fail_silently=False,
        )
        return True, ''
    except Exception as e:
        return False, str(e)

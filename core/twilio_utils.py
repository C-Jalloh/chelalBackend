import os
from django.conf import settings
from twilio.rest import Client


def send_sms_via_twilio(to_number, message):
    """
    Send an SMS using Twilio.
    :param to_number: Recipient phone number in E.164 format (e.g. +2547XXXXXXX)
    :param message: Message string
    :return: (success, sid or error message)
    """
    account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', os.environ.get('TWILIO_ACCOUNT_SID'))
    auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', os.environ.get('TWILIO_AUTH_TOKEN'))
    from_number = getattr(settings, 'TWILIO_PHONE_NUMBER', os.environ.get('TWILIO_PHONE_NUMBER'))
    if not (account_sid and auth_token and from_number):
        return False, 'Twilio configuration missing.'
    try:
        client = Client(account_sid, auth_token)
        message_obj = client.messages.create(
            body=message,
            from_=from_number,
            to=to_number
        )
        return True, message_obj.sid
    except Exception as e:
        return False, str(e)

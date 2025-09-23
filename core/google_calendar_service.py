import os
import logging
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
from django.conf import settings

from .models import Appointment, GoogleCalendarToken

logger = logging.getLogger(__name__)

class GoogleCalendarService:
    """
    Service class for Google Calendar integration
    """

    def __init__(self):
        self.client_id = getattr(settings, 'GOOGLE_CLIENT_ID', None)
        self.client_secret = getattr(settings, 'GOOGLE_CLIENT_SECRET', None)
        self.redirect_uri = getattr(settings, 'GOOGLE_REDIRECT_URI', None)

        if not all([self.client_id, self.client_secret, self.redirect_uri]):
            logger.warning("Google Calendar credentials not properly configured")

    def get_credentials(self, token_obj):
        """
        Get Google OAuth2 credentials from stored tokens
        """
        try:
            credentials = Credentials(
                token=token_obj.access_token,
                refresh_token=token_obj.refresh_token,
                token_uri='https://oauth2.googleapis.com/token',
                client_id=self.client_id,
                client_secret=self.client_secret,
                scopes=['https://www.googleapis.com/auth/calendar']
            )

            # Refresh token if expired
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                # Update stored tokens
                token_obj.access_token = credentials.token
                token_obj.token_expiry = datetime.fromtimestamp(credentials.expiry.timestamp())
                token_obj.save()

            return credentials
        except Exception as e:
            logger.error(f"Error getting credentials: {str(e)}")
            return None

    def exchange_code_for_tokens(self, code):
        """
        Exchange authorization code for access and refresh tokens
        """
        try:
            import requests
            from datetime import datetime, timedelta

            logger.info(f"Client ID: {self.client_id}")
            logger.info(f"Client Secret: {self.client_secret[:10]}...")  # Log first 10 chars for debugging
            logger.info(f"Redirect URI: {self.redirect_uri}")
            logger.info(f"Code: {code[:20]}...")  # Log first 20 chars of code

            # Check if client secret is still placeholder
            if self.client_secret == "YOUR_ACTUAL_CLIENT_SECRET_HERE":
                logger.error("Client secret is still placeholder - please update .env file")
                return None

            # Direct token exchange using requests
            token_url = 'https://oauth2.googleapis.com/token'
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': self.redirect_uri
            }

            logger.info("Making token request...")
            response = requests.post(token_url, data=data)
            logger.info(f"Token response status: {response.status_code}")
            logger.info(f"Token response: {response.text}")

            if response.status_code == 200:
                token_data = response.json()
                logger.info("Token exchange successful")

                # Calculate expiry time
                expires_in = token_data.get('expires_in', 3600)
                expires_at = datetime.now() + timedelta(seconds=expires_in)

                return {
                    'access_token': token_data['access_token'],
                    'refresh_token': token_data.get('refresh_token'),
                    'expires_at': expires_at.timestamp()
                }
            else:
                logger.error(f"Token exchange failed: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"Error exchanging code for tokens: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def create_appointment_event(self, appointment, token_obj):
        """
        Create a Google Calendar event for an appointment
        """
        try:
            credentials = self.get_credentials(token_obj)
            if not credentials:
                return None

            service = build('calendar', 'v3', credentials=credentials)

            # Create event data
            event_data = {
                'summary': f'Appointment with {appointment.patient.first_name} {appointment.patient.last_name}',
                'description': f'Appointment scheduled for {appointment.date} at {appointment.time}',
                'start': {
                    'dateTime': f'{appointment.date}T{appointment.time}',
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': f'{appointment.date}T{(datetime.combine(appointment.date, appointment.time) + timedelta(hours=1)).time()}',
                    'timeZone': 'UTC',
                },
                'attendees': [
                    {'email': appointment.doctor.email} if appointment.doctor.email else None,
                    # Add patient email if available
                ],
                'reminders': {
                    'useDefault': True,
                },
            }

            # Remove None attendees
            event_data['attendees'] = [attendee for attendee in event_data['attendees'] if attendee]

            event = service.events().insert(
                calendarId=token_obj.calendar_id,
                body=event_data
            ).execute()

            logger.info(f"Created calendar event: {event.get('id')}")
            return event.get('id')

        except HttpError as e:
            logger.error(f"Google Calendar API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error creating calendar event: {str(e)}")
            return None

    def update_appointment_event(self, appointment, token_obj):
        """
        Update an existing Google Calendar event
        """
        try:
            credentials = self.get_credentials(token_obj)
            if not credentials:
                return False

            service = build('calendar', 'v3', credentials=credentials)

            # Get existing event (assuming we store event_id somewhere)
            # For now, we'll need to find the event by date/time
            events_result = service.events().list(
                calendarId=token_obj.calendar_id,
                timeMin=f'{appointment.date}T00:00:00Z',
                timeMax=f'{appointment.date}T23:59:59Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])
            target_event = None

            # Find event matching appointment time
            appointment_datetime = f'{appointment.date}T{appointment.time}'
            for event in events:
                if event['start'].get('dateTime', '').startswith(appointment_datetime):
                    target_event = event
                    break

            if not target_event:
                logger.warning(f"No matching calendar event found for appointment {appointment.id}")
                return False

            # Update event
            updated_event = {
                'summary': f'Appointment with {appointment.patient.first_name} {appointment.patient.last_name}',
                'description': f'Appointment scheduled for {appointment.date} at {appointment.time}',
                'start': {
                    'dateTime': f'{appointment.date}T{appointment.time}',
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': f'{appointment.date}T{(datetime.combine(appointment.date, appointment.time) + timedelta(hours=1)).time()}',
                    'timeZone': 'UTC',
                },
            }

            service.events().update(
                calendarId=token_obj.calendar_id,
                eventId=target_event['id'],
                body=updated_event
            ).execute()

            logger.info(f"Updated calendar event: {target_event['id']}")
            return True

        except HttpError as e:
            logger.error(f"Google Calendar API error: {e}")
            return False
        except Exception as e:
            logger.error(f"Error updating calendar event: {str(e)}")
            return False

    def delete_appointment_event(self, appointment, token_obj):
        """
        Delete a Google Calendar event
        """
        try:
            credentials = self.get_credentials(token_obj)
            if not credentials:
                return False

            service = build('calendar', 'v3', credentials=credentials)

            # Find and delete event (similar to update)
            events_result = service.events().list(
                calendarId=token_obj.calendar_id,
                timeMin=f'{appointment.date}T00:00:00Z',
                timeMax=f'{appointment.date}T23:59:59Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])
            target_event = None

            appointment_datetime = f'{appointment.date}T{appointment.time}'
            for event in events:
                if event['start'].get('dateTime', '').startswith(appointment_datetime):
                    target_event = event
                    break

            if not target_event:
                logger.warning(f"No matching calendar event found for appointment {appointment.id}")
                return False

            service.events().delete(
                calendarId=token_obj.calendar_id,
                eventId=target_event['id']
            ).execute()

            logger.info(f"Deleted calendar event: {target_event['id']}")
            return True

        except HttpError as e:
            logger.error(f"Google Calendar API error: {e}")
            return False
        except Exception as e:
            logger.error(f"Error deleting calendar event: {str(e)}")
            return False

    def get_calendar_events(self, token_obj, start_date, end_date):
        """
        Get calendar events for a date range
        """
        try:
            credentials = self.get_credentials(token_obj)
            if not credentials:
                return []

            service = build('calendar', 'v3', credentials=credentials)

            events_result = service.events().list(
                calendarId=token_obj.calendar_id,
                timeMin=f'{start_date}T00:00:00Z',
                timeMax=f'{end_date}T23:59:59Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])
            return events

        except HttpError as e:
            logger.error(f"Google Calendar API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Error getting calendar events: {str(e)}")
            return []

    def test_connection(self, token_obj):
        """
        Test if the calendar connection is working
        """
        try:
            credentials = self.get_credentials(token_obj)
            if not credentials:
                return False

            service = build('calendar', 'v3', credentials=credentials)

            # Try to get calendar list
            calendar_list = service.calendarList().list().execute()
            return len(calendar_list.get('items', [])) > 0

        except Exception as e:
            logger.error(f"Error testing calendar connection: {str(e)}")
            return False

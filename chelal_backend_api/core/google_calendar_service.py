from django.conf import settings
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
import os
import pickle
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class GoogleCalendarService:
    """Backend service for Google Calendar integration"""

    def __init__(self):
        self.credentials = None
        self.service = None

    def get_credentials(self, user) -> Optional[Credentials]:
        """Get Google OAuth credentials for a user"""
        # In a real implementation, you'd store tokens in the database
        # For now, we'll use file-based storage as an example
        token_path = f'/tmp/google_tokens_{user.id}.pickle'

        if os.path.exists(token_path):
            with open(token_path, 'rb') as token:
                self.credentials = pickle.load(token)

        # If credentials exist but are expired, refresh them
        if self.credentials and self.credentials.expired and self.credentials.refresh_token:
            try:
                self.credentials.refresh(Request())
                # Save refreshed credentials
                with open(token_path, 'wb') as token:
                    pickle.dump(self.credentials, token)
            except Exception as e:
                logger.error(f"Failed to refresh Google credentials: {e}")
                return None

        return self.credentials

    def build_service(self, credentials: Credentials):
        """Build Google Calendar API service"""
        try:
            self.service = build('calendar', 'v3', credentials=credentials)
            return self.service
        except Exception as e:
            logger.error(f"Failed to build Google Calendar service: {e}")
            return None

    def create_appointment_event(self, user, appointment_data: Dict) -> Optional[str]:
        """Create a Google Calendar event for an appointment"""
        credentials = self.get_credentials(user)
        if not credentials:
            return None

        service = self.build_service(credentials)
        if not service:
            return None

        # Parse appointment data
        start_datetime = datetime.fromisoformat(appointment_data['scheduled_datetime'])
        duration = appointment_data.get('duration_minutes', 60)
        end_datetime = start_datetime + timedelta(minutes=duration)

        event = {
            'summary': f"{appointment_data['appointment_type']} - {appointment_data['patient_name']}",
            'description': f"""
Patient: {appointment_data['patient_name']}
Doctor: {appointment_data['doctor_name']}
Type: {appointment_data['appointment_type']}
Notes: {appointment_data.get('notes', 'N/A')}

Created by Chelal HMS
            """.strip(),
            'start': {
                'dateTime': start_datetime.isoformat(),
                'timeZone': 'UTC',  # Adjust based on your timezone
            },
            'end': {
                'dateTime': end_datetime.isoformat(),
                'timeZone': 'UTC',
            },
            'location': appointment_data.get('location', 'Chelal Hospital'),
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 30},
                    {'method': 'email', 'minutes': 60},
                ],
            },
        }

        # Add patient email if available
        if appointment_data.get('patient_email'):
            event['attendees'] = [{
                'email': appointment_data['patient_email'],
                'displayName': appointment_data['patient_name']
            }]

        try:
            created_event = service.events().insert(
                calendarId='primary',
                body=event,
                sendUpdates='all'  # Notify attendees
            ).execute()

            logger.info(f"Created Google Calendar event: {created_event['id']}")
            return created_event['id']

        except HttpError as e:
            logger.error(f"Google Calendar API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating calendar event: {e}")
            return None

    def update_appointment_event(self, user, event_id: str, appointment_data: Dict) -> bool:
        """Update an existing Google Calendar event"""
        credentials = self.get_credentials(user)
        if not credentials:
            return False

        service = self.build_service(credentials)
        if not service:
            return False

        # Similar to create, but update existing event
        start_datetime = datetime.fromisoformat(appointment_data['scheduled_datetime'])
        duration = appointment_data.get('duration_minutes', 60)
        end_datetime = start_datetime + timedelta(minutes=duration)

        event = {
            'summary': f"{appointment_data['appointment_type']} - {appointment_data['patient_name']}",
            'description': f"""
Patient: {appointment_data['patient_name']}
Doctor: {appointment_data['doctor_name']}
Type: {appointment_data['appointment_type']}
Notes: {appointment_data.get('notes', 'N/A')}

Updated by Chelal HMS
            """.strip(),
            'start': {
                'dateTime': start_datetime.isoformat(),
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end_datetime.isoformat(),
                'timeZone': 'UTC',
            },
        }

        try:
            service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event,
                sendUpdates='all'
            ).execute()

            logger.info(f"Updated Google Calendar event: {event_id}")
            return True

        except HttpError as e:
            logger.error(f"Google Calendar API error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error updating calendar event: {e}")
            return False

    def delete_appointment_event(self, user, event_id: str) -> bool:
        """Delete a Google Calendar event"""
        credentials = self.get_credentials(user)
        if not credentials:
            return False

        service = self.build_service(credentials)
        if not service:
            return False

        try:
            service.events().delete(
                calendarId='primary',
                eventId=event_id,
                sendUpdates='all'
            ).execute()

            logger.info(f"Deleted Google Calendar event: {event_id}")
            return True

        except HttpError as e:
            logger.error(f"Google Calendar API error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting calendar event: {e}")
            return False

    def get_calendar_events(self, user, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get calendar events for a date range"""
        credentials = self.get_credentials(user)
        if not credentials:
            return []

        service = self.build_service(credentials)
        if not service:
            return []

        try:
            events_result = service.events().list(
                calendarId='primary',
                timeMin=start_date.isoformat() + 'Z',
                timeMax=end_date.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            return events_result.get('items', [])

        except HttpError as e:
            logger.error(f"Google Calendar API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching calendar events: {e}")
            return []


# Global service instance
google_calendar_service = GoogleCalendarService()

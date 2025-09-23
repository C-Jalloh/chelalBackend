from django.shortcuts import redirect
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
import json
import logging
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request

from .models import User, Appointment, GoogleCalendarToken
from .google_calendar_service import GoogleCalendarService

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def google_calendar_auth(request):
    """
    Initiate Google OAuth flow for calendar integration
    """
    try:
        # Include user ID in state parameter for secure callback identification
        state = f"user_{request.user.id}"

        # This would typically redirect to Google's OAuth consent screen
        # For now, return instructions for manual setup
        auth_url = "https://accounts.google.com/o/oauth2/auth?" + "&".join([
            "client_id=" + settings.GOOGLE_CLIENT_ID,
            "redirect_uri=" + settings.GOOGLE_REDIRECT_URI,
            "scope=https://www.googleapis.com/auth/calendar",
            "response_type=code",
            "access_type=offline",
            "prompt=consent",
            "state=" + state
        ])

        return Response({
            'auth_url': auth_url,
            'message': 'Redirect user to this URL to authorize Google Calendar access'
        })

    except Exception as e:
        logger.error(f"Error initiating Google Calendar auth: {str(e)}")
        return Response(
            {'error': 'Failed to initiate authentication'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def google_calendar_callback(request):
    """
    Handle OAuth callback and store tokens
    """
    try:
        # Get authorization code from query parameters (GET) or request data (POST)
        code = request.GET.get('code') or request.data.get('code')
        state = request.GET.get('state') or request.data.get('state')

        if not code:
            return Response(
                {'error': 'Authorization code required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check for error in callback
        error = request.GET.get('error')
        if error:
            logger.error(f"OAuth error: {error}")

            # Check if this is a popup request (Referer indicates popup)
            referer = request.META.get('HTTP_REFERER', '')
            is_popup = 'google-oauth' in referer or request.GET.get('popup') == 'true'

            if is_popup:
                # Return HTML page that sends message to parent window
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Authentication Complete</title>
                    <script>
                        window.onload = function() {{
                            if (window.opener) {{
                                window.opener.postMessage({{
                                    type: 'GOOGLE_OAUTH_ERROR',
                                    error: '{error}'
                                }}, '*');
                            }}
                            window.close();
                        }};
                    </script>
                </head>
                <body>
                    <p>Authentication failed. Closing window...</p>
                </body>
                </html>
                """
                return Response(html_content, content_type='text/html')
            else:
                # Redirect back to frontend with OAuth error
                frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
                error_url = f"{frontend_url}/appointments?calendar_error=true&oauth_error={error}"
                return redirect(error_url)

        # Extract user ID from state parameter
        user_id = None
        if state and state.startswith('user_'):
            try:
                user_id = int(state.replace('user_', ''))
            except ValueError:
                logger.warning(f"Invalid state parameter: {state}")

        # Get the user
        try:
            if user_id:
                user = User.objects.get(id=user_id)
            else:
                # Fallback to first user if no state (for backward compatibility)
                user = User.objects.first()
                if not user:
                    return Response(
                        {'error': 'No users found in system'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Exchange code for tokens
        service = GoogleCalendarService()
        tokens = service.exchange_code_for_tokens(code)

        if not tokens:
            return Response(
                {'error': 'Failed to exchange code for tokens'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Store tokens in database
        token_obj, created = GoogleCalendarToken.objects.update_or_create(
            user=user,
            defaults={
                'access_token': tokens['access_token'],
                'refresh_token': tokens.get('refresh_token', ''),
                'token_expiry': now() + timedelta(seconds=tokens['expires_at'] - datetime.now().timestamp()),
                'calendar_id': 'primary',
                'is_active': True
            }
        )

        # Check if this is a popup request
        referer = request.META.get('HTTP_REFERER', '')
        is_popup = 'google-oauth' in referer or request.GET.get('popup') == 'true'

        if is_popup:
            # Return HTML page that sends success message to parent window
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Authentication Complete</title>
                <script>
                    window.onload = function() {{
                        if (window.opener) {{
                            window.opener.postMessage({{
                                type: 'GOOGLE_OAUTH_SUCCESS',
                                user_id: {user.id}
                            }}, '*');
                        }}
                        window.close();
                    }};
                </script>
            </head>
            <body>
                <p>Authentication successful! Closing window...</p>
            </body>
            </html>
            """
            return Response(html_content, content_type='text/html')
        else:
            # Redirect back to frontend with success
            frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
            success_url = f"{frontend_url}/appointments?calendar_connected=true&user_id={user.id}"
            return redirect(success_url)

    except Exception as e:
        logger.error(f"Error in Google Calendar callback: {str(e)}")

        # Check if this is a popup request
        referer = request.META.get('HTTP_REFERER', '')
        is_popup = 'google-oauth' in referer or request.GET.get('popup') == 'true'

        if is_popup:
            # Return HTML page that sends error message to parent window
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Authentication Failed</title>
                <script>
                    window.onload = function() {{
                        if (window.opener) {{
                            window.opener.postMessage({{
                                type: 'GOOGLE_OAUTH_ERROR',
                                error: '{str(e)[:100]}'
                            }}, '*');
                        }}
                        window.close();
                    }};
                </script>
            </head>
            <body>
                <p>Authentication failed. Closing window...</p>
            </body>
            </html>
            """
            return Response(html_content, content_type='text/html')
        else:
            # Redirect back to frontend with error
            frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
            error_url = f"{frontend_url}/appointments?calendar_error=true&error={str(e)[:100]}"
            return redirect(error_url)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_appointment_to_calendar(request):
    """
    Sync an appointment to Google Calendar
    """
    try:
        appointment_id = request.data.get('appointment_id')
        if not appointment_id:
            return Response(
                {'error': 'Appointment ID required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        appointment = Appointment.objects.get(id=appointment_id)

        # Check if user has Google Calendar integration
        try:
            token_obj = GoogleCalendarToken.objects.get(
                user=request.user,
                is_active=True
            )
        except GoogleCalendarToken.DoesNotExist:
            return Response(
                {'error': 'Google Calendar not connected. Please authenticate first.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        service = GoogleCalendarService()
        event_id = service.create_appointment_event(appointment, token_obj)

        if event_id:
            # Store the event ID in appointment (you might need to add this field)
            # appointment.google_event_id = event_id
            # appointment.save()

            return Response({
                'message': 'Appointment synced to Google Calendar',
                'event_id': event_id
            })
        else:
            return Response(
                {'error': 'Failed to sync appointment'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    except Appointment.DoesNotExist:
        return Response(
            {'error': 'Appointment not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error syncing appointment to calendar: {str(e)}")
        return Response(
            {'error': 'Failed to sync appointment'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_calendar_event(request):
    """
    Update an existing calendar event
    """
    try:
        appointment_id = request.data.get('appointment_id')
        if not appointment_id:
            return Response(
                {'error': 'Appointment ID required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        appointment = Appointment.objects.get(id=appointment_id)

        # Check if user has Google Calendar integration
        try:
            token_obj = GoogleCalendarToken.objects.get(
                user=request.user,
                is_active=True
            )
        except GoogleCalendarToken.DoesNotExist:
            return Response(
                {'error': 'Google Calendar not connected'},
                status=status.HTTP_400_BAD_REQUEST
            )

        service = GoogleCalendarService()
        success = service.update_appointment_event(appointment, token_obj)

        if success:
            return Response({
                'message': 'Calendar event updated successfully'
            })
        else:
            return Response(
                {'error': 'Failed to update calendar event'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    except Appointment.DoesNotExist:
        return Response(
            {'error': 'Appointment not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error updating calendar event: {str(e)}")
        return Response(
            {'error': 'Failed to update calendar event'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_calendar_event(request):
    """
    Delete a calendar event
    """
    try:
        appointment_id = request.data.get('appointment_id')
        if not appointment_id:
            return Response(
                {'error': 'Appointment ID required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        appointment = Appointment.objects.get(id=appointment_id)

        # Check if user has Google Calendar integration
        try:
            token_obj = GoogleCalendarToken.objects.get(
                user=request.user,
                is_active=True
            )
        except GoogleCalendarToken.DoesNotExist:
            return Response(
                {'error': 'Google Calendar not connected'},
                status=status.HTTP_400_BAD_REQUEST
            )

        service = GoogleCalendarService()
        success = service.delete_appointment_event(appointment, token_obj)

        if success:
            return Response({
                'message': 'Calendar event deleted successfully'
            })
        else:
            return Response(
                {'error': 'Failed to delete calendar event'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    except Appointment.DoesNotExist:
        return Response(
            {'error': 'Appointment not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error deleting calendar event: {str(e)}")
        return Response(
            {'error': 'Failed to delete calendar event'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_calendar_events(request):
    """
    Get calendar events for a date range
    """
    try:
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if not start_date or not end_date:
            return Response(
                {'error': 'Start date and end date required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if user has Google Calendar integration
        try:
            token_obj = GoogleCalendarToken.objects.get(
                user=request.user,
                is_active=True
            )
        except GoogleCalendarToken.DoesNotExist:
            return Response(
                {'error': 'Google Calendar not connected'},
                status=status.HTTP_400_BAD_REQUEST
            )

        service = GoogleCalendarService()
        events = service.get_calendar_events(token_obj, start_date, end_date)

        return Response({
            'events': events
        })

    except Exception as e:
        logger.error(f"Error getting calendar events: {str(e)}")
        return Response(
            {'error': 'Failed to get calendar events'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_calendar_connection(request):
    """
    Check if Google Calendar is connected and working
    """
    try:
        token_obj = GoogleCalendarToken.objects.filter(
            user=request.user,
            is_active=True
        ).first()

        if not token_obj:
            return Response({
                'connected': False,
                'message': 'Google Calendar not connected'
            })

        service = GoogleCalendarService()
        is_connected = service.test_connection(token_obj)

        return Response({
            'connected': is_connected,
            'calendar_id': token_obj.calendar_id if is_connected else None
        })

    except Exception as e:
        logger.error(f"Error checking calendar connection: {str(e)}")
        return Response(
            {'error': 'Failed to check connection'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_calendar_connection(request):
    """
    Check if user has Google Calendar connected
    """
    try:
        # Check if user has Google Calendar tokens
        token_obj = GoogleCalendarToken.objects.filter(
            user=request.user,
            is_active=True
        ).first()

        if not token_obj:
            return Response({
                'connected': False,
                'message': 'No Google Calendar connection found'
            })

        # Check if token is expired
        if token_obj.token_expiry and token_obj.token_expiry < now():
            # Try to refresh the token
            service = GoogleCalendarService()
            refreshed = service.refresh_access_token(token_obj)

            if not refreshed:
                return Response({
                    'connected': False,
                    'message': 'Google Calendar token expired and could not be refreshed'
                })

        return Response({
            'connected': True,
            'message': 'Google Calendar is connected',
            'email': getattr(token_obj, 'calendar_email', None) or 'Connected'
        })

    except Exception as e:
        logger.error(f"Error checking calendar connection: {str(e)}")
        return Response(
            {'error': 'Failed to check connection'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

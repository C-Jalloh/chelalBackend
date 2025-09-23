from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.conf import settings
import json
from .google_calendar_service import google_calendar_service
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def google_calendar_auth(request):
    """Handle Google Calendar OAuth callback and store credentials"""
    try:
        # This would handle the OAuth callback from Google
        # In a real implementation, you'd exchange the authorization code for tokens
        auth_code = request.POST.get('code')

        if not auth_code:
            return JsonResponse({'error': 'Authorization code required'}, status=400)

        # Exchange code for tokens and store them
        # This is a simplified example - you'd use the Google OAuth library

        return JsonResponse({'message': 'Google Calendar connected successfully'})

    except Exception as e:
        logger.error(f"Google Calendar auth error: {e}")
        return JsonResponse({'error': 'Failed to connect Google Calendar'}, status=500)

@login_required
@require_http_methods(["POST"])
def sync_appointment_to_calendar(request):
    """Sync an appointment to Google Calendar"""
    try:
        data = json.loads(request.body)
        appointment_data = data.get('appointment')

        if not appointment_data:
            return JsonResponse({'error': 'Appointment data required'}, status=400)

        event_id = google_calendar_service.create_appointment_event(
            request.user,
            appointment_data
        )

        if event_id:
            return JsonResponse({
                'message': 'Appointment synced to Google Calendar',
                'event_id': event_id
            })
        else:
            return JsonResponse({'error': 'Failed to sync appointment'}, status=500)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Sync appointment error: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)

@login_required
@require_http_methods(["PUT"])
def update_calendar_event(request, event_id):
    """Update an existing Google Calendar event"""
    try:
        data = json.loads(request.body)
        appointment_data = data.get('appointment')

        if not appointment_data:
            return JsonResponse({'error': 'Appointment data required'}, status=400)

        success = google_calendar_service.update_appointment_event(
            request.user,
            event_id,
            appointment_data
        )

        if success:
            return JsonResponse({'message': 'Calendar event updated successfully'})
        else:
            return JsonResponse({'error': 'Failed to update calendar event'}, status=500)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Update calendar event error: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)

@login_required
@require_http_methods(["DELETE"])
def delete_calendar_event(request, event_id):
    """Delete a Google Calendar event"""
    try:
        success = google_calendar_service.delete_appointment_event(
            request.user,
            event_id
        )

        if success:
            return JsonResponse({'message': 'Calendar event deleted successfully'})
        else:
            return JsonResponse({'error': 'Failed to delete calendar event'}, status=500)

    except Exception as e:
        logger.error(f"Delete calendar event error: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)

@login_required
@require_http_methods(["GET"])
def get_calendar_events(request):
    """Get Google Calendar events for a date range"""
    try:
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')

        if not start_date_str or not end_date_str:
            return JsonResponse({'error': 'Start and end dates required'}, status=400)

        from datetime import datetime
        start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))

        events = google_calendar_service.get_calendar_events(
            request.user,
            start_date,
            end_date
        )

        return JsonResponse({'events': events})

    except ValueError as e:
        return JsonResponse({'error': 'Invalid date format'}, status=400)
    except Exception as e:
        logger.error(f"Get calendar events error: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)

@login_required
@require_http_methods(["GET"])
def check_calendar_connection(request):
    """Check if user has Google Calendar connected"""
    try:
        credentials = google_calendar_service.get_credentials(request.user)
        is_connected = credentials is not None and not credentials.expired

        return JsonResponse({
            'connected': is_connected,
            'email': credentials.id_token.get('email') if credentials and is_connected else None
        })

    except Exception as e:
        logger.error(f"Check calendar connection error: {e}")
        return JsonResponse({'connected': False})

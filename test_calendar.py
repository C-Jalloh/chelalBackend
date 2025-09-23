#!/usr/bin/env python3
"""
Test script for Google Calendar integration
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append('/home/c_jalloh/Documents/School/Second Semester/ITCA Week/code/chelalBackend')

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Backend.settings')
django.setup()

from core.models import GoogleCalendarToken, User
from core.google_calendar_service import GoogleCalendarService

def test_google_calendar_integration():
    print("🔍 Testing Google Calendar Integration")
    print("=" * 50)

    # Check if tokens exist
    tokens = GoogleCalendarToken.objects.all()
    print(f"📊 Found {tokens.count()} Google Calendar tokens in database")

    if tokens.count() == 0:
        print("❌ No Google Calendar tokens found")
        return

    for token in tokens:
        print(f"\n👤 User: {token.user.username}")
        print(f"📅 Calendar ID: {token.calendar_id}")
        print(f"✅ Active: {token.is_active}")
        print(f"⏰ Expires: {token.token_expiry}")

        # Test connection
        print("🔗 Testing connection...")
        service = GoogleCalendarService()
        is_connected = service.test_connection(token)

        if is_connected:
            print("✅ Connection successful!")
        else:
            print("❌ Connection failed")

    print("\n" + "=" * 50)
    print("🎉 Google Calendar integration test completed!")

if __name__ == "__main__":
    test_google_calendar_integration()

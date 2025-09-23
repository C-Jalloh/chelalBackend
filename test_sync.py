#!/usr/bin/env python3
import requests
import json

# Backend URL
BASE_URL = 'http://127.0.0.1:8000/api'

def get_auth_token():
    """Get authentication token"""
    login_data = {
        'username': 'cjalloh',  # Use the specified username
        'password': 'password123'
    }

    response = requests.post(f'{BASE_URL}/auth/', json=login_data)
    if response.status_code == 200:
        return response.json()['access']
    else:
        print(f'Login failed: {response.status_code} - {response.text}')
        return None

def test_sync_endpoint(token, appointment_id):
    """Test the Google Calendar sync endpoint"""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    data = {
        'appointment_id': appointment_id
    }

    response = requests.post(
        f'{BASE_URL}/google-calendar/sync/',
        json=data,
        headers=headers
    )

    print(f'Sync response: {response.status_code}')
    print(f'Response: {response.text}')
    return response

def test_connection_endpoint(token):
    """Test the Google Calendar connection check endpoint"""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    response = requests.get(
        f'{BASE_URL}/google-calendar/connection/',
        headers=headers
    )

    print(f'Connection check response: {response.status_code}')
    print(f'Response: {response.text}')
    return response

def main():
    print('Testing Google Calendar endpoints...')

    # Get auth token
    token = get_auth_token()
    if not token:
        print('Failed to authenticate')
        return

    print('Authentication successful')

    # Test connection check
    print('\n--- Testing Connection Check ---')
    conn_response = test_connection_endpoint(token)

    # Test sync
    print('\n--- Testing Sync Endpoint ---')
    sync_response = test_sync_endpoint(token, 1)

    print('\n--- Summary ---')
    if conn_response.status_code == 200:
        print('✅ Connection check endpoint working')
    else:
        print('❌ Connection check endpoint failed')

    if sync_response.status_code == 200 and 'event_id' in sync_response.text:
        print('✅ Sync endpoint working correctly - appointment synced!')
    elif sync_response.status_code == 400 and 'not connected' in sync_response.text.lower():
        print('❌ Sync endpoint requires Google Calendar authentication')
    else:
        print('❌ Sync endpoint not working as expected')

if __name__ == '__main__':
    main()
